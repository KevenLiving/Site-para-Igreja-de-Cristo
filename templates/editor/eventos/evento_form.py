from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class Event_(FlaskForm):
    titulo = StringField('Título', validators=[
        DataRequired(message='O título é obrigatório'),
        Length(max=200)
    ])

    descricao = TextAreaField('Descrição', validators=[
        Optional()
    ])

    banner = FileField('Banner', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], message='Envie apenas imagens (jpg, jpeg, png)')
    ])

    local = StringField('Local', validators=[
        Optional(),
        Length(max=150)
    ])

    data = DateField('Data do Evento', validators=[
        DataRequired(message='A data do evento é obrigatória')
    ])

    hora = TimeField('Hora do Evento', validators=[
        Optional()
    ])

    inscricao_necessaria = BooleanField('Requer inscrição')
    destaque = BooleanField('Destacar evento')
    publicar = BooleanField('Publicar evento')

    submit = SubmitField('Cadastrar')