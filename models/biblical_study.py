from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Text, func
from models.database import Base
import datetime


class BiblicalStudy(Base):
    __tablename__ = 'tb_biblical_studies'

    STUDY_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    STUDY_TITLE: Mapped[str] = mapped_column(String(200), nullable=False)
    STUDY_CONTENT: Mapped[str] = mapped_column(Text, nullable=False)
    STUDY_BIBLICAL_REFERENCE: Mapped[str] = mapped_column(String(150), nullable=True)
    STUDY_THEME: Mapped[str] = mapped_column(String(100), nullable=True)
    STUDY_BANNER: Mapped[str] = mapped_column(String(100), nullable=True)

    # Administrador responsável pela criação/edição do estudo (rastreabilidade)
    STUDY_ADMINISTRADOR_ID: Mapped[int] = mapped_column(ForeignKey('tb_admins.ADMIN_ID'), nullable=False)

    STUDY_FEATURED: Mapped[bool] = mapped_column(Boolean, default=False)
    STUDY_PUBLISHED: Mapped[bool] = mapped_column(Boolean, default=False)
    STUDY_VIEWS: Mapped[int] = mapped_column(Integer, default=0)

    STUDY_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now, nullable=False)
    STUDY_UPDATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # Relacionamento com o administrador que criou/editou o estudo
    administrador = relationship('Administrador')

    def is_published(self):
        # Facilita a checagem de visibilidade do estudo
        return self.STUDY_PUBLISHED

    def add_view(self):
        # Incrementa o contador de visualizações
        self.STUDY_VIEWS += 1

    def toggle_featured(self):
        # Alterna o destaque do estudo na plataforma
        self.STUDY_FEATURED = not self.STUDY_FEATURED