from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Boolean, DateTime, Time, Enum, Text, func
from models.database import Base
import datetime


class WeeklySchedule(Base):
    __tablename__ = 'tb_weekly_schedule'

    SCHEDULE_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    SCHEDULE_TITLE: Mapped[str] = mapped_column(String(150), nullable=False)

    # Dia da semana em português, para facilitar a organização culturalmente adaptada
    SCHEDULE_DAY: Mapped[str] = mapped_column(
        Enum(
            'Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira',
            'Quinta-feira', 'Sexta-feira', 'Sábado',
            name='dia_semana_enum'
        ),
        nullable=False
    )

    SCHEDULE_TIME: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    SCHEDULE_LOCATION: Mapped[str] = mapped_column(String(150), nullable=True)
    SCHEDULE_DESCRIPTION: Mapped[str] = mapped_column(Text, nullable=True)

    SCHEDULE_ACTIVE: Mapped[bool] = mapped_column(Boolean, default=True)

    SCHEDULE_ADMINISTRADOR_ID: Mapped[int] = mapped_column(ForeignKey('tb_admins.ADMIN_ID'), nullable=False)

    SCHEDULE_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    SCHEDULE_UPDATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    administrador = relationship('Administrador')

    def is_active(self):
        return self.SCHEDULE_ACTIVE

    def deactivate(self):
        # Desativa o evento recorrente sem excluí-lo do sistema
        self.SCHEDULE_ACTIVE = False

    def activate(self):
        self.SCHEDULE_ACTIVE = True