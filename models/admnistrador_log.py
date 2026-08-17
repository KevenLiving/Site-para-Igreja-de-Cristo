from flask_login import UserMixin
from models.database import SessionFactory
from models.administrador import Administrador
import pyotp
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Carregando as variáveis do ambiente
load_dotenv()

class AdministradorLog(Administrador, UserMixin):
    def __init__(self, ADMIN_ID, ADMIN_NAME, ADMIN_EMAIL, ADMIN_ROLE, ADMIN_ACTIVE, ADMIN_CREATED_AT, ADMIN_UPDATED_AT, ADMIN_TWO_FACTOR_FIRST, ADMIN_CODE):
        self.ADMIN_ID = ADMIN_ID
        self.ADMIN_NAME = ADMIN_NAME
        self.ADMIN_EMAIL = ADMIN_EMAIL
        self.ADMIN_ROLE = ADMIN_ROLE
        self.ADMIN_ACTIVE = ADMIN_ACTIVE
        self.ADMIN_CREATED_AT = ADMIN_CREATED_AT
        self.ADMIN_UPDATED_AT = ADMIN_UPDATED_AT
        self.ADMIN_TWO_FACTOR_FIRST = ADMIN_TWO_FACTOR_FIRST
        self.ADMIN_CODE = ADMIN_CODE

    
    def is_root(self):
        if self.ADMIN_ROLE == 'root':
            return True
        else:
            return False

    def is_active(self):
        return self.ADMIN_ACTIVE
    
    def create_code(self):
        # Essa função cria um código de autenticação que será usado com a finalidade de gerar o QR-CODE 
        if not self.ADMIN_TWO_FACTOR_FIRST:
            # Gerando uma senha aleatória no formato base32
            chave_secreta = pyotp.random_base32()
            # Carregando a senha do sistema
            chave_do_sistema = os.environ.get('chave_teste_base64')
            # Criando um objeto para poder criptografar
            object_cript = Fernet(chave_do_sistema.encode())
            # Criptografando a senha
            chave_secreta_criptografada = object_cript.encrypt(chave_secreta.encode())
            # Salvando a senha gerada no banco
            self.ADMIN_CODE = chave_secreta_criptografada.decode()

            return True
        else:
            return False
    
    def get_id(self):
        return str(self.ADMIN_ID)
    
    # Essa função será muito importante uma vez que ela vai identificar se o usuário é a primeira pela autentificação de duas etapas 
    # Se for, aparecerá instruções para baixar o aplicativo do Google Authentication, na Play Store, e um QR code será gerado para ele ter
    # acesso ao código de autentificação. Caso ele já tenha passado por essa etapa, ele vai direto para a página inserir código.
    def is_two_factor_first(self):
        return self.ADMIN_TWO_FACTOR_FIRST
    
    @staticmethod
    def get_by_id(ADMIN_ID):
        session = SessionFactory()
        administrador = session.query(Administrador).filter(Administrador.ADMIN_ID == ADMIN_ID).first()
        session.close()
        if administrador:
            return AdministradorLog(administrador.ADMIN_ID, administrador.ADMIN_NAME, administrador.ADMIN_EMAIL, administrador.ADMIN_ROLE, administrador.ADMIN_ACTIVE, administrador.ADMIN_CREATED_AT, administrador.ADMIN_UPDATED_AT, administrador.ADMIN_TWO_FACTOR_FIRST, administrador.ADMIN_CODE)
        return None
    
    @staticmethod
    def get_by_email(ADMIN_EMAIL):
        session = SessionFactory()
        administrador = session.query(Administrador).filter(Administrador.ADMIN_EMAIL == ADMIN_EMAIL).first()
        session.close()
        if administrador:
            return AdministradorLog(administrador.ADMIN_ID, administrador.ADMIN_NAME, administrador.ADMIN_EMAIL, administrador.ADMIN_ROLE, administrador.ADMIN_ACTIVE, administrador.ADMIN_CREATED_AT, administrador.ADMIN_UPDATED_AT, administrador.ADMIN_TWO_FACTOR_FIRST, administrador.ADMIN_CODE)
        return None