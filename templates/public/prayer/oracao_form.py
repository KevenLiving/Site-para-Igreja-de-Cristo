from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Email, NoneOf


class PrayerRequest_(FlaskForm):
    
    nome = StringField('Nome', validators=[
        Optional(),
        Length(max=150)
    ])

    pedido = TextAreaField('Pedido de Oração', validators=[
        DataRequired(message='O pedido de oração é obrigatório')
    ])

    categoria = SelectField(
        'Categoria',
        choices=[('default', 'Selecione uma categoria'),
                 ('saude', 'Saúde'),
                 ('familia', 'Família'),
                 ('trabalho', 'Trabalho'),
                 ('financeiro', 'Financeiro'),
                 ('espiritual', 'Espiritual'),
                 ('outro', 'Outro')
                 ],
                 default='default',
                 validators=[
                     NoneOf(['default'], message='Selecione uma categoria')
                 ]
    )

    prioridade = SelectField(
        'Prioridade',
        choices=[('normal', 'Normal'),
                 ('urgent', 'Urgente')
                 ],
                 default='normal'
    )

    anonimo = BooleanField('Enviar como anônimo')

    contato_email = StringField('E-mail para contato', validators=[
        Optional(),
        Email(message='Informe um e-mail válido'),
        Length(max=150)
    ])

    contato_telefone = StringField('Telefone para contato', validators=[
        Optional(),
        Length(max=30)
    ])

    submit = SubmitField('Enviar Pedido')