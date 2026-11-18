from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp

class RegisterForm(FlaskForm):
    name=StringField('Full name',validators=[DataRequired(),Length(min=2,max=120)])
    email=StringField('Email',validators=[DataRequired(),Email(),Length(max=255)])
    phone=StringField('Phone',validators=[Optional(),Length(max=30)])
    organization_id=SelectField('Organization',coerce=int,validators=[Optional()])
    password=PasswordField('Password',validators=[DataRequired(),Length(min=8),Regexp(r'^(?=.*[A-Za-z])(?=.*\d).+$',message='Use at least one letter and one number.')])
    confirm=PasswordField('Confirm password',validators=[DataRequired(),EqualTo('password')])
    submit=SubmitField('Create account')
class LoginForm(FlaskForm):
    email=StringField('Email',validators=[DataRequired(),Length(max=255)])
    password=PasswordField('Password',validators=[DataRequired()])
    remember=BooleanField('Remember me')
    submit=SubmitField('Login')
