from flask_login import UserMixin
from models.database import SessionFactory
from models.administrador import Administrador

class AdministradorLog(Administrador, UserMixin):
    def __init__(self, ADMIN_ID, ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_ROLE, ADMIN_ACTIVE, ADMIN_CREATED_AT, ADMIN_UPDATED_AT):
        self.ADMIN_ID = ADMIN_ID
        self.ADMIN_NAME = ADMIN_NAME
        self.ADMIN_EMAIL = ADMIN_EMAIL
        self.ADMIN_PASSWORD = ADMIN_PASSWORD
        self.ADMIN_ROLE = ADMIN_ROLE
        self.ADMIN_ACTIVE = ADMIN_ACTIVE
        self.ADMIN_CREATED_AT = ADMIN_CREATED_AT
        self.ADMIN_UPDATED_AT = ADMIN_UPDATED_AT

    
    def is_adm(self):
        return self.adm

    def is_active(self):
        return self.ativo
    
    def get_id(self):
        return str(self.id)
    
    @staticmethod
    def get_by_id(id):
        session = SessionFactory()
        secretario = session.query(Administrador).filter(Administrador.ADMIN_ID == id).first()
        if secretario:
            return AdministradorLog(secretario.id, secretario.username, secretario.password_hash, secretario.membro_id, secretario.ativo, secretario.adm)
        return None
    
    @staticmethod
    def get_by_username(username):
        session = SessionFactory()
        secretario = session.query(Administrador).filter(Administrador.ADMIN_NAME == username).first()
        if secretario:
            return AdministradorLog(secretario.id, secretario.username, secretario.password_hash, secretario.membro_id, secretario.ativo, secretario.adm)
        return None