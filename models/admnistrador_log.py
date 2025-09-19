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

    
    def is_root(self):
        if self.ADMIN_ROLE == 'root':
            return True
        else:
            return False

    def is_active(self):
        return self.ADMIN_ACTIVE
    
    def get_id(self):
        return str(self.ADMIN_ID)
    
    @staticmethod
    def get_by_id(ADMIN_ID):
        session = SessionFactory()
        administrador = session.query(Administrador).filter(Administrador.ADMIN_ID == id).first()
        if administrador:
            return AdministradorLog(administrador.ADMIN_ID, administrador.ADMIN_NAME, administrador.ADMIN_EMAIL, administrador.ADMIN_ROLE, administrador.ADMIN_ACTIVE, administrador.ADMIN_CREATED_AT, administrador.ADMIN_UPDATED_AT)
        return None
    
    @staticmethod
    def get_by_email(ADMIN_EMAIL):
        session = SessionFactory()
        administrador = session.query(Administrador).filter(Administrador.ADMIN_EMAIL == ADMIN_EMAIL).first()
        if administrador:
            return AdministradorLog(administrador.ADMIN_ID, administrador.ADMIN_NAME, administrador.ADMIN_EMAIL, administrador.ADMIN_ROLE, administrador.ADMIN_ACTIVE, administrador.ADMIN_CREATED_AT, administrador.ADMIN_UPDATED_AT)
        return None