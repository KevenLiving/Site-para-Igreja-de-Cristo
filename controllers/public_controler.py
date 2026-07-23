
from flask import url_for, render_template, Blueprint, redirect, request, flash, session, current_app
from flask_login import login_required, current_user
# Importando formulários 
from security.forms_security import CadastroForm, PasswordConfirm, AtualizarForm, PasswordUpdate
# Importando modelos do banco para realizar as operações 
from models.administrador import Administrador
from models.biblical_study import BiblicalStudy
from models.database import SessionFactory
from models.weekly_schedule import WeeklySchedule
from models.devotional import Devotional
from models.video_message import VideoMessage
from models.church_history import ChurchHistory
from models.department import Department
from models.event import Event
from models.social_link import SocialLink
from models.prayer_request import PrayerRequest
# Formulários 
from templates.public.prayer.oracao_form import PrayerRequest_
# Recursos extras para o trabalho de administração
import datetime
import os
from werkzeug.utils import secure_filename
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError



public_bp = Blueprint('public', __name__, url_prefix='/public')

@public_bp.route('/')
def index():
    return render_template('public/main.html')

# Pedir oração
@public_bp.route('/prayer_request', methods=['GET', 'POST'])
def prayer_request():
    formulario = PrayerRequest_()

    # Recebendo formulário
    if formulario.validate_on_submit():
        nome = request.form.get('nome')
        pedido = request.form.get('pedido')
        categoria = formulario.categoria.data
        prioridade = formulario.prioridade.data
        anonimo = formulario.anonimo.data
        contato_email = formulario.contato_email.data
        contato_telefone = formulario.contato_telefone.data

        if anonimo:
            nome = None
            contato_email = None
            contato_telefone = None

        # Cadastrando pedido
        with SessionFactory() as session_db:
            novo_pedido = PrayerRequest(PRAYER_NAME = nome, PRAYER_REQUEST_TEXT= pedido, PRAYER_CATEGORY = categoria, PRAYER_PRIORITY = prioridade, PRAYER_ANONYMOUS = anonimo, PRAYER_CONTACT_EMAIL = contato_email, PRAYER_CONTACT_PHONE = contato_telefone)
            session_db.add(novo_pedido)
            session_db.commit()
            return redirect(url_for('public.index'))

    return render_template('public/prayer/cadastrar_pedido_oracao.html', formulario=formulario)