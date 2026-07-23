from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, URL, NoneOf, Optional


class SocialLink_(FlaskForm):
    plataforma = SelectField(
        'Plataforma',
        choices=[('default', 'Selecione uma plataforma'),
                 ('instagram', 'Instagram'),
                 ('facebook', 'Facebook'),
                 ('youtube', 'YouTube'),
                 ('whatsapp', 'WhatsApp'),
                 ('tiktok', 'TikTok'),
                 ('spotify', 'Spotify'),
                 ('telegram', 'Telegram'),
                 ('site', 'Site')
                 ],
                 default='default',
                 validators=[
                     NoneOf(['default'], message='Selecione uma plataforma')
                 ]
    )

    url = StringField('URL', validators=[
        DataRequired(message='A URL é obrigatória'),
        URL(message='Informe uma URL válida'),
        Length(max=255)
    ])

    ordem = IntegerField('Ordem de Exibição', validators=[
        Optional()
    ], default=0)

    ativo = BooleanField('Link ativo', default=True)

    submit = SubmitField('Cadastrar')