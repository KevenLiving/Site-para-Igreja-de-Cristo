from flask import Blueprint, render_template, request, abort, redirect, url_for, flash
from models.database import SessionFactory
from models.department      import Department
from models.biblical_study  import BiblicalStudy
from models.video_message   import VideoMessage
from models.devotional      import Devotional
from models.weekly_schedule import WeeklySchedule
from models.event           import Event
from models.church_history  import ChurchHistory
from models.social_link     import SocialLink
from models.prayer_request  import PrayerRequest
import datetime
from flask import current_app
from flask_mail import Message
import bleach # Para limpar scripts maliciosos que podem ser enviados nos pedidos de oração


public_bp = Blueprint('public', __name__, url_prefix='/')


# Aqui eu carredo os dados que irão aparecer em todas as páginas html, mesmo sem ser chamados diretamente
@public_bp.context_processor
def dados_globais_do_site():
    with SessionFactory() as session:
        ministerios = session.query(Department).filter(Department.DEPARTMENT_ACTIVE == True).order_by(Department.DEPARTMENT_ORDER, Department.DEPARTMENT_NAME).all()
        redes_sociais_publicas = session.query(SocialLink).filter(SocialLink.SOCIAL_ACTIVE == True).order_by(SocialLink.SOCIAL_ORDER).all()

    return dict(ministerios=ministerios, redes_sociais_publicas=redes_sociais_publicas)


# Carregando os dados que serão usados na agenda semanal 
def _agrupar_agenda_semanal(itens):
    abreviacoes = {
        'Domingo': 'Dom',
        'Segunda-feira': 'Seg',
        'Terça-feira': 'Ter',
        'Quarta-feira': 'Qua',
        'Quinta-feira': 'Qui',
        'Sexta-feira': 'Sex',
        'Sábado': 'Sáb',
    }

    ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira',
                  'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    agrupado = {}

    for item in itens:
        chave = item.SCHEDULE_TITLE
        if chave not in agrupado:
            agrupado[chave] = {'titulo': chave, 'dias': {}}


        dia = item.SCHEDULE_DAY
        if dia not in agrupado[chave]['dias']:
            agrupado[chave]['dias'][dia] = []

        # Formata o horário no padrão que a comunidade lê melhor: 19h30 / 20h
        hora = item.SCHEDULE_TIME
        if hora.minute == 0:
            texto_hora = f'{hora.hour}h'
        else:
            texto_hora = f'{hora.hour}h{hora.minute:02d}'

        agrupado[chave]['dias'][dia].append(texto_hora)


    # Converto o dict interno de dias em uma lista ordenada segundo a semana
    resultado = []
    for bloco in agrupado.values():
        dias_ordenados = []
        for nome_dia in ordem_dias:
            if nome_dia in bloco['dias']:
                dias_ordenados.append({
                    'abreviacao': abreviacoes[nome_dia],
                    'horarios': bloco['dias'][nome_dia]
                })
        resultado.append({'titulo': bloco['titulo'], 'dias': dias_ordenados})


    return resultado


# Rota principal
@public_bp.route('/')
def index():
    hoje = datetime.date.today()

    with SessionFactory() as session:
    # Carregando dados da página principal
        agenda_bruta = session.query(WeeklySchedule).filter(WeeklySchedule.SCHEDULE_ACTIVE == True).all()
        agenda_home = _agrupar_agenda_semanal(agenda_bruta)
        devocional = session.query(Devotional).filter(Devotional.DEVOTIONAL_PUBLISHED == True, Devotional.DEVOTIONAL_WEEK_START <= hoje, Devotional.DEVOTIONAL_WEEK_END   >= hoje).order_by(Devotional.DEVOTIONAL_CREATED_AT.desc()).first()
        estudos_recentes = session.query(BiblicalStudy).filter(BiblicalStudy.STUDY_PUBLISHED == True).order_by(BiblicalStudy.STUDY_CREATED_AT.desc()).limit(6).all()
        videos_recentes = session.query(VideoMessage).filter(VideoMessage.VIDEO_PUBLISHED == True).order_by(VideoMessage.VIDEO_CREATED_AT.desc()).limit(4).all()
        eventos_proximos = session.query(Event).filter(Event.EVENT_PUBLISHED == True, Event.EVENT_DATE >= hoje).order_by(Event.EVENT_DATE.asc(), Event.EVENT_TIME.asc()).limit(3).all()
        

    return render_template(
        'public.html',
        hoje=hoje,
        agenda_home=agenda_home,
        devocional=devocional,
        estudos_recentes=estudos_recentes,
        videos_recentes=videos_recentes,
        eventos_proximos=eventos_proximos
    )


# Rota de sobre nós
@public_bp.route('/sobre')
def sobre():
    with SessionFactory() as session:
        historia = session.query(ChurchHistory).order_by(ChurchHistory.HISTORY_ORDER, ChurchHistory.HISTORY_YEAR_START).all()

    return render_template('public_sobre_nos.html', historia=historia)

# Todos os estudos
@public_bp.route('/estudos')
def estudos():
    with SessionFactory() as session:
        estudos = session.query(BiblicalStudy).filter(BiblicalStudy.STUDY_PUBLISHED == True).order_by(BiblicalStudy.STUDY_CREATED_AT.desc()).all()

    return render_template('public_pregacoes.html', estudos=estudos)


# Rota de exibir estudo invividual
@public_bp.route('/estudo/<int:estudo_id>')
def estudo(estudo_id):
    with SessionFactory() as session:

        estudo = session.query(BiblicalStudy).filter(BiblicalStudy.STUDY_ID == estudo_id, BiblicalStudy.STUDY_PUBLISHED == True).first()

        if not estudo:
            abort(404)

        # Aqui marca que o usuário vizualisou o estudo e foi contabilizado no banco de dados
        estudo.add_view()
        session.commit()

        # Três estudos relacionados: mesmo tema, exceto o atual
        estudos_relacionados = session.query(BiblicalStudy).filter(BiblicalStudy.STUDY_PUBLISHED == True, BiblicalStudy.STUDY_ID != estudo.STUDY_ID, BiblicalStudy.STUDY_THEME == estudo.STUDY_THEME).order_by(BiblicalStudy.STUDY_CREATED_AT.desc()).limit(3).all()

        # Se não houver 3 do mesmo tema, completa com os mais recentes
        if len(estudos_relacionados) < 3:
            faltando = 3 - len(estudos_relacionados)
            ids_ja_usados = [e.STUDY_ID for e in estudos_relacionados] + [estudo.STUDY_ID]
            complementos = session.query(BiblicalStudy).filter(BiblicalStudy.STUDY_PUBLISHED == True, BiblicalStudy.STUDY_ID.in_(ids_ja_usados)).order_by(BiblicalStudy.STUDY_CREATED_AT.desc()).limit(faltando).all()
            estudos_relacionados.extend(complementos)

    return render_template(
        'public_estudo.html',
        estudo=estudo,
        estudos_relacionados=estudos_relacionados
    )


# Rota de exibir os vídeos contidos no canal do youtube
@public_bp.route('/videos')
def videos():
    with SessionFactory() as session:
        videos = session.query(VideoMessage).filter(VideoMessage.VIDEO_PUBLISHED == True).order_by(VideoMessage.VIDEO_CREATED_AT.desc()).all()

    return render_template('public_videos.html', videos=videos)

# Quando o usuário clica em um vídeo, ao invés dele cair diretamente no youtube, ele vem para esta rota para que a visualização seja contabilizada
@public_bp.route('/video/<int:video_id>/ver')
def ver_video(video_id):
    with SessionFactory() as session:
        video = session.query(VideoMessage).filter(VideoMessage.VIDEO_ID == video_id, VideoMessage.VIDEO_PUBLISHED == True).first()

        if not video:
            abort(404)

        video.add_view()
        session.commit()

        return redirect(video.VIDEO_URL)

# Rota para exibir detalhadamento as informações de um evento
@public_bp.route('/evento/<int:evento_id>')
def evento(evento_id):
    hoje = datetime.date.today()

    with SessionFactory() as session:
        evento = session.query(Event).filter(Event.EVENT_ID == evento_id, Event.EVENT_PUBLISHED == True).first()

        if not evento:
            abort(404)

        # Outros eventos futuros para a seção "Continue explorando"
        outros_eventos = session.query(Event).filter(Event.EVENT_PUBLISHED == True, Event.EVENT_ID != evento.EVENT_ID, Event.EVENT_DATE >= hoje).order_by(Event.EVENT_DATE.asc()).limit(3).all()

    return render_template(
        'public_evento.html',
        evento=evento,
        outros_eventos=outros_eventos,
        hoje=hoje
    )

# Rota de agenda
@public_bp.route('/agenda')
def agenda():
    hoje = datetime.date.today()

    with SessionFactory() as session:

        agenda_semanal = session.query(WeeklySchedule).filter(WeeklySchedule.SCHEDULE_ACTIVE == True).order_by(WeeklySchedule.SCHEDULE_TIME).all()

        # Traz eventos a partir de hoje para frente; o JS filtra por mês
        eventos = session.query(Event).filter(Event.EVENT_PUBLISHED == True, Event.EVENT_DATE >= hoje).order_by(Event.EVENT_DATE.asc()).all()

    return render_template('public_agenda.html', agenda_semanal=agenda_semanal, eventos=eventos)


# Rota de exibição de ministério selecionado
@public_bp.route('/ministerio/<int:ministerio_id>')
def ministerio(ministerio_id):
    with SessionFactory() as session:

        ministerio = session.query(Department).filter(Department.DEPARTMENT_ID == ministerio_id, Department.DEPARTMENT_ACTIVE == True).first()

        if not ministerio:
            abort(404)

    return render_template('public_ministerios.html', ministerio=ministerio)


# Rota de exibir a parte de contatos
@public_bp.route('/contato')
def contato():
    return render_template('public_contatos.html')





# Aqui eu pre-selecionei as categorias que eu acho interessantes para serem disponibilizadas para o usuário
_CATEGORIAS_VALIDAS = {'saude', 'familia', 'trabalho', 'financeiro', 'espiritual', 'outro'}

# Rota de pedido de oração :)
@public_bp.route('/pedido_oracao', methods=['POST'])
def pedido_oracao():

    # Se cair aqui por GET, manda para a home
    if request.method != 'POST':
        return redirect(url_for('public.index'))

    # Pegando dados do formulário
    nome         = (request.form.get('nome') or '').strip()
    pedido_texto = (request.form.get('pedido') or '').strip()
    categoria    = (request.form.get('categoria') or 'outro').strip().lower()
    email        = (request.form.get('email') or '').strip()
    # Checkboxes chegam como '1' quando marcados (definido no template)
    anonimato    = request.form.get('anonimato') == '1'
    autorizacao  = request.form.get('autorizacao') == '1'

    # Limpando qualquer script malicioso do texto livre
    nome         = bleach.clean(nome, tags=[], strip=True)
    pedido_texto = bleach.clean(pedido_texto, tags=[], strip=True)

    # Validação mínima: o pedido em si é obrigatório
    if not pedido_texto:
        flash('Por favor, escreva seu pedido antes de enviar.', 'danger')
        return redirect(url_for('public.index') + '#form_oracao')

    # Categorias fora do enum caem em "outro"
    if categoria not in _CATEGORIAS_VALIDAS:
        categoria = 'outro'

    # Se o solicitante quer anonimato, apagamos qualquer identificação antes mesmo de tocar no banco
    if anonimato:
        nome = None
        email = None
        # Se pediu anonimato, ele automaticamente não autorizou contato
        autorizacao = False

    # Se não autorizou contato, e-mail não é gravado (mesmo que ele tenha digitado por engano)
    email_para_gravar = email if (autorizacao and email) else None

    # Salvando no banco
    with SessionFactory() as session_db:
        novo_pedido = PrayerRequest(
            PRAYER_NAME=(nome or None),
            PRAYER_REQUEST_TEXT=pedido_texto,
            PRAYER_CATEGORY=categoria,
            PRAYER_ANONYMOUS=anonimato,
            PRAYER_CONTACT_EMAIL=email_para_gravar
        )
        session_db.add(novo_pedido)
        session_db.commit()

    flash('Recebemos seu pedido. Nossa equipe pastoral vai orar por você.', 'success')
    return redirect(url_for('public.index'))

# Quando a pessoa lê o devocional, e quer deixar um pedido de oração, ela vai para um formulário exclusivo
@public_bp.route('/pedido-oracao', methods=['GET'])
def pagina_pedido_oracao():
    return render_template('public_pedido_oracao.html')


# Rota de exibição detalhada do devocional
@public_bp.route('/devocional/<int:devocional_id>')
def devocional(devocional_id):
    hoje = datetime.date.today()

    with SessionFactory() as session:
        devocional = session.query(Devotional).filter(Devotional.DEVOTIONAL_ID == devocional_id, Devotional.DEVOTIONAL_PUBLISHED == True).first()

        if not devocional:
            abort(404)

        # Devocional programado para o futuro fica oculto do público
        if devocional.DEVOTIONAL_WEEK_START > hoje:
            abort(404)

        # Aqui, contebilizamos que o devocional foi visualizado
        devocional.add_view()
        session.commit()

        # Devocionais anteriores para o "Continue lendo" (histórico). Ordeno pelos mais recentes que já começaram, excluindo o atual.
        devocionais_anteriores = session.query(Devotional)\
            .filter(Devotional.DEVOTIONAL_PUBLISHED == True, Devotional.DEVOTIONAL_ID != devocional.DEVOTIONAL_ID, Devotional.DEVOTIONAL_WEEK_START <= hoje).order_by(Devotional.DEVOTIONAL_WEEK_START.desc()).limit(3).all()

    return render_template('public_devocional.html', devocional=devocional, devocionais_anteriores=devocionais_anteriores, hoje=hoje)


# Rota para contactar com a igreja
EMAIL_INSTITUCIONAL = 'icjjucurutu@Ggmail.com'  # e-mail que recebe os contatos

@public_bp.route('/enviar_contato', methods=['POST'])
def enviar_contato():
    nome    = (request.form.get('name') or '').strip()
    email   = (request.form.get('email') or '').strip()
    assunto = (request.form.get('subject') or '').strip()
    mensagem = (request.form.get('message') or '').strip()

    nome     = bleach.clean(nome, tags=[], strip=True)
    assunto  = bleach.clean(assunto, tags=[], strip=True)
    mensagem = bleach.clean(mensagem, tags=[], strip=True)

    if not (nome and email and assunto and mensagem):
        flash('Preencha todos os campos antes de enviar.', 'danger')
        return redirect(url_for('public.contato') + '#contact')

    try:
        from app import mail 
        # Enviando a mensagem
        msg = Message(
            subject=f'[Contato do site] {assunto}',
            recipients=[EMAIL_INSTITUCIONAL],
            reply_to=email,
            body=(
                f'Nome: {nome}\n'
                f'E-mail: {email}\n'
                f'Assunto: {assunto}\n\n'
                f'Mensagem:\n{mensagem}'
            )
        )
        mail.send(msg)
        flash('Mensagem enviada! Retornaremos em breve.', 'success')

    except Exception as e:
        current_app.logger.error(f'Erro ao enviar contato: {e}')
        flash('Não foi possível enviar a mensagem. Tente novamente mais tarde.', 'danger')

    return redirect(url_for('public.contato') + '#contact')