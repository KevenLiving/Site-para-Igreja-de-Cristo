from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, func
from models.database import Base
import datetime


class ChurchHistory(Base):
    __tablename__ = 'tb_church_history'

    HISTORY_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    HISTORY_TITLE: Mapped[str] = mapped_column(String(200), nullable=False)
    HISTORY_CONTENT: Mapped[str] = mapped_column(Text, nullable=False)
    HISTORY_IMAGE: Mapped[str] = mapped_column(String(255), nullable=True)

    # Contextualização temporal do período histórico
    HISTORY_YEAR_START: Mapped[int] = mapped_column(Integer, nullable=False)
    HISTORY_YEAR_END: Mapped[int] = mapped_column(Integer, nullable=True)

    # Ordem de exibição cronológica ou temática
    HISTORY_ORDER: Mapped[int] = mapped_column(Integer, default=0)

    HISTORY_ADMINISTRADOR_ID: Mapped[int] = mapped_column(ForeignKey('tb_admins.ADMIN_ID'), nullable=False)

    HISTORY_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    HISTORY_UPDATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    administrador = relationship('Administrador')

    def get_period(self):
        # Retorna o período formatado para exibição (ex: "1998 - 2005" ou "1998 - atual")
        if self.HISTORY_YEAR_END:
            return f'{self.HISTORY_YEAR_START} - {self.HISTORY_YEAR_END}'
        return f'{self.HISTORY_YEAR_START} - atual'