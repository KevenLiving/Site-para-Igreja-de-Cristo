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
from models.admin_log import AdminLog
# Importando decorador que eu criei para impedir um usuário de entrar sem ter a autenticação de 2 fatores
from security.two_factor_authentication.decorador import adm_2af_required
# Importando outro decorador que eu criei para impedir que o adm comum acesse rotas exclusivas para administradores root
from security.root.permission import root_permission
# Formulário para funções de administração 
from templates.editor.flask_form.every_forms import Biblical_Study, UpBiblical_Study
from templates.editor.agenda.agenda_form import Weekly_Schedule
from templates.editor.devocional.devocional_form import Devotional_, DevotionalUpdate
from templates.editor.mensagens_videos.videos_form import Video_Message
from templates.editor.historia.historia_form import ChurchHistory_, ChurchHistoryUpdate
from templates.editor.departamento.departamento_form import Department_
from templates.editor.eventos.evento_form import Event_
from templates.editor.redes_sociais.social_form import SocialLink_
from templates.editor.prayer_request.prayer_manager_form import PrayerManager_
# Recursos extras para o trabalho de administração
import datetime
from datetime import date
import os
from werkzeug.utils import secure_filename
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from sqlalchemy import func
from flask import jsonify



administrador_bp = Blueprint('administrador', __name__, url_prefix='/admin')


# Aqui eu crio as funções iniciais que vão auxiliar nas rotas administrativas

def _serializar_valor_log(valor):
    """Converte valores do SQLAlchemy para tipos compatíveis com JSON."""
    if isinstance(valor, (datetime.datetime, datetime.date, datetime.time)):
        return valor.isoformat()


    if isinstance(valor, dict):
        return {str(chave): _serializar_valor_log(item) for chave, item in valor.items()}

    if isinstance(valor, (list, tuple, set)):
        return [_serializar_valor_log(item) for item in valor]



    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor

    return str(valor)


def _snapshot_log(objeto):
    """
    Cria uma cópia dos campos persistidos do objeto para old_values/new_values.
    Campos potencialmente sensíveis (senha, segredo, token etc.) não são gravados.
    """
    if objeto is None:
        return None
    dados = {}
    termos_sensiveis = ('PASSWORD', 'SECRET', 'TOKEN', 'TOTP', 'OTP_SECRET')

    for coluna in objeto.__table__.columns:
        nome = coluna.name

        if any(termo in nome.upper() for termo in termos_sensiveis):
            continue
        try:
            valor = getattr(objeto, coluna.key)
        except AttributeError:
            valor = getattr(objeto, nome, None)

        dados[nome] = _serializar_valor_log(valor)

    return dados


def _id_registro_log(objeto):
    """Obtém automaticamente o valor da chave primária do objeto."""
    if objeto is None:
        return None

    chaves = list(objeto.__table__.primary_key.columns)
    if not chaves:
        return None
    coluna_pk = chaves[0]


    try:
        return getattr(objeto, coluna_pk.key)
    except AttributeError:
        return getattr(objeto, coluna_pk.name, None)


def _registrar_log(session_db, acao, objeto=None, tabela=None, record_id=None,
                   old_values=None, new_values=None):
    """
    Registra a ação do administrador logado, incluindo IP e User-Agent.
    Usa o método AdminLog.registrar() já existente no projeto.
    """
    if not current_user or not getattr(current_user, 'is_authenticated', False):
        return None



    if objeto is not None:
        tabela = tabela or objeto.__tablename__
        record_id = record_id if record_id is not None else _id_registro_log(objeto)
    return AdminLog.registrar(
        session=session_db,
        admin_id=current_user.ADMIN_ID,
        acao=acao,
        tabela=tabela,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
        ip=request.remote_addr,
        user_agent=(request.user_agent.string[:255] if request.user_agent else None)
    )

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
# Página do administrador
@administrador_bp.route('/')
@adm_2af_required
def index():

    with SessionFactory() as session_db:

        administrador = current_user
        hoje = datetime.date.today()

        # Carregando os dados que serão apresentados na tela principal do painel administrativo
        administradores_ativos = (session_db.query(Administrador).filter(Administrador.ADMIN_ACTIVE == True).count())
        total_administradores = (session_db.query(Administrador).count())
        acessaram_hoje = (session_db.query(AdminLog.LOG_ADMIN_ID).filter(AdminLog.LOG_ACTION == 'login',func.date(AdminLog.LOG_CREATED_AT) == hoje).distinct().count())


        if current_user.ADMIN_ROLE == 'root':
            return render_template(
                'root_main.html',
                administrador=administrador,
                administradores_ativos=administradores_ativos,
                total_administradores=total_administradores,
                acessaram_hoje=acessaram_hoje
            )

        # Carregando dados para a navbar do adm
        partes_nome = (administrador.ADMIN_NAME or '').split()
        primeiro_nome = (partes_nome[0] if partes_nome else 'Administrador')
        iniciais_administrador = ''.join(parte[0] for parte in partes_nome[:2] if parte).upper() or 'AD'
        pregacoes_publicadas = (session_db.query(BiblicalStudy).filter(BiblicalStudy.STUDY_PUBLISHED == True).count())


        # Aqui eu carrego dados do que tem cadastrado/registrado no sistema
        videos_acervo = (session_db.query(VideoMessage).count())
        devocionais_agendados = (session_db.query(Devotional).filter(Devotional.DEVOTIONAL_WEEK_END >= hoje, Devotional.DEVOTIONAL_PUBLISHED == True).count())
        eventos_proximos = (session_db.query(Event).filter(Event.EVENT_DATE >= hoje).count())
        encontros_fixos = (session_db.query(WeeklySchedule).filter(WeeklySchedule.SCHEDULE_ACTIVE == True).count())

        hoje = date.today()
        pedidos_oracao = (
            session_db.query(PrayerRequest)
            .filter(func.date(PrayerRequest.PRAYER_CREATED_AT) == hoje)
            .all()
        )

        pedidos_oracao_contexto = 'hoje'
        pedidos_oracao_titulo = 'Pedidos de oração hoje'
        departamentos_ativos = (session_db.query(Department).filter(Department.DEPARTMENT_ACTIVE == True).count())
        capitulos_historia = (session_db.query(ChurchHistory).count())
        redes_sociais_ativas = (session_db.query(SocialLink).filter(SocialLink.SOCIAL_ACTIVE == True).count())


        # Aqui, como são muitos dados para serem carregados no painel administrativo, carreguei eles em formas de blocos
        return render_template(
            'admin_main.html',

            # Administrador
            administrador=administrador,
            primeiro_nome=primeiro_nome,
            iniciais_administrador=iniciais_administrador,

            # Conteúdo
            pregacoes_publicadas=pregacoes_publicadas,
            videos_acervo=videos_acervo,
            devocionais_agendados=devocionais_agendados,

            # Comunidade
            eventos_proximos=eventos_proximos,
            encontros_fixos=encontros_fixos,

            pedidos_oracao=pedidos_oracao,
            pedidos_oracao_contexto=pedidos_oracao_contexto,
            pedidos_oracao_titulo=pedidos_oracao_titulo,

            # Instituição
            departamentos_ativos=departamentos_ativos,
            capitulos_historia=capitulos_historia,
            redes_sociais_ativas=redes_sociais_ativas
        )
    
    
# ROTAS EXCLUSIVAS PARA USUÁRIOS ROOT

# Listar administradores
@administrador_bp.route('/listar_admins', methods=['GET'])
@adm_2af_required
@root_permission
def listar_admins():
    administrador = current_user
    with SessionFactory() as session_db:
        admins = session_db.query(Administrador).order_by(Administrador.ADMIN_CREATED_AT.desc()).all()
    return render_template('root_listar_admins.html', admins=admins, administrador=administrador)


# Cadastrar administrador
@administrador_bp.route('/cadastrar_adm', methods=['POST', 'GET'])
@adm_2af_required
@root_permission
def cadastrar_adm():
    administrador = current_user
    # Configurando formulário 
    formulario_cadastro = CadastroForm()
    # Recebendo dados do formulário
    if formulario_cadastro.validate_on_submit(): # Isso é melhor, pois veririfca se o formulário foi enviado com os dados já validados. 
        nome = request.form.get('nome')
        email = request.form.get('email')
        password = request.form.get('password')
        ativo = request.form.get('ativo')

        # Verificador de email 
        with SessionFactory() as db_session: 
            email_existente = db_session.query(Administrador).filter(Administrador.ADMIN_EMAIL == email).first()
            if email_existente:
                formulario_cadastro.email.errors = list(formulario_cadastro.email.errors)
                formulario_cadastro.email.errors.append('Este email já está cadastrado')
                return render_template('root_cadastrar_admin.html', formulario=formulario_cadastro, administrador=administrador)
                # return redirect(url_for('administrador.cadastrar_adm'))

    
        
        # Criando administrador
        novo_administrador = Administrador(ADMIN_NAME = nome, ADMIN_EMAIL = email, ADMIN_ACTIVE = True if ativo == 'ativo' else False)
        novo_administrador.set_password(password)
        # Salvando no banco 
        with SessionFactory() as session:
            session.add(novo_administrador)
            session.commit()

            # LOG: administrador criado
            _registrar_log(
                session,
                'create',
                objeto=novo_administrador,
                old_values=None,
                new_values=_snapshot_log(novo_administrador)
            )
    
        # Redirecionando para a página principal de administradores
        return redirect(url_for('administrador.index'))
    return render_template('root_cadastrar_admin.html', formulario=formulario_cadastro, administrador=administrador)


# Rota de redirecionamento de update
@administrador_bp.route('/redirectupdate_adm', methods=['POST', 'GET'])
@adm_2af_required
@root_permission
def redirectupdate_adm():
    # Pegando ID do usuário a ser atualizado
    user_id = request.args.get('user_id')

    # Página de opções de atualização
    return render_template('root/updatepage.html', user_id=user_id)


# Atualizar administrador 
@administrador_bp.route('/atualizar_adm', methods=['POST', 'GET'])
@adm_2af_required
@root_permission
def atualizar_adm():
    # Configurando formulário 
    formulario = AtualizarForm()
    administrador = current_user
    # Atualizando dados 
    if formulario.validate_on_submit():
        nome = request.form.get('nome')
        email = request.form.get('email')
        ativo = request.form.get('ativo')
        user_id = request.args.get('user_id')
        
        # Atualizando usuário
        with SessionFactory() as session_db:

            # Selecionando usuário
            administrador_selected = session_db.query(Administrador).filter(Administrador.ADMIN_ID==int(user_id)).first()

            # Verificando email 
            email_existente = session_db.query(Administrador).filter(Administrador.ADMIN_EMAIL == email).first()
            if email_existente and email != administrador_selected.ADMIN_EMAIL:
                formulario.email.errors = list(formulario.email.errors)
                formulario.email.errors.append('Este email já está cadastrado')
                return render_template('root_editar_admin.html', formulario=formulario, administrador_selected=administrador_selected, administrador=administrador)
            
            else:
                # LOG: estado anterior do administrador
                old_values_log = _snapshot_log(administrador_selected)

                # Atualizar o administrador
                administrador_selected.ADMIN_NAME = nome
                administrador_selected.ADMIN_EMAIL = email
                administrador_selected.ADMIN_ACTIVE = (True if ativo == 'ativo' else False)
                session_db.commit()

                # LOG: administrador atualizado
                _registrar_log(
                    session_db,
                    'update',
                    objeto=administrador_selected,
                    old_values=old_values_log,
                    new_values=_snapshot_log(administrador_selected)
                )

                # Redirecionando para o menu principal
                return redirect(url_for('administrador.index'))
            
        
    # Carregando ID do usuário
    user_id = request.args.get('user_id')
    if user_id:
        with SessionFactory() as session_db:
            administrador_selected = session_db.query(Administrador).filter(Administrador.ADMIN_ID==int(user_id)).first()
            if administrador_selected:
                # Definindo status (não tem como enviar pré carregado direto no template)
                formulario.nome.data = administrador_selected.ADMIN_NAME
                formulario.email.data = administrador_selected.ADMIN_EMAIL
                formulario.ativo.data = ('ativo' if administrador_selected.ADMIN_ACTIVE else 'desativo') 
                return render_template('root_editar_admin.html', formulario=formulario, administrador_selected=administrador_selected, administrador=administrador)
            else:
                return redirect(url_for('administrador.index'))
    else:
        return redirect(url_for('administrador.index'))
    
# Mudar senha do administrador 
@administrador_bp.route('/atualizarsenha_adm', methods=['POST', 'GET'])
@adm_2af_required
@root_permission
def atualizarsenha_adm():
    # Configurando formulário 
    formulario = PasswordUpdate()
    # Pegando ID do usuário selecionado 
    user_id = request.args.get('user_id')

    administrador = current_user
    # Pegando o administrador selecionado
    with SessionFactory() as session_db:
        administrador_selected = session_db.query(Administrador).filter(Administrador.ADMIN_ID == int(user_id)).first()

    if formulario.validate_on_submit():
        # Pegando dados do formulário
        password = request.form.get('password')
        if user_id:
            with SessionFactory() as session_db:
                administrador_selected = session_db.query(Administrador).filter(Administrador.ADMIN_ID == int(user_id)).first()
                if administrador_selected:
                    # LOG: estado anterior sem armazenar senha/sigilos
                    old_values_log = _snapshot_log(administrador_selected)

                    administrador_selected.set_password(password)
                    administrador_selected.ADMIN_TWO_FACTOR_FIRST = False
                    session_db.commit()

                    # LOG: alteração de senha (a senha nunca é armazenada no log)
                    new_values_log = _snapshot_log(administrador_selected)
                    new_values_log['CREDENCIAL'] = 'senha alterada'
                    old_values_log['CREDENCIAL'] = 'senha anterior preservada'
                    _registrar_log(
                        session_db,
                        'update',
                        objeto=administrador_selected,
                        old_values=old_values_log,
                        new_values=new_values_log
                    )

                    # Pegando o administrador root
                    administrador = current_user
                    # 1º) Se ele mudar senha de terceiro, ele volta ao painel principal
                    if administrador.ADMIN_ID != administrador_selected.ADMIN_ID:
                        return redirect(url_for('administrador.index'))
                    # 2º) Se ele tentar mudar a propria senha, ele volta para o painel de login para passar pela autenticação de 2 fatores e gerar o QR-CODE novamente
                    else:
                        return redirect(url_for('auth.deslogar_do_sistema'))
                        
        else:
            return redirect(url_for('administrador.index'))

    return render_template('root/atualizarsenha_adm.html', user_id=user_id, administrador_selected=administrador_selected, formulario=formulario, administrador=administrador)


# Excluir administrador
@administrador_bp.route('/excluir_adm', methods=['POST', 'GET'])
@adm_2af_required
@root_permission
def excluir_adm():
    administrador = current_user
    # Em caso de confirmação da exclusão
    if request.method == 'POST':

        # Pegando dados do formulário 
        senha = request.form.get('password')

        # Pegando ID
        user_id = request.args.get('user_id') 

        # Comparando a senha com a do administrador root
        administrador_root = current_user

        # Carregando usuário
        if user_id and int(user_id) != administrador_root.ADMIN_ID :
            with SessionFactory() as session_db:
                user_delete = session_db.query(Administrador).filter(Administrador.ADMIN_ID==int(user_id)).first()
                # Condicionais estão presentes no código para garantir funcionamento estável do sistema mesmo com falhas e não carregamento de ID ou usuários.
                if user_delete:
                    # LOG: salva os dados antes da exclusão
                    old_values_log = _snapshot_log(user_delete)
                    record_id_log = _id_registro_log(user_delete)

                    session_db.delete(user_delete)
                    session_db.commit()

                    # LOG: administrador excluído
                    _registrar_log(
                        session_db,
                        'delete',
                        tabela=Administrador.__tablename__,
                        record_id=record_id_log,
                        old_values=old_values_log,
                        new_values=None
                    )

                    # Retornando para o painel principal após ser deletado
                    return redirect(url_for('administrador.index'))
                else:
                    return redirect(url_for('administrador.index'))
        else:
            return redirect(url_for('administrador.index'))
        
        if administrador_root.check_password(administrador_root.ADMIN_EMAIL, senha):
            # Deletando usuário
            return f"Usuário do id: {user_id}, foi deletado com sucesso"
        else:
            flash('Digite a senha corretamente para realizar esta ação')
        with SessionFactory() as session_db:
                administrador_selected = session_db.query(Administrador).filter(Administrador.ADMIN_ID == identificador).first()
            return render_template('root_excluir_administrador.html', administrador_selected=administrador_selected, formulario=formulario, id=identificador, administrador=administrador)
  
    # Carregando formulário de senha de confirmação para execução
    formulario = PasswordConfirm()
    # Carregando dados do administrador selecionado para ser excluido
    identificador = int(request.args.get('id')) 
    with SessionFactory() as session_db:
        administrador_selected = session_db.query(Administrador).filter(Administrador.ADMIN_ID == identificador).first()
    return render_template('root_excluir_administrador.html', administrador_selected=administrador_selected, formulario=formulario, id=identificador, administrador=administrador)
    


# FUNÇÕES DE ADMINISTRAÇÃO

# FUNÇÕES DE ADMINISTRAÇÃO

# Listar pregações (estudos bíblicos)
@administrador_bp.route('/exibir_pregacoes', methods=['GET'])
@adm_2af_required
def exibir_pregacoes():

    administrador = current_user

    with SessionFactory() as session_db:
        pregacoes = (session_db.query(BiblicalStudy).order_by(BiblicalStudy.STUDY_CREATED_AT.desc()).all())
        total_pregacoes = len(pregacoes)
        publicadas = sum(1 for p in pregacoes if p.STUDY_PUBLISHED)
        rascunhos = total_pregacoes - publicadas
        em_destaque = sum(1 for p in pregacoes if p.STUDY_FEATURED)

    return render_template(
        'admin_pregacoes.html',
        administrador=administrador,
        pregacoes=pregacoes,
        total_pregacoes=total_pregacoes,
        publicadas=publicadas,
        rascunhos=rascunhos,
        em_destaque=em_destaque
    )


@administrador_bp.route('/cadastrar_estudo', methods=['POST', 'GET'])
@adm_2af_required
def cadastrar_estudo():
    # Configurando formulário 
    formulario = Biblical_Study()

    if formulario.validate_on_submit():
        # Pegando os valores obtidos pelo formulário
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        referencia = request.form.get('referencia')
        tema = request.form.get('tema')
        destaque = formulario.destaque.data
        publicar = formulario.publicar.data
        banner = formulario.banner.data

        # Aqui é para garantir que a pregação não venha vazia, porém mesmo se eu não digitar nada, o editor de texto retorna paragrafos, e eu tenho que garantir que ele não mande nada 
        if conteudo == '<p><br></p>':
            flash('Preencha o campo de conteúdo para realizar o cadastro do estudo')
            return render_template('admin_cadastrar_pregacao.html',formulario=formulario)

        # Salvando no banco de dados 
        with SessionFactory() as session_db:
            novo_estudo_biblico = BiblicalStudy(STUDY_TITLE = titulo, STUDY_CONTENT=conteudo, STUDY_BIBLICAL_REFERENCE = referencia, STUDY_THEME=tema, STUDY_FEATURED = destaque, STUDY_PUBLISHED = publicar, STUDY_ADMINISTRADOR_ID=current_user.ADMIN_ID)
            session_db.add(novo_estudo_biblico)
            session_db.flush()
            # Se a foto de estudo for enviada
            if banner:
                # Salvando a imagem
                extensao = os.path.splitext(secure_filename(banner.filename))[1]
                nome_foto = f'estudo_{novo_estudo_biblico.STUDY_ID}{extensao}'
                banner.save(
                    os.path.join(current_app.config['UPLOADS_FOLDER'], "estudos", nome_foto)
                )

                # Salvando caminho no banco de dados
                novo_estudo_biblico.STUDY_BANNER = nome_foto
              
            
            session_db.commit()

            # LOG: estudo bíblico criado
            _registrar_log(
                session_db,
                'create',
                objeto=novo_estudo_biblico,
                old_values=None,
                new_values=_snapshot_log(novo_estudo_biblico)
            )

            flash('Pregação cadastrada com sucesso.', 'success')
            return redirect(url_for('administrador.exibir_pregacoes'))


    return render_template('admin_cadastrar_pregacao.html',formulario=formulario)


@administrador_bp.route('/atualizar_estudo', methods=['POST', 'GET'])
@adm_2af_required
def atualizar_estudo():
    formulario = UpBiblical_Study()
    
    estudo_id = request.args.get('estudo_id')

    if request.method == 'POST':
        titulo     = request.form.get('titulo', '').strip()
        conteudo   = request.form.get('conteudo', '').strip()
        referencia = request.form.get('referencia', '').strip()
        tema       = request.form.get('tema', '').strip()
        destaque   = request.form.get('destaque') == 'on'
        publicar   = request.form.get('publicar') == 'on'
        banner     = request.files.get('banner')

        if not titulo:
            flash('O título é obrigatório.', 'danger')
            return redirect(url_for('administrador.atualizar_estudo', estudo_id=estudo_id))

        if not conteudo or conteudo == '<p><br></p>':
            flash('Preencha o campo de conteúdo.', 'danger')
            return redirect(url_for('administrador.atualizar_estudo', estudo_id=estudo_id))

        with SessionFactory() as session_db:
            estudo_selected = (
                session_db.query(BiblicalStudy)
                .filter(BiblicalStudy.STUDY_ID == int(estudo_id))
                .first()
            )
            if not estudo_selected:
                return redirect(url_for('administrador.exibir_pregacoes'))

            old_values_log = _snapshot_log(estudo_selected)

            # só troca banner se veio um arquivo novo de verdade
            if banner and banner.filename:
                extensao = os.path.splitext(secure_filename(banner.filename))[1]
                nome_foto = f'estudo_{estudo_selected.STUDY_ID}{extensao}'
                banner.save(os.path.join(
                    current_app.config['UPLOADS_FOLDER'], 'estudos', nome_foto
                ))
                estudo_selected.STUDY_BANNER = nome_foto

            estudo_selected.STUDY_TITLE = titulo
            estudo_selected.STUDY_CONTENT = conteudo
            estudo_selected.STUDY_BIBLICAL_REFERENCE = referencia
            estudo_selected.STUDY_THEME = tema
            estudo_selected.STUDY_FEATURED = destaque
            estudo_selected.STUDY_PUBLISHED = publicar

            session_db.commit()

            _registrar_log(
                session_db, 'update',
                objeto=estudo_selected,
                old_values=old_values_log,
                new_values=_snapshot_log(estudo_selected)
            )
            flash('Pregação atualizada com sucesso.', 'success')
            return redirect(url_for('administrador.exibir_pregacoes'))

   
    if not estudo_id:
        return redirect(url_for('administrador.exibir_pregacoes'))

    with SessionFactory() as session_db:
        estudo_selected = (
            session_db.query(BiblicalStudy)
            .filter(BiblicalStudy.STUDY_ID == int(estudo_id))
            .first()
        )
        if not estudo_selected:
            return redirect(url_for('administrador.exibir_pregacoes'))

        formulario.titulo.data     = estudo_selected.STUDY_TITLE
        formulario.conteudo.data   = estudo_selected.STUDY_CONTENT
        formulario.referencia.data = estudo_selected.STUDY_BIBLICAL_REFERENCE
        formulario.tema.data       = estudo_selected.STUDY_THEME
        formulario.destaque.data   = estudo_selected.STUDY_FEATURED
        formulario.publicar.data   = estudo_selected.STUDY_PUBLISHED
        
        return render_template(
            'admin_atualizar_pregacao.html',
            formulario=formulario,
            estudo_selected=estudo_selected,
        )

# Excluir estudo bíblico
@administrador_bp.route('/excluir_estudo', methods=['POST', 'GET'])
@adm_2af_required
def excluir_estudo():
    # Carregando formulário de senha de confirmação para execução
    formulario = PasswordConfirm()
    # Carregando dados do estudo selecionado para ser excluido
    identificador = int(request.args.get('estudo_id'))
    with SessionFactory() as session_db:
        estudo_selected = session_db.query(BiblicalStudy).filter(BiblicalStudy.STUDY_ID == identificador).first()

    if request.method == 'POST':

        # Pegando dados do formulário 
        senha = request.form.get('password')

        # Pegando ID
        estudo_id = request.args.get('estudo_id')

        # Pegando o administrador logado para confirmar a senha
        administrador = current_user

        # Carregando estudo
        if estudo_id:
            with SessionFactory() as session_db:
                estudo_delete = session_db.query(BiblicalStudy).filter(BiblicalStudy.STUDY_ID == int(estudo_id)).first()
                # Verificando se estudo existe para evitar erros de código que afetem a experiencia do usuário
                if estudo_delete:
                    if administrador.check_password(administrador.ADMIN_EMAIL, senha):
                        # LOG: salva os dados antes da exclusão
                        old_values_log = _snapshot_log(estudo_delete)
                        record_id_log = _id_registro_log(estudo_delete)

                        session_db.delete(estudo_delete)
                        session_db.commit()

                        # LOG: estudo bíblico excluído
                        _registrar_log(
                            session_db,
                            'delete',
                            tabela=BiblicalStudy.__tablename__,
                            record_id=record_id_log,
                            old_values=old_values_log,
                            new_values=None
                        )

                        # Retornando para a listagem de pregações após ser deletado
                        flash('Pregação excluída com sucesso.', 'success')
                        return redirect(url_for('administrador.exibir_pregacoes'))
                    else:
                        flash('Senha incorreta, por favor, digite novamente')
                        return render_template('admin_excluir_pregacao.html', estudo_selected=estudo_selected, formulario=formulario, id=identificador)
                else:
                    return redirect(url_for('administrador.exibir_pregacoes'))
        else:
            return redirect(url_for('administrador.exibir_pregacoes'))

    
    return render_template('admin_excluir_pregacao.html', estudo_selected=estudo_selected, formulario=formulario, id=identificador)


# AGENDA DA SEMANA

# Para facilitar e deixar o processo mais automático, as listas e dicionários aqui feitas serão carregadas com jinja no html para carregar e facilitar o manuseio da agenda

# Aqui está a lista de dias na semana com ordem de exibição padrão de segunda a domingo
ORDEM_DIAS = [
    'Segunda-feira', 'Terça-feira', 'Quarta-feira',
    'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo',
]

# Ordem para o botão-picker do form (Dom → Sáb — ordem clássica de calendário)
ORDEM_PICKER = [
    'Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira',
    'Quinta-feira', 'Sexta-feira', 'Sábado',
]

# Aqui são as siglas que são exibidas na hora de cadastrar algo na agenda
DIAS_INFO = {
    'Segunda-feira': {'sigla': 'S', 'abrev': 'Seg', 'sub_padrao': 'Início da semana'},
    'Terça-feira':   {'sigla': 'T', 'abrev': 'Ter', 'sub_padrao': None},
    'Quarta-feira':  {'sigla': 'Q', 'abrev': 'Qua', 'sub_padrao': None},
    'Quinta-feira':  {'sigla': 'Q', 'abrev': 'Qui', 'sub_padrao': None},
    'Sexta-feira':   {'sigla': 'S', 'abrev': 'Sex', 'sub_padrao': None},
    'Sábado':        {'sigla': 'S', 'abrev': 'Sáb', 'sub_padrao': None},
    'Domingo':       {'sigla': 'D', 'abrev': 'Dom', 'sub_padrao': 'Dia do Senhor'},
}


def _lista_existentes(session_db, ignorar_id=None):
    query = session_db.query(WeeklySchedule)
    if ignorar_id:
        query = query.filter(WeeklySchedule.SCHEDULE_ID != ignorar_id)
    return [
        {
            'dia': e.SCHEDULE_DAY,
            'hora': e.SCHEDULE_TIME.strftime('%H:%M') if e.SCHEDULE_TIME else '',
            'titulo': e.SCHEDULE_TITLE,
        }
        for e in query.all()
    ]

def _lista_picker():
    return [
        {'nome': d, 'abrev': DIAS_INFO[d]['abrev']}
        for d in ORDEM_PICKER
    ]




def _bool_form(nome):
    return request.form.get(nome) in ('y', 'on', '1', 'true', 'True')


# EXIBIR AGENDA
@administrador_bp.route('/exibir_agenda', methods=['GET'])
@adm_2af_required
def exibir_agenda():
    administrador = current_user

    with SessionFactory() as session_db:
        encontros = (
            session_db.query(WeeklySchedule)
            .order_by(WeeklySchedule.SCHEDULE_TIME.asc())
            .all()
        )

        encontros_ativos = sum(1 for e in encontros if e.SCHEDULE_ACTIVE)
        encontros_desativados = sum(1 for e in encontros if not e.SCHEDULE_ACTIVE)
        dias_com_programacao = len({e.SCHEDULE_DAY for e in encontros})
        locais_diferentes = len({
            e.SCHEDULE_LOCATION for e in encontros
            if e.SCHEDULE_LOCATION
        })

        # Agrupa por dia mantendo ordem cronológica dentro de cada dia
        encontros_por_dia = {d: [] for d in ORDEM_DIAS}
        for e in encontros:
            if e.SCHEDULE_DAY in encontros_por_dia:
                encontros_por_dia[e.SCHEDULE_DAY].append(e)

        dias_semana = []
        for nome_dia in ORDEM_DIAS:
            encontros_dia = encontros_por_dia[nome_dia]
            ativos = sum(1 for e in encontros_dia if e.SCHEDULE_ACTIVE)
            dias_semana.append({
                'nome': nome_dia,
                'sigla': DIAS_INFO[nome_dia]['sigla'],
                'abrev': DIAS_INFO[nome_dia]['abrev'],
                'sub_padrao': DIAS_INFO[nome_dia]['sub_padrao'],
                'encontros': encontros_dia,
                'ativos': ativos,
                'inativos': len(encontros_dia) - ativos,
            })

    return render_template(
        'admin_agenda.html',
        administrador=administrador,
        dias_semana=dias_semana,
        encontros_ativos=encontros_ativos,
        encontros_desativados=encontros_desativados,
        dias_com_programacao=dias_com_programacao,
        locais_diferentes=locais_diferentes,
    )


# ADICIONAR ENCONTRO
@administrador_bp.route('/adicionar_agenda', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_agenda():
    formulario = Weekly_Schedule()

    # Pré-seleção do dia via querystring (do botão + em cada card do menu)
    dia_preselecionado = request.args.get('dia', '').strip()
    if dia_preselecionado not in DIAS_INFO:
        dia_preselecionado = None

    with SessionFactory() as session_db:
        existentes = _lista_existentes(session_db)

    def _renderizar(msg=None, categoria='danger'):
        if msg:
            flash(msg, categoria)
        return render_template(
            'admin_cadastrar_agenda.html',
            formulario=formulario,
            dias_lista=_lista_picker(),
            dia_preselecionado=dia_preselecionado,
            existentes=existentes,
        )

    if formulario.validate_on_submit():
        titulo = (request.form.get('titulo') or '').strip()
        descricao = (request.form.get('descricao') or '').strip() or None
        local = (request.form.get('local') or '').strip() or None
        dia = (request.form.get('dia') or '').strip()
        hora = formulario.hora.data
        activate = _bool_form('activate') or bool(formulario.activate.data)

        # Validações
        if not titulo:
            return _renderizar('Informe o nome do encontro.')
        if dia not in DIAS_INFO:
            return _renderizar('Escolha um dia da semana válido.')
        if not hora:
            return _renderizar('Informe o horário.')

        with SessionFactory() as session_db:
            # Conflito no mesmo dia + mesmo horário
            conflito = (
                session_db.query(WeeklySchedule)
                .filter(
                    WeeklySchedule.SCHEDULE_DAY == dia,
                    WeeklySchedule.SCHEDULE_TIME == hora,
                )
                .first()
            )
            if conflito:
                return _renderizar(
                    f'Já existe "{conflito.SCHEDULE_TITLE}" na {dia} '
                    f'às {hora.strftime("%H:%M")}. Escolha outro horário.'
                )

            novo = WeeklySchedule(
                SCHEDULE_TITLE=titulo,
                SCHEDULE_DAY=dia,
                SCHEDULE_TIME=hora,
                SCHEDULE_LOCATION=local,
                SCHEDULE_DESCRIPTION=descricao,
                SCHEDULE_ACTIVE=activate,
                SCHEDULE_ADMINISTRADOR_ID=current_user.ADMIN_ID,
            )
            session_db.add(novo)
            session_db.commit()

            _registrar_log(
                session_db, 'create',
                objeto=novo,
                old_values=None,
                new_values=_snapshot_log(novo),
            )

            flash(f'"{titulo}" cadastrado com sucesso.', 'success')
            return redirect(url_for('administrador.exibir_agenda'))

    return _renderizar()


# ATUALIZAR ENCONTRO
@administrador_bp.route('/atualizar_agenda', methods=['POST', 'GET'])
@adm_2af_required
def atualizar_agenda():
    formulario = Weekly_Schedule()
    agenda_id = request.args.get('agenda_id', type=int)

    if not agenda_id:
        return redirect(url_for('administrador.exibir_agenda'))

    with SessionFactory() as session_db:
        agenda = (
            session_db.query(WeeklySchedule)
            .filter(WeeklySchedule.SCHEDULE_ID == agenda_id)
            .first()
        )
        if not agenda:
            flash('Encontro não encontrado.', 'danger')
            return redirect(url_for('administrador.exibir_agenda'))

        existentes = _lista_existentes(session_db, ignorar_id=agenda_id)

    def _renderizar(msg=None, categoria='danger'):
        if msg:
            flash(msg, categoria)
        return render_template(
            'admin_atualizar_agenda.html',
            formulario=formulario,
            agenda=agenda,
            dias_lista=_lista_picker(),
            dias_info=DIAS_INFO,
            existentes=existentes,
        )

    # POST — atualizar
    if formulario.validate_on_submit():
        titulo = (request.form.get('titulo') or '').strip()
        descricao = (request.form.get('descricao') or '').strip() or None
        local = (request.form.get('local') or '').strip() or None
        dia = (request.form.get('dia') or '').strip()
        hora = formulario.hora.data
        activate = _bool_form('activate') or bool(formulario.activate.data)

        if not titulo:
            return _renderizar('Informe o nome do encontro.')
        if dia not in DIAS_INFO:
            return _renderizar('Escolha um dia da semana válido.')
        if not hora:
            return _renderizar('Informe o horário.')

        with SessionFactory() as session_db:
            agenda_db = (
                session_db.query(WeeklySchedule)
                .filter(WeeklySchedule.SCHEDULE_ID == agenda_id)
                .first()
            )
            if not agenda_db:
                flash('Encontro não encontrado.', 'danger')
                return redirect(url_for('administrador.exibir_agenda'))

            # Conflito no mesmo dia+hora, ignorando o próprio registro
            conflito = (
                session_db.query(WeeklySchedule)
                .filter(
                    WeeklySchedule.SCHEDULE_DAY == dia,
                    WeeklySchedule.SCHEDULE_TIME == hora,
                    WeeklySchedule.SCHEDULE_ID != agenda_id,
                )
                .first()
            )
            if conflito:
                return _renderizar(
                    f'Já existe "{conflito.SCHEDULE_TITLE}" na {dia} '
                    f'às {hora.strftime("%H:%M")}. Escolha outro horário.'
                )

            old_values_log = _snapshot_log(agenda_db)

            agenda_db.SCHEDULE_TITLE = titulo
            agenda_db.SCHEDULE_DESCRIPTION = descricao
            agenda_db.SCHEDULE_LOCATION = local
            agenda_db.SCHEDULE_DAY = dia
            agenda_db.SCHEDULE_TIME = hora
            agenda_db.SCHEDULE_ACTIVE = activate
            session_db.commit()

            _registrar_log(
                session_db, 'update',
                objeto=agenda_db,
                old_values=old_values_log,
                new_values=_snapshot_log(agenda_db),
            )

            flash(f'"{titulo}" atualizado com sucesso.', 'success')
            return redirect(url_for('administrador.exibir_agenda'))

    # GET — pré-preenche
    formulario.titulo.data = agenda.SCHEDULE_TITLE
    formulario.descricao.data = agenda.SCHEDULE_DESCRIPTION
    formulario.local.data = agenda.SCHEDULE_LOCATION
    formulario.dia.data = agenda.SCHEDULE_DAY
    formulario.hora.data = agenda.SCHEDULE_TIME
    formulario.activate.data = agenda.SCHEDULE_ACTIVE

    return _renderizar()


# ALTERNAR ATIVO/INATIVO (botão play/pause do menu)
@administrador_bp.route('/alternar_agenda/<int:agenda_id>', methods=['POST'])
@adm_2af_required
def alternar_agenda(agenda_id):
    with SessionFactory() as session_db:
        agenda = (
            session_db.query(WeeklySchedule)
            .filter(WeeklySchedule.SCHEDULE_ID == agenda_id)
            .first()
        )
        if not agenda:
            flash('Encontro não encontrado.', 'danger')
            return redirect(url_for('administrador.exibir_agenda'))

        old_values_log = _snapshot_log(agenda)
        agenda.SCHEDULE_ACTIVE = not agenda.SCHEDULE_ACTIVE
        session_db.commit()

        _registrar_log(
            session_db, 'update',
            objeto=agenda,
            old_values=old_values_log,
            new_values=_snapshot_log(agenda),
        )

        estado = 'reativado' if agenda.SCHEDULE_ACTIVE else 'pausado'
        flash(f'"{agenda.SCHEDULE_TITLE}" {estado} com sucesso.', 'success')

    return redirect(url_for('administrador.exibir_agenda'))


# EXCLUIR ENCONTRO
@administrador_bp.route('/excluir_agenda', methods=['POST', 'GET'])
@adm_2af_required
def excluir_agenda():
    agenda_id = request.args.get('agenda_id', type=int)

    if not agenda_id:
        return redirect(url_for('administrador.exibir_agenda'))

    with SessionFactory() as session_db:
        agenda = (
            session_db.query(WeeklySchedule)
            .filter(WeeklySchedule.SCHEDULE_ID == agenda_id)
            .first()
        )
        if not agenda:
            flash('Encontro não encontrado.', 'danger')
            return redirect(url_for('administrador.exibir_agenda'))

        titulo = agenda.SCHEDULE_TITLE
        old_values_log = _snapshot_log(agenda)
        record_id_log = _id_registro_log(agenda)

        session_db.delete(agenda)
        session_db.commit()

        _registrar_log(
            session_db, 'delete',
            tabela=WeeklySchedule.__tablename__,
            record_id=record_id_log,
            old_values=old_values_log,
            new_values=None,
        )

        flash(f'"{titulo}" excluído com sucesso.', 'success')

    return redirect(url_for('administrador.exibir_agenda'))


# ADMINISTRANDO DEVOCIONAIS 

# Exibir devocionais
@administrador_bp.route('/exibir_devocionais', methods=['GET'])
@adm_2af_required
def exibir_devocionais():
    hoje = datetime.date.today()

    with SessionFactory() as session_db:
        devocionais = (
            session_db.query(Devotional)
            .order_by(Devotional.DEVOTIONAL_WEEK_START.desc())
            .all()
        )
        # Separando por status
        no_ar     = []
        agendados = []
        historico = []

        for d in devocionais:
            inicio = d.DEVOTIONAL_WEEK_START
            fim    = d.DEVOTIONAL_WEEK_END

            if inicio <= hoje <= fim and d.DEVOTIONAL_PUBLISHED:
                no_ar.append(d)
            elif inicio > hoje:
                agendados.append(d)
            else:
                historico.append(d)

        # ordena agendados por proximidade (menor data primeiro)
        agendados.sort(key=lambda d: d.DEVOTIONAL_WEEK_START)

    return render_template(
        'admin_devocionais.html',
        no_ar=no_ar,
        agendados=agendados,
        historico=historico,
        hoje=hoje,
    )

# ADICIONAR DEVOCIONAL 
@administrador_bp.route('/adicionar_devocional', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_devocional():
    # Carregando dados necessários 
    formulario = Devotional_()
    # Definindo data minima para o periodo de exibição do devocional
    hoje = datetime.date.today().isoformat()

    # Períodos já ocupados por outros devocionais (para bloquear no calendário)
    with SessionFactory() as session_db:
        ocupados = [
            {'inicio': d.DEVOTIONAL_WEEK_START.isoformat(),
             'fim':    d.DEVOTIONAL_WEEK_END.isoformat()}
            for d in session_db.query(Devotional).all()
        ]

    # Adicionando novo devocional
    if formulario.validate_on_submit():
        titulo    = request.form.get('titulo')
        conteudo  = request.form.get('conteudo')
        versiculo = request.form.get('versiculo')
        banner    = formulario.banner.data
        inicio    = formulario.inicio.data
        fim       = formulario.fim.data
        publicar  = formulario.publicar.data

        # Salvando devocional 
        with SessionFactory() as session_db:
            devocional_verify = session_db.query(Devotional).filter(
                Devotional.DEVOTIONAL_WEEK_START <= fim,
                Devotional.DEVOTIONAL_WEEK_END >= inicio
            ).first()

            if devocional_verify:
                flash('Data indisponível, tente outro periodo')
                formulario.titulo.data    = titulo
                formulario.conteudo.data  = conteudo
                formulario.versiculo.data = versiculo
                formulario.publicar.data  = publicar
                return render_template(
                    'admin_cadastrar_devocional.html',
                    formulario=formulario, hoje=hoje, ocupados=ocupados
                )

            # Salvando no banco de dados
            devotional = Devotional(
                DEVOTIONAL_TITLE=titulo,
                DEVOTIONAL_CONTENT=conteudo,
                DEVOTIONAL_BIBLICAL_VERSE=versiculo,
                DEVOTIONAL_WEEK_START=inicio,
                DEVOTIONAL_WEEK_END=fim,
                DEVOTIONAL_ADMINISTRADOR_ID=current_user.ADMIN_ID,
                DEVOTIONAL_PUBLISHED=publicar
            )
            session_db.add(devotional)
            session_db.commit()

            # Salvando a imagem
            extensao = os.path.splitext(secure_filename(banner.filename))[1]
            nome_banner = f'devocional_{devotional.DEVOTIONAL_ID}{extensao}'
            banner.save(
                os.path.join(current_app.config['UPLOADS_FOLDER'], "devocionais", nome_banner)
            )

            devotional.DEVOTIONAL_BANNER = nome_banner
            session_db.commit()

            # LOG: devocional criado
            _registrar_log(
                session_db,
                'create',
                objeto=devotional,
                old_values=None,
                new_values=_snapshot_log(devotional)
            )

            return redirect(url_for('administrador.exibir_devocionais'))

    # Carregando a página de cadastro
    return render_template(
        'admin_cadastrar_devocional.html',
        formulario=formulario, hoje=hoje, ocupados=ocupados
    )

@administrador_bp.route('/editar_devocional', methods=['POST', 'GET'])
@adm_2af_required
def editar_devocional():
    formulario = DevotionalUpdate()
    devocional_id = request.args.get('devocional_id')

    if not devocional_id:
        return redirect(url_for('administrador.exibir_devocionais'))

    # Carrega o devocional e a lista de períodos ocupados por OUTROS devocionais
    with SessionFactory() as session_db:
        devocional_selecionado = (
            session_db.query(Devotional)
            .filter(Devotional.DEVOTIONAL_ID == int(devocional_id))
            .first()
        )
        if not devocional_selecionado:
            return redirect(url_for('administrador.exibir_devocionais'))

        ocupados = [
            {'inicio': d.DEVOTIONAL_WEEK_START.isoformat(),
             'fim':    d.DEVOTIONAL_WEEK_END.isoformat()}
            for d in session_db.query(Devotional)
                .filter(Devotional.DEVOTIONAL_ID != int(devocional_id)).all()
        ]

    # POST — atualizar
    if formulario.validate_on_submit():
        titulo    = request.form.get('titulo')
        conteudo  = request.form.get('conteudo')
        versiculo = request.form.get('versiculo')
        banner    = formulario.banner.data
        inicio    = formulario.inicio.data
        fim       = formulario.fim.data
        publicar  = formulario.publicar.data

        with SessionFactory() as session_db:
            devotional = (
                session_db.query(Devotional)
                .filter(Devotional.DEVOTIONAL_ID == int(devocional_id))
                .first()
            )
            old_values_log = _snapshot_log(devotional)

            permitido, mensagem = devotional.can_update_period(inicio, fim)
            if not permitido:
                flash(mensagem)
                return render_template(
                    'admin_atualizar_devocional.html',
                    formulario=formulario,
                    devocional=devotional,
                    ocupados=ocupados,
                )

            conflito = session_db.query(Devotional).filter(
                Devotional.DEVOTIONAL_ID != devotional.DEVOTIONAL_ID,
                Devotional.DEVOTIONAL_WEEK_START <= fim,
                Devotional.DEVOTIONAL_WEEK_END >= inicio
            ).first()
            if conflito:
                flash('Já existe devocional reservado neste horário')
                return render_template(
                    'admin_atualizar_devocional.html',
                    formulario=formulario,
                    devocional=devotional,
                    ocupados=ocupados,
                )

            devotional.DEVOTIONAL_TITLE = titulo
            devotional.DEVOTIONAL_CONTENT = conteudo
            devotional.DEVOTIONAL_BIBLICAL_VERSE = versiculo
            devotional.DEVOTIONAL_WEEK_START = inicio
            devotional.DEVOTIONAL_WEEK_END = fim
            devotional.DEVOTIONAL_ADMINISTRADOR_ID = current_user.ADMIN_ID
            devotional.DEVOTIONAL_PUBLISHED = publicar
            session_db.commit()

            if banner:
                if devotional.DEVOTIONAL_BANNER:
                    caminho = os.path.join(
                        current_app.config['UPLOADS_FOLDER'],
                        'devocionais',
                        devotional.DEVOTIONAL_BANNER
                    )
                    if os.path.exists(caminho):
                        os.remove(caminho)

                extensao = os.path.splitext(secure_filename(banner.filename))[1]
                nome_banner = f'devocional_{devotional.DEVOTIONAL_ID}{extensao}'
                banner.save(os.path.join(
                    current_app.config['UPLOADS_FOLDER'], 'devocionais', nome_banner
                ))
                devotional.DEVOTIONAL_BANNER = nome_banner
                session_db.commit()

            _registrar_log(
                session_db, 'update',
                objeto=devotional,
                old_values=old_values_log,
                new_values=_snapshot_log(devotional)
            )

            flash('Devocional atualizado com sucesso.', 'success')
            return redirect(url_for('administrador.exibir_devocionais'))

    # GET — pré-carrega o form
    formulario.titulo.data    = devocional_selecionado.DEVOTIONAL_TITLE
    formulario.conteudo.data  = devocional_selecionado.DEVOTIONAL_CONTENT
    formulario.versiculo.data = devocional_selecionado.DEVOTIONAL_BIBLICAL_VERSE
    formulario.inicio.data    = devocional_selecionado.DEVOTIONAL_WEEK_START
    formulario.fim.data       = devocional_selecionado.DEVOTIONAL_WEEK_END
    formulario.publicar.data  = devocional_selecionado.DEVOTIONAL_PUBLISHED

    return render_template(
        'admin_atualizar_devocional.html',
        formulario=formulario,
        devocional=devocional_selecionado,
        ocupados=ocupados,
    )

# Excluir devocional
@administrador_bp.route('/excluir_devocional', methods=['POST', 'GET'])
@adm_2af_required
def excluir_devocional():
    # Recebendo ID do devocional a ser excluida
    devocional_id = request.args.get('devocional_id')

    if devocional_id:
        # Excluindo agenda
        with SessionFactory() as session_db:
            devocional_selecionado = session_db.query(Devotional).filter(Devotional.DEVOTIONAL_ID == int(devocional_id)).first()
            if devocional_selecionado:
                # LOG: salva os dados antes da exclusão
                old_values_log = _snapshot_log(devocional_selecionado)
                record_id_log = _id_registro_log(devocional_selecionado)

                session_db.delete(devocional_selecionado)
                session_db.commit()

                # LOG: devocional excluído
                _registrar_log(
                    session_db,
                    'delete',
                    tabela=Devotional.__tablename__,
                    record_id=record_id_log,
                    old_values=old_values_log,
                    new_values=None
                )

                return redirect(url_for('administrador.exibir_devocionais'))
            else:
                return redirect(url_for('administrador.exibir_devocionais'))
            
    else:
        return redirect(url_for('administrador.exibir_devocionais'))
    





# FUNÇÕES DE ADMINISTRAÇÃO - VÍDEOS/MENSAGENS

@administrador_bp.route('/exibir_videos', methods=['GET'])
@adm_2af_required
def exibir_videos():
    with SessionFactory() as session_db:
        videos = (
            session_db.query(VideoMessage)
            .order_by(VideoMessage.VIDEO_CREATED_AT.desc())
            .all()
        )

        total      = len(videos)
        publicados = sum(1 for v in videos if v.VIDEO_PUBLISHED)
        rascunhos  = total - publicados
        destaques  = sum(1 for v in videos if v.VIDEO_FEATURED)
        pregadores = sorted({v.VIDEO_PREACHER for v in videos if v.VIDEO_PREACHER})

        # >>> categorias vindas do form (fonte única)
        categorias = Video_Message().categoria.choices

        return render_template(
            'admin_videos.html',
            videos=videos,
            stats={'total': total, 'publicados': publicados,
                   'rascunhos': rascunhos, 'destaques': destaques},
            pregadores=pregadores,
            categorias=categorias,
        )

    
# Cadastrar vídeo
@administrador_bp.route('/cadastrar_video', methods=['POST', 'GET'])
@adm_2af_required
def cadastrar_video():
    # Configurando formulário
    formulario = Video_Message()

    if formulario.validate_on_submit():
        
        # Pegando os valores obtidos pelo formulário
        titulo = request.form.get('titulo')
        url = request.form.get('url')
        pregador = request.form.get('pregador')
        categoria = formulario.categoria.data
        destaque = formulario.destaque.data
        publicar = formulario.publicar.data

        # Verificando se a URL foi repassada no campo
        if not url:
            flash('Preencha o campo de URL para realizar o cadastro do vídeo')
            return render_template('admin_cadastrar_video.html', formulario=formulario)

        # Validando se a URL aponta para um vídeo mesmo
        def url_validator(url):
            try:
                with YoutubeDL({"quiet": True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                
                return info.get("extractor") == "youtube" # Isso aqui retorna True se for um vídeo do Youtube
            
            except DownloadError:
                return False
        

        if not url_validator(url):
            flash("Informe uma URL válida de um vídeo do YouTube.", "error")
            formulario.titulo.data = titulo
            formulario.url.data = url
            formulario.pregador.data = pregador
            formulario.categoria.data = categoria
            formulario.destaque.data = destaque
            formulario.publicar.data = publicar
            return render_template('admin_cadastrar_video.html', formulario=formulario)
            
        with YoutubeDL({"quiet": True}) as ydl: # Essa biblioteca é perfeita pois extrai informações com base na url
            info = ydl.extract_info(url, download=False)
        # Pegando duração e capa diretamente da plataforma do youtube, evitando que o administrador do site tenha que perder tempo digitando
        duracao = info['duration'] # Extraindo a duração em segundos 
        thumbnail = info['thumbnail'] # Extraindo link da foto da capa

        # Salvando no banco de dados
        with SessionFactory() as session_db:
            novo_video = VideoMessage(VIDEO_TITLE=titulo, VIDEO_URL=url, VIDEO_THUMBNAIL=thumbnail, VIDEO_DURATION=int(duracao) if duracao else None, VIDEO_PREACHER=pregador, VIDEO_CATEGORY=categoria, VIDEO_FEATURED=destaque, VIDEO_PUBLISHED=publicar, VIDEO_ADMINISTRADOR_ID=current_user.ADMIN_ID)
            session_db.add(novo_video)
            session_db.commit()

            # LOG: vídeo criado
            _registrar_log(
                session_db,
                'create',
                objeto=novo_video,
                old_values=None,
                new_values=_snapshot_log(novo_video)
            )

            return redirect(url_for('administrador.exibir_videos'))

    return render_template('admin_cadastrar_video.html', formulario=formulario)


# Atualizar vídeo
@administrador_bp.route('/atualizar_video', methods=['POST', 'GET'])
@adm_2af_required
def atualizar_video():
    formulario = Video_Message()

    # Pegando ID do vídeo a ser atualizado
    video_id = request.args.get('video_id')

    if formulario.validate_on_submit():
        # Carregando os valores obtidos no formulário
        titulo = request.form.get('titulo')
        url = request.form.get('url')
        pregador = request.form.get('pregador')
        categoria = request.form.get('categoria')
        destaque = formulario.destaque.data
        publicar = formulario.publicar.data

        # Atualizando vídeo
        with SessionFactory() as session_db:
            video_selected = session_db.query(VideoMessage).filter(VideoMessage.VIDEO_ID == int(video_id)).first()

            # LOG: estado anterior do vídeo
            old_values_log = _snapshot_log(video_selected)

            # Verificando se URL foi carregada
            if not url:
                flash('Preencha o campo de URL para realizar o cadastro do vídeo')
                return redirect(url_for('administrador.atualizar_video', video_selected=video_selected))
            
            # Verificando se a thumbnail foi alterada. Aqui eu basicamente repito o mesmo código de validar a URL, e verificar a THUMBNAIL em casos de alterações, e também se o administrador errou no link, ai ele troca a thumbnail e a duração
            # Validando se a URL aponta para um vídeo mesmo
            def url_validator(url):
                try:
                    with YoutubeDL({"quiet": True}) as ydl:
                        info = ydl.extract_info(url, download=False)
                    
                    return info.get("extractor") == "youtube" # Isso aqui retorna True se for um vídeo do Youtube
                
                except DownloadError:
                    return False
            

            if not url_validator(url):
                flash("Informe uma URL válida de um vídeo do YouTube.", "error")
                formulario.titulo.data = titulo
                formulario.url.data = url
                formulario.pregador.data = pregador
                formulario.categoria.data = categoria
                formulario.destaque.data = destaque
                formulario.publicar.data = publicar
                return render_template('admin_atualizar_video.html', formulario=formulario, video_selected=video_selected)
                
            with YoutubeDL({"quiet": True}) as ydl: # Essa biblioteca é perfeita pois extrai informações com base na url
                info = ydl.extract_info(url, download=False)
            
            # Pegando duração e capa diretamente da plataforma do youtube, evitando que o administrador do site tenha que perder tempo digitando
            duracao = info['duration'] # Extraindo a duração em segundos 
            thumbnail = info['thumbnail'] # Extraindo link da foto da capa

            if video_selected:
                video_selected.VIDEO_TITLE = titulo
                video_selected.VIDEO_URL = url
                video_selected.VIDEO_THUMBNAIL = thumbnail
                video_selected.VIDEO_DURATION = duracao
                video_selected.VIDEO_PREACHER = pregador
                video_selected.VIDEO_CATEGORY = categoria
                video_selected.VIDEO_FEATURED = destaque
                video_selected.VIDEO_PUBLISHED = publicar
                session_db.commit()

                # LOG: vídeo atualizado
                _registrar_log(
                    session_db,
                    'update',
                    objeto=video_selected,
                    old_values=old_values_log,
                    new_values=_snapshot_log(video_selected)
                )

                # Redirecionando para a rota de gerenciamento de vídeos
                return redirect(url_for('administrador.exibir_videos'))
            else:
                return redirect(url_for('administrador.exibir_videos'))

    # Carregando dados do vídeo selecionado
    if video_id:
        with SessionFactory() as session_db:
            video_selected = session_db.query(VideoMessage).filter(VideoMessage.VIDEO_ID == int(video_id)).first()
            if video_selected:
                # Aqui é o que diferencia o sistema, onde eu carrego os dados de forma pré-carregada no proprio formulario
                formulario.titulo.data = video_selected.VIDEO_TITLE
                formulario.url.data = video_selected.VIDEO_URL
                formulario.pregador.data = video_selected.VIDEO_PREACHER
                formulario.categoria.data = video_selected.VIDEO_CATEGORY
                formulario.destaque.data = video_selected.VIDEO_FEATURED
                formulario.publicar.data = video_selected.VIDEO_PUBLISHED
                return render_template('admin_atualizar_video.html', formulario=formulario, video_selected=video_selected)
            else:
                return redirect(url_for('administrador.exibir_videos'))
    else:
        return redirect(url_for('administrador.exibir_videos'))


# Excluir vídeo
@administrador_bp.route('/excluir_video', methods=['POST', 'GET'])
@adm_2af_required
def excluir_video():
    # Pegando o ID do vídeo a ser excluído
    identificador = int(request.args.get('video_id'))
    with SessionFactory() as session_db:
        video_selected = session_db.query(VideoMessage).filter(VideoMessage.VIDEO_ID == identificador).first()
        if video_selected:
            # LOG: salva os dados antes da exclusão
            old_values_log = _snapshot_log(video_selected)
            record_id_log = _id_registro_log(video_selected)

            session_db.delete(video_selected)
            session_db.commit()

            # LOG: vídeo excluído
            _registrar_log(
                session_db,
                'delete',
                tabela=VideoMessage.__tablename__,
                record_id=record_id_log,
                old_values=old_values_log,
                new_values=None
            )

            return redirect(url_for('administrador.exibir_videos')) 

        else:
            return redirect(url_for('administrador.exibir_videos'))



# SETOR DE HISTÓRIA DA IGREJA

# Essa função aqui é com o intuito de montar um caminho absoluto para a localização da imagem dentro do arquivo
def _caminho_imagem_historia(nome_arquivo):
    return os.path.join(
        current_app.config['UPLOADS_FOLDER'],
        'historia',
        nome_arquivo
    )

# Exibir etapas da história
@administrador_bp.route('/exibir_historia', methods=['GET'])
@adm_2af_required
def exibir_historia():
    ano_atual = datetime.date.today().year

    with SessionFactory() as session_db:
        historia = (
            session_db.query(ChurchHistory)
            .order_by(
                ChurchHistory.HISTORY_ORDER.asc(),
                ChurchHistory.HISTORY_YEAR_START.asc()
            )
            .all()
        )

        # Anos totais de história (do capítulo mais antigo até hoje)
        if historia:
            primeiro_ano = min(e.HISTORY_YEAR_START for e in historia)
            anos_totais = max(ano_atual - primeiro_ano, 1)
        else:
            anos_totais = 0

        # Décadas presentes (para o filtro do topo)
        decadas = sorted({
            (e.HISTORY_YEAR_START // 10) * 10
            for e in historia
        })

    return render_template(
        'admin_historia.html',
        historia=historia,
        ano_atual=ano_atual,
        anos_totais=anos_totais,
        decadas=decadas
    )


# ADICIONAR ETAPA DA HISTÓRIA
@administrador_bp.route('/adicionar_historia', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_historia():
    formulario = ChurchHistory_()
    ano_atual = datetime.date.today().year

    # Próxima posição sugerida (última + 1), para evitar conflitos de posicionamento na ordem de acontecimentos
    with SessionFactory() as session_db:
        maior_ordem = session_db.query(
            func.max(ChurchHistory.HISTORY_ORDER)
        ).scalar() or 0
        proxima_ordem = maior_ordem + 1

    if formulario.validate_on_submit():
        titulo     = (request.form.get('titulo') or '').strip()
        conteudo   = (request.form.get('conteudo') or '').strip()
        imagem     = formulario.imagem.data
        ano_inicio = formulario.ano_inicio.data
        # Checkbox "em andamento" — quando marcada, ano_fim é ignorado
        em_andamento = request.form.get('andamento') == '1'
        ano_fim = None if em_andamento else formulario.ano_fim.data
        ordem = formulario.ordem.data or 0

        # Renderização de fallback com valores preservados
        def _renderizar_com_valores(msg=None, categoria='danger'):
            if msg:
                flash(msg, categoria)
            formulario.titulo.data     = titulo
            formulario.conteudo.data   = conteudo
            formulario.ano_inicio.data = ano_inicio
            formulario.ano_fim.data    = ano_fim
            formulario.ordem.data      = ordem
            return render_template(
                'admin_cadastrar_historia.html',
                formulario=formulario,
                ano_atual=ano_atual,
                proxima_ordem=proxima_ordem
            )

        # Validação do período
        if ano_fim and int(ano_fim) < int(ano_inicio):
            return _renderizar_com_valores(
                'O ano de término não pode ser anterior ao ano de início.'
            )

        with SessionFactory() as session_db:
            # Conflito de ordem (só valida quando ordem > 0)
            if ordem and ordem > 0:
                conflito = session_db.query(ChurchHistory).filter(
                    ChurchHistory.HISTORY_ORDER == ordem
                ).first()
                if conflito:
                    return _renderizar_com_valores(
                        'Já existe uma etapa cadastrada nesta posição. '
                        'Escolha outra ordem.'
                    )

            nova_etapa = ChurchHistory(
                HISTORY_TITLE=titulo,
                HISTORY_CONTENT=conteudo,
                HISTORY_YEAR_START=int(ano_inicio),
                HISTORY_YEAR_END=int(ano_fim) if ano_fim else None,
                HISTORY_ORDER=int(ordem) if ordem else 0,
                HISTORY_ADMINISTRADOR_ID=current_user.ADMIN_ID
            )
            session_db.add(nova_etapa)
            session_db.flush()  # gera o ID sem precisar de commit 

            # Salvando a imagem 
            if imagem and imagem.filename:
                pasta = os.path.join(
                    current_app.config['UPLOADS_FOLDER'], 'historia'
                )
                os.makedirs(pasta, exist_ok=True)

                extensao = os.path.splitext(
                    secure_filename(imagem.filename)
                )[1].lower()
                nome_imagem = f'historia_{nova_etapa.HISTORY_ID}{extensao}'
                imagem.save(os.path.join(pasta, nome_imagem))
                nova_etapa.HISTORY_IMAGE = nome_imagem

            session_db.commit()

            _registrar_log(
                session_db,
                'create',
                objeto=nova_etapa,
                old_values=None,
                new_values=_snapshot_log(nova_etapa)
            )

            flash('Capítulo cadastrado com sucesso.', 'success')
            return redirect(url_for('administrador.exibir_historia'))

    return render_template(
        'admin_cadastrar_historia.html',
        formulario=formulario,
        ano_atual=ano_atual,
        proxima_ordem=proxima_ordem
    )


# EDITAR ETAPA DA HISTÓRIA
@administrador_bp.route('/editar_historia', methods=['POST', 'GET'])
@adm_2af_required
def editar_historia():
    formulario = ChurchHistoryUpdate()
    historia_id = request.args.get('historia_id', type=int)
    ano_atual = datetime.date.today().year

    if not historia_id:
        return redirect(url_for('administrador.exibir_historia'))

    # POST — atualizar
    if formulario.validate_on_submit():
        titulo     = (request.form.get('titulo') or '').strip()
        conteudo   = (request.form.get('conteudo') or '').strip()
        imagem     = formulario.imagem.data
        ano_inicio = formulario.ano_inicio.data
        em_andamento = request.form.get('andamento') == '1'
        ano_fim = None if em_andamento else formulario.ano_fim.data
        ordem = formulario.ordem.data or 0

        with SessionFactory() as session_db:
            etapa = session_db.query(ChurchHistory).filter(
                ChurchHistory.HISTORY_ID == historia_id
            ).first()

            if not etapa:
                flash('Capítulo não encontrado.', 'danger')
                return redirect(url_for('administrador.exibir_historia'))

            old_values_log = _snapshot_log(etapa)

            def _renderizar_com_valores(msg):
                flash(msg, 'danger')
                formulario.titulo.data     = titulo
                formulario.conteudo.data   = conteudo
                formulario.ano_inicio.data = ano_inicio
                formulario.ano_fim.data    = ano_fim
                formulario.ordem.data      = ordem
                return render_template(
                    'admin_editar_historia.html',
                    formulario=formulario,
                    etapa=etapa,
                    ano_atual=ano_atual
                )

            if ano_fim and int(ano_fim) < int(ano_inicio):
                return _renderizar_com_valores(
                    'O ano de término não pode ser anterior ao ano de início.'
                )

            # Para evitar conflito de ordem. Não pode ocupar a mesma ordem que outro dá esteja ocupando, e isso ignora se for minha ordem atual ou uma ordem que não esteja sendo utlizada
            if ordem and ordem > 0:
                conflito = session_db.query(ChurchHistory).filter(
                    ChurchHistory.HISTORY_ORDER == ordem,
                    ChurchHistory.HISTORY_ID != etapa.HISTORY_ID
                ).first()
                if conflito:
                    return _renderizar_com_valores(
                        'Já existe um capítulo cadastrado nesta posição. '
                        'Escolha outra ordem.'
                    )

            etapa.HISTORY_TITLE = titulo
            etapa.HISTORY_CONTENT = conteudo
            etapa.HISTORY_YEAR_START = int(ano_inicio)
            etapa.HISTORY_YEAR_END = int(ano_fim) if ano_fim else None
            etapa.HISTORY_ORDER = int(ordem) if ordem else 0

            # Troca de imagem 
            if imagem and imagem.filename:
                pasta = os.path.join(
                    current_app.config['UPLOADS_FOLDER'], 'historia'
                )
                os.makedirs(pasta, exist_ok=True)

                # Remove a antiga se existir 
                if etapa.HISTORY_IMAGE:
                    caminho_antigo = _caminho_imagem_historia(etapa.HISTORY_IMAGE)
                    if os.path.exists(caminho_antigo):
                        try:
                            os.remove(caminho_antigo)
                        except OSError:
                            pass 

                extensao = os.path.splitext(
                    secure_filename(imagem.filename)
                )[1].lower()
                nome_imagem = f'historia_{etapa.HISTORY_ID}{extensao}'
                imagem.save(os.path.join(pasta, nome_imagem))
                etapa.HISTORY_IMAGE = nome_imagem

            session_db.commit()

            _registrar_log(
                session_db,
                'update',
                objeto=etapa,
                old_values=old_values_log,
                new_values=_snapshot_log(etapa)
            )

            flash('Capítulo atualizado com sucesso.', 'success')
            return redirect(url_for('administrador.exibir_historia'))


    with SessionFactory() as session_db:
        etapa_selecionada = session_db.query(ChurchHistory).filter(
            ChurchHistory.HISTORY_ID == historia_id
        ).first()

        if not etapa_selecionada:
            flash('Capítulo não encontrado.', 'danger')
            return redirect(url_for('administrador.exibir_historia'))

        formulario.titulo.data     = etapa_selecionada.HISTORY_TITLE
        formulario.conteudo.data   = etapa_selecionada.HISTORY_CONTENT
        formulario.ano_inicio.data = etapa_selecionada.HISTORY_YEAR_START
        formulario.ano_fim.data    = etapa_selecionada.HISTORY_YEAR_END
        formulario.ordem.data      = etapa_selecionada.HISTORY_ORDER

        return render_template(
            'admin_editar_historia.html',
            formulario=formulario,
            etapa=etapa_selecionada,
            ano_atual=ano_atual
        )


# EXCLUIR ETAPA DA HISTÓRIA
@administrador_bp.route('/excluir_historia', methods=['POST', 'GET'])
@adm_2af_required
def excluir_historia():
    historia_id = request.args.get('historia_id', type=int)

    if not historia_id:
        return redirect(url_for('administrador.exibir_historia'))

    with SessionFactory() as session_db:
        etapa = session_db.query(ChurchHistory).filter(ChurchHistory.HISTORY_ID == historia_id).first()

        if not etapa:
            flash('Capítulo não encontrado.', 'danger')
            return redirect(url_for('administrador.exibir_historia'))

        old_values_log = _snapshot_log(etapa)
        record_id_log = _id_registro_log(etapa)
        nome_imagem = etapa.HISTORY_IMAGE  # guarda antes de deletar

        session_db.delete(etapa)
        session_db.commit()

        # Remove o arquivo físico da imagem (só depois do commit)
        if nome_imagem:
            caminho = _caminho_imagem_historia(nome_imagem)
            if os.path.exists(caminho):
                try:
                    os.remove(caminho)
                except OSError:
                    pass

        _registrar_log(
            session_db,
            'delete',
            tabela=ChurchHistory.__tablename__,
            record_id=record_id_log,
            old_values=old_values_log,
            new_values=None
        )

        flash('Capítulo excluído com sucesso.', 'success')
        return redirect(url_for('administrador.exibir_historia'))


# SETOR DE DEPARTAMENTOS

# Exibir departamentos
@administrador_bp.route('/exibir_departamentos', methods=['GET'])
@adm_2af_required
def exibir_departamentos():

    administrador = current_user

    # Preparando as iniciais do administrador para exibição na navbar
    partes_nome = (administrador.ADMIN_NAME or '').split()

    iniciais_administrador = ''.join(
        parte[0]
        for parte in partes_nome[:2]
        if parte
    ).upper() or 'AD'

    with SessionFactory() as session_db:

        # Carregando departamentos existentes em ordem de exibição
        departamentos = (session_db.query(Department).order_by(Department.DEPARTMENT_ORDER.asc(),Department.DEPARTMENT_ID.asc()).all())



        departamentos_ativos = sum(1 for departamento in departamentos if departamento.DEPARTMENT_ACTIVE)
        departamentos_desativados = sum(1 for departamento in departamentos if not departamento.DEPARTMENT_ACTIVE)
        departamentos_com_lideranca = sum(1 for departamento in departamentos if departamento.DEPARTMENT_LEADER_NAME)
        departamentos_sem_contato = sum(1 for departamento in departamentos if not departamento.DEPARTMENT_CONTACT_EMAIL and not departamento.DEPARTMENT_CONTACT_PHONE)

        return render_template(
            'admin_departamento.html',

            # Administrador
            administrador=administrador,
            iniciais_administrador=iniciais_administrador,

            # Departamentos
            departamentos=departamentos,

            # Estatísticas
            departamentos_ativos=departamentos_ativos,
            departamentos_desativados=departamentos_desativados,
            departamentos_com_lideranca=departamentos_com_lideranca,
            departamentos_sem_contato=departamentos_sem_contato
        )



# ATIVAR OU DESATIVAR DEPARTAMENTO
@administrador_bp.route('/alternar_status_departamento/<int:departamento_id>', methods=['POST'])
@adm_2af_required
def alternar_status_departamento(departamento_id):

    with SessionFactory() as session_db:

        # Carregando departamento selecionado
        departamento = (session_db.query(Department).filter(Department.DEPARTMENT_ID == departamento_id).first())

        # Verificando se o departamento existe
        if not departamento:

            return {
                'sucesso': False,
                'mensagem': 'Departamento não encontrado.'
            }, 404

        # LOG: estado anterior do departamento
        old_values_log = _snapshot_log(departamento)

        # Alterando o status atual
        departamento.DEPARTMENT_ACTIVE = (
            not departamento.DEPARTMENT_ACTIVE
        )

        session_db.commit()

        # LOG: departamento atualizado
        _registrar_log(
            session_db,
            'update',
            objeto=departamento,
            old_values=old_values_log,
            new_values=_snapshot_log(
                departamento
            )
        )

        return {
            'sucesso': True,
            'ativo': bool(
                departamento.DEPARTMENT_ACTIVE
            )
        }

# Reordenar departamentos
@administrador_bp.route('/reordenar_departamentos', methods=['POST'])
@adm_2af_required
def reordenar_departamentos():

    dados = request.get_json(silent=True) or {}
    nova_ordem = dados.get('ordem', [])

    # Garantindo que foi enviada uma lista válida
    if not isinstance(nova_ordem, list) or not nova_ordem:
        return {
            'sucesso': False,
            'mensagem': 'Ordem inválida.'
        }, 400

    try:
        ids_departamentos = [
            int(item)
            for item in nova_ordem
        ]

    except (TypeError, ValueError):

        return {
            'sucesso': False,
            'mensagem': 'Identificador de departamento inválido.'
        }, 400

    # Evitando IDs repetidos
    if len(ids_departamentos) != len(set(ids_departamentos)):
        return {
            'sucesso': False,
            'mensagem': 'Existem departamentos repetidos na nova ordem.'
        }, 400

    with SessionFactory() as session_db:

        departamentos = (session_db.query(Department).filter(Department.DEPARTMENT_ID.in_(ids_departamentos)).all())

        if len(departamentos) != len(ids_departamentos):
            return {
                'sucesso': False,
                'mensagem': 'Um ou mais departamentos não foram encontrados.'
            }, 404

        departamentos_por_id = {
            departamento.DEPARTMENT_ID: departamento
            for departamento in departamentos
        }

        # Guardando os estados anteriores
        old_values_logs = {}

        for posicao, departamento_id in enumerate(
            ids_departamentos,
            start=1
        ):

            departamento = (
                departamentos_por_id[departamento_id]
            )

            if departamento.DEPARTMENT_ORDER != posicao:

                old_values_logs[departamento_id] = (
                    _snapshot_log(departamento)
                )

        # Usando números temporários para evitar conflitos durante a troca das posições
        for posicao, departamento_id in enumerate(
            ids_departamentos,
            start=1
        ):

            departamentos_por_id[
                departamento_id
            ].DEPARTMENT_ORDER = -posicao

        session_db.flush()

        # Salvando ordem definitiva
        for posicao, departamento_id in enumerate(
            ids_departamentos,
            start=1
        ):

            departamentos_por_id[
                departamento_id
            ].DEPARTMENT_ORDER = posicao

        session_db.commit()

        # LOG das alterações
        for departamento_id, old_values_log in (
            old_values_logs.items()
        ):

            departamento = (
                departamentos_por_id[departamento_id]
            )

            _registrar_log(
                session_db,
                'update',
                objeto=departamento,
                old_values=old_values_log,
                new_values=_snapshot_log(departamento)
            )

        return {
            'sucesso': True,
            'mensagem': 'Ordem atualizada com sucesso.'
        }


# ADICIONAR DEPARTAMENTO
@administrador_bp.route('/adicionar_departamento', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_departamento():
    # Carregando dados necessários
    administrador = current_user
    formulario = Department_()

    # Preparando as iniciais do administrador para exibição na navbar
    partes_nome = (administrador.ADMIN_NAME or '').split()
    iniciais_administrador = ''.join(parte[0] for parte in partes_nome[:2] if parte).upper() or 'AD'

    with SessionFactory() as session_db:
        maior_ordem = (session_db.query(func.max(Department.DEPARTMENT_ORDER)).scalar()) or 0
        proxima_ordem = maior_ordem + 1

    if request.method == 'GET':
        formulario.ordem.data = proxima_ordem

    # Adicionando novo departamento
    if formulario.validate_on_submit():

        # Pegando os valores já validados pelo formulário
        nome = (formulario.nome.data.strip() if formulario.nome.data else '')
        descricao = (formulario.descricao.data.strip() if formulario.descricao.data else None)
        lider_nome = (formulario.lider_nome.data.strip() if formulario.lider_nome.data else None)
        lider_foto = formulario.lider_foto.data
        lider_bio = (formulario.lider_bio.data.strip() if formulario.lider_bio.data else None)
        contato_email = (formulario.contato_email.data.strip() if formulario.contato_email.data else None)
        contato_telefone = (formulario.contato_telefone.data.strip() if formulario.contato_telefone.data else None)
        ordem = formulario.ordem.data
        ativo = formulario.ativo.data

        # Salvando no banco de dados
        with SessionFactory() as session_db:
            # Verificando se já existe um departamento
            ordem_verify = (session_db.query(Department).filter( Department.DEPARTMENT_ORDER == ordem).first())

            if ordem_verify:
                flash(
                    'Já existe um departamento cadastrado nesta posição. '
                    'Escolha outra ordem.',
                    'danger'
                )

                return render_template('admin_criar_departamento.html',formulario=formulario, administrador=administrador, iniciais_administrador=iniciais_administrador, proxima_ordem=proxima_ordem)

            # Criando o novo departamento
            novo_departamento = Department(
                DEPARTMENT_NAME=nome,
                DEPARTMENT_DESCRIPTION=descricao,
                DEPARTMENT_LEADER_NAME=lider_nome,
                DEPARTMENT_LEADER_BIO=lider_bio,
                DEPARTMENT_CONTACT_EMAIL=contato_email,
                DEPARTMENT_CONTACT_PHONE=contato_telefone,
                DEPARTMENT_ORDER=ordem,
                DEPARTMENT_ACTIVE=ativo,
                DEPARTMENT_ADMINISTRADOR_ID=current_user.ADMIN_ID
            )

            session_db.add(novo_departamento)
            session_db.flush()

            # Se uma foto do líder foi enviada
            if lider_foto and lider_foto.filename:

                # Garantindo que a pasta de departamentos exista
                pasta_departamentos = os.path.join(current_app.config['UPLOADS_FOLDER'],'departamentos')
                os.makedirs(pasta_departamentos,exist_ok=True)

                # Preparando um nome seguro para o arquivo
                nome_original_seguro = secure_filename(lider_foto.filename)

                extensao = os.path.splitext(
                    nome_original_seguro
                )[1].lower()

                nome_foto = (
                    f'departamento_'
                    f'{novo_departamento.DEPARTMENT_ID}'
                    f'{extensao}'
                )

                # Salvando a imagem
                lider_foto.save(os.path.join(pasta_departamentos,nome_foto))

                # Salvando o nome da imagem no banco
                novo_departamento.DEPARTMENT_LEADER_PHOTO = (nome_foto)


            session_db.commit()


            # Registrando o log de departamento criado
            _registrar_log(
                session_db,
                'create',
                objeto=novo_departamento,
                old_values=None,
                new_values=_snapshot_log(
                    novo_departamento
                )
            )

            flash('Departamento cadastrado com sucesso.', 'success')



            return redirect(url_for('administrador.exibir_departamentos'))

    
    return render_template('admin_criar_departamento.html', formulario=formulario, administrador=administrador, iniciais_administrador=iniciais_administrador, proxima_ordem=proxima_ordem)


# EDITAR DEPARTAMENTO
@administrador_bp.route('/editar_departamento', methods=['POST', 'GET'])
@adm_2af_required
def editar_departamento():
    # Carregando dados necessários
    formulario = Department_()
    # Pegando o ID do departamento a ser editado
    departamento_id = request.args.get('departamento_id')

    # Atualizando departamento
    if formulario.validate_on_submit():
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        lider_nome = request.form.get('lider_nome')
        lider_foto = formulario.lider_foto.data
        lider_bio = request.form.get('lider_bio')
        contato_email = request.form.get('contato_email')
        contato_telefone = request.form.get('contato_telefone')
        ordem = formulario.ordem.data
        ativo = formulario.ativo.data



        if departamento_id:
            with SessionFactory() as session_db:
                departamento = session_db.query(Department).filter(Department.DEPARTMENT_ID == int(departamento_id)).first()

                # LOG: estado anterior do departamento
                old_values_log = _snapshot_log(departamento)

                # Verificando conflito de ordem, ignorando o próprio departamento que está sendo editado
                ordem_verify = session_db.query(Department).filter(Department.DEPARTMENT_ORDER == ordem,Department.DEPARTMENT_ID != departamento.DEPARTMENT_ID).first()

                if ordem_verify:
                    flash('Já existe um departamento cadastrado nesta ordem, escolha outra')
                    formulario.nome.data = nome
                    formulario.descricao.data = descricao
                    formulario.lider_nome.data = lider_nome
                    formulario.lider_bio.data = lider_bio
                    formulario.contato_email.data = contato_email
                    formulario.contato_telefone.data = contato_telefone
                    formulario.ativo.data = ativo
                    return render_template('admin_editar_departamento.html', formulario=formulario, departamento=departamento)

                departamento.DEPARTMENT_NAME = nome
                departamento.DEPARTMENT_DESCRIPTION = descricao
                departamento.DEPARTMENT_LEADER_NAME = lider_nome
                departamento.DEPARTMENT_LEADER_BIO = lider_bio
                departamento.DEPARTMENT_CONTACT_EMAIL = contato_email
                departamento.DEPARTMENT_CONTACT_PHONE = contato_telefone
                departamento.DEPARTMENT_ORDER = ordem if ordem else 0
                departamento.DEPARTMENT_ACTIVE = ativo
                session_db.commit()

                # Se o administrador adicionou uma nova foto do líder
                if lider_foto:
                    # Deletando antiga imagem, se existir
                    if departamento.DEPARTMENT_LEADER_PHOTO:
                        caminho = os.path.join(
                            current_app.config['UPLOADS_FOLDER'],
                            'departamentos',
                            departamento.DEPARTMENT_LEADER_PHOTO
                        )
                        if os.path.exists(caminho):
                            os.remove(caminho)

                    # Salvando a imagem
                    extensao = os.path.splitext(secure_filename(lider_foto.filename))[1]
                    nome_foto = f'departamento_{departamento.DEPARTMENT_ID}{extensao}'
                    lider_foto.save(
                        os.path.join(current_app.config['UPLOADS_FOLDER'], "departamentos", nome_foto)
                    )

                    # Salvando caminho no banco de dados
                    departamento.DEPARTMENT_LEADER_PHOTO = nome_foto
                    session_db.commit()

                # LOG: departamento atualizado
                _registrar_log(
                    session_db,
                    'update',
                    objeto=departamento,
                    old_values=old_values_log,
                    new_values=_snapshot_log(departamento)
                )

                return redirect(url_for('administrador.exibir_departamentos'))

    # Carregando formulário já preenchido com os dados atuais
    if departamento_id:
        with SessionFactory() as session_db:
            departamento_selecionado = session_db.query(Department).filter(Department.DEPARTMENT_ID == int(departamento_id)).first()
            if departamento_selecionado:
                formulario.nome.data = departamento_selecionado.DEPARTMENT_NAME
                formulario.descricao.data = departamento_selecionado.DEPARTMENT_DESCRIPTION
                formulario.lider_nome.data = departamento_selecionado.DEPARTMENT_LEADER_NAME
                formulario.lider_bio.data = departamento_selecionado.DEPARTMENT_LEADER_BIO
                formulario.contato_email.data = departamento_selecionado.DEPARTMENT_CONTACT_EMAIL
                formulario.contato_telefone.data = departamento_selecionado.DEPARTMENT_CONTACT_PHONE
                formulario.ordem.data = departamento_selecionado.DEPARTMENT_ORDER
                formulario.ativo.data = departamento_selecionado.DEPARTMENT_ACTIVE
                return render_template('admin_editar_departamento.html', formulario=formulario, departamento=departamento_selecionado)
            else:
                return redirect(url_for('administrador.exibir_departamentos'))
    else:
        return redirect(url_for('administrador.exibir_departamentos'))


# Excluir departamento
@administrador_bp.route('/excluir_departamento', methods=['POST', 'GET'])
@adm_2af_required
def excluir_departamento():
    # Recebendo ID do departamento a ser excluido
    departamento_id = request.args.get('departamento_id')

    if departamento_id:
        with SessionFactory() as session_db:
            departamento_selecionado = session_db.query(Department).filter(Department.DEPARTMENT_ID == int(departamento_id)).first()
            if departamento_selecionado:
                # LOG: salva os dados antes da exclusão
                old_values_log = _snapshot_log(departamento_selecionado)
                record_id_log = _id_registro_log(departamento_selecionado)

                session_db.delete(departamento_selecionado)
                session_db.commit()

                # LOG: departamento excluído
                _registrar_log(
                    session_db,
                    'delete',
                    tabela=Department.__tablename__,
                    record_id=record_id_log,
                    old_values=old_values_log,
                    new_values=None
                )

                return redirect(url_for('administrador.exibir_departamentos'))
            else:
                return redirect(url_for('administrador.exibir_departamentos'))

    else:
        return redirect(url_for('administrador.exibir_departamentos'))
    





# SETOR DE EVENTOS

@administrador_bp.route('/exibir_eventos', methods=['GET'])
@adm_2af_required
def exibir_eventos():
    hoje = datetime.date.today()

    with SessionFactory() as session_db:
        eventos = (session_db.query(Event).order_by(Event.EVENT_DATE).all())

        # Separa por status
        futuros    = [e for e in eventos if e.EVENT_DATE >= hoje]
        historico  = [e for e in eventos if e.EVENT_DATE <  hoje]

        # Próximo (o primeiro futuro publicado)
        proximo    = next((e for e in futuros if e.EVENT_PUBLISHED), None)
        agendados  = [e for e in futuros if e is not proximo]

        # Histórico do mais recente pro mais antigo
        historico.sort(key=lambda e: e.EVENT_DATE, reverse=True)

    return render_template(
        'admin_eventos.html',
        proximo=proximo,
        agendados=agendados,
        historico=historico,
        hoje=hoje,
    )


# Adicionar evento
@administrador_bp.route('/adicionar_evento', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_evento():

    # Carregando dados necessários
    administrador = current_user
    formulario = Event_()
    hoje = datetime.date.today().isoformat()


    # Adicionando novo evento
    if formulario.validate_on_submit():
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        banner = formulario.banner.data
        local = request.form.get('local')
        data = formulario.data.data
        hora = formulario.hora.data
        inscricao_necessaria = formulario.inscricao_necessaria.data
        destaque = formulario.destaque.data
        publicar = formulario.publicar.data


        # Salvando no banco de dados
        with SessionFactory() as session_db:
            novo_evento = Event(
                EVENT_TITLE=titulo,
                EVENT_DESCRIPTION=descricao,
                EVENT_LOCATION=local,
                EVENT_DATE=data,
                EVENT_TIME=hora,
                EVENT_REGISTRATION_REQUIRED=inscricao_necessaria,
                EVENT_FEATURED=destaque,
                EVENT_PUBLISHED=publicar,
                EVENT_ADMINISTRADOR_ID=current_user.ADMIN_ID
            )
            session_db.add(novo_evento)
            session_db.flush()

            # Se um banner foi enviado
            if banner:
                extensao = os.path.splitext(secure_filename(banner.filename))[1]
                nome_banner = (f'evento_{novo_evento.EVENT_ID}{extensao}')
                banner.save(os.path.join(current_app.config['UPLOADS_FOLDER'],"eventos",nome_banner))
                # Salvando caminho no banco de dados
                novo_evento.EVENT_BANNER = nome_banner
            session_db.commit()

            # Registrando o log do evento que foi criado
            _registrar_log(
                session_db,
                'create',
                objeto=novo_evento,
                old_values=None,
                new_values=_snapshot_log(novo_evento)
            )
            return redirect(url_for('administrador.exibir_eventos'))

    # Carregando a página de adicionar evento
    return render_template('admin_cadastrar_evento.html',formulario=formulario,hoje=hoje,administrador=administrador)


# EDITAR EVENTO
@administrador_bp.route('/editar_evento', methods=['POST', 'GET'])
@adm_2af_required
def editar_evento():
    # Carregando dados necessários
    administrador = current_user
    formulario = Event_()
    # Pegando o ID do evento a ser editado
    evento_id = request.args.get('evento_id')
    hoje = datetime.date.today().isoformat()

    # Atualizando evento
    if formulario.validate_on_submit():
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        banner = formulario.banner.data
        local = request.form.get('local')
        data = formulario.data.data
        hora = formulario.hora.data
        inscricao_necessaria = formulario.inscricao_necessaria.data
        destaque = formulario.destaque.data
        publicar = formulario.publicar.data
        # Verificando se evento existe para poder atualizar
        if evento_id:
            with SessionFactory() as session_db:
                evento = (session_db.query(Event).filter(Event.EVENT_ID == int(evento_id)).first())

                if not evento:
                    return redirect(url_for('administrador.exibir_eventos'))

                # LOG: estado anterior do evento
                old_values_log = _snapshot_log(evento)

                evento.EVENT_TITLE = titulo
                evento.EVENT_DESCRIPTION = descricao
                evento.EVENT_LOCATION = local
                evento.EVENT_DATE = data
                evento.EVENT_TIME = hora
                evento.EVENT_REGISTRATION_REQUIRED = inscricao_necessaria
                evento.EVENT_FEATURED = destaque
                evento.EVENT_PUBLISHED = publicar

                # Se o administrador adicionou um novo banner
                if banner:
                  
                    if evento.EVENT_BANNER:
                        caminho = os.path.join(current_app.config['UPLOADS_FOLDER'], 'eventos', evento.EVENT_BANNER)
                        if os.path.exists(caminho):
                            os.remove(caminho)

                    # Salvando a nova imagem
                    extensao = os.path.splitext(secure_filename(banner.filename))[1]
                    nome_banner = (f'evento_{evento.EVENT_ID}{extensao}')
                    banner.save(os.path.join(current_app.config['UPLOADS_FOLDER'],"eventos",nome_banner))
                    evento.EVENT_BANNER = nome_banner

                session_db.commit()

                # LOG: evento atualizado
                _registrar_log(
                    session_db,
                    'update',
                    objeto=evento,
                    old_values=old_values_log,
                    new_values=_snapshot_log(evento)
                )

                flash('Evento atualizado com sucesso.','success')
                return redirect(url_for('administrador.exibir_eventos'))

    # Carregando formulário já preenchido
    if evento_id:
        with SessionFactory() as session_db:
            evento_selecionado = (session_db.query(Event).filter(Event.EVENT_ID == int(evento_id)).first())

            if evento_selecionado:
                formulario.titulo.data = evento_selecionado.EVENT_TITLE
                formulario.descricao.data = evento_selecionado.EVENT_DESCRIPTION
                formulario.local.data = evento_selecionado.EVENT_LOCATION
                formulario.data.data = evento_selecionado.EVENT_DATE
                formulario.hora.data = evento_selecionado.EVENT_TIME
                formulario.inscricao_necessaria.data = evento_selecionado.EVENT_REGISTRATION_REQUIRED
                formulario.destaque.data = evento_selecionado.EVENT_FEATURED
                formulario.publicar.data = evento_selecionado.EVENT_PUBLISHED

                return render_template(
                    'admin_atualizar_evento.html',
                    formulario=formulario,
                    evento=evento_selecionado,
                    hoje=hoje,
                    administrador=administrador
                )

            else:
                return redirect(url_for('administrador.exibir_eventos'))


    else:
        return redirect(url_for('administrador.exibir_eventos'))

# Excluir evento
@administrador_bp.route('/excluir_evento', methods=['POST', 'GET'])
@adm_2af_required
def excluir_evento():
    # Recebendo ID do evento a ser excluido
    evento_id = request.args.get('evento_id')

    if evento_id:
        with SessionFactory() as session_db:
            evento_selecionado = session_db.query(Event).filter(Event.EVENT_ID == int(evento_id)).first()
            if evento_selecionado:
                # LOG: salva os dados antes da exclusão
                old_values_log = _snapshot_log(evento_selecionado)
                record_id_log = _id_registro_log(evento_selecionado)

                session_db.delete(evento_selecionado)
                session_db.commit()

                # LOG: evento excluído
                _registrar_log(
                    session_db,
                    'delete',
                    tabela=Event.__tablename__,
                    record_id=record_id_log,
                    old_values=old_values_log,
                    new_values=None
                )

                return redirect(url_for('administrador.exibir_eventos'))
            else:
                return redirect(url_for('administrador.exibir_eventos'))

    else:
        return redirect(url_for('administrador.exibir_eventos'))




# SETOR DE REDES SOCIAIS

# Aqui eu passo as pré configurações que terão cada APP ao serem carregados no html, dando um visual bem bonito e moderno
PLATAFORMAS_REDES = {
    'instagram': {
        'nome': 'Instagram', 'sub': 'Perfil oficial',
        'icone': 'fa fa-instagram',
        'cor': '#e4405f', 'cor2': '#c72a48',
        'sombra': 'rgba(228,64,95,.5)',
        'cor_bg': 'rgba(228,64,95,0.25)', 'cor_ic': '#e4405f',
        'ex': 'https://instagram.com/igrejadecristo',
    },
    'youtube': {
        'nome': 'YouTube', 'sub': 'Canal oficial',
        'icone': 'fa fa-youtube-play',
        'cor': '#ff0000', 'cor2': '#c40000',
        'sombra': 'rgba(255,0,0,.45)',
        'cor_bg': 'rgba(255,0,0,0.25)', 'cor_ic': '#ff5252',
        'ex': 'https://youtube.com/@igrejadecristo',
    },
    'whatsapp': {
        'nome': 'WhatsApp', 'sub': 'Grupo ou contato',
        'icone': 'fa fa-whatsapp',
        'cor': '#25d366', 'cor2': '#1ea952',
        'sombra': 'rgba(37,211,102,.5)',
        'cor_bg': 'rgba(37,211,102,0.25)', 'cor_ic': '#25d366',
        'ex': 'https://wa.me/55XXXXXXXXXXX',
    },
    'facebook': {
        'nome': 'Facebook', 'sub': 'Página oficial',
        'icone': 'fa fa-facebook',
        'cor': '#1877f2', 'cor2': '#0e5cbf',
        'sombra': 'rgba(24,119,242,.45)',
        'cor_bg': 'rgba(24,119,242,0.25)', 'cor_ic': '#4a90e2',
        'ex': 'https://facebook.com/igrejadecristo',
    },
    'spotify': {
        'nome': 'Spotify', 'sub': 'Podcast ou louvor',
        'icone': 'fa fa-spotify',
        'cor': '#1db954', 'cor2': '#158f40',
        'sombra': 'rgba(29,185,84,.5)',
        'cor_bg': 'rgba(29,185,84,0.25)', 'cor_ic': '#1db954',
        'ex': 'https://open.spotify.com/user/igrejadecristo',
    },
    'tiktok': {
        'nome': 'TikTok', 'sub': 'Perfil da igreja',
        'icone': 'fa fa-music',
        'gradiente': 'linear-gradient(135deg,#000 0%,#25f4ee 50%,#fe2c55 100%)',
        'cor': '#000000', 'cor2': '#000000',
        'sombra': 'rgba(0,0,0,.4)',
        'cor_bg': 'rgba(0,0,0,0.25)', 'cor_ic': '#fe2c55',
        'ex': 'https://tiktok.com/@igrejadecristo',
    },
    'telegram': {
        'nome': 'Telegram', 'sub': 'Canal ou grupo',
        'icone': 'fa fa-paper-plane',
        'cor': '#0088cc', 'cor2': '#006699',
        'sombra': 'rgba(0,136,204,.5)',
        'cor_bg': 'rgba(0,136,204,0.25)', 'cor_ic': '#0088cc',
        'ex': 'https://t.me/igrejadecristo',
    },
    'twitter': {
        'nome': 'X (Twitter)', 'sub': 'Perfil oficial',
        'icone': 'fa fa-twitter',
        'cor': '#0f1419', 'cor2': '#000000',
        'sombra': 'rgba(15,20,25,.4)',
        'cor_bg': 'rgba(15,20,25,0.35)', 'cor_ic': '#8899a6',
        'ex': 'https://x.com/igrejadecristo',
    },
}


# EXIBIR REDES SOCIAIS
@administrador_bp.route('/exibir_redes_sociais', methods=['GET'])
@adm_2af_required
def exibir_redes_sociais():
    with SessionFactory() as session_db:
        redes = (
            session_db.query(SocialLink)
            .order_by(SocialLink.SOCIAL_ORDER.asc(), SocialLink.SOCIAL_ID.asc())
            .all()
        )

        redes_por_slug = {r.SOCIAL_PLATFORM: r for r in redes}
        redes_ativas = [r for r in redes if r.SOCIAL_ACTIVE]
        redes_no_rodape = sorted(redes_ativas, key=lambda r: (r.SOCIAL_ORDER or 999))

        total_ativas = len(redes_ativas)
        total_pausadas = sum(1 for r in redes if not r.SOCIAL_ACTIVE)
        total_disponiveis = len(PLATAFORMAS_REDES) - len(redes)

    return render_template(
        'admin_social.html',
        plataformas=PLATAFORMAS_REDES,
        redes_por_slug=redes_por_slug,
        redes_no_rodape=redes_no_rodape,
        total_ativas=total_ativas,
        total_pausadas=total_pausadas,
        total_disponiveis=total_disponiveis,
    )


# ADICIONAR REDE SOCIAL
@administrador_bp.route('/adicionar_rede_social', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_rede_social():
    formulario = SocialLink_()

    # Pré-seleção da plataforma via querystring (?plataforma=spotify)
    plataforma_preselecionada = request.args.get('plataforma', '').strip().lower()
    if plataforma_preselecionada not in PLATAFORMAS_REDES:
        plataforma_preselecionada = None

    # Dados auxiliares para o template
    with SessionFactory() as session_db:
        slugs_tomados = {
            r.SOCIAL_PLATFORM
            for r in session_db.query(SocialLink.SOCIAL_PLATFORM).all()
        }
        redes_ativas = (
            session_db.query(SocialLink)
            .filter(SocialLink.SOCIAL_ACTIVE.is_(True))
            .order_by(SocialLink.SOCIAL_ORDER.asc())
            .all()
        )
        maior_ordem = session_db.query(func.max(SocialLink.SOCIAL_ORDER)).scalar() or 0
        proxima_ordem = maior_ordem + 1

    # Se a plataforma pré-selecionada já está tomada, redireciona pra edição
    if plataforma_preselecionada and plataforma_preselecionada in slugs_tomados:
        with SessionFactory() as session_db:
            existente = (
                session_db.query(SocialLink)
                .filter(SocialLink.SOCIAL_PLATFORM == plataforma_preselecionada)
                .first()
            )
        if existente:
            flash(f'{PLATAFORMAS_REDES[plataforma_preselecionada]["nome"]} '
                'já está conectado — editando a conexão existente.',
                'info'
            )
            return redirect(url_for('administrador.editar_rede_social', social_id=existente.SOCIAL_ID))

    def _renderizar(msg=None, categoria='danger'):
        if msg:
            flash(msg, categoria)
        return render_template(
            'admin_cadastrar_social.html',
            formulario=formulario,
            plataformas=PLATAFORMAS_REDES,
            slugs_tomados=slugs_tomados,
            plataforma_preselecionada=plataforma_preselecionada,
            redes_ativas=redes_ativas,
            proxima_ordem=proxima_ordem,
        )

    if formulario.validate_on_submit():
        plataforma = (request.form.get('plataforma') or '').strip().lower()
        url_perfil = (request.form.get('url') or '').strip()
        ordem = formulario.ordem.data or 0
        ativo = request.form.get('ativo') in ('y', 'on', '1', 'true')

        # Validações
        if plataforma not in PLATAFORMAS_REDES:
            return _renderizar('Plataforma inválida — escolha uma da lista.')

        if not url_perfil.lower().startswith(('http://', 'https://')):
            return _renderizar('A URL precisa começar com http:// ou https://')

        meta = PLATAFORMAS_REDES[plataforma]
        icone = meta['icone']

        with SessionFactory() as session_db:
            # Impede duplicata de plataforma
            duplicada = (
                session_db.query(SocialLink)
                .filter(SocialLink.SOCIAL_PLATFORM == plataforma)
                .first()
            )
            if duplicada:
                return _renderizar(f'{meta["nome"]} já está conectado. Edite a conexão existente.')

            # Conflito de ordem — só valida quando ordem > 0
            if ordem and ordem > 0:
                conflito = (session_db.query(SocialLink).filter(SocialLink.SOCIAL_ORDER == ordem).first())
                if conflito:
                    return _renderizar(f'A posição #{ordem} já está ocupada. Escolha outra ordem.')

            novo_link = SocialLink(
                SOCIAL_PLATFORM=plataforma,
                SOCIAL_URL=url_perfil,
                SOCIAL_ICON=icone,
                SOCIAL_ORDER=int(ordem) if ordem else 0,
                SOCIAL_ACTIVE=ativo,
            )
            session_db.add(novo_link)
            session_db.commit()

            _registrar_log(
                session_db,
                'create',
                objeto=novo_link,
                old_values=None,
                new_values=_snapshot_log(novo_link)
            )

            flash(f'{meta["nome"]} conectado com sucesso.', 'success')
            return redirect(url_for('administrador.exibir_redes_sociais'))

    return _renderizar()


# EDITAR REDE SOCIAL
@administrador_bp.route('/editar_rede_social', methods=['POST', 'GET'])
@adm_2af_required
def editar_rede_social():
    formulario = SocialLink_()
    social_id = request.args.get('social_id', type=int)

    if not social_id:
        return redirect(url_for('administrador.exibir_redes_sociais'))

    with SessionFactory() as session_db:
        link = (
            session_db.query(SocialLink)
            .filter(SocialLink.SOCIAL_ID == social_id)
            .first()
        )
        if not link:
            flash('Rede social não encontrada.', 'danger')
            return redirect(url_for('administrador.exibir_redes_sociais'))

        redes_ativas = (session_db.query(SocialLink).filter(SocialLink.SOCIAL_ACTIVE.is_(True)).order_by(SocialLink.SOCIAL_ORDER.asc()).all())

    meta = PLATAFORMAS_REDES.get(link.SOCIAL_PLATFORM, {
        'nome': link.SOCIAL_PLATFORM.title(),
        'icone': link.SOCIAL_ICON or 'fa fa-globe',
        'cor': '#0e5ca6', 'cor2': '#0a3d70',
        'sombra': 'rgba(14,92,166,.5)',
        'ex': 'https://exemplo.com/perfil',
    })

    def _renderizar(msg=None, categoria='danger'):
        if msg:
            flash(msg, categoria)
        return render_template(
            'admin_editar_social.html',
            formulario=formulario,
            link=link,
            meta=meta,
            plataformas=PLATAFORMAS_REDES,
            redes_ativas=redes_ativas,
        )

    # POST — atualizar
    if formulario.validate_on_submit():
        url_perfil = (request.form.get('url') or '').strip()
        ordem = formulario.ordem.data or 0
        ativo = request.form.get('ativo') in ('y', 'on', '1', 'true')

        if not url_perfil.lower().startswith(('http://', 'https://')):
            return _renderizar('A URL precisa começar com http:// ou https://')

        with SessionFactory() as session_db:
            link_db = (
                session_db.query(SocialLink)
                .filter(SocialLink.SOCIAL_ID == social_id)
                .first()
            )
            if not link_db:
                flash('Rede social não encontrada.', 'danger')
                return redirect(url_for('administrador.exibir_redes_sociais'))

            old_values_log = _snapshot_log(link_db)

            # Conflito de ordem — ignora o próprio e ordens 0/vazias
            if ordem and ordem > 0:
                conflito = (
                    session_db.query(SocialLink)
                    .filter(SocialLink.SOCIAL_ORDER == ordem, SocialLink.SOCIAL_ID != link_db.SOCIAL_ID).first())
                if conflito:
                    return _renderizar(f'A posição #{ordem} já está ocupada. Escolha outra ordem.')

            # Plataforma é imutável — mantém a original, ignora qualquer tentativa
            # de troca via form
            link_db.SOCIAL_URL = url_perfil
            link_db.SOCIAL_ORDER = int(ordem) if ordem else 0
            link_db.SOCIAL_ACTIVE = ativo
            # SOCIAL_ICON reforçado a partir do catálogo (garante consistência
            # caso o admin do sistema atualize o mapa de ícones)
            if link_db.SOCIAL_PLATFORM in PLATAFORMAS_REDES:
                link_db.SOCIAL_ICON = PLATAFORMAS_REDES[link_db.SOCIAL_PLATFORM]['icone']

            session_db.commit()

            _registrar_log(
                session_db,
                'update',
                objeto=link_db,
                old_values=old_values_log,
                new_values=_snapshot_log(link_db)
            )

            flash(f'{meta["nome"]} atualizado com sucesso.', 'success')
            return redirect(url_for('administrador.exibir_redes_sociais'))

    
    formulario.url.data = link.SOCIAL_URL
    formulario.ordem.data = link.SOCIAL_ORDER
    formulario.ativo.data = link.SOCIAL_ACTIVE
    if hasattr(formulario, 'plataforma'):
        formulario.plataforma.data = link.SOCIAL_PLATFORM

    return _renderizar()


# EXCLUIR REDE SOCIAL
@administrador_bp.route('/excluir_rede_social', methods=['POST', 'GET'])
@adm_2af_required
def excluir_rede_social():
    social_id = request.args.get('social_id', type=int)

    if not social_id:
        return redirect(url_for('administrador.exibir_redes_sociais'))

    with SessionFactory() as session_db:
        link = (session_db.query(SocialLink).filter(SocialLink.SOCIAL_ID == social_id).first())
        if not link:
            flash('Rede social não encontrada.', 'danger')
            return redirect(url_for('administrador.exibir_redes_sociais'))

        nome = PLATAFORMAS_REDES.get(link.SOCIAL_PLATFORM, {}).get('nome', link.SOCIAL_PLATFORM)
        old_values_log = _snapshot_log(link)
        record_id_log = _id_registro_log(link)

        session_db.delete(link)
        session_db.commit()

        _registrar_log(
            session_db,
            'delete',
            tabela=SocialLink.__tablename__,
            record_id=record_id_log,
            old_values=old_values_log,
            new_values=None
        )

        flash(f'{nome} desconectado com sucesso.', 'success')
        return redirect(url_for('administrador.exibir_redes_sociais'))




# SETOR DE ORAÇÕES

# Exibir pedidos
@administrador_bp.route('/exibir_pedidos_oracao', methods=['GET'])
@adm_2af_required
def exibir_pedidos_oracao():
    # Carregando os dados
    with SessionFactory() as session_db:
        pedidos = session_db.query(PrayerRequest).all()
        administrador = current_user

        # dados
        pendentes = sum(1 for pedido in pedidos  if pedido.PRAYER_STATUS == 'pendente')
        orando = sum(1 for pedido in pedidos if pedido.PRAYER_STATUS == 'orando')
        respondidas = sum(1 for pedido in pedidos  if pedido.PRAYER_STATUS == 'respondida')
        hoje = datetime.datetime.today().date()
        urgentes = sum( 1 for pedido in pedidos  if pedido.PRAYER_PRIORITY == 'urgent' and pedido.PRAYER_CREATED_AT.date() == hoje)

        return render_template(
            'admin_oracao.html',
            pedidos=pedidos,
            administrador=administrador,
            pendentes=pendentes,
            orando=orando,
            respondidas=respondidas,
            urgentes=urgentes,
            hoje=hoje
        )

    

# Rota de editar pedidos
@administrador_bp.route('/editar_pedidos_oracao', methods=['POST'])
@adm_2af_required
def editar_pedidos_oracao():
    pedido_id = request.args.get('pedido_id', type=int)
    novo_status = (request.form.get('status') or '').strip()

    if not pedido_id or novo_status not in ('pendente', 'orando', 'respondida'):
        return jsonify({'sucesso': False, 'mensagem': 'Dados inválidos.'}), 400

    with SessionFactory() as session_db:
        pedido = session_db.query(PrayerRequest).filter(PrayerRequest.PRAYER_ID == pedido_id).first()

        if not pedido:
            return jsonify({'sucesso': False, 'mensagem': 'Pedido não encontrado.'}), 404

        old_values_log = _snapshot_log(pedido)
        pedido.PRAYER_STATUS = novo_status
        session_db.commit()

        _registrar_log(
            session_db, 'update',
            objeto=pedido,
            old_values=old_values_log,
            new_values=_snapshot_log(pedido)
        )

        return jsonify({'sucesso': True, 'status': novo_status})

# Excluir oração
@administrador_bp.route('/excluir_pedido_oracao', methods=['POST', 'GET'])
@adm_2af_required
def excluir_pedido_oracao():
    # Recebendo ID do link a ser excluido
    pedido_id = request.args.get('pedido_id')

    if pedido_id:
        with SessionFactory() as session_db:
            pedido_selecionado = session_db.query(PrayerRequest).filter(PrayerRequest.PRAYER_ID == int(pedido_id)).first()
            if pedido_selecionado:
                # LOG: salva os dados antes da exclusão
                old_values_log = _snapshot_log(pedido_selecionado)
                record_id_log = _id_registro_log(pedido_selecionado)

                session_db.delete(pedido_selecionado)
                session_db.commit()

                # LOG: pedido de oração excluído
                _registrar_log(
                    session_db,
                    'delete',
                    tabela=PrayerRequest.__tablename__,
                    record_id=record_id_log,
                    old_values=old_values_log,
                    new_values=None
                )

                return redirect(url_for('administrador.exibir_pedidos_oracao'))
            else:
                return redirect(url_for('administrador.exibir_pedidos_oracao'))

    else:
        return redirect(url_for('administrador.exibir_pedidos_oracao'))



# SETOR DE LOGS

# Primeiro eu criei varias funções auxiliares para ajudar no desenvolvimento da rota de registrar os logs no sistema

# Função para pegar uma data, e mensurar a quando tempo se passou dela e trazer um texto escrito, tipo|: Se passou 7 minutos..
def formatar_tempo_relativo(dt):
    agora = datetime.datetime.now()
    diferenca = agora - dt
    segundos = diferenca.total_seconds()

    if segundos < 60:
        return 'agora mesmo'
    elif segundos < 3600:
        minutos = int(segundos // 60)
        return f'há {minutos} minuto{"s" if minutos != 1 else ""}'
    elif segundos < 86400 and diferenca.days == 0:
        horas = int(segundos // 3600)
        return f'há {horas} hora{"s" if horas != 1 else ""}'
    elif diferenca.days == 1:
        return 'ontem'
    elif diferenca.days < 7:
        return f'há {diferenca.days} dias'
    else:
        return dt.strftime('%d/%m/%Y')


# São os icones de ação que estarão presente no html
ACAO_ICONE = {
    'create': 'fa-plus',
    'update': 'fa-pencil',
    'delete': 'fa-trash',
    'login': 'fa-sign-in',
    'logout': 'fa-sign-out',
}

# Icones de trabalho
ACAO_LABEL = {
    'create': 'Criação',
    'update': 'Atualização',
    'delete': 'Exclusão',
    'login': 'Login',
    'logout': 'Logout',
}


# Monta a descrição curta exibida ao lado do nome do administrador 
def montar_descricao(acao, tabela):
    if acao == 'login':
        return 'entrou no painel'
    elif acao == 'logout':
        return 'encerrou a sessão'
    elif acao == 'create':
        return f'cadastrou um novo registro em {tabela}'
    elif acao == 'update':
        return f'atualizou um registro em {tabela}'
    elif acao == 'delete':
        return f'excluiu um registro em {tabela}'
    return f'realizou uma ação em {tabela}'


# Monta a lista de diferenças (antes/depois) a partir dos JSONs salvos no log
def montar_diff(old_values, new_values):
    # Ações de login/logout não têm diff de dados, então isso nem é chamado pra elas
    old_values = old_values or {}
    new_values = new_values or {}

    # Pega todas as chaves envolvidas, mantendo a ordem: primeiro as do "antes", depois as novas do "depois"
    chaves = list(old_values.keys())
    for chave in new_values.keys():
        if chave not in chaves:
            chaves.append(chave)


    diff = []
    for chave in chaves:
        valor_antes = old_values.get(chave)
        valor_depois = new_values.get(chave)
        diff.append({
            'campo': chave,
            'antes': valor_antes,
            'depois': valor_depois,
            'mudou': valor_antes != valor_depois,
        })


    return diff


# Registro de acessos (logs administrativos) — apenas para root
@administrador_bp.route('/registro_acessos', methods=['GET'])
@adm_2af_required
@root_permission
def registro_acessos():
    administrador = current_user

    # Parâmetros de filtro vindos da URL (query string)
    busca = request.args.get('q', '').strip()
    acao_filtro = request.args.get('acao', '').strip()
    admin_filtro = request.args.get('admin_id', '').strip()
    periodo_filtro = request.args.get('periodo', '').strip()
    pagina = request.args.get('pagina', 1, type=int)
    por_pagina = 20

    with SessionFactory() as session_db:
        query = (session_db.query(AdminLog).join(Administrador, AdminLog.LOG_ADMIN_ID == Administrador.ADMIN_ID))

        # Filtro de busca livre: nome do admin, tabela afetada ou IP
        if busca:
            termo = f'%{busca}%'
            query = query.filter(
                (Administrador.ADMIN_NAME.ilike(termo)) |
                (AdminLog.LOG_TABLE_AFFECTED.ilike(termo)) |
                (AdminLog.LOG_IP_ADDRESS.ilike(termo))
            )

        # Filtros por tipo de ação, administrador e por periodo
        
        if acao_filtro:
            query = query.filter(AdminLog.LOG_ACTION == acao_filtro)
        if admin_filtro:
            query = query.filter(AdminLog.LOG_ADMIN_ID == int(admin_filtro))

        hoje = datetime.date.today()

        if periodo_filtro == 'hoje':
            query = query.filter(func.date(AdminLog.LOG_CREATED_AT) == hoje)
        elif periodo_filtro == '7':
            query = query.filter(AdminLog.LOG_CREATED_AT >= hoje - datetime.timedelta(days=7))
        elif periodo_filtro == '30':
            query = query.filter(AdminLog.LOG_CREATED_AT >= hoje - datetime.timedelta(days=30))

        # Do mais recente para o mais antigo
        query = query.order_by(AdminLog.LOG_CREATED_AT.desc())

        # Contando o total ANTES de paginar, pra calcular quantas páginas existem
        total_registros = query.count()
        total_paginas = max(1, (total_registros + por_pagina - 1) // por_pagina)
        pagina = min(max(pagina, 1), total_paginas)

        # Aplicando a paginação de fato
        logs = (query.offset((pagina - 1) * por_pagina).limit(por_pagina).all())

        # Estatísticas do topo da página (cards)
        total_logs = session_db.query(AdminLog).count()

        logins_30_dias = (session_db.query(AdminLog).filter(AdminLog.LOG_ACTION == 'login',AdminLog.LOG_CREATED_AT >= hoje - datetime.timedelta(days=30)).count())

        inicio_mes = hoje.replace(day=1)
        alteracoes_mes = (session_db.query(AdminLog).filter(AdminLog.LOG_ACTION.in_(['create', 'update']), func.date(AdminLog.LOG_CREATED_AT) >= inicio_mes).count())
        exclusoes_mes = (session_db.query(AdminLog).filter(AdminLog.LOG_ACTION == 'delete', func.date(AdminLog.LOG_CREATED_AT) >= inicio_mes).count())

        # Lista de administradores pra preencher o select de filtro
        administradores = session_db.query(Administrador).order_by(Administrador.ADMIN_NAME).all()


        logs_processados = []
        for log in logs:
            item = {
                'log': log,
                'admin_nome': log.administrador.ADMIN_NAME if log.administrador else 'Administrador removido',
                'tempo_relativo': formatar_tempo_relativo(log.LOG_CREATED_AT),
                'data_formatada': log.LOG_CREATED_AT.strftime('%d/%m/%Y · %H:%M'),
                'icone': ACAO_ICONE.get(log.LOG_ACTION, 'fa-info-circle'),
                'label': ACAO_LABEL.get(log.LOG_ACTION, log.LOG_ACTION),
                'descricao': montar_descricao(log.LOG_ACTION, log.LOG_TABLE_AFFECTED),
                'tem_diff': log.LOG_ACTION in ('create', 'update', 'delete'),
                'diff': montar_diff(log.LOG_OLD_VALUES, log.LOG_NEW_VALUES) if log.LOG_ACTION in ('create', 'update', 'delete') else [],
            }
            logs_processados.append(item)

        # Janela de páginas exibidas na paginação (ex: 3 4 [5] 6 7)
        janela = 2
        inicio_pag = max(1, pagina - janela)
        fim_pag = min(total_paginas, pagina + janela)
        paginas_exibir = list(range(inicio_pag, fim_pag + 1))

    return render_template(
        'logs.html',
        administrador=administrador,
        logs=logs_processados,
        administradores=administradores,
        total_registros=total_registros,
        total_logs=total_logs,
        logins_30_dias=logins_30_dias,
        alteracoes_mes=alteracoes_mes,
        exclusoes_mes=exclusoes_mes,
        pagina=pagina,
        total_paginas=total_paginas,
        por_pagina=por_pagina,
        paginas_exibir=paginas_exibir,
        busca=busca,
        acao_filtro=acao_filtro,
        admin_filtro=admin_filtro,
        periodo_filtro=periodo_filtro,
    )













