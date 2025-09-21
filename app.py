from flask import Flask
from models.database import init_db
# Flask Login 
from flask_login import LoginManager
from models.admnistrador_log import AdministradorLog
# Importando Bluenprints 
from controllers.auth_controller import auth_bp
from controllers.admin_controller import administrador_bp


app = Flask(__name__)
app.secret_key = 'Abracadabra' # Configurando a chave secreta

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
