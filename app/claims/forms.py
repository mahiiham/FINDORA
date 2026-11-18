from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
class ClaimForm(FlaskForm):
    verification_response=TextAreaField('Describe private details that prove ownership',validators=[DataRequired(),Length(min=10,max=3000)]); submit=SubmitField('Submit claim')
class ReviewForm(FlaskForm):
    reason=TextAreaField('Review reason',validators=[DataRequired(),Length(min=3,max=2000)]); submit=SubmitField('Submit decision')
