# Essa biblioteca é nativa do Python, e permite interagir com o sistema operacional. Você pode entrar, criar, editar ou remover pastas ou arquivos. Ela é uma biblioteca maravilhosa e 
# sem ela não teriamos acesso ao sistema operacional do nosso computador. 
import os
from flask import Flask
from models.database import init_db
# Flask Login 
from flask_login import LoginManager
from models.admnistrador_log import AdministradorLog
# Importando Bluenprints 
from controllers.auth_controller import auth_bp
from controllers.admin_controller import administrador_bp
from controllers.public_controler import public_bp
# Bibliotecas para limitar tentativas de login por IP
from security.extensions import limiter
# Bloquear ataques vindos de outros sites, especificamente contra CSRF
from flask_wtf import CSRFProtect
# A biblioteca flask-talisman é utilizada para implementar recursos web de segurança ao lhe dar com o servidor, 
# como conexões HTTPS obrigatórias, impedir injeções de arquivos maliciosos (impede que o navegador interprete aquele arquivo com base na sua tipificação(".txt, .js, .py, etc...")). 
# Impede também ataques de frame, e SOMENTE CARREGA RECURSOS DO PRÓPRIO DOMINIO.
from flask_talisman import Talisman
# Para usar no tempo de duração máximo de um cookie
from datetime import timedelta
# A biblioteca a seguir é nativa do python, usada para gerar valores aleatoriamente de forma segura e criptografada, previnida contra hackers. Pode gerar tokes, senhas, esolher opções aleatoriamente de uma lista, etc..
# Usarei ela para gerar uma chave secreta para o sistema 
import secrets
# Para importar as variáveis de ambiente
from dotenv import load_dotenv
# Biblioteca para enviar mensagens via Email
from flask_mail import Mail, Message


app = Flask(__name__)

# Para verificar se o sistema está em fase de desenvolvimento ou em produção
IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production' 

# Configurando pasta de uploads
app.config["UPLOADS_FOLDER"] = os.path.join("static", "uploads")

# Configurando o APP de modo mais seguro ao invés de só colocar uma senha

# Carregando as variáveis do ambiente
load_dotenv()

app.config.update(
        SECRET_KEY = os.environ.get('senha_do_app') or secrets.token_hex(64), # A senha da aplicação não fica exposta aqui, mas nas variáveis do sistema. Isso é uma forma extremamente mais segura de guardar a senha.
        SESSION_COOKIE_SECURE = IS_PRODUCTION, # Cookies somente serão usados em sessão https segura. Isso previne roubo de sessão em público. Se o sistema estiver em desenvolvimento, ele desliga, se estiver em produção, ele ativa
        SESSION_COOKIE_HTTPONLY = True, # Isso faz com que JavaScript malicioso não acesse o Cookie
        SESSION_COOKIE_SAMESITE = 'Strict', # O Cookie é somente para requesições feitas unicamente no mesmo site. Outros sites não tem acesso aos meus cookies, é unica e exclusivamente para o usuário usar somente naquele ambiente.
        PERMANENT_SESSION_LIFETIME = timedelta(minutes=30 if IS_PRODUCTION else 180), # Caso o hacker tente roubar seu cookie, e tentar invadir usando ele, o tempo máximo em que o cookie fica disponível é por uma hora, o que reduz a janela de ataques ao invés de deixar por tempo infinito.
        SESSION_COOKIE_NAME = 'secure_session' if IS_PRODUCTION else 'dev_secure', # Nome do cookie que o navegador irá utilizar
        SESSION_COOKIE_DOMAIN = None, # O cookie só vale para o site que está sendo utilizado. Não funciona em subdominios ou outros sites
        SESSION_REFRESH_EACH_REQUEST = True, # Isso aqui é genial: A sessão expira com 30 minutos como nos definimos, certo? E se o usuário ainda estiver usando? Acontece que sempre que o usuário entra em uma nova página, faz uma requisição, ou algo do tipo, ele automáticamente regenera o cronometro de 30 minutos. Ou seja: Se ele ficar parado e ausente por 30 minutos, a sessão fecha, evitando que ela fique exposta a ataques por muito tempo ou por tempo infinito. É semelhante a sessão que a página do IF tem, que tem que ficar renovando a todo momento.
        MAX_CONTENT_LENGTH= 16 * 1024 * 1024 # Limita o tamanho dos arquivos que o usuário pode mandar por sessão, evitando envio de arquivos enormes que sobrecarregue o site e quebre
    )
    


# Configurando a Talisman 
if IS_PRODUCTION:
    # De modo mais didático, é como uma a construção de uma casa. Quando ela está pronta, colocamos todos os métodos de segurança nela:
    # Grane, cerca elétrica, alarme... mas quando está em reforma ou em construção, deixamos ela "desprotegida" para facilitar a vida
    # dos trabalhadores. 
    # IS_PRODUCTION ativa a segurança máxima no sistema que está em funcionamento ativo. 
    Talisman(app, 
            force_https = False, # Obriga a usar método seguro para realizar requisições ao servidor
            strict_transport_security=True, # Mesmo que alguém tente usar outro método, ele é redirecionado para o protocolo HTTPS
            strict_transport_security_max_age=31536000,  # 1 ano de proteção contado em segundos
            strict_transport_security_include_subdomains=True, # Proteje subdominios além da rota principal 
            content_security_policy={ # Aqui define a regra de quais recursos podem ser carregados 
                'default-src': [ # Somente aceita recursos do proprio servidor ou do google
                    "'self'",
                    "https://www.google.com"
                    ], 
                'script-src': [ # Só scripts internos, não aceita scripts soltos pela internet, evitando ataques XSS, com excessão do editor de texto para estudos e pregações.
                    "'self'",
                    "https://cdn.jsdelivr.net"
                    ],  
                'style-src': [
                    "'self'",
                    "'unsafe-inline'",
                    "https://cdn.jsdelivr.net",
                    "https://fonts.googleapis.com"
                ],
                'img-src': [
                    "'self'",
                    "data:",
                    "https://i.ytimg.com",
                    "https://img.youtube.com"
                ],
                'font-src': [
                    "'self'",
                    "https://fonts.gstatic.com"
                ], # Fontes de letras somente vindas do meu servidor
                'connect-src': "'self'", # Controla de onde o site por abrir conexões dinâmicas (somente do proprio servidor). Isso permite controle sobre quem meu servidor está se relacionando. Posso liberar acesso a servidores externos específicos e de confiança.
                'object-src': "'none'", # Proibe plugins externos comuns que as individuos maliciosos utilizam para acessar o sistema.
                'base-uri': "'self'",  # Redirecionamentos apenas para o próprio servidor
                'frame-ancestors': "'none'" # Proibe que meu servidor seja carregado dentro de outro (inframes)
            },
            referrer_policy='strict-origin-when-cross-origin' # Controla o acesso de informações quando você navega por outros servidores evitando que eles acessem informações importantes. Pode mostrar o site que vc estava anteriormente, mas não mostra mais nada a respeito das rotas que vc acessou nele, qual usuário vc é, etc... ou seja, o servidor externo só tem acesso a: ele estava em "meusite.com" e não a: "meusite.com/user_id=1/pay_value=...."
            )

else:
    # CONFIGURAÇÃO PARA DESENVOLVIMENTO (flexível)
    Talisman(
            app,
            force_https=False,
            strict_transport_security=False,
            session_cookie_secure=False,
            content_security_policy={
                'default-src': [
                    "'self'",
                    "https://www.google.com"
                ],

                'script-src': [
                    "'self'",
                    "'unsafe-inline'",
                    "https://cdn.jsdelivr.net"
                ],

                'style-src': [
                    "'self'",
                    "'unsafe-inline'",
                    "https://cdn.jsdelivr.net",
                    "https://fonts.googleapis.com"
                ],

                'img-src': [
                    "'self'",
                    "data:",
                    "https://i.ytimg.com",
                    "https://img.youtube.com"
                ],

                'font-src': [
                    "'self'",
                    "https://fonts.gstatic.com"
                ]
            }
        )

@app.after_request
def after_request(response):
    """Headers de segurança aplicados em TODAS as rotas""" # São tipo placas de regras de segurança que o navagador idêntifica para poder gerenciar o acesso ao seu servidor
    response.headers['X-Content-Type-Options'] = 'nosniff' # O navegador não está nem ai para qualquer arquivo que venha de fora, nem advinha o tipo (.js, .py, .css, etc...)
    response.headers['X-Frame-Options'] = 'DENY' # Não pode colocar seu site dentro de outro (inframe)
    response.headers['X-XSS-Protection'] = '1; mode=block' # Bloqueia scripts maliciosos, sendo efetivo contra ataques XSS
    
    # Em produção, adicionar headers extras
    if IS_PRODUCTION:
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin' # Protege a privaciadade do usuario de sua página, não revelando a outros servidores de qual site ele veio
        # Remove headers que vazam informações
        response.headers.pop('Server', None) # Impede usuários maliciosos de saber detalhes acerca de meu servidor 

    # Evita cache do HTML e das imagens
    if (
        response.content_type.startswith('text/html')
        or response.content_type.startswith('image/')
    ):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    return response   
    



# Configurando CSRF
crf = CSRFProtect(app)

# Isso faz com que o Flask-limiter funcione
# Ele é útil na segurança do sistema uma vez que limita o numero de requisições que um IP pode fazer
limiter.init_app(app)

# Configurando o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Configurando email
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('Igreja de Cristo', os.environ.get('MAIL_USERNAME'))
mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return AdministradorLog.get_by_id(user_id)


# Registradando Blueprints
app.register_blueprint(administrador_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(public_bp)

# Inicio do banco 
init_db()
