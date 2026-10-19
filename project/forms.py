from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import InputRequired, Length, EqualTo, Regexp

class LoginForm(FlaskForm):
    identifier = StringField('Username or email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Log in')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=50)])
    #simple pattern check so we don't need the email_validator package
    email = StringField('Email address', validators=[InputRequired(), Length(max=100),
                                                     Regexp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', message='Enter a valid email address')])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, message='Use at least 8 characters')])
    confirm = PasswordField('Confirm password', validators=[InputRequired(), EqualTo('password', message='Passwords must match')])
    #Admin accounts can't be self-registered, only Supporters (customer table) and Creators
    role = SelectField('I want to', choices=[('Customer', 'Support creators'), ('Creator', 'Raise money as a creator')])
    submit = SubmitField('Create account')
