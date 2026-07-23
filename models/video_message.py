from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, func
from models.database import Base
import datetime


class VideoMessage(Base):
    __tablename__ = 'tb_video_messages'

    VIDEO_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    VIDEO_TITLE: Mapped[str] = mapped_column(String(200), nullable=False)
    VIDEO_URL: Mapped[str] = mapped_column(String(255), nullable=False)
    VIDEO_THUMBNAIL: Mapped[str] = mapped_column(String(255), nullable=True)
    VIDEO_DURATION: Mapped[int] = mapped_column(Integer, nullable=True)  # duração em segundos
    VIDEO_PREACHER: Mapped[str] = mapped_column(String(150), nullable=True)
    VIDEO_CATEGORY: Mapped[str] = mapped_column(String(100), nullable=True)

    # Administrador que gerenciou o vídeo
    VIDEO_ADMINISTRADOR_ID: Mapped[int] = mapped_column(ForeignKey('tb_admins.ADMIN_ID'), nullable=False)

    VIDEO_FEATURED: Mapped[bool] = mapped_column(Boolean, default=False)
    VIDEO_PUBLISHED: Mapped[bool] = mapped_column(Boolean, default=False)
    VIDEO_VIEWS: Mapped[int] = mapped_column(Integer, default=0)

    VIDEO_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    VIDEO_UPDATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    administrador = relationship('Administrador')

    def is_published(self):
        return self.VIDEO_PUBLISHED

    def add_view(self):
        self.VIDEO_VIEWS += 1

    def get_duration_formatted(self):
        # Retorna a duração no formato mm:ss para exibição
        if self.VIDEO_DURATION is None:
            return '00:00'
        minutos, segundos = divmod(self.VIDEO_DURATION, 60)
        return f'{minutos:02d}:{segundos:02d}'