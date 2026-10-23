from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed

from wtforms import StringField, PasswordField, SelectField, SubmitField, TextAreaField, DecimalField, DateField, BooleanField
from wtforms.validators import InputRequired, Length, EqualTo, Regexp, NumberRange, Optional, ValidationError

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


IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'gif', 'webp']
CATEGORIES = ['Arts', 'Community', 'Education', 'Health', 'Technology', 'Sports', 'Music']


class CampaignForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired(), Length(min=3, max=150)])
    description = TextAreaField('Description', validators=[InputRequired(), Length(min=10, max=2000)])
    goal = DecimalField('Fundraising Goal ($)', places=2, validators=[InputRequired(), NumberRange(min=1, max=10000000)])
    category = SelectField('Category', choices=[(c, c) for c in CATEGORIES])
    start_date = DateField('Start Date', validators=[InputRequired()])
    end_date = DateField('End Date', validators=[InputRequired()])
    image_url = StringField('Image URL (optional)', validators=[Optional(), Length(max=255),
                                                               Regexp(r'^https?://\S+$', message='Enter a full link starting with http:// or https://')])
    image_file = FileField('Or upload an image', validators=[FileAllowed(IMAGE_TYPES, 'Images only')])
    submit = SubmitField('Save')

    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data <= self.start_date.data:
            raise ValidationError('End date must be after the start date.')


class PostForm(FlaskForm):
    title = StringField('Update Title', validators=[InputRequired(), Length(min=3, max=150)])
    content = TextAreaField('Update Content', validators=[InputRequired(), Length(max=5000)])
    image = FileField('Upload Image (optional)', validators=[FileAllowed(IMAGE_TYPES, 'Images only')])
    remove_image = BooleanField('Remove current image')
    submit = SubmitField('Post Update')


class DonationForm(FlaskForm):
    donor_name = StringField('Full Name', validators=[InputRequired(), Length(max=100)])
    email = StringField('Email', validators=[InputRequired(), Length(max=100),
                                             Regexp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', message='Enter a valid email address')])
    address = StringField('Address', validators=[InputRequired(), Length(min=5, max=255)])
    tier = SelectField('Tier', coerce=int, validators=[Optional()])
    amount = DecimalField('Amount ($)', places=2, validators=[InputRequired(), NumberRange(min=1, max=100000)])
    payment_method = SelectField('Payment Method', choices=[('Mastercard', 'Mastercard'), ('Visa', 'Visa'),
                                                            ('Apple Pay', 'Apple Pay'), ('PayPal', 'PayPal')])
    message = TextAreaField('Message', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Donate')

    def set_tiers(self, tiers):
        self.tier_prices = {t['id']: t['price'] for t in tiers}
        self.tier.choices = [(0, 'One-off donation (no tier)')] + [(t['id'], f"{t['tierName']} (${t['price']:,.0f}/month)") for t in tiers]

    def validate_amount(self, field):
        price = getattr(self, 'tier_prices', {}).get(self.tier.data)
        if price is not None and field.data is not None and field.data < price:
            raise ValidationError(f'That tier costs ${price:,.2f}, please donate at least that much.')

class AdminUserForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[InputRequired(), Length(max=100),
                                             Regexp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', message='Enter a valid email address')])
    verified = BooleanField('Verified creator')
    submit = SubmitField('Save changes')
