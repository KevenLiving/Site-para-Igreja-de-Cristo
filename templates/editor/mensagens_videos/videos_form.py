from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, IntegerField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional, URL, NoneOf


class Video_Message(FlaskForm):
    titulo = StringField('Título', validators=[
        DataRequired(message='O título é obrigatório'), 
        Length(max=200)
        ])
    
    url = StringField('URL do Vídeo', validators=
                      [DataRequired(message='A URL é obrigatória'), 
                       URL(message='Informe uma URL válida'), Length(max=255)
                       ])
    
    pregador = StringField('Pregador', validators=
                           [Optional(), Length(max=150)
                            ])
    
    categoria = SelectField(
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

    destaque = BooleanField('Destacar vídeo')
    publicar = BooleanField('Publicar vídeo')
    submit = SubmitField('Cadastrar')