from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Date, Text, func
from models.database import Base
import datetime


class Devotional(Base):
    __tablename__ = 'tb_devotionals'

    DEVOTIONAL_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    DEVOTIONAL_TITLE: Mapped[str] = mapped_column(String(200), nullable=False)
    DEVOTIONAL_CONTENT: Mapped[str] = mapped_column(Text, nullable=False)
    DEVOTIONAL_BIBLICAL_VERSE: Mapped[str] = mapped_column(String(150), nullable=True)
    DEVOTIONAL_BANNER: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Período de vigência do devocional (diário ou semanal)
    DEVOTIONAL_WEEK_START: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    DEVOTIONAL_WEEK_END: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    DEVOTIONAL_ADMINISTRADOR_ID: Mapped[int] = mapped_column(ForeignKey('tb_admins.ADMIN_ID'), nullable=False)

    DEVOTIONAL_PUBLISHED: Mapped[bool] = mapped_column(Boolean, default=False)
    DEVOTIONAL_VIEWS: Mapped[int] = mapped_column(Integer, default=0)

    DEVOTIONAL_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    DEVOTIONAL_UPDATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    administrador = relationship('Administrador')

    def is_published(self):
        return self.DEVOTIONAL_PUBLISHED

    def add_view(self):
        self.DEVOTIONAL_VIEWS += 1

    @property
    def is_future(self):
        """Retorna True se o devocional ainda não começou."""
        hoje = datetime.date.today()
        return hoje < self.DEVOTIONAL_WEEK_START

    @property
    def is_running(self):
        """Retorna True se o devocional está sendo exibido."""
        hoje = datetime.date.today()
        return self.DEVOTIONAL_WEEK_START <= hoje <= self.DEVOTIONAL_WEEK_END

    @property
    def is_finished(self):
        """Retorna True se o período do devocional terminou."""
        hoje = datetime.date.today()
        return hoje > self.DEVOTIONAL_WEEK_END

    @property
    def can_be_displayed(self):
        """Retorna True se o devocional deve aparecer no site."""
        return self.DEVOTIONAL_PUBLISHED and self.is_running
    
    def can_update_period(self, new_start: datetime.date, new_end: datetime.date):
        """
        Verifica se o período pode ser alterado.

        Retorna:
            (True, None) -> permitido
            (False, "mensagem") -> não permitido
        """

        hoje = datetime.date.today()

        # Datas invertidas
        if new_end < new_start:
            return False, "A data final não pode ser anterior à inicial."

        # Nunca permitir início antes de hoje
        if new_start < hoje:
            return False, "A data inicial não pode ser anterior à data atual."

        # Se ainda não começou, pode alterar livremente
        if self.is_future:
            return True, None

        # Se está em exibição
        if self.is_running:

            # Não permitir voltar a data inicial
            if new_start < hoje:
                return False, "A data inicial não pode ser anterior a hoje."

            # Não permitir diminuir o período
            if new_end < self.DEVOTIONAL_WEEK_END:
                return False, "A data final só pode ser ampliada."

            return True, None

        # Se terminou
        if self.is_finished:

            if new_start < hoje:
                return False, "Informe um novo período futuro."

            return True, None

        return True, None