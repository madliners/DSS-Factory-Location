from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, make_response, abort
import os
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from io import BytesIO
import base64
from models import db, Criteria, Alternative, Analysis, AlternativeCriteriaValue, User
from forms import CriteriaForm, AlternativeForm, AnalysisForm
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import helpers
from helpers import CRITERIA_OPTION_LABELS, role_required
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = '123'  # Ganti dengan kunci rahasia yang kuat
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///saw_dss.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route login
@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login succes!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Wrong Username or password', 'danger')
    return render_template('login.html')

# Route logout
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('you have logged out.', 'info')
    return redirect(url_for('login'))

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/dashboard')
@login_required
@role_required('admin', 'chief_strategic_officer', 'strategic_officer_manager', 'strategic_officer_staff')
def index():
    analyses = Analysis.query.order_by(Analysis.created_at.desc()).limit(5).all()
    current_time = datetime.now()
    return render_template('index.html', analyses=analyses, current_time=current_time)

@app.route('/criteria', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'chief_strategic_officer', 'strategic_officer_manager')
def manage_criteria():
    form = CriteriaForm()
    if form.validate_on_submit():
        total_existing_weight = db.session.query(db.func.sum(Criteria.weight)).scalar() or 0
        proposed_total = total_existing_weight + form.weight.data
        if proposed_total > 1.0:
            flash(f'Total bobot saat ini adalah {total_existing_weight:.2f}. '
                  f'Tidak bisa menambahkan bobot {form.weight.data:.2f} karena melebihi 1.0.', 'danger')
            return redirect(url_for('manage_criteria'))
        criteria = Criteria(
            name=form.name.data,
            description=form.description.data,
            weight=form.weight.data,
            is_benefit=form.is_benefit.data
        )
        db.session.add(criteria)
        db.session.commit()
        flash('Criteria added successfully!', 'success')
        return redirect(url_for('manage_criteria'))
    criteria_list = Criteria.query.all()
    return render_template('criteria.html', form=form, criteria_list=criteria_list)

@app.route('/criteria/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'chief_strategic_officer', 'strategic_officer_manager')
def edit_criteria(id):
    criteria = Criteria.query.get_or_404(id)
    form = CriteriaForm(obj=criteria)
    if form.validate_on_submit():
        criteria.name = form.name.data
        criteria.description = form.description.data
        criteria.weight = form.weight.data
        criteria.is_benefit = form.is_benefit.data
        db.session.commit()
        flash('Criteria updated successfully!', 'success')
        return redirect(url_for('manage_criteria'))
    return render_template('edit_criteria.html', form=form, criteria=criteria)

@app.route('/criteria/delete/<int:id>')
@login_required
@role_required('admin', 'chief_strategic_officer', 'strategic_officer_manager')
def delete_criteria(id):
    criteria = Criteria.query.get_or_404(id)
    db.session.delete(criteria)
    db.session.commit()
    flash('Criteria deleted successfully!', 'success')
    return redirect(url_for('manage_criteria'))

@app.route('/alternatives', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'chief_strategic_officer','strategic_officer_manager', 'strategic_officer_staff')
def manage_alternatives():
    form = AlternativeForm()
    criteria_list = Criteria.query.all()
    if form.validate_on_submit():
        alternative = Alternative(
            name=form.name.data,
            description=form.description.data,
            location=form.location.data
        )
        db.session.add(alternative)
        db.session.commit()
        for criteria in criteria_list:
            value = request.form.get(f'criteria_{criteria.id}')
            if value:
                alternative.set_criteria_value(criteria.id, float(value))
        flash('Alternative added successfully!', 'success')
        return redirect(url_for('manage_alternatives'))
    alternatives = Alternative.query.all()
    return render_template(
        'alternatives.html',
        form=form,
        alternatives=alternatives,
        criteria_list=criteria_list,
        CRITERIA_OPTION_LABELS=CRITERIA_OPTION_LABELS
    )

@app.route('/alternatives/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'strategic_officer_manager', 'strategic_officer_staff')
def edit_alternative(id):
    alternative = Alternative.query.get_or_404(id)
    criteria_list = Criteria.query.all()
    if request.method == 'POST':
        alternative.name = request.form['name']
        alternative.location = request.form['location']
        db.session.commit()
        for criteria in criteria_list:
            val = request.form.get(f'criteria_{criteria.id}')
            existing_value = AlternativeCriteriaValue.query.filter_by(
                alternative_id=alternative.id,
                criteria_id=criteria.id
            ).first()
            if existing_value:
                existing_value.value = val
            else:
                db.session.add(AlternativeCriteriaValue(
                    alternative_id=alternative.id,
                    criteria_id=criteria.id,
                    value=val
                ))
        db.session.commit()
        flash('Alternative updated!', 'success')
        return redirect(url_for('manage_alternatives'))
    criteria_values = {
        val.criteria_id: val.value
        for val in AlternativeCriteriaValue.query.filter_by(alternative_id=id).all()
    }
    return render_template('edit_alternative.html',
                           alternative=alternative,
                           criteria_list=criteria_list,
                           criteria_values=criteria_values)

@app.route('/alternatives/delete/<int:id>')
@login_required
@role_required('admin', 'strategic_officer_manager', 'strategic_officer_staff')
def delete_alternative(id):
    alternative = Alternative.query.get_or_404(id)
    db.session.delete(alternative)
    db.session.commit()
    flash('Alternative deleted successfully!', 'success')
    return redirect(url_for('manage_alternatives'))

@app.route('/analyze', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'strategic_officer_manager')
def analyze():
    form = AnalysisForm()
    if form.validate_on_submit():
        criteria_list = Criteria.query.all()
        alternatives = Alternative.query.all()
        if not criteria_list or not alternatives:
            flash('You need to add criteria and alternatives before analysis', 'warning')
            return redirect(url_for('analyze'))
        for criteria in criteria_list:
            new_weight = request.form.get(f'weight_{criteria.id}')
            if new_weight:
                criteria.weight = float(new_weight)
        db.session.commit()
        decision_matrix, normalized_matrix, weighted_matrix, final_scores = helpers.calculate_saw(
            criteria_list, alternatives
        )
        ranked_alternatives = []
        for i, alt in enumerate(alternatives):
            ranked_alternatives.append({
                'id': alt.id,
                'name': alt.name,
                'location': alt.location,
                'score': final_scores[i],
                'rank': 0
            })
        ranked_alternatives.sort(key=lambda x: x['score'], reverse=True)
        for i, alt in enumerate(ranked_alternatives):
            alt['rank'] = i + 1
        analysis = Analysis(
            name=form.name.data,
            description=form.description.data,
            created_at=datetime.now()
        )
        db.session.add(analysis)
        db.session.commit()
        plt.figure(figsize=(10, 6))
        bars = plt.bar(
            [alt['name'] for alt in ranked_alternatives],
            [alt['score'] for alt in ranked_alternatives]
        )
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2.,
                height + 0.01,
                f'{height:.3f}',
                ha='center', va='bottom',
                fontweight='bold'
            )
        plt.xlabel('Alternatives')
        plt.ylabel('Final Score')
        plt.title('SAW Method Results')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        analysis.set_chart(buf.read())
        db.session.commit()
        analysis.set_calculation_details({
            'decision_matrix': decision_matrix.tolist(),
            'normalized_matrix': normalized_matrix.tolist(),
            'weighted_matrix': weighted_matrix.tolist(),
            'final_scores': final_scores.tolist(),
            'ranked_alternatives': ranked_alternatives
        })
        db.session.commit()
        return redirect(url_for('view_analysis', id=analysis.id))
    criteria_list = Criteria.query.all()
    alternatives = Alternative.query.all()
    return render_template('analyze.html', form=form, criteria_list=criteria_list, alternatives=alternatives)

@app.route('/analysis')
@login_required
@role_required('admin', 'chief_strategic_officer', 'strategic_officer_manager', 'strategic_officer_staff')
def analysis_list():
    analyses = Analysis.query.order_by(Analysis.created_at.desc()).all()
    return render_template('analysis_list.html', analyses=analyses)

@app.route('/analysis/<int:id>')
@login_required
@role_required('admin', 'chief_strategic_officer', 'strategic_officer_manager', 'strategic_officer_staff')
def view_analysis(id):
    analysis = Analysis.query.get_or_404(id)
    details = analysis.get_calculation_details()
    chart_data = None
    if analysis.chart:
        chart_data = base64.b64encode(analysis.chart).decode('utf-8')
    current_time = datetime.now()
    return render_template(
        'view_analysis.html',
        analysis=analysis,
        details=details,
        chart_data=chart_data,
        current_time=current_time
    )

@app.route('/analysis/export/<int:id>')
@login_required
@role_required('admin', 'chief_strategic_officer', 'strategic_officer_manager', 'strategic_officer_staff')
def export_analysis(id):
    analysis = Analysis.query.get_or_404(id)
    details = analysis.get_calculation_details()
    pdf_data = helpers.generate_pdf_report(analysis, details)
    return send_file(
        BytesIO(pdf_data),
        download_name=f'analysis_{analysis.id}.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )

@app.context_processor
def utility_processor():
    def format_date(date):
        return date.strftime('%Y-%m-%d %H:%M')
    def get_criteria_value(alternative_id, criteria_id):
        value = Alternative.get_criteria_value(alternative_id, criteria_id)
        return value if value is not None else ''
    return dict(
        format_date=format_date,
        get_criteria_value=get_criteria_value
    )

@app.template_filter('format_rupiah')
def format_rupiah(value):
    try:
        return f"Rp {value:,.0f}".replace(",", ".")
    except:
        return value

if __name__ == '__main__':
    app.run(debug=True)