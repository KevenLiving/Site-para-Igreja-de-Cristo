from flask import Flask
from models.database import init_db

app = Flask(__name__)

@app.route('/')
def main():
    return "Seu banco foi criado com sucesso!"

# Inicio do banco 
init_db()
