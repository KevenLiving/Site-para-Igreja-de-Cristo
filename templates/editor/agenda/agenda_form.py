from wtforms.fields import TimeField
import re
# Formulário de login mais seguro e prático
from wtforms import StringField, SubmitField, ValidationError, IntegerField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NoneOf
from flask_wtf import FlaskForm

# Formulário para cadastrar estudo biblico 

class Weekly_Schedule(FlaskForm):

    titulo = StringField('Título', validators=[
        Length(max=200, message='No máximo 200 caracteres'),
        DataRequired(message='Título é obrigatório')
    ])

    descricao = StringField('Descrição', validators=[
        DataRequired(message='Descrição é obrigatória')
    ])

    local = StringField('Local', validators=[
        DataRequired(message='Local é obrigatorio')
    ])

    dia = SelectField(
        'Dia',
        choices=[('default','Selecione um dia da semana'),
                 ('Segunda-feira', 'Segunda'),
                 ('Terça-feira', 'Terça'),
                 ('Quarta-feira','Quarta'),
                 ('Quinta-feira','Quinta'),
                 ('Sexta-feira','Sexta'),
                 ('Sábado','Sábado'),
                 ('Domingo','Domingo')
                 ],
                 default='default',
                 validators=[
                     NoneOf(['default'], message='Selecione um dia da semana')
                 ]
    )

    hora = TimeField(
        'Horário de inicio',
        format="%H:%M",
        validators=[
            DataRequired(message='Horário é obrigatório')
        ]
        )

    activate = BooleanField('Ativar evento na agenda')

    submit = SubmitField('Salvar')

