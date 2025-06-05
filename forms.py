from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms import FieldList, FormField, HiddenField

class CriteriaOptionForm(FlaskForm):
    option_label = StringField('Option Label', validators=[DataRequired(), Length(max=100)])
    option_value = StringField('Option Value', validators=[DataRequired()])

class CriteriaForm(FlaskForm):
    name = StringField('Criteria Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    weight = FloatField('Weight', validators=[DataRequired(), NumberRange(min=0.0, max=10)], default=1.0)
    is_benefit = BooleanField('Is Benefit Criteria', default=True)
    use_dropdown = BooleanField('Use Dropdown Input?')
    option_labels = FieldList(StringField('Label'), min_entries=3)
    option_values = FieldList(StringField('Value'), min_entries=3)
    submit = SubmitField('Add Criteria')

class AlternativeForm(FlaskForm):
    name = StringField('Alternative Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    location = StringField('Location', validators=[DataRequired(), Length(min=2, max=200)])
    submit = SubmitField('Add Alternative')

class AnalysisForm(FlaskForm):
    name = StringField('Analysis Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Run Analysis')