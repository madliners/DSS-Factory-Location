from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):  # ← Tambahkan UserMixin di sini
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Criteria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    weight = db.Column(db.Float, default=1.0)
    is_benefit = db.Column(db.Boolean, default=True)  # True if higher is better, False if lower is better
    
    def __repr__(self):
        return f'<Criteria {self.name}>'

class AlternativeCriteriaValue(db.Model):
    alternative_id = db.Column(db.Integer, db.ForeignKey('alternative.id'), primary_key=True)
    criteria_id = db.Column(db.Integer, db.ForeignKey('criteria.id'), primary_key=True)
    value = db.Column(db.Float, nullable=False)
    
    alternative = db.relationship('Alternative', back_populates='criteria_values')
    criteria = db.relationship('Criteria')


class Alternative(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    criteria_values = db.relationship('AlternativeCriteriaValue', back_populates='alternative', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Alternative {self.name}>'
    
    def set_criteria_value(self, criteria_id, value):
        # Check if value already exists
        existing = AlternativeCriteriaValue.query.filter_by(
            alternative_id=self.id, criteria_id=criteria_id
        ).first()
        
        if existing:
            existing.value = value
        else:
            new_value = AlternativeCriteriaValue(
                alternative_id=self.id,
                criteria_id=criteria_id,
                value=value
            )
            db.session.add(new_value)
        
        db.session.commit()
    
    @staticmethod
    def get_criteria_value(alternative_id, criteria_id):
        value = AlternativeCriteriaValue.query.filter_by(
            alternative_id=alternative_id, criteria_id=criteria_id
        ).first()
        
        return value.value if value else None
    
class CriteriaOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    criteria_id = db.Column(db.Integer, db.ForeignKey('criteria.id'), nullable=False)
    label = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Integer, nullable=False)

    criteria = db.relationship('Criteria', backref=db.backref('options', lazy=True))


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    calculation_details = db.Column(db.Text, nullable=True)
    chart = db.Column(db.LargeBinary, nullable=True)
    
    def __repr__(self):
        return f'<Analysis {self.name}>'
    
    def set_calculation_details(self, details):
        self.calculation_details = json.dumps(details)
    
    def get_calculation_details(self):
        return json.loads(self.calculation_details) if self.calculation_details else {}
    
    def set_chart(self, chart_data):
        self.chart = chart_data
    