import os
from flask import url_for, render_template, Blueprint, redirect, request, flash, session
from flask_login import login_required, current_user
# Importando formulários 
from security.forms_security import CadastroForm
# Importando modelos do banco para realizar as operações 
from models.administrador import Administrador
from models.database import SessionFactory
# Importando decorador que eu criei para impedir um usuário de entrar sem ter a autenticação de 2 fatores
from security.two_factor_authentication.decorador import adm_2af_required
# Importando outro decorador que eu criei para impedir que o adm comum acesse rotas exclusivas para administradores root
from security.root.permission import root_permission


administrador_bp = Blueprint('administrador', __name__, url_prefix='/admin')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
# Página do administrador 
@administrador_bp.route('/')
@adm_2af_required
def index():
    dados_sensiveis = session.get('dados_sensiveis')
    administrador = current_user
    return render_template('admin.html', dados_sensiveis=dados_sensiveis, administrador=administrador)


# ROTAS EXCLUSIVAS PARA USUÁRIOS ROOT

# Cadastrar administrador
@administrador_bp.route('/cadastrar_adm', methods=['POST', 'GET'])
@adm_2af_required
@root_permission
def cadastrar_adm():
    # Configurando formulário 
    formulario = CadastroForm()
    # Recebendo dados do formulário
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        password = request.form.get('password')
        ativo = request.form.get('ativo')

        # Criando administrador
        novo_administrador = Administrador(ADMIN_NAME = nome, ADMIN_EMAIL = email, ADMIN_ACTIVE = True if ativo == 'ativo' else False)
        novo_administrador.set_password(password)
        # Salvando no banco 
        with SessionFactory() as session:
            session.add(novo_administrador)
            session.commit()
    
        # Redirecionando para a página principal de administradores
        return redirect(url_for('administrador.index'))
    return render_template('root/cadastro_administrador.html', formulario=formulario)
        

    