from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class FlagForm(FlaskForm):
    reason=StringField('Reason for flagging',validators=[DataRequired(),Length(min=5,max=255)])
    submit=SubmitField('Flag report')
