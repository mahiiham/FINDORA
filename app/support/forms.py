from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class TicketForm(FlaskForm):
    kind = SelectField('What is this about?', choices=[
        ('QUESTION', 'A question for the admin'),
        ('DIRECT_REPORT', 'Direct report (item handed over / urgent issue)'),
        ('MATCH_QUERY', 'Why was my report not matched?'),
    ])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=3, max=160)])
    item_id = SelectField('Related report (optional)', coerce=int, validators=[])
    body = TextAreaField('Message', validators=[DataRequired(), Length(min=1, max=2000)])
    submit = SubmitField('Send to admin')


class ReplyForm(FlaskForm):
    body = TextAreaField('Reply', validators=[DataRequired(), Length(min=1, max=2000)])
    submit = SubmitField('Send')


class AdminContactForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(min=3, max=160)])
    body = TextAreaField('Message to the user', validators=[DataRequired(), Length(min=1, max=2000)])
    submit = SubmitField('Send message')
