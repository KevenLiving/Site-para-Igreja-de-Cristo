from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Boolean, DateTime, Date, Time, Text, func
from models.database import Base
import datetime


class Event(Base):
    __tablename__ = 'tb_events'

    EVENT_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    EVENT_TITLE: Mapped[str] = mapped_column(String(200), nullable=False)
    EVENT_DESCRIPTION: Mapped[str] = mapped_column(Text, nullable=True)
    EVENT_BANNER: Mapped[str] = mapped_column(String(255), nullable=True)
    EVENT_LOCATION: Mapped[str] = mapped_column(String(150), nullable=True)

    # Diferente da programação semanal, o evento possui data específica (não recorrente)
    EVENT_DATE: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    EVENT_TIME: Mapped[datetime.time] = mapped_column(Time, nullable=True)

    EVENT_REGISTRATION_REQUIRED: Mapped[bool] = mapped_column(Boolean, default=False)
    EVENT_FEATURED: Mapped[bool] = mapped_column(Boolean, default=False)
    EVENT_PUBLISHED: Mapped[bool] = mapped_column(Boolean, default=False)

    EVENT_ADMINISTRADOR_ID: Mapped[int] = mapped_column(ForeignKey('tb_admins.ADMIN_ID'), nullable=False)

    EVENT_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    EVENT_UPDATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    administrador = relationship('Administrador')

    def is_published(self):
        return self.EVENT_PUBLISHED

    def is_upcoming(self):
        # Verifica se o evento ainda vai acontecer
        return self.EVENT_DATE >= datetime.date.today()

    def requires_registration(self):
        return self.EVENT_REGISTRATION_REQUIRED