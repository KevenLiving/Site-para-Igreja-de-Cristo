# OS será chamdado para manipulações necessárias no sistema operacional
import os
# Importações padrões do Flask
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from models.admnistrador_log import AdministradorLog
# Ele foi importado de extensions para evitar problemas de importação circular
from security.forms_security import LoginForm
from security.extensions import limiter
# Essa é uma tag para usar futuramente para os pedidos de oração que a comunidade irá realizar para evitar ataques com <scripit>
import bleach
# A seguinte biblioteca é uma implementação de um sistema próprio que ela oferece para registro de logs no sistema
# Ela será utilizada para verificar atividades de login. Ajuda também no processo de depuração
import logging
import logging.handlers

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# Configurando a biblioteca de segurança para logs
# Garantindo que a pasta sempre exista
os.makedirs('security/login_security', exist_ok=True)

# Criando loggers específico para segurança que não intervenham ou afetem outros logs
security_logger = logging.getLogger('security')
# Configurando o nível de captura para capturar sucessos no login
security_logger.setLevel(logging.INFO)

# Configuração de handlers para evitar superlotação da memória com logs 
handler = logging.handlers.RotatingFileHandler(
    "security/login_security/security.log",
    maxBytes=5*1024*1024, # Cada arquivo com no máximo 5MB
    backupCount=3, # Apenas 3 arquivos antigos permancem quando o limite de 5 arquivos for atingido
    encoding='utf-8' # Funciona melhor com os diferentes tipos de letras, especialmente no latin
)

# Formatação personalizada dos registro
formatter = logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
) 
handler.setFormatter(formatter)
security_logger.addHandler(handler)


# Rota para login
@auth_bp.route('/login', methods=['GET', 'POST'])
# Aqui eu limito para que só haja no máximo 5 requisições por minuto nessa rota
@limiter.limit("5 per minute")
def logar_no_sistema():
    # Resolvi realizar um formulário efetivamente seguro. Para não sujar meu código, coloquei ele dentro da pasta de segurança e importei ele aqui.
    formulario = LoginForm()
    if request.method == 'POST':
        # Pegando os dados do formulário e limpando possíveis scripts maliciosos com a biblioteca bleach
        admin_email = formulario.email.data
        admin_password = formulario.password.data 

        # Verificando a sua validação
        if formulario.validate_on_submit():

            administrador = AdministradorLog.get_by_email(admin_email)
            if administrador and administrador.check_password(admin_email, admin_password) and administrador.ADMIN_ACTIVE==True:
                
                # Para que adm possa ter acesso ao sistema
                login_user(administrador)

                # Registando o registro efetivo de log de segurança 
                security_logger.info(f'LOGIN_SUCESS: {admin_email} from {request.remote_addr}')

                if administrador.is_root():
                    session['dados_sensiveis'] = "Aaaaaah, estou chorando :("
                    return redirect(url_for('administrador.index'))
                else:
                    return redirect(url_for('administrador.index'))

            else:
                # Registrando tentativa falha de login no log de segurança
                security_logger.warning(f'LOGIN_FAILURE: {admin_email} from {request.remote_addr}')
                flash ('Email ou senha incorretos', 'danger')
        
            

    return render_template('login.html', formulario=formulario)


@auth_bp.route('/logout')
@login_required
def deslogar_do_sistema():
    logout_user()
    return redirect(url_for('auth.logar_no_sistema'))
