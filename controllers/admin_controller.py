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
from templates.editor.flask_form.every_forms import Biblical_Study
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
import os
from werkzeug.utils import secure_filename
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError



administrador_bp = Blueprint('administrador', __name__, url_prefix='/admin')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
# Página do administrador 
@administrador_bp.route('/')
@adm_2af_required
def index():
    # Carregando dados dos administradores
    with SessionFactory() as session_db:
        administradores = session_db.query(Administrador).all()
        estudos = session_db.query(BiblicalStudy).all()
    dados_sensiveis = session.get('dados_sensiveis')
    administrador = current_user
    return render_template('admin.html', dados_sensiveis=dados_sensiveis, administrador=administrador, administradores = administradores, estudos=estudos)


# ROTAS EXCLUSIVAS PARA USUÁRIOS ROOT

# Cadastrar administrador
@administrador_bp.route('/cadastrar_adm', methods=['POST', 'GET'])
@adm_2af_required
@root_permission
def cadastrar_adm():
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
                return render_template('root/cadastro_administrador.html', formulario=formulario_cadastro)
                # return redirect(url_for('administrador.cadastrar_adm'))

    
        
        # Criando administrador
        novo_administrador = Administrador(ADMIN_NAME = nome, ADMIN_EMAIL = email, ADMIN_ACTIVE = True if ativo == 'ativo' else False)
        novo_administrador.set_password(password)
        # Salvando no banco 
        with SessionFactory() as session:
            session.add(novo_administrador)
            session.commit()
    
        # Redirecionando para a página principal de administradores
        return redirect(url_for('administrador.index'))
    return render_template('root/cadastro_administrador.html', formulario=formulario_cadastro)


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
                return render_template('root/editar_administrador.html', formulario=formulario, administrador_selected=administrador_selected)
            
            else:
                # Atualizar o administrador
                administrador_selected.ADMIN_NAME = nome
                administrador_selected.ADMIN_EMAIL = email
                administrador_selected.ADMIN_ACTIVE = (True if ativo == 'ativo' else False)
                session_db.commit()

                # Redirecionando para o menu principal
                return redirect(url_for('administrador.index'))
            
        
    # Carregando ID do usuário
    user_id = request.args.get('user_id')
    if user_id:
        with SessionFactory() as session_db:
            administrador_selected = session_db.query(Administrador).filter(Administrador.ADMIN_ID==int(user_id)).first()
            if administrador_selected:
                # Definindo status (não tem como enviar pré carregado direto no template)
                formulario.ativo.data = ('ativo' 
                                        if administrador_selected.ADMIN_ACTIVE 
                                        else 
                                        'desativo') 
                return render_template('root/editar_administrador.html', formulario=formulario, administrador_selected=administrador_selected)
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
                    administrador_selected.set_password(password)
                    administrador_selected.ADMIN_TWO_FACTOR_FIRST = False
                    session_db.commit()
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

    return render_template('root/atualizarsenha_adm.html', user_id=user_id, administrador_selected=administrador_selected, formulario=formulario)


# Excluir administrador
@administrador_bp.route('/excluir_adm', methods=['POST', 'GET'])
@adm_2af_required
@root_permission
def excluir_adm():
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
                    session_db.delete(user_delete)
                    session_db.commit()
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
            return ('Digite a senha corretamente para realizar esta ação')
  
    # Carregando formulário de senha de confirmação para execução
    formulario = PasswordConfirm()
    # Carregando dados do administrador selecionado para ser excluido
    identificador = int(request.args.get('id')) 
    with SessionFactory() as session_db:
        administrador_selected = session_db.query(Administrador).filter(Administrador.ADMIN_ID == identificador).first()
    return render_template('root/excluir_administrador.html', administrador_selected=administrador_selected, formulario=formulario, id=identificador)
    


# FUNÇÕES DE ADMINISTRAÇÃO 

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

        if conteudo == '<p><br></p>':
            flash('Preencha o campo de conteúdo para realizar o cadastro do estudo')
            return render_template('editor/biblical_study_forms.html',formulario=formulario)

        # Salvando no banco de dados 
        with SessionFactory() as session_db:
            novo_estudo_biblico = BiblicalStudy(STUDY_TITLE = titulo, STUDY_CONTENT=conteudo, STUDY_BIBLICAL_REFERENCE = referencia, STUDY_THEME=tema, STUDY_FEATURED = destaque, STUDY_PUBLISHED = publicar, STUDY_ADMINISTRADOR_ID=current_user.ADMIN_ID)
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
            session_db.add(novo_estudo_biblico)
            session_db.commit()
            return redirect(url_for('administrador.index'))
                        

    return render_template('editor/biblical_study_forms.html',formulario=formulario)


# Atualizar estudo bíblico 
@administrador_bp.route('/atualizar_estudo', methods=['POST', 'GET'])
@adm_2af_required
def atualizar_estudo():
    formulario = Biblical_Study()

    # Pegando ID do estudo a ser atualizado
    estudo_id = request.args.get('estudo_id')

    if formulario.validate_on_submit():
        # Carregando os valores obditos no formuário
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        referencia = request.form.get('referencia')
        tema = request.form.get('tema')
        destaque = formulario.destaque.data
        publicar = formulario.publicar.data
        banner = formulario.banner.data


        # Atualizando estudo
        with SessionFactory() as session_db:
            estudo_selected = session_db.query(BiblicalStudy).filter(BiblicalStudy.STUDY_ID == int(estudo_id)).first()
            
            # Verificando se conteudo foi carregado
            if conteudo == '<p><br></p>':
                flash('Preencha o campo de conteúdo para realizar o cadastro do estudo')
                return redirect(url_for('administrador.atualizar_estudo', estudo_id=estudo_id))
            
        

            if estudo_selected:
                # Se o banner de estudo for enviada
                if banner:
                    # Salvando a imagem
                    extensao = os.path.splitext(secure_filename(banner.filename))[1]
                    nome_foto = f'estudo_{estudo_selected.STUDY_ID}{extensao}'
                    banner.save(
                        os.path.join(current_app.config['UPLOADS_FOLDER'], "estudos", nome_foto)
                    )
                    # Salvando caminho no banco de dados
                    estudo_selected.STUDY_BANNER = nome_foto

                estudo_selected.STUDY_TITLE = titulo
                estudo_selected.STUDY_CONTENT = conteudo
                estudo_selected.STUDY_BIBLICAL_REFERENCE = referencia
                estudo_selected.STUDY_THEME = tema
                estudo_selected.STUDY_FEATURED = destaque
                estudo_selected.STUDY_PUBLISHED = publicar
                session_db.commit()

                # Redirecionando para a rota principal de administrador 
                return redirect(url_for('administrador.index'))
            else:
                return redirect(url_for('administrador.index'))

    # Carregando dados do estudo selecionado
    if estudo_id:
        with SessionFactory() as session_db:
            estudo_selected = session_db.query(BiblicalStudy).filter(BiblicalStudy.STUDY_ID == int(estudo_id)).first()
            if estudo_selected:
                # Aqui é o que diferencia o sistema, onde eu carrego os dados de forma pré-carregada no proprio formulario
                formulario.titulo.data = estudo_selected.STUDY_TITLE
                formulario.conteudo.data = estudo_selected.STUDY_CONTENT
                formulario.referencia.data = estudo_selected.STUDY_BIBLICAL_REFERENCE
                formulario.tema.data = estudo_selected.STUDY_THEME
                formulario.destaque.data = estudo_selected.STUDY_FEATURED
                formulario.publicar.data = estudo_selected.STUDY_PUBLISHED
                return render_template('editor/atualizar_estudo.html', formulario=formulario, estudo_selected=estudo_selected)
            else:
                return redirect(url_for('administrador.index'))
    else:
        return redirect(url_for('administrador.index'))


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
                        session_db.delete(estudo_delete)
                        session_db.commit()
                        # Retornando para o painel principal após ser deletado
                        return redirect(url_for('administrador.index'))
                    else:
                        flash('Senha incorreta, por favor, digite novamente')
                        render_template('editor/excluir_estudo.html', estudo_selected=estudo_selected, formulario=formulario, id=identificador)
                else:
                    return redirect(url_for('administrador.index'))
        else:
            return redirect(url_for('administrador.index'))

    
    return render_template('editor/excluir_estudo.html', estudo_selected=estudo_selected, formulario=formulario, id=identificador)


# AGENDA DA SEMANA 

# ADICIONAR EVENTO NA AGENDA
@administrador_bp.route('/adicionar_agenda', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_agenda():
    # Carregando dados necessários 
    formulario = Weekly_Schedule()
    with SessionFactory() as session_db:
        agenda = session_db.query(WeeklySchedule).all()
    
    # Adicionando novo evento
    if formulario.validate_on_submit():
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        local = request.form.get('local')
        dia = request.form.get('dia')
        hora = formulario.hora.data
        activate = formulario.activate.data
        
        # Salvando no banco
        with SessionFactory() as session_db:
            novo_evento = WeeklySchedule(SCHEDULE_TITLE=titulo, SCHEDULE_DAY=dia, SCHEDULE_TIME = hora, SCHEDULE_LOCATION=local, SCHEDULE_DESCRIPTION = descricao, SCHEDULE_ACTIVE = activate, SCHEDULE_ADMINISTRADOR_ID=current_user.ADMIN_ID)
            session_db.add(novo_evento)
            session_db.commit()
            return redirect(url_for('administrador.adicionar_agenda'))


    # Carregando a página de exibir e adicionar eventos a agenda
    return render_template('editor/agenda/menu.html', formulario=formulario, agenda=agenda)

# ATUALIZANDO EVENTO DA AGENDA
@administrador_bp.route('/atualizar_agenda', methods=['POST', 'GET'])
@adm_2af_required
def atualizar_agenda():
    # Carregando dados necessários 
    formulario = Weekly_Schedule()
    agenda_id = request.args.get('agenda_id')
    
    # Coletando dados obtidos do formulário
    if formulario.validate_on_submit():
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        local = request.form.get('local')
        dia = request.form.get('dia')
        hora = formulario.hora.data
        activate = formulario.activate.data
        
        # Salvando no banco
        with SessionFactory() as session_db:
            evento_selecionado = session_db.query(WeeklySchedule).filter(WeeklySchedule.SCHEDULE_ID == int(agenda_id)).first()
            evento_selecionado.SCHEDULE_TITLE = titulo
            evento_selecionado.SCHEDULE_DESCRIPTION = descricao
            evento_selecionado.SCHEDULE_LOCATION = local
            evento_selecionado.SCHEDULE_DAY = dia
            evento_selecionado.SCHEDULE_TIME = hora
            evento_selecionado.SCHEDULE_ACTIVE = activate
            session_db.commit()
            return redirect(url_for('administrador.adicionar_agenda'))
    
    if agenda_id:
        with SessionFactory() as session_db:
            agenda = session_db.query(WeeklySchedule).filter(WeeklySchedule.SCHEDULE_ID == int(agenda_id)).first()
            formulario.titulo.data = agenda.SCHEDULE_TITLE
            formulario.descricao.data = agenda.SCHEDULE_DESCRIPTION
            formulario.dia.data = agenda.SCHEDULE_DAY
            formulario.local.data = agenda.SCHEDULE_LOCATION
            formulario.hora.data = agenda.SCHEDULE_TIME
            formulario.activate.data = agenda.SCHEDULE_ACTIVE
    else:
        return redirect(url_for('administrador.adicionar_agenda'))


    return render_template('editor/agenda/atualizar_agenda.html', formulario=formulario, agenda=agenda)


# EXCLUINDO AGENDA

@administrador_bp.route('/excluir_agenda', methods=['POST', 'GET'])
@adm_2af_required
def excluir_agenda():
    # Recebendo ID da agenda a ser excluida
    agenda_id = request.args.get('agenda_id')

    if agenda_id:
        # Excluindo agenda
        with SessionFactory() as session_db:
            agenda_selecionada = session_db.query(WeeklySchedule).filter(WeeklySchedule.SCHEDULE_ID == int(agenda_id)).first()
            if agenda_selecionada:
                session_db.delete(agenda_selecionada)
                session_db.commit()
                return redirect(url_for('administrador.adicionar_agenda'))
            else:
                return redirect(url_for('administrador.adicionar_agenda'))
            
    else:
        return redirect(url_for('administrador.adicionar_agenda'))
    

# ADMINISTRANDO DEVOCIONAIS 

# Exibir devocionais
@administrador_bp.route('/exibir_devocionais', methods=['GET'])
@adm_2af_required
def exibir_devocionais():
    # Carregando devocionais existentes e exibindo página principal
    with SessionFactory() as session_db:
        devocionais = session_db.query(Devotional).all()
    return render_template('editor/devocional/menu.html', devocionais=devocionais)

# ADICIONAR DEVOCIONAL 
@administrador_bp.route('/adicionar_devocional', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_devocional():
    # Carregando dados necessários 
    formulario = Devotional_()
    # Definindo data minima para o periodo de exibição do devocional
    hoje = datetime.date.today().isoformat()
    
    # Adicionando novo devocional
    if formulario.validate_on_submit():
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        versiculo = request.form.get('versiculo')
        banner = formulario.banner.data
        inicio = formulario.inicio.data
        fim = formulario.fim.data
        publicar = formulario.publicar.data
        

        # Salvando devocional 
        with SessionFactory() as session_db:
            # Verificando data para ver se ela é válida
            devocional_verify = session_db.query(Devotional).filter(Devotional.DEVOTIONAL_WEEK_START <= fim, Devotional.DEVOTIONAL_WEEK_END >= inicio).first()

            if devocional_verify:
                flash('Data indisponível, tente outro periodo')
                formulario.titulo.data = titulo
                formulario.conteudo.data = conteudo 
                formulario.versiculo.data = versiculo 
                formulario.publicar.data = publicar 
                return render_template('editor/devocional/cadastrar_devocional.html', formulario=formulario, hoje=hoje)
            
            # Salvando no banco de dados
            devotional = Devotional(DEVOTIONAL_TITLE=titulo, DEVOTIONAL_CONTENT=conteudo, DEVOTIONAL_BIBLICAL_VERSE = versiculo, DEVOTIONAL_WEEK_START = inicio, DEVOTIONAL_WEEK_END = fim, DEVOTIONAL_ADMINISTRADOR_ID=current_user.ADMIN_ID, DEVOTIONAL_PUBLISHED = publicar)
            session_db.add(devotional)
            session_db.commit()

            # Salvando a imagem
            extensao = os.path.splitext(secure_filename(banner.filename))[1]
            nome_banner = f'devocional_{devotional.DEVOTIONAL_ID}{extensao}'
            banner.save(
                os.path.join(current_app.config['UPLOADS_FOLDER'], "devocionais", nome_banner)
            )

            # Salvando caminho no banco de dados
            devotional.DEVOTIONAL_BANNER = nome_banner
            session_db.commit()

            return redirect(url_for('administrador.exibir_devocionais'))


    # Carregando a página de exibir e adicionar eventos a agenda
    return render_template('editor/devocional/cadastrar_devocional.html', formulario=formulario, hoje=hoje)

# EDITAR DEVOCIONAL
@administrador_bp.route('/editar_devocional', methods=['POST', 'GET'])
@adm_2af_required
def editar_devocional():
    # Carregando dados necessários 
    formulario = DevotionalUpdate()
    # Pegando o ID do devocional a ser editado
    devocional_id = request.args.get('devocional_id')

    # Atualizando devocional 
    if formulario.validate_on_submit():
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        versiculo = request.form.get('versiculo')
        banner = formulario.banner.data
        inicio = formulario.inicio.data
        fim = formulario.fim.data
        publicar = formulario.publicar.data
        
        if devocional_id:
            # Salvando devocional 
            with SessionFactory() as session_db:
                devotional = session_db.query(Devotional).filter(Devotional.DEVOTIONAL_ID == int(devocional_id)).first()

                # Validação dos dados de datas de uma maneira EXTREMAMENTE SIMPLIFICADA E FÁCIL, graças as novas funções que adicionei ao sistema

                # 1º Etapa: Validando as regras do periodo
                permitido, mensagem = devotional.can_update_period(inicio, fim)

                if not permitido:
                    flash(mensagem)
                    formulario.titulo.data = titulo
                    formulario.conteudo.data = conteudo 
                    formulario.versiculo.data = versiculo 
                    formulario.publicar.data = publicar 
                    return render_template('editor/devocional/atualizar_devocional.html', formulario=formulario, devocional=devotional)
                
                # Verificando se existe conflito de horário
                conflito = session_db.query(Devotional).filter(
                    Devotional.DEVOTIONAL_ID != devotional.DEVOTIONAL_ID,
                    Devotional.DEVOTIONAL_WEEK_START <= fim,
                    Devotional.DEVOTIONAL_WEEK_END >= inicio
                ).first()

                if conflito:
                    flash('Já existe devocional reservado neste horário')
                    formulario.titulo.data = titulo
                    formulario.conteudo.data = conteudo 
                    formulario.versiculo.data = versiculo 
                    formulario.publicar.data = publicar 
                    return render_template('editor/devocional/atualizar_devocional.html', formulario=formulario, devocional=devotional)


                devotional.DEVOTIONAL_TITLE=titulo
                devotional.DEVOTIONAL_CONTENT=conteudo
                devotional.DEVOTIONAL_BIBLICAL_VERSE = versiculo
                devotional.DEVOTIONAL_WEEK_START = inicio
                devotional.DEVOTIONAL_WEEK_END = fim
                devotional.DEVOTIONAL_ADMINISTRADOR_ID=current_user.ADMIN_ID
                devotional.DEVOTIONAL_PUBLISHED = publicar
                session_db.commit()

                # Se a pessoa adicionou um novo banner
                if banner:
                    # Deletando antiga imagem
                    caminho = os.path.join(
                        current_app.config['UPLOADS_FOLDER'],
                        'devocionais',
                        devotional.DEVOTIONAL_BANNER
                    )
                    if os.path.exists(caminho):
                        os.remove(caminho)

                        # Salvando a imagem
                        extensao = os.path.splitext(secure_filename(banner.filename))[1]
                        nome_banner = f'devocional_{devotional.DEVOTIONAL_ID}{extensao}'
                        banner.save(
                            os.path.join(current_app.config['UPLOADS_FOLDER'], "devocionais", nome_banner)
                        )

                        # Salvando caminho no banco de dados
                        devotional.DEVOTIONAL_BANNER = nome_banner
                        session_db.commit()

                return redirect(url_for('administrador.exibir_devocionais'))

    # carregando formulário já preenchido com os atuais dados
    if devocional_id:
        with SessionFactory() as session_db:
            devocional_selecionado = session_db.query(Devotional).filter(Devotional.DEVOTIONAL_ID == int(devocional_id)).first()
            formulario.titulo.data = devocional_selecionado.DEVOTIONAL_TITLE
            formulario.conteudo.data = devocional_selecionado.DEVOTIONAL_CONTENT
            formulario.versiculo.data = devocional_selecionado.DEVOTIONAL_BIBLICAL_VERSE
            formulario.inicio.data = devocional_selecionado.DEVOTIONAL_WEEK_START
            formulario.fim.data = devocional_selecionado.DEVOTIONAL_WEEK_END
            formulario.publicar = devocional_selecionado.DEVOTIONAL_PUBLISHED

    # Carregando a página de exibir e adicionar eventos a agenda
    return render_template('editor/devocional/atualizar_devocional.html', formulario=formulario, devocional = devocional_selecionado)


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
                session_db.delete(devocional_selecionado)
                session_db.commit()
                return redirect(url_for('administrador.exibir_devocionais'))
            else:
                return redirect(url_for('administrador.exibir_devocionais'))
            
    else:
        return redirect(url_for('administrador.exibir_devocionais'))
    





# FUNÇÕES DE ADMINISTRAÇÃO - VÍDEOS/MENSAGENS

# Exibir vídeos 
@administrador_bp.route('/exibir_videos', methods=['GET'])
@adm_2af_required
def exibir_videos():
    with SessionFactory() as session_db:
        videos = session_db.query(VideoMessage).all()
        return render_template('editor/mensagens_videos/main.html', videos=videos)

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
            return render_template('editor/mensagens_videos/cadastrar_videos.html', formulario=formulario)

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
            return render_template("editor/mensagens_videos/cadastrar_videos.html",formulario=formulario)
            
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
            return redirect(url_for('administrador.exibir_videos'))

    return render_template('editor/mensagens_videos/cadastrar_videos.html', formulario=formulario)


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
                return render_template("editor/mensagens_videos/atualizar_videos.html",formulario=formulario, video_selected=video_selected)
                
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
                return render_template('editor/mensagens_videos/atualizar_videos.html', formulario=formulario, video_selected=video_selected)
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
            session_db.delete(video_selected)
            session_db.commit()
            return redirect(url_for('administrador.exibir_videos')) 

        else:
            return redirect(url_for('administrador.exibir_videos'))



# SETOR DE HISTÓRIA DA IGREJA

# Exibir etapas da história
@administrador_bp.route('/exibir_historia', methods=['GET'])
@adm_2af_required
def exibir_historia():
    # Carregando etapas existentes em ordem de exibição
    with SessionFactory() as session_db:
        historia = session_db.query(ChurchHistory).order_by(ChurchHistory.HISTORY_ORDER).all()
    return render_template('editor/historia/menu.html', historia=historia)


# ADICIONAR ETAPA DA HISTÓRIA
@administrador_bp.route('/adicionar_historia', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_historia():
    # Carregando dados necessários
    formulario = ChurchHistory_()

    # Adicionando nova etapa
    if formulario.validate_on_submit():
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        imagem = formulario.imagem.data
        ano_inicio = formulario.ano_inicio.data
        ano_fim = formulario.ano_fim.data
        ordem = formulario.ordem.data

        # Verificando datas
        if ano_fim and int(ano_fim)<int(ano_inicio):
            flash('O ano de termino não pode ser mais recente que o ano de início')
            formulario.titulo.data = titulo
            formulario.conteudo.data= conteudo
            formulario.ano_inicio.data = ano_inicio
            formulario.ano_fim.data = ano_fim
            formulario.ordem.data = ordem
            return render_template('editor/historia/cadastrar_historia.html', formulario=formulario)

        # Salvando no banco de dados
        with SessionFactory() as session_db:
            nova_etapa = ChurchHistory(HISTORY_TITLE=titulo, HISTORY_CONTENT=conteudo, HISTORY_YEAR_START=int(ano_inicio),  HISTORY_YEAR_END=int(ano_fim) if ano_fim else None, HISTORY_ORDER=ordem if ordem else 0, HISTORY_ADMINISTRADOR_ID=current_user.ADMIN_ID)
            
            # Verificando conflito de ordem
            ordem_verify = session_db.query(ChurchHistory).filter(
                ChurchHistory.HISTORY_ORDER == ordem
            ).first()

            if ordem_verify:
                flash('Já existe uma etapa cadastrada nesta ordem, escolha outra')
                formulario.titulo.data = titulo
                formulario.conteudo.data = conteudo
                formulario.ano_inicio.data = ano_inicio
                formulario.ano_fim.data = ano_fim
                return render_template('editor/historia/cadastrar_historia.html', formulario=formulario)

            # Cadastrando usuário
            session_db.add(nova_etapa)
            session_db.commit()

            # Salvando a imagem
            extensao = os.path.splitext(secure_filename(imagem.filename))[1]
            nome_imagem = f'historia_{nova_etapa.HISTORY_ID}{extensao}'
            imagem.save(
                os.path.join(current_app.config['UPLOADS_FOLDER'], "historia", nome_imagem)
            )

            # Salvando caminho no banco de dados
            nova_etapa.HISTORY_IMAGE = nome_imagem
            session_db.commit()

            return redirect(url_for('administrador.exibir_historia'))

    # Carregando a página de adicionar etapa
    return render_template('editor/historia/cadastrar_historia.html', formulario=formulario)


# EDITAR ETAPA DA HISTÓRIA
@administrador_bp.route('/editar_historia', methods=['POST', 'GET'])
@adm_2af_required
def editar_historia():
    # Carregando dados necessários
    formulario = ChurchHistoryUpdate()
    # Pegando o ID da etapa a ser editada
    historia_id = request.args.get('historia_id')

    # Atualizando etapa
    if formulario.validate_on_submit():
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        imagem = formulario.imagem.data
        ano_inicio = formulario.ano_inicio.data
        ano_fim = formulario.ano_fim.data
        ordem = formulario.ordem.data

        if historia_id:
            # Salvando etapa
            with SessionFactory() as session_db:
                etapa = session_db.query(ChurchHistory).filter(ChurchHistory.HISTORY_ID == int(historia_id)).first()

                if ano_fim and int(ano_fim)<int(ano_inicio):
                    flash('A data de termino não pode ser mais recente que a data de início')
                    formulario.titulo.data = titulo
                    formulario.conteudo.data= conteudo
                    formulario.ano_inicio.data = str(ano_inicio)
                    formulario.ano_fim.data = str(ano_fim) 
                    formulario.ordem.data = ordem
                    return render_template('editor/historia/atualizar_historia.html', formulario=formulario, etapa=etapa)
                
                # Verificando conflito de ordem
                ordem_verify = session_db.query(ChurchHistory).filter(
                    ChurchHistory.HISTORY_ORDER == ordem,
                    ChurchHistory.HISTORY_ID != etapa.HISTORY_ID
                ).first()

                if ordem_verify:
                    flash('Já existe uma etapa cadastrada nesta ordem, escolha outra')
                    formulario.titulo.data = titulo
                    formulario.conteudo.data = conteudo
                    formulario.ano_inicio.data = str(ano_inicio)
                    formulario.ano_fim.data = str(ano_fim) 
                    return render_template('editor/historia/atualizar_historia.html', formulario=formulario, etapa=etapa)

                etapa.HISTORY_TITLE = titulo
                etapa.HISTORY_CONTENT = conteudo
                etapa.HISTORY_YEAR_START = ano_inicio
                etapa.HISTORY_YEAR_END = int(ano_fim) if ano_fim else None
                etapa.HISTORY_ORDER = ordem if ordem else 0
                session_db.commit()

                # Se o administrador adicionou uma nova imagem
                if imagem:
                    # Deletando antiga imagem
                    caminho = os.path.join(
                        current_app.config['UPLOADS_FOLDER'],
                        'historia',
                        etapa.HISTORY_IMAGE
                    )
                    if os.path.exists(caminho):
                        os.remove(caminho)

                    # Salvando a imagem
                    extensao = os.path.splitext(secure_filename(imagem.filename))[1]
                    nome_imagem = f'historia_{etapa.HISTORY_ID}{extensao}'
                    imagem.save(
                        os.path.join(current_app.config['UPLOADS_FOLDER'], "historia", nome_imagem)
                    )

                    # Salvando caminho no banco de dados
                    etapa.HISTORY_IMAGE = nome_imagem
                    session_db.commit()

                return redirect(url_for('administrador.exibir_historia'))

    # Carregando formulário já preenchido com os dados atuais
    if historia_id:
        with SessionFactory() as session_db:
            etapa_selecionada = session_db.query(ChurchHistory).filter(ChurchHistory.HISTORY_ID == int(historia_id)).first()
            if etapa_selecionada:
                formulario.titulo.data = etapa_selecionada.HISTORY_TITLE
                formulario.conteudo.data = etapa_selecionada.HISTORY_CONTENT
                formulario.ano_inicio.data = str(etapa_selecionada.HISTORY_YEAR_START) 
                formulario.ano_fim.data = str(etapa_selecionada.HISTORY_YEAR_END)
                formulario.ordem.data = etapa_selecionada.HISTORY_ORDER
                return render_template('editor/historia/atualizar_historia.html', formulario=formulario, etapa=etapa_selecionada)
            else:
                return redirect(url_for('administrador.exibir_historia'))
    else:
        return redirect(url_for('administrador.exibir_historia'))


# Excluir etapa da história
@administrador_bp.route('/excluir_historia', methods=['POST', 'GET'])
@adm_2af_required
def excluir_historia():
    # Recebendo ID da etapa a ser excluida
    historia_id = request.args.get('historia_id')

    if historia_id:
        # Excluindo etapa
        with SessionFactory() as session_db:
            etapa_selecionada = session_db.query(ChurchHistory).filter(ChurchHistory.HISTORY_ID == int(historia_id)).first()
            if etapa_selecionada:
                session_db.delete(etapa_selecionada)
                session_db.commit()
                return redirect(url_for('administrador.exibir_historia'))
            else:
                return redirect(url_for('administrador.exibir_historia'))

    else:
        return redirect(url_for('administrador.exibir_historia'))



# SETOR DE DEPARTAMENTOS

# Exibir departamentos
@administrador_bp.route('/exibir_departamentos', methods=['GET'])
@adm_2af_required
def exibir_departamentos():
    # Carregando departamentos existentes em ordem de exibição
    with SessionFactory() as session_db:
        departamentos = session_db.query(Department).order_by(Department.DEPARTMENT_ORDER).all()
    return render_template('editor/departamento/menu.html', departamentos=departamentos)


# ADICIONAR DEPARTAMENTO
@administrador_bp.route('/adicionar_departamento', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_departamento():
    # Carregando dados necessários
    formulario = Department_()

    # Adicionando novo departamento
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

        # Salvando no banco de dados
        with SessionFactory() as session_db:
            # Verificando se já existe um departamento cadastrado nessa mesma ordem
            ordem_verify = session_db.query(Department).filter(Department.DEPARTMENT_ORDER == ordem).first()

            if ordem_verify:
                flash('Já existe um departamento cadastrado nesta ordem, escolha outra')
                formulario.nome.data = nome
                formulario.descricao.data = descricao
                formulario.lider_nome.data = lider_nome
                formulario.lider_bio.data = lider_bio
                formulario.contato_email.data = contato_email
                formulario.contato_telefone.data = contato_telefone
                formulario.ativo.data = ativo
                return render_template('editor/departamento/cadastrar_departamento.html', formulario=formulario)

            novo_departamento = Department(DEPARTMENT_NAME=nome, DEPARTMENT_DESCRIPTION=descricao, DEPARTMENT_LEADER_NAME=lider_nome, DEPARTMENT_LEADER_BIO=lider_bio, DEPARTMENT_CONTACT_EMAIL=contato_email, DEPARTMENT_CONTACT_PHONE=contato_telefone, DEPARTMENT_ORDER=ordem if ordem else 0, DEPARTMENT_ACTIVE=ativo, DEPARTMENT_ADMINISTRADOR_ID=current_user.ADMIN_ID)
            session_db.add(novo_departamento)
            session_db.commit()

            # Se uma foto do líder foi enviada
            if lider_foto:
                # Salvando a imagem
                extensao = os.path.splitext(secure_filename(lider_foto.filename))[1]
                nome_foto = f'departamento_{novo_departamento.DEPARTMENT_ID}{extensao}'
                lider_foto.save(
                    os.path.join(current_app.config['UPLOADS_FOLDER'], "departamentos", nome_foto)
                )

                # Salvando caminho no banco de dados
                novo_departamento.DEPARTMENT_LEADER_PHOTO = nome_foto
                session_db.commit()

            return redirect(url_for('administrador.exibir_departamentos'))

    # Carregando a página de adicionar departamento
    return render_template('editor/departamento/cadastrar_departamento.html', formulario=formulario)


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

                # Verificando conflito de ordem, ignorando o próprio departamento que está sendo editado
                ordem_verify = session_db.query(Department).filter(
                    Department.DEPARTMENT_ORDER == ordem,
                    Department.DEPARTMENT_ID != departamento.DEPARTMENT_ID
                ).first()

                if ordem_verify:
                    flash('Já existe um departamento cadastrado nesta ordem, escolha outra')
                    formulario.nome.data = nome
                    formulario.descricao.data = descricao
                    formulario.lider_nome.data = lider_nome
                    formulario.lider_bio.data = lider_bio
                    formulario.contato_email.data = contato_email
                    formulario.contato_telefone.data = contato_telefone
                    formulario.ativo.data = ativo
                    return render_template('editor/departamento/atualizar_departamento.html', formulario=formulario, departamento=departamento)

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
                return render_template('editor/departamento/atualizar_departamento.html', formulario=formulario, departamento=departamento_selecionado)
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
                session_db.delete(departamento_selecionado)
                session_db.commit()
                return redirect(url_for('administrador.exibir_departamentos'))
            else:
                return redirect(url_for('administrador.exibir_departamentos'))

    else:
        return redirect(url_for('administrador.exibir_departamentos'))
    



# SETOR DE EVENTOS

# Exibir eventos
@administrador_bp.route('/exibir_eventos', methods=['GET'])
@adm_2af_required
def exibir_eventos():
    # Carregando eventos existentes ordenados por data
    with SessionFactory() as session_db:
        eventos = session_db.query(Event).order_by(Event.EVENT_DATE).all()
    return render_template('editor/eventos/menu.html', eventos=eventos)


# ADICIONAR EVENTO
@administrador_bp.route('/adicionar_evento', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_evento():
    # Carregando dados necessários
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
            novo_evento = Event(EVENT_TITLE=titulo, EVENT_DESCRIPTION=descricao, EVENT_LOCATION=local, EVENT_DATE=data, EVENT_TIME=hora, EVENT_REGISTRATION_REQUIRED=inscricao_necessaria, EVENT_FEATURED=destaque, EVENT_PUBLISHED=publicar, EVENT_ADMINISTRADOR_ID=current_user.ADMIN_ID)
            session_db.add(novo_evento)
            session_db.commit()

            # Se um banner foi enviado
            if banner:
                # Salvando a imagem
                extensao = os.path.splitext(secure_filename(banner.filename))[1]
                nome_banner = f'evento_{novo_evento.EVENT_ID}{extensao}'
                banner.save(
                    os.path.join(current_app.config['UPLOADS_FOLDER'], "eventos", nome_banner)
                )

                # Salvando caminho no banco de dados
                novo_evento.EVENT_BANNER = nome_banner
                session_db.commit()

            return redirect(url_for('administrador.exibir_eventos'))

    # Carregando a página de adicionar evento
    return render_template('editor/eventos/cadastrar_evento.html', formulario=formulario, hoje=hoje)


# EDITAR EVENTO
@administrador_bp.route('/editar_evento', methods=['POST', 'GET'])
@adm_2af_required
def editar_evento():
    # Carregando dados necessários
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

        if evento_id:
            with SessionFactory() as session_db:
                evento = session_db.query(Event).filter(Event.EVENT_ID == int(evento_id)).first()

                evento.EVENT_TITLE = titulo
                evento.EVENT_DESCRIPTION = descricao
                evento.EVENT_LOCATION = local
                evento.EVENT_DATE = data
                evento.EVENT_TIME = hora
                evento.EVENT_REGISTRATION_REQUIRED = inscricao_necessaria
                evento.EVENT_FEATURED = destaque
                evento.EVENT_PUBLISHED = publicar
                session_db.commit()

                # Se o administrador adicionou um novo banner
                if banner:
                    # Deletando antigo banner, se existir
                    if evento.EVENT_BANNER:
                        caminho = os.path.join(
                            current_app.config['UPLOADS_FOLDER'],
                            'eventos',
                            evento.EVENT_BANNER
                        )
                        if os.path.exists(caminho):
                            os.remove(caminho)

                    # Salvando a imagem
                    extensao = os.path.splitext(secure_filename(banner.filename))[1]
                    nome_banner = f'evento_{evento.EVENT_ID}{extensao}'
                    banner.save(
                        os.path.join(current_app.config['UPLOADS_FOLDER'], "eventos", nome_banner)
                    )

                    # Salvando caminho no banco de dados
                    evento.EVENT_BANNER = nome_banner
                    session_db.commit()

                return redirect(url_for('administrador.exibir_eventos'))

    # Carregando formulário já preenchido com os dados atuais
    if evento_id:
        with SessionFactory() as session_db:
            evento_selecionado = session_db.query(Event).filter(Event.EVENT_ID == int(evento_id)).first()
            if evento_selecionado:
                formulario.titulo.data = evento_selecionado.EVENT_TITLE
                formulario.descricao.data = evento_selecionado.EVENT_DESCRIPTION
                formulario.local.data = evento_selecionado.EVENT_LOCATION
                formulario.data.data = evento_selecionado.EVENT_DATE
                formulario.hora.data = evento_selecionado.EVENT_TIME
                formulario.inscricao_necessaria.data = evento_selecionado.EVENT_REGISTRATION_REQUIRED
                formulario.destaque.data = evento_selecionado.EVENT_FEATURED
                formulario.publicar.data = evento_selecionado.EVENT_PUBLISHED
                return render_template('editor/eventos/atualizar_evento.html', formulario=formulario, evento=evento_selecionado, hoje=hoje)
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
                session_db.delete(evento_selecionado)
                session_db.commit()
                return redirect(url_for('administrador.exibir_eventos'))
            else:
                return redirect(url_for('administrador.exibir_eventos'))

    else:
        return redirect(url_for('administrador.exibir_eventos'))




# SETOR DE REDES SOCIAIS

# Exibir redes sociais
@administrador_bp.route('/exibir_redes_sociais', methods=['GET'])
@adm_2af_required
def exibir_redes_sociais():
    # Carregando links existentes em ordem de exibição
    with SessionFactory() as session_db:
        redes_sociais = session_db.query(SocialLink).order_by(SocialLink.SOCIAL_ORDER).all()
    return render_template('editor/redes_sociais/menu.html', redes_sociais=redes_sociais)


# ADICIONAR REDE SOCIAL
@administrador_bp.route('/adicionar_rede_social', methods=['POST', 'GET'])
@adm_2af_required
def adicionar_rede_social():
    # Carregando dados necessários
    formulario = SocialLink_()

    # Adicionando novo link
    if formulario.validate_on_submit():
        plataforma = formulario.plataforma.data
        url = request.form.get('url')
        ordem = formulario.ordem.data
        ativo = formulario.ativo.data

        # Salvando icone
        icone = f'bi-globe' if plataforma == 'site' else f'bi-{plataforma}'

        # Salvando no banco de dados
        with SessionFactory() as session_db:
            # Verificando se já existe um link cadastrado nessa mesma ordem
            ordem_verify = session_db.query(SocialLink).filter(SocialLink.SOCIAL_ORDER == ordem).first()

            if ordem_verify:
                flash('Já existe um link cadastrado nesta ordem, escolha outra')
                formulario.plataforma.data = plataforma
                formulario.url.data = url
                formulario.ativo.data = ativo
                return render_template('editor/redes_sociais/cadastrar_rede_social.html', formulario=formulario)

            novo_link = SocialLink(SOCIAL_PLATFORM=plataforma, SOCIAL_URL=url, SOCIAL_ICON=icone, SOCIAL_ORDER=ordem if ordem else 0, SOCIAL_ACTIVE=ativo)
            session_db.add(novo_link)
            session_db.commit()

            return redirect(url_for('administrador.exibir_redes_sociais'))

    # Carregando a página de adicionar rede social
    return render_template('editor/redes_sociais/cadastrar_rede_social.html', formulario=formulario)


# EDITAR REDE SOCIAL
@administrador_bp.route('/editar_rede_social', methods=['POST', 'GET'])
@adm_2af_required
def editar_rede_social():
    # Carregando dados necessários
    formulario = SocialLink_()
    # Pegando o ID do link a ser editado
    social_id = request.args.get('social_id')

    # Atualizando link
    if formulario.validate_on_submit():
        plataforma = formulario.plataforma.data
        url = request.form.get('url')
        ordem = formulario.ordem.data
        ativo = formulario.ativo.data

        # Salvando icone
        icone = f'bi-globe' if plataforma == 'site' else f'bi-{plataforma}'

        if social_id:
            with SessionFactory() as session_db:
                link = session_db.query(SocialLink).filter(SocialLink.SOCIAL_ID == int(social_id)).first()

                # Verificando conflito de ordem, ignorando o próprio link que está sendo editado
                ordem_verify = session_db.query(SocialLink).filter(
                    SocialLink.SOCIAL_ORDER == ordem,
                    SocialLink.SOCIAL_ID != link.SOCIAL_ID
                ).first()

                if ordem_verify:
                    flash('Já existe um link cadastrado nesta ordem, escolha outra')
                    formulario.plataforma.data = plataforma
                    formulario.url.data = url
                    formulario.ativo.data = ativo
                    return render_template('editor/redes_sociais/atualizar_rede_social.html', formulario=formulario, link=link)

                link.SOCIAL_PLATFORM = plataforma
                link.SOCIAL_URL = url
                link.SOCIAL_ICON = icone
                link.SOCIAL_ORDER = ordem if ordem else 0
                link.SOCIAL_ACTIVE = ativo
                session_db.commit()

                return redirect(url_for('administrador.exibir_redes_sociais'))

    # Carregando formulário já preenchido com os dados atuais
    if social_id:
        with SessionFactory() as session_db:
            link_selecionado = session_db.query(SocialLink).filter(SocialLink.SOCIAL_ID == int(social_id)).first()
            if link_selecionado:
                formulario.plataforma.data = link_selecionado.SOCIAL_PLATFORM
                formulario.url.data = link_selecionado.SOCIAL_URL
                formulario.ordem.data = link_selecionado.SOCIAL_ORDER
                formulario.ativo.data = link_selecionado.SOCIAL_ACTIVE
                return render_template('editor/redes_sociais/atualizar_rede_social.html', formulario=formulario, link=link_selecionado)
            else:
                return redirect(url_for('administrador.exibir_redes_sociais'))
    else:
        return redirect(url_for('administrador.exibir_redes_sociais'))


# Excluir rede social
@administrador_bp.route('/excluir_rede_social', methods=['POST', 'GET'])
@adm_2af_required
def excluir_rede_social():
    # Recebendo ID do link a ser excluido
    social_id = request.args.get('social_id')

    if social_id:
        with SessionFactory() as session_db:
            link_selecionado = session_db.query(SocialLink).filter(SocialLink.SOCIAL_ID == int(social_id)).first()
            if link_selecionado:
                session_db.delete(link_selecionado)
                session_db.commit()
                return redirect(url_for('administrador.exibir_redes_sociais'))
            else:
                return redirect(url_for('administrador.exibir_redes_sociais'))

    else:
        return redirect(url_for('administrador.exibir_redes_sociais'))

# SETOR DE ORAÇÕES

# Exibir pedidos
@administrador_bp.route('/exibir_pedidos_oracao', methods=['GET'])
@adm_2af_required
def exibir_pedidos_oracao():
    # Definindo formulários dos pedidos
    formulario = PrayerManager_()
    
    
    with SessionFactory() as session_db:
        pedidos = session_db.query(PrayerRequest).all()

        return render_template('editor/prayer_request/main.html', pedidos=pedidos, formulario=formulario)


# Editando status do pedido
@administrador_bp.route('/editar_pedidos_oracao', methods=['POST', 'GET'])
@adm_2af_required
def editar_pedidos_oracao():
    # Definindo formulários dos pedidos
    formulario = PrayerManager_()
    # Pegando ID da oração
    pedido_id = request.args.get('pedido_id')
    # Recebendo formulário para atualização de status de oração.
    if formulario.validate_on_submit():
        if pedido_id:
            status = formulario.status.data
            with SessionFactory() as session_db:
                pedido = session_db.query(PrayerRequest).filter(PrayerRequest.PRAYER_ID == int(pedido_id)).first()
                pedido.PRAYER_STATUS = status
                session_db.commit()
                return redirect(url_for('administrador.exibir_pedidos_oracao'))
        else:
            return redirect(url_for('administrador.exibir_pedidos_oracao'))
    
    return redirect(url_for('administrador.exibir_pedidos_oracao'))

# Excluir oração
@administrador_bp.route('/excluir_pedido_oracao', methods=['POST', 'GET'])
@adm_2af_required
def excluir_rede_social():
    # Recebendo ID do link a ser excluido
    pedido_id = request.args.get('pedido_id')

    if pedido_id:
        with SessionFactory() as session_db:
            pedido_selecionado = session_db.query(PrayerRequest).filter(PrayerRequest.PRAYER_ID == int(pedido_id)).first()
            if pedido_selecionado:
                session_db.delete(pedido_selecionado)
                session_db.commit()
                return redirect(url_for('administrador.exibir_pedidos_oracao'))
            else:
                return redirect(url_for('administrador.exibir_pedidos_oracao'))

    else:
        return redirect(url_for('administrador.exibir_pedidos_oracao'))














