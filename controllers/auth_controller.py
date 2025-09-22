from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from models.admnistrador_log import AdministradorLog


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Rota para login
@auth_bp.route('/login', methods=['GET', 'POST'])
def logar_no_sistema():
    if request.method == 'POST':
        admin_email = request.form.get('email')
        admin_password = request.form.get('password')


        administrador = AdministradorLog.get_by_email(admin_email)
        if administrador and administrador.check_password(admin_email, admin_password) and administrador.ADMIN_ACTIVE==True:
            
            # Variaveis para dados especiais que ó podem ser utilizados por um usuário root
            dados_sensiveis = None
            login_user(administrador)
            session['ADMIN_ID'] = administrador.ADMIN_ID
            if administrador.is_root():
                dados_sensiveis = "Aaaaaah, estou chorando :("
                return redirect(url_for('administrador.index', dados_sensiveis=dados_sensiveis, administrador=administrador))
            else:
                return redirect(url_for('administrador.index', administrador=administrador))

        else:
            flash ('Email ou senha incorretos', 'danger')
            

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def deslogar_do_sistema():
    logout_user()
    return redirect(url_for('auth.logar_no_sistema'))
