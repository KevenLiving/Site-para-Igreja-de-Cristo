import os
from flask import url_for, render_template, Blueprint, redirect, request, flash
from flask_login import login_required, current_user


administrador_bp = Blueprint('administrador', __name__, url_prefix='/admin')

# Página do administrador 

@administrador_bp.route('/')
@login_required
def index():
    dados_sensiveis = request.args.get('dados_sensiveis')
    return render_template('admin.html')
1