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



app = Flask(__name__)
app.secret_key = 'Abracadabra' # Configurando a chave secreta

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
