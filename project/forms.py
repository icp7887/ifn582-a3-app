from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import InputRequired, Length

class ItemForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(max=100)])
    description = TextAreaField('Description')
    submit = SubmitField('Add')
