from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, Enum, Text, func
from models.database import Base
import datetime


class PrayerRequest(Base):
    __tablename__ = 'tb_prayer_requests'

    PRAYER_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)

    # Nome opcional, já que o pedido pode ser anônimo
    PRAYER_NAME: Mapped[str] = mapped_column(String(150), nullable=True)
    PRAYER_REQUEST_TEXT: Mapped[str] = mapped_column(Text, nullable=False)

    PRAYER_CATEGORY: Mapped[str] = mapped_column(
        Enum('saude', 'familia', 'trabalho', 'financeiro', 'espiritual', 'outro', name='categoria_oracao_enum'),
        default='outro'
    )
    PRAYER_PRIORITY: Mapped[str] = mapped_column(
        Enum('normal', 'urgent', name='prioridade_oracao_enum'),
        default='normal'
    )
    PRAYER_STATUS: Mapped[str] = mapped_column(
        Enum('pendente', 'orando', 'respondida', name='status_oracao_enum'),
        default='pendente'
    )

    PRAYER_ANONYMOUS: Mapped[bool] = mapped_column(Boolean, default=False)

    # Contatos opcionais, usados apenas se o solicitante autorizar follow-up
    PRAYER_CONTACT_EMAIL: Mapped[str] = mapped_column(String(150), nullable=True)
    PRAYER_CONTACT_PHONE: Mapped[str] = mapped_column(String(30), nullable=True)

    PRAYER_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    PRAYER_UPDATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    def is_urgent(self):
        return self.PRAYER_PRIORITY == 'urgent'

    def is_anonymous(self):
        return self.PRAYER_ANONYMOUS

    def mark_as_praying(self):
        # Atualiza o status para indicar que o pedido está sendo orado
        self.PRAYER_STATUS = 'orando'

    def mark_as_answered(self):
        # Atualiza o status para indicar que a oração foi respondida
        self.PRAYER_STATUS = 'respondida'

    def get_display_name(self):
        # Respeita a privacidade do solicitante ao exibir o pedido
        if self.PRAYER_ANONYMOUS or not self.PRAYER_NAME:
            return 'Anônimo'
        return self.PRAYER_NAME