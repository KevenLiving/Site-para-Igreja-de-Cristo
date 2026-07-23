from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, DateTime, func
from models.database import Base
import datetime


class SocialLink(Base):
    __tablename__ = 'tb_social_links'

    SOCIAL_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    SOCIAL_PLATFORM: Mapped[str] = mapped_column(String(50), nullable=False)  # ex: Instagram, YouTube, WhatsApp
    SOCIAL_URL: Mapped[str] = mapped_column(String(255), nullable=False)
    SOCIAL_ICON: Mapped[str] = mapped_column(String(150), nullable=True)  # nome/classe do ícone (ex: bi-instagram)

    # Ordem de exibição dos ícones nas interfaces
    SOCIAL_ORDER: Mapped[int] = mapped_column(Integer, default=0)
    SOCIAL_ACTIVE: Mapped[bool] = mapped_column(Boolean, default=True)

    SOCIAL_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    SOCIAL_UPDATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    def is_active(self):
        return self.SOCIAL_ACTIVE