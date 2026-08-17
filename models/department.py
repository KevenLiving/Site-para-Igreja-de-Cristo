from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Text, func
from models.database import Base
import datetime


class Department(Base):
    __tablename__ = 'tb_departments'

    DEPARTMENT_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    DEPARTMENT_NAME: Mapped[str] = mapped_column(String(150), nullable=False)
    DEPARTMENT_DESCRIPTION: Mapped[str] = mapped_column(Text, nullable=True)

    DEPARTMENT_LEADER_NAME: Mapped[str] = mapped_column(String(150), nullable=True)
    DEPARTMENT_LEADER_PHOTO: Mapped[str] = mapped_column(String(255), nullable=True)
    DEPARTMENT_LEADER_BIO: Mapped[str] = mapped_column(Text, nullable=True)

    DEPARTMENT_CONTACT_EMAIL: Mapped[str] = mapped_column(String(150), nullable=True)
    DEPARTMENT_CONTACT_PHONE: Mapped[str] = mapped_column(String(30), nullable=True)

    # Ordem personalizada de exibição dos departamentos
    DEPARTMENT_ORDER: Mapped[int] = mapped_column(Integer, default=0)
    DEPARTMENT_ACTIVE: Mapped[bool] = mapped_column(Boolean, default=True)

    DEPARTMENT_ADMINISTRADOR_ID: Mapped[int] = mapped_column(ForeignKey('tb_admins.ADMIN_ID'), nullable=False)

    DEPARTMENT_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    DEPARTMENT_UPDATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    administrador = relationship('Administrador')

    def is_active(self):
        return self.DEPARTMENT_ACTIVE

    def deactivate(self):
        # Desativa temporariamente um departamento inoperante
        self.DEPARTMENT_ACTIVE = False

    def activate(self):
        self.DEPARTMENT_ACTIVE = True