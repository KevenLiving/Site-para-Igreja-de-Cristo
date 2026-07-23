from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Email


class Department_(FlaskForm):
    nome = StringField('Nome do Departamento', validators=[
        DataRequired(message='O nome é obrigatório'),
        Length(max=150)
    ])

    descricao = TextAreaField('Descrição', validators=[
        Optional()
    ])

    lider_nome = StringField('Nome do Líder', validators=[
        Optional(),
        Length(max=150)
    ])

    lider_foto = FileField('Foto do Líder', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], message='Envie apenas imagens (jpg, jpeg, png)')
    ])

    lider_bio = TextAreaField('Biografia do Líder', validators=[
        Optional()
    ])

    contato_email = StringField('E-mail de Contato', validators=[
        Optional(),
        Email(message='Informe um e-mail válido'),
        Length(max=150)
    ])

    contato_telefone = StringField('Telefone de Contato', validators=[
        Optional(),
        Length(max=30)
    ])

    ordem = IntegerField('Ordem de Exibição', validators=[
        Optional()
    ], default=0)

    ativo = BooleanField('Departamento ativo', default=True)

    submit = SubmitField('Cadastrar')