from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Boolean, Enum, DateTime, Date
from models.database import Base
from werkzeug.security import generate_password_hash, check_password_hash
import datetime


class Administrador(Base):
    __tablename__='tb_admins'

    ADMIN_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    ADMIN_NAME: Mapped[str] = mapped_column(String(100), nullable=False)
    ADMIN_EMAIL: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    ADMIN_PASSWORD: Mapped[str] = mapped_column(String(255), nullable=False)
    ADMIN_ROLE: Mapped[bool] = mapped_column(Enum('editor', 'root'), default=False)
    ADMIN_ACTIVE: Mapped[bool] = mapped_column(Boolean, default=False)
    ADMIN_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, nullable=False, autoincrement=True)
    ADMIN_UPDATED_AT: Mapped[datetime.date] = mapped_column(Date, nullable=True)

 
def set_password(self, password):
    # Deixando a senha codificada e para agregar da consolificação do requisito de segurança
    self.password_hash = generate_password_hash(password)

def check_password(self, password):
    # Para poder comparar com a senha inserida no momento do login 
    return check_password_hash(self.password_hash, password)
    
def is_active(self):
    # Modo de ativação
    return self.ADMIN_ACTIVE
    
def get_id(self):
    # Retornando o id
    return str(self.ADMIN_ID)