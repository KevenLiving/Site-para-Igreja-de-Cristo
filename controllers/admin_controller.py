import os
from flask import url_for, render_template, Blueprint, redirect, request, flash, session
from flask_login import login_required, current_user
# Importando decorador que eu criei para impedir um usuário de entrar sem ter a autenticação de 2 fatores
from security.two_factor_authentication.decorador import adm_2af_required


administrador_bp = Blueprint('administrador', __name__, url_prefix='/admin')

# Página do administrador 

@administrador_bp.route('/')
@adm_2af_required
def index():
    dados_sensiveis = session.get('dados_sensiveis')
    administrador = current_user
    return render_template('admin.html', dados_sensiveis=dados_sensiveis, administrador=administrador)