# OS será chamdado para manipulações necessárias no sistema operacional
import os
# Importações padrões do Flask
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from models.admnistrador_log import AdministradorLog
# Ele foi importado de extensions para evitar problemas de importação circular
from security.forms_security import LoginForm, Two_Factor
from security.extensions import limiter
# Essa é uma tag para usar futuramente para os pedidos de oração que a comunidade irá realizar para evitar ataques com <scripit>
import bleach
# A seguinte biblioteca é uma implementação de um sistema próprio que ela oferece para registro de logs no sistema
# Ela será utilizada para verificar atividades de login. Ajuda também no processo de depuração
import logging
import logging.handlers
# Bibliotecas para realizar autenticação 2F
import pyotp
import qrcode
import time
# Importando decorador que eu criei para impedir um usuário de entrar sem ter a autenticação de 2 fatores
from security.two_factor_authentication.decorador import new_user_required
# Para importar as variáveis de ambiente
from dotenv import load_dotenv
# A biblioteca a seguir será utilizada no sistema de criptografia de dados sensiveis 
from cryptography.fernet import Fernet
import io
import base64
# A seguir serão trazidas mudanças para que as mudanças que eu fiz no usuário persistam no bando (essa ou outra alternativa mais eficaz)
from models.database import SessionFactory 
# Decorador que bloqueia acessar a geração de QR-CODE se ele já foi gerado e o usuário teve acesso ao sistema

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# Configurando a biblioteca de segurança para logs
# Garantindo que a pasta sempre exista
os.makedirs('security/login_security', exist_ok=True)

# Carregando as variáveis do ambiente
load_dotenv()

# Carregando chave do sistema
secret_key = os.environ.get('chave_teste_base64').encode()

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

# Váriavel para definir se o usuário passou na primeira etapa
login = False

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
                
                # Para que adm possa passar pela primeira etapa de autenticação
                login_user(administrador)
                

                # Criando sessão para verificar se o usuário passou pela segunda etapa de autenticação
                session['admin_2af_verifield'] = False


                # PLANO DE AUTENTICAÇÃO ETAPA 01
                # Aqui o sistema detectará se esse usuário é novato, nunca fez login, ou já passou pelo cadastramento do sistema de autenticação dupla
                # Caso ele seja novato, o ADM_TWO_FACTOR_FIRST enviará ele para a rota de cadastramento de autenticação de 2 fatores
                if not current_user.ADMIN_TWO_FACTOR_FIRST:
                    return redirect(url_for('auth.two_factor_first'))

                # Caso ele já tenha passado por essa etapa, ele vai direto para a rota de checegem do codigo de verificação de duas etapas
                else:
                    # Retorna para o segundo passo de autenticação
                    return redirect(url_for('auth.two_factor_authentication'))

            else:
                # Registrando tentativa falha de login no log de segurança
                security_logger.warning(f'LOGIN_FAILURE: {admin_email} from {request.remote_addr}')
                flash ('Email ou senha incorretos', 'danger')
        
            

    return render_template('login.html', formulario=formulario)


# Caso o usuário tenha passado pela condicional, ele é novato. Ai que o jogo começa
# Aqui ele será cadastrado no sistema de autentifição 2AF, e será gerado e fornecido um QR-CODE
# Analisado o código QR-CODE com o Google Authentication, ele vai para a página tão esperada de inserir o código e acessar o painel de administradores
@auth_bp.route('/two_factor_first')
# Impede usuários que já logaram de acessar a rota de novos usuários 
@new_user_required
# Somente permite usuários que estejam logados
@login_required
def two_factor_first():

    # Se o código dele já foi gerado, não deve gerar outro

    if not session.get('generate_qr_code'):
        
        # Salvando mudanças no objeto
        check_secure_code = current_user.create_code()

        # Salvando mudanças no banco
        with SessionFactory() as db_session:
            db_session.merge(current_user)
            db_session.commit()

            # No momento em que o a chave_secreta e o qr-code forem gerados, vai ficar armazenado na sessão 
            # Isso sevirá para evitar mudar chave_secreta do usuário toda vida que ele voltar aqui
            # Isso significa que sera feita apenas uma chave_secreta e um QR-CODE será gerado
            session['generate_qr_code'] = True

        if check_secure_code:

            # Para descriptografar, é necessário criar o objeto "object_cript" com a mesma chave que foi inserida da outra vez para criptografar
            object_cript = Fernet(os.environ.get('chave_teste_base64').encode())

            # Aqui a chave é "descriptada" usando o objeto portador da senha secreta
            if isinstance(current_user.ADMIN_CODE, bytes):
                chave_descriptografada = object_cript.decrypt(current_user.ADMIN_CODE).decode()
            else:
                chave_descriptografada = object_cript.decrypt(current_user.ADMIN_CODE.encode()).decode()

            # Criando caminho único para gerar o QR-CODE
            uri = pyotp.totp.TOTP(chave_descriptografada).provisioning_uri(name=f'QR-CODE ICB ADMINISTRATION - {current_user.ADMIN_EMAIL}', issuer_name=f'{current_user.ADMIN_NAME}')

            # Salvando QR-CODE em memória, e não em arquivo para não gerar vulnerabilidade no sistema
            qr_code = qrcode.QRCode(version=1, box_size=10, border=5)
            qr_code.add_data(uri)
            qr_code.make(fit=True)

            qr_img = qr_code.make_image(fill_color='black', back_color='white')

            # Convertendo para base64, que é um modelo seguro para se usar em URL
            buffer = io.BytesIO()
            qr_img.save(buffer, format='png')
            qr_img_base64 = base64.b64encode(buffer.getvalue()).decode()


            # Renderizando o QR CODE 
            return render_template('two_factor_first.html', qr_img_base64=qr_img_base64)
        
        else:
            return "Você está quase chegando lá e consquistando seus sonhos, anima-te"
        
    else: 
        # Para descriptografar, é necessário criar o objeto "object_cript" com a mesma chave que foi inserida da outra vez para criptografar
        object_cript = Fernet(os.environ.get('chave_teste_base64').encode())

        # Aqui a chave é "descriptada" usando o objeto portador da senha secreta
        if isinstance(current_user.ADMIN_CODE, bytes):
            chave_descriptografada = object_cript.decrypt(current_user.ADMIN_CODE).decode()
        else:
            chave_descriptografada = object_cript.decrypt(current_user.ADMIN_CODE.encode()).decode()

        # Criando caminho único para gerar o QR-CODE
        uri = pyotp.totp.TOTP(chave_descriptografada).provisioning_uri(name=f'QR-CODE ICB ADMINISTRATION - {current_user.ADMIN_EMAIL}', issuer_name=f'{current_user.ADMIN_NAME}')

        # Salvando QR-CODE em memória, e não em arquivo para não gerar vulnerabilidade no sistema
        qr_code = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_code.add_data(uri)
        qr_code.make(fit=True)

        qr_img = qr_code.make_image(fill_color='black', back_color='white')

        # Convertendo para base64, que é um modelo seguro para se usar em URL
        buffer = io.BytesIO()
        qr_img.save(buffer, format='png')
        qr_img_base64 = base64.b64encode(buffer.getvalue()).decode()


        # Renderizando o QR CODE 
        return render_template('two_factor_first.html', qr_img_base64=qr_img_base64)
        

            



    

# Rota para autenticação de 2 fatores
@auth_bp.route('/two_factor', methods=['POST', 'GET'])
@login_required
def two_factor_authentication():
    code_form = Two_Factor()

    # Para descriptografar, é necessário criar o objeto "object_cript" com a mesma chave que foi inserida da outra vez para criptografar
    object_cript = Fernet(os.environ.get('chave_teste_base64').encode())

    # Aqui a chave é "descriptada" usando o objeto portador da senha secreta
    chave_descriptografada = object_cript.decrypt(current_user.ADMIN_CODE).decode()

    if request.method == 'POST':
        codigo = int(code_form.code.data)
        time_out = pyotp.TOTP(chave_descriptografada)

        if time_out.verify(codigo):

            # Mudando status no banco de dados do two_factor_authentication quando ele consegue logar 100% no sistema
            # Isso indica que o gerador das senhas de acesso já está no celular dele e que não precisará mais daquele 
            # QR-CODE(que será apago por questões de segurança).

            # Para ele não passar pelo gerador de chave secreta e qr-code, esse campo no banco de dados do usuário é alterado como True
            # e salvo no bando 
            if not current_user.ADMIN_TWO_FACTOR_FIRST:
                current_user.ADMIN_TWO_FACTOR_FIRST = True
                with SessionFactory() as db_session:
                    db_session.merge(current_user)
                    db_session.commit()
                    db_session.close()

            # Necessário para ele passar pelo decorador que bloqueia as rotas de dashboard de quem não passou pela etapa dulpla 
            # de autenticação
            session['admin_2af_verifield'] = True

            # Registrando o registro efetivo de log de segurança 
            security_logger.info(f'LOGIN_SUCESS: {current_user.ADMIN_EMAIL} from {request.remote_addr}')

            # Se for root carrega dados importantes
            if current_user.is_root:
                session['dados_sensiveis'] = "Mister President"
                return redirect(url_for('administrador.index'))
            
            else:
                return redirect(url_for('administrador.index'))
        
        else:
            return redirect(url_for('auth.two_factor_authentication'))
        
    else:
        return render_template('two_factor.html', code_form=code_form)





@auth_bp.route('/logout')
@login_required
def deslogar_do_sistema():
    logout_user()
    return redirect(url_for('auth.logar_no_sistema'))
