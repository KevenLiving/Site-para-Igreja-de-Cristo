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
# Bibliotecas para limitar tentativas de login por IP
from security.extensions import limiter
# Bloquear ataques vindos de outros sites, especificamente contra CSRF
from flask_wtf import CSRFProtect
# A biblioteca flask-talisman é utilizada para implementar recursos web de segurança ao lhe dar com o servidor, 
# como conexões HTTPS obrigatórias, impedir injeções de arquivos maliciosos (impede que o navegador interprete aquele arquivo com base na sua tipificação(".txt, .js, .py, etc...")). 
# Impede também ataques de frame, e SOMENTE CARREGA RECURSOS DO PRÓPRIO DOMINIO.
from flask_talisman import Talisman

app = Flask(__name__)
app.secret_key = 'Abracadabra' # Configurando a chave secreta

# Para verificar se o sistema está em fase de desenvolvimento ou em produção
IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production' 


# Configurando a Talisman 
if IS_PRODUCTION:
    # De modo mais didático, é como uma a construção de uma casa. Quando ela está pronta, colocamos todos os métodos de segurança nela:
    # Grane, cerca elétrica, alarme... mas quando está em reforma ou em construção, deixamos ela "desprotegida" para facilitar a vida
    # dos trabalhadores. 
    # IS_PRODUCTION ativa a segurança máxima no sistema que está em funcionamento ativo. 
    Talisman(app, 
            force_https = True, # Obriga a usar método seguro para realizar requisições ao servidor
            strict_transport_security=True, # Mesmo que alguém tente usar outro método, ele é redirecionado para o protocolo HTTPS
            strict_transport_security_max_age=31536000,  # 1 ano de proteção contado em segundos
            strict_transport_security_include_subdomains=True, # Proteje subdominios além da rota principal 
            content_security_policy={ # Aqui define a regra de quais recursos podem ser carregados 
                'default-src': "'self'", # Somente aceita recursos do proprio servidor
                'script-src': "'self'",  # Só scripts internos, não aceita scripts soltos pela internet, evitando ataques XSS
                'style-src': "'self' 'unsafe-inline'", # Aceita CSS inline porque não oferece perigo
                'img-src': "'self' data:", # Aceita imagens próprias e em formato Base64(diretamente no html precisar carregá-las)
                'font-src': "'self'", # Fontes de letras somente vindas do meu servidor
                'connect-src': "'self'", # Controla de onde o site por abrir conexões dinâmicas (somente do proprio servidor). Isso permite controle sobre quem meu servidor está se relacionando. Posso liberar acesso a servidores externos específicos e de confiança.
                'object-src': "'none'", # Proibe plugins externos comuns que as individuos maliciosos utilizam para acessar o sistema.
                'base-uri': "'self'",  # Redirecionamentos apenas para o próprio servidor
                'frame-ancestors': "'none'" # Proibe que meu servidor seja carregado dentro de outro (inframes)
            },
            referrer_policy='strict-origin-when-cross-origin' # Controla o acesso de informações quando você navega por outros servidores evitando que eles acessem informações importantes. Pode mostrar o site que vc estava anteriormente, mas não mostra mais nada a respeito das rotas que vc acessou nele, qual usuário vc é, etc... ou seja, o servidor externo só tem acesso a: ele estava em "meusite.com" e não a: "meusite.com/user_id=1/pay_value=...."
            )

else:
    # CONFIGURAÇÃO PARA DESENVOLVIMENTO (flexível)
    Talisman(app,
        force_https=False,  # Não força HTTPS no localhost
        strict_transport_security=False,  # Desabilita o redirecionamento para HTTPS caso tente por outra via
        content_security_policy={
            'default-src': "'self'", # Continua aceitando recursos somente do proprio servidor
            'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",  # Permite scripts externos em inline(código js direto no html) e eval(), que transforma textos em códigos java script que auxilia na detecção de erros no sistema
            'style-src': "'self' 'unsafe-inline'", # Permenece igual ao de produção, permitindo css direto no html
            'img-src': "'self' data:", # Permanece igual, permitindo imagens carregadas, e também aquelas já processadas direto no html
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
    
    return response



# Configurando CSRF
crf = CSRFProtect(app)

# Isso faz com que o Flask-limiter funcione
# Ele é útil na segurança do sistema uma vez que limita o numero de requisições que um IP pode fazer
limiter.init_app(app)

# Configurando o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return AdministradorLog.get_by_id(user_id)

@app.route('/')
def main():
    return "Seu banco foi criado com sucesso!"

# Registradando Blueprints
app.register_blueprint(administrador_bp)
app.register_blueprint(auth_bp)

# Inicio do banco 
init_db()
