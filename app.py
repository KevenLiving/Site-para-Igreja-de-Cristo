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

# Para verificar se o sistema está ativo ou em produção
IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production' 


# Configurando a Talisman de maneira condicional ao ambiente de produção. Caso contrário, ele bloqueia o prosseguimento do trabalho em localhost

if IS_PRODUCTION:
    Talisman(app, 
            force_https = True,
            strict_transport_security=True:, # Genialmente, força ps navegadores a usar HTTPS, mesmo que um usuário qualquer tente acessar usando HTTP
            strict_transport_security_max_age=31536000,  # 1 ano de proteção contado em segundos
            strict_transport_security_include_subdomains=True,
            content_security_policy={
                'default-src': "'self'",
                'script-src': "'self'",  # Sem unsafe-inline em produção
                'style-src': "'self' 'unsafe-inline'",
                'img-src': "'self' data:",
                'font-src': "'self'",
                'connect-src': "'self'",
                'object-src': "'none'",
                'base-uri': "'self'",
                'frame-ancestors': "'none'"
            },
            referrer_policy='strict-origin-when-cross-origin'
            )

else:
    # CONFIGURAÇÃO PARA DESENVOLVIMENTO (flexível)
    Talisman(app,
        force_https=False,  # Não força HTTPS no localhost
        strict_transport_security=False,  # Desabilita HSTS no desenvolvimento
        content_security_policy={
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",  # Mais permissivo para dev
            'style-src': "'self' 'unsafe-inline'",
            'img-src': "'self' data:",
        }
    )

@app.after_request
def after_request(response):
    """Headers de segurança aplicados em TODAS as rotas"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Em produção, adicionar headers extras
    if IS_PRODUCTION:
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Remove headers que vazam informações
        response.headers.pop('Server', None)
    
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
