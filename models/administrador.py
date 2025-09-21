from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Boolean, Enum, DateTime, Date, func
from models.database import Base, SessionFactory
from werkzeug.security import generate_password_hash, check_password_hash
import datetime


class Administrador(Base):
    __tablename__='tb_admins'

    ADMIN_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    ADMIN_NAME: Mapped[str] = mapped_column(String(100), nullable=False)
    ADMIN_EMAIL: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    ADMIN_PASSWORD: Mapped[str] = mapped_column(String(255), nullable=False)
    ADMIN_ROLE: Mapped[str] = mapped_column(Enum('editor', 'root'), default='editor')
    ADMIN_ACTIVE: Mapped[bool] = mapped_column(Boolean, default=True)
    ADMIN_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    ADMIN_UPDATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

 
    def set_password(self, password):
        # Deixando a senha codificada e para agregar da consolificação do requisito de segurança.
        # Aqui eu fortaleci a senha com método scrypt e salt_length 64. Isso deixa a senha extremamente forte contra ataques de força bruta.
        self.ADMIN_PASSWORD = generate_password_hash(password, method='scrypt', salt_length=64)

    def check_password(self,email, password):
        # Para poder comparar com a senha inserida no momento do login
        with SessionFactory() as session:
            admin = session.query(Administrador).filter(Administrador.ADMIN_EMAIL == email).first()
            if not admin:
                return False
        return check_password_hash(admin.ADMIN_PASSWORD, password)

    def is_active(self):
        # Para quando eu precisar verrificar se aquele administrador está ativo ou não
        return self.ADMIN_ACTIVE
    
    def actvate(self):
        # Para facilitar a ativação do administrador
        self.ADMIN_ACTIVE = True
        
    def deactivate(self):
        # Para facilitar a desativação do administrador
        self.ADMIN_ACTIVE = False
    
    def is_root(self):
        # Para quando eu precisar verrificar se aquele administrador é root ou não. Isso ajuda na hora de liberar ou não o acesso a certas funcionalidades.
        if self.ADMIN_ROLE == 'root':
            return True
        else:
            return False
        
    def get_id(self):
        # Retornando o id
        return str(self.ADMIN_ID)