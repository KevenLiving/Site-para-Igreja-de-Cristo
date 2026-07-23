from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Email, NoneOf


class PrayerManager_(FlaskForm):

    status = SelectField(
        'Status',
        choices=[('pendente', 'Pendente'),
                 ('orando', 'Orando'),
                 ('respondida', 'Respondida')
                 ],
                 default='normal'
    )

