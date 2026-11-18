from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional

class ProfileForm(FlaskForm):
    name=StringField('Full name',validators=[DataRequired(),Length(min=2,max=120)])
    email=StringField('Email',validators=[DataRequired(),Email(),Length(max=255)])
    phone=StringField('Phone',validators=[Optional(),Length(max=30)])
    submit=SubmitField('Save profile')
