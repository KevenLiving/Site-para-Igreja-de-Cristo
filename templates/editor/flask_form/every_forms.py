from wtforms import ValidationError
import re
# Formulário de login mais seguro e prático
from wtforms import StringField, SubmitField, ValidationError, IntegerField, SelectField, TextAreaField, BooleanField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, Email, Length, NoneOf
from flask_wtf import FlaskForm

# Formulário para cadastrar estudo biblico 

class Biblical_Study(FlaskForm):

    titulo = StringField('Título', validators=[
        Length(max=200, message='No máximo 200 caracteres'),
        DataRequired(message='Título é obrigatório')
    ])

    conteudo = TextAreaField('Conteudo', validators=[
        DataRequired(message='Conteúdo é obrigatório')
    ])

    banner = FileField('Selecione um banner de capa para o estudo', validators=[
        FileRequired("Selecione uma imagem para o banner do estudo"),
        FileAllowed(['jpeg', 'jpg', 'png', 'webp'], 'Apenas imagem.')

    ])

    referencia = StringField('Referência', validators=[
        DataRequired(message='Referência bíblica é obrigatória')
    ])

    tema = SelectField(
        'Tema',
        choices=[('default','Selecione um tema'),
                 ('apologetica', 'Apologética'),
                 ('sabedoria', 'Sabedoria para Vida'),
                 ('financeiro','Finanças e Mordomia'),
                 ('batalha_espiritual','Batalha Espiritual'),
                 ('escatologia','Escatologia'),
                 ('evangelismo','Missão e Evangelismo'),
                 ('eclesiologia','Eclesiologia'),
                 ('vida_devocional','Oração e Vida Devocional'),
                 ('familia', 'Família'),
                 ('vida_crista','Vida Cristã'),
                 ('pneumatologia','Pneumatologia'),
                 ('cristologia','Cristologia'),
                 ('soteriologia','Soteriologia')
                 ],
                 default='default',
                 validators=[
                     NoneOf(['default'], message='Selecione um tema')
                 ]
    )

    destaque = BooleanField('Destacar estudo')

    publicar = BooleanField('Publicar estudo')

    submit = SubmitField('Cadastrar')

class UpBiblical_Study(FlaskForm):

    titulo = StringField('Título', validators=[
        Length(max=200, message='No máximo 200 caracteres'),
        DataRequired(message='Título é obrigatório')
    ])

    conteudo = TextAreaField('Conteudo', validators=[
        DataRequired(message='Conteúdo é obrigatório')
    ])

    banner = FileField('Selecione um banner de capa para o estudo', validators=[
        FileAllowed(['jpeg', 'jpg', 'png', 'webp'], 'Apenas imagem.')
    ])

    referencia = StringField('Referência', validators=[
        DataRequired(message='Referência bíblica é obrigatória')
    ])

    tema = SelectField(
        'Tema',
        choices=[('default','Selecione um tema'),
                 ('apologetica', 'Apologética'),
                 ('sabedoria', 'Sabedoria para Vida'),
                 ('financeiro','Finanças e Mordomia'),
                 ('batalha_espiritual','Batalha Espiritual'),
                 ('escatologia','Escatologia'),
                 ('evangelismo','Missão e Evangelismo'),
                 ('eclesiologia','Eclesiologia'),
                 ('vida_devocional','Oração e Vida Devocional'),
                 ('familia', 'Família'),
                 ('vida_crista','Vida Cristã'),
                 ('pneumatologia','Pneumatologia'),
                 ('cristologia','Cristologia'),
                 ('soteriologia','Soteriologia')
                 ],
                 default='default',
                 validators=[
                     NoneOf(['default'], message='Selecione um tema')
                 ]
    )

    destaque = BooleanField('Destacar estudo')

    publicar = BooleanField('Publicar estudo')

    submit = SubmitField('Cadastrar')

