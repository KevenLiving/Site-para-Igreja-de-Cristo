from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from models.admnistrador_log import AdministradorLog
# Ele foi importado de extensions para evitar problemas de importação circular
from security.forms_security import LoginForm
from security.extensions import limiter



auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# Rota para login
@auth_bp.route('/login', methods=['GET', 'POST'])
# Aqui eu limito para que só haja no máximo 5 requisições por minuto nessa rota
@limiter.limit("5 per minute")
def logar_no_sistema():
    # Resolvi realizar um formulário efetivamente seguro. Para não sujar meu código, coloquei ele dentro da pasta de segurança e importei ele aqui.
    formulario = LoginForm()
    if request.method == 'POST':
        # Pegando os dados do formulário
        admin_email = formulario.email.data
        admin_password = formulario.password.data

        # Verificando a sua validação
        if formulario.validate_on_submit():

            administrador = AdministradorLog.get_by_email(admin_email)
            if administrador and administrador.check_password(admin_email, admin_password) and administrador.ADMIN_ACTIVE==True:
                
                # Variaveis para dados especiais que ó podem ser utilizados por um usuário root
                login_user(administrador)
                if administrador.is_root():
                    session['dados_sensiveis'] = "Aaaaaah, estou chorando :("
                    return redirect(url_for('administrador.index'))
                else:
                    return redirect(url_for('administrador.index'))

            else:
                flash ('Email ou senha incorretos', 'danger')
        
            

    return render_template('login.html', formulario=formulario)


@auth_bp.route('/logout')
@login_required
def deslogar_do_sistema():
    logout_user()
    return redirect(url_for('auth.logar_no_sistema'))
