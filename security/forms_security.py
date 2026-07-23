from wtforms import ValidationError
import re
# Formulário de login mais seguro e prático
from wtforms import StringField, PasswordField, SubmitField, ValidationError, IntegerField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf import FlaskForm

class PasswordValidator:
    """Validador de senhas robusto e configurável"""
    
    def __init__(self, 
                 min_length=8, 
                 max_length=128,
                 require_uppercase=True,
                 require_lowercase=True, 
                 require_digits=True,
                 require_symbols=True,
                 min_unique_chars=6,
                 check_common_passwords=True,
                 check_personal_info=True):
        
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_symbols = require_symbols
        self.min_unique_chars = min_unique_chars
        self.check_common_passwords = check_common_passwords
        self.check_personal_info = check_personal_info
    
    def __call__(self, form, field):
        password = field.data
        errors = []
        
        # 1. Verificar comprimento
        if len(password) < self.min_length:
            errors.append(f'Senha deve ter pelo menos {self.min_length} caracteres')
        if len(password) > self.max_length:
            errors.append(f'Senha deve ter no máximo {self.max_length} caracteres')
        
        # 2. Verificar tipos de caracteres
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append('Senha deve conter pelo menos uma letra minúscula')
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append('Senha deve conter pelo menos uma letra maiúscula')
        
        if self.require_digits and not re.search(r'\d', password):
            errors.append('Senha deve conter pelo menos um número')
        
        if self.require_symbols and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Senha deve conter pelo menos um símbolo (!@#$%^&*...)')
        
        # 3. Verificar caracteres únicos
        unique_chars = len(set(password))
        if unique_chars < self.min_unique_chars:
            errors.append(f'Senha deve ter pelo menos {self.min_unique_chars} caracteres diferentes')
        
        # 4. Verificar padrões fracos
        if self.has_weak_patterns(password):
            errors.append('Senha contém padrões fracos (ex: 123, abc, qwerty)')
        
        # 5. Verificar senhas comuns
        if self.check_common_passwords and self.is_common_password(password):
            errors.append('Esta é uma senha muito comum. Escolha outra')
        
        # 6. Verificar informações pessoais (se disponível)
        if self.check_personal_info and hasattr(form, 'email'):
            if self.contains_personal_info(password, form):
                errors.append('Senha não pode conter informações pessoais')
        
        if errors:
            raise ValidationError(errors[0])  # Mostrar primeiro erro
    
    def has_weak_patterns(self, password):
        """Detecta padrões fracos comuns"""
        weak_patterns = [
            r'123+',           # sequências numéricas
            r'abc+',           # sequências alfabéticas
            r'qwerty',         # layout teclado
            r'password',       # palavra "password"
            r'(.)\1{3,}',     # repetição de caracteres (aaaa)
            r'^[0-9]+$',      # apenas números
            r'^[a-zA-Z]+$',   # apenas letras
        ]
        
        password_lower = password.lower()
        return any(re.search(pattern, password_lower) for pattern in weak_patterns)
    
    def is_common_password(self, password):
        """Verifica contra lista de senhas comuns"""
        # Lista das 100+ senhas mais comuns
        common_passwords = {
            '123456', 'password', '123456789', '12345678', '12345',
            '1234567', '1234567890', 'qwerty', 'abc123', '111111',
            '123123', 'admin', 'letmein', 'welcome', 'monkey',
            '1234', 'dragon', '123', 'password123', 'master',
            'hello', 'login', 'pass', '123321', 'target123',
            'sunshine', 'iloveyou', 'princess', 'football', 'charlie',
            'aa123456', 'donald', 'password1', 'qwerty123'
        }
        
        return password.lower() in common_passwords
    
    def contains_personal_info(self, password, form):
        """Verifica se senha contém informações pessoais"""
        password_lower = password.lower()
        
        # Verificar email
        if hasattr(form, 'email') and form.email.data:
            email_parts = form.email.data.lower().split('@')[0]
            if len(email_parts) > 3 and email_parts in password_lower:
                return True
        
        # Verificar nome (se disponível)
        if hasattr(form, 'name') and form.name.data:
            name_lower = form.name.data.lower()
            if len(name_lower) > 3 and name_lower in password_lower:
                return True
        
        return False
    
# Formulário de login

class LoginForm(FlaskForm):

    # EMAIL
    email = StringField('Email', validators=[
        DataRequired(message="O email é obrigatório."),
        Length(max=100, message="O email deve ter entre 5 e 120 caracteres."),
        Email(message="Por favor, insira um email válido.")
    ])

    # SENHA 

    password = PasswordField('Senha', validators=[
            DataRequired(message="A senha é obrigatória")
        ])
    
    


    # BOTÃO DE ENVIO

    submit = SubmitField('Login')


class Two_Factor(FlaskForm):

    code = StringField(
        'Código', validators=[
            DataRequired(),
            Length(min=6, max=6)
        ]
    )

    submit = SubmitField('Enviar')




# Formulário de cadastro

class CadastroForm(FlaskForm):

    # NOME 
    nome = StringField('Nome', validators=[
        DataRequired(message="O nome é obrigatório."),
        Length(max=100, min=3, message="O nome deve ter entre 3 e 100 caracteres.")
    ])

    # EMAIL
    email = StringField('Email', validators=[
        DataRequired(message="O email é obrigatório."),
        Length(max=100, message="O email deve ter entre 5 e 120 caracteres."),
        Email(message="Por favor, insira um email válido.")
    ])

    # SENHA 

    password = PasswordField('Senha', validators=[
            DataRequired(),
            PasswordValidator(
                min_length=8,
                require_uppercase=True,
                require_lowercase=True,
                require_digits=True,
                require_symbols=True,
                min_unique_chars=6,
                check_common_passwords=True,
                check_personal_info=True
            )
        ])
    
    password_confirm = PasswordField('Confirme sua senha', 
                                     validators=[DataRequired(message='Confirme sua senha')])
    
    # STATUS DE ATIVIDADE 
    ativo = SelectField(
        'Status de atividade',
        choices=[('ativo', 'Em atividade'),
                 ('desativo', 'Conta desativada')
                 ],
                 default='desativo'
    )
    
    # Validação de email personalizado

    def validate_email(self, email):
        # Como a proposta do site é ser seguro, eu restringi os tipos de emails que podem ser usados para logar no sistema. Coloquei apenas os tipos mais comuns e seguros usados mundialmente.
        emails_permitidos = [
            # Google
            'gmail.com', 'googlemail.com',
            
            # Microsoft
            'outlook.com', 'hotmail.com', 'live.com', 'msn.com',
            
            # Yahoo
            'yahoo.com', 'yahoo.com.br', 'yahoo.co.uk', 'yahoo.fr', 
            'yahoo.de', 'yahoo.es', 'yahoo.it', 'yahoo.ca',
            'ymail.com', 'rocketmail.com',
            
            # Apple
            'icloud.com', 'me.com', 'mac.com',
        ""]

        dominio = email.data.split('@')[-1].lower()
        if dominio not in emails_permitidos:
            raise ValidationError("Esse dominio de email não é permitido por questões de segurança.")
    
    def validate_password_confirm(self, field):
        if field.data != self.password.data:
            raise ValidationError("As senhas devem ser correspondentes!")



    # BOTÃO DE ENVIO
    submit = SubmitField('Cadastrar')

    


# Formulário de atualização

class AtualizarForm(FlaskForm):

    # NOME 
    nome = StringField('Nome', validators=[
        DataRequired(message="O nome é obrigatório."),
        Length(max=100, message="O nome deve ter entre 3 e 100 caracteres.")
    ])

    # EMAIL
    email = StringField('Email', validators=[
        DataRequired(message="O email é obrigatório."),
        Length(max=100, message="O email deve ter entre 5 e 120 caracteres."),
        Email(message="Por favor, insira um email válido.")
    ])

    
    # STATUS DE ATIVIDADE 
    ativo = SelectField(
        'Status de atividade',
        choices=[('ativo', 'Em atividade'),
                 ('desativo', 'Conta desativada')
                 ],
                 default='desativado'
    )
    
    # Validação de email personalizado

    def validate_email(self, email):
        # Como a proposta do site é ser seguro, eu restringi os tipos de emails que podem ser usados para logar no sistema. Coloquei apenas os tipos mais comuns e seguros usados mundialmente.
        emails_permitidos = [""
            # Google
            'gmail.com', 'googlemail.com',
            
            # Microsoft
            'outlook.com', 'hotmail.com', 'live.com', 'msn.com',
            
            # Yahoo
            'yahoo.com', 'yahoo.com.br', 'yahoo.co.uk', 'yahoo.fr', 
            'yahoo.de', 'yahoo.es', 'yahoo.it', 'yahoo.ca',
            'ymail.com', 'rocketmail.com',
            
            # Apple
            'icloud.com', 'me.com', 'mac.com',
        ""]

        dominio = email.data.split('@')[-1].lower()
        if dominio not in emails_permitidos:
            raise ValidationError("Esse dominio de email não é permitido por questões de segurança.")
    


    # BOTÃO DE ENVIO

    submit = SubmitField('Atualizar')


# Formulário para atualizar senha

class PasswordUpdate(FlaskForm):

    # SENHA 

    password = PasswordField('Senha', validators=[
            DataRequired(),
            PasswordValidator(
                min_length=8,
                require_uppercase=True,
                require_lowercase=True,
                require_digits=True,
                require_symbols=True,
                min_unique_chars=6,
                check_common_passwords=True,
                check_personal_info=True
            )
        ])
    
    password_confirm = PasswordField('Confirme sua senha', 
                                     validators=[DataRequired(message='Confirme sua senha')])
    
    # BOTÃO DE ENVIO

    submit = SubmitField('Atualizar senha')

# Formulário de confirmação de senha
class PasswordConfirm(FlaskForm):

    # SENHA 

    password = PasswordField('Senha', validators=[
            DataRequired(message="A senha é obrigatória")
        ])
    
    
    # BOTÃO DE ENVIO

    submit = SubmitField('Confirmar exclusão')



