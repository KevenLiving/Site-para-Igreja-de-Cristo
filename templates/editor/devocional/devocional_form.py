from wtforms.fields import DateField
from flask_wtf.file import FileField, FileAllowed, FileRequired
# Formulário de login mais seguro e prático
from wtforms import StringField, SubmitField, ValidationError, IntegerField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NoneOf
from flask_wtf import FlaskForm

# Formulário para cadastrar estudo biblico 

class Devotional_(FlaskForm):

    titulo = StringField('Título', validators=[
        Length(max=200, message='No máximo 200 caracteres'),
        DataRequired(message='Título é obrigatório')
    ])

    conteudo = StringField('Mensagem', validators=[
        DataRequired(message='Descrição é obrigatória')
    ])

    versiculo = StringField('Versículo base', validators=[
        DataRequired(message='Descrição é obrigatória')
    ])

    banner = FileField('Banner', validators=[
        FileRequired("Selecione uma imagem para o banner do devocional"),
        FileAllowed(['jpeg', 'jpg', 'png', 'webp'], 'Apenas imagem.')

    ])


    inicio = DateField(
        'Data de inicio',
        format="%Y-%m-%d",
        validators=[
            DataRequired(message='Data de começo é obrigatória')
        ]
        )
    
    fim = DateField(
        'Data de termino',
        format="%Y-%m-%d",
        validators=[
            DataRequired(message='Data de termino é obrigatória')
        ]
        )

    publicar = BooleanField('Publicar devocional')

    submit = SubmitField('Salvar')



class DevotionalUpdate(FlaskForm):

    titulo = StringField('Título', validators=[
        Length(max=200, message='No máximo 200 caracteres'),
        DataRequired(message='Título é obrigatório')
    ])

    conteudo = StringField('Mensagem', validators=[
        DataRequired(message='Descrição é obrigatória')
    ])

    versiculo = StringField('Versículo base', validators=[
        DataRequired(message='Descrição é obrigatória')
    ])

    banner = FileField('Banner', validators=[
        FileAllowed(['jpeg', 'jpg', 'png', 'webp'], 'Apenas imagem.')
    ])


    inicio = DateField(
        'Data de inicio',
        format="%Y-%m-%d",
        validators=[
            DataRequired(message='Data de começo é obrigatória')
        ]
        )
    
    fim = DateField(
        'Data de termino',
        format="%Y-%m-%d",
        validators=[
            DataRequired(message='Data de termino é obrigatória')
        ]
        )

    publicar = BooleanField('Publicar devocional')

    submit = SubmitField('Atualizar')