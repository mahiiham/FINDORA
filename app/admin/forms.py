from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, FloatField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class MasterDataForm(FlaskForm):
    name=StringField('Name',validators=[DataRequired(),Length(min=2,max=120)])
    description=TextAreaField('Description',validators=[Optional(),Length(max=1000)])
    submit=SubmitField('Save')

class OrganizationForm(MasterDataForm):
    type=StringField('Organization type',validators=[Optional(),Length(max=50)])

class LocationForm(MasterDataForm):
    organization_id=SelectField('Organization',coerce=int,validators=[Optional()])
    latitude=FloatField('Latitude (for the smart location map)',validators=[Optional(),NumberRange(min=-90,max=90)])
    longitude=FloatField('Longitude (for the smart location map)',validators=[Optional(),NumberRange(min=-180,max=180)])
