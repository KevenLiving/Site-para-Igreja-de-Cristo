from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional
from datetime import datetime


class ChurchHistory_(FlaskForm):
    titulo = StringField('Título', validators=[
        DataRequired(message='O título é obrigatório'),
        Length(max=200)
    ])

    conteudo = TextAreaField('Conteúdo', validators=[
        DataRequired(message='O conteúdo é obrigatório')
    ])

    imagem = FileField('Imagem', validators=[
        FileRequired(message='A imagem é obrigatória'),
        FileAllowed(['jpg', 'jpeg', 'png'], message='Envie apenas imagens (jpg, jpeg, png)')
    ])

    ano_inicio = SelectField("Ano de inicio",
        choices=[
            ("", "Selecione o ano de inicio")
        ] +
        
        [
            (str(ano), str(ano))
            for ano in range(datetime.now().year, 1900, -1)
        ],
        validators=[
            DataRequired(message='Ano de inicio é obrigatório')
        ]
    )

    ano_fim = SelectField("Ano de fim (caso não tenha, não selecione nenhum número)",
        choices=[
            ("", "Selecione o ano termino (se houver)")
        ] +
        
        [
            (str(ano), str(ano))
            for ano in range(datetime.now().year, 1900, -1)
        ],
        validators=[Optional()]
    )


    ordem = IntegerField('Ordem de Exibição', validators=[
        Optional()
    ], default=0)

    submit = SubmitField('Cadastrar')



class ChurchHistoryUpdate(FlaskForm):
    titulo = StringField('Título', validators=[
        DataRequired(message='O título é obrigatório'),
        Length(max=200)
    ])

    conteudo = TextAreaField('Conteúdo', validators=[
        DataRequired(message='O conteúdo é obrigatório')
    ])

    imagem = FileField('Alterar Imagem', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], message='Envie apenas imagens (jpg, jpeg, png)')
    ])

    ano_inicio = SelectField("Ano de inicio",
        choices=[
            ("", "Selecione o ano de inicio")
        ] +
        
        [
            (str(ano), str(ano))
            for ano in range(datetime.now().year, 1900, -1)
        ],
        validators=[
            DataRequired(message='Ano de inicio é obrigatório')
        ]
    )

    ano_fim = SelectField("Ano de fim (caso não tenha, não selecione nenhum número)",
        choices=[
            ("", "Selecione o ano termino (se houver)")
        ] +
        
        [
            (str(ano), str(ano))
            for ano in range(datetime.now().year, 1900, -1)
        ],
        validators=[Optional()]
    )

    ordem = IntegerField('Ordem de Exibição', validators=[
        Optional()
    ])

    submit = SubmitField('Atualizar')