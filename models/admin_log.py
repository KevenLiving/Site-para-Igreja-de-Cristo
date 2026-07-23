from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum, JSON, func
from models.database import Base
import datetime


class AdminLog(Base):
    __tablename__ = 'tb_admin_logs'

    LOG_ID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)

    LOG_ADMIN_ID: Mapped[int] = mapped_column(ForeignKey('tb_admins.ADMIN_ID'), nullable=False)

    # Tipo de ação realizada pelo administrador
    LOG_ACTION: Mapped[str] = mapped_column(
        Enum('create', 'update', 'delete', 'login', 'logout', name='acao_log_enum'),
        nullable=False
    )

    LOG_TABLE_AFFECTED: Mapped[str] = mapped_column(String(100), nullable=False)
    LOG_RECORD_ID: Mapped[int] = mapped_column(Integer, nullable=True)

    # Permitem reconstruir alterações com precisão (auditoria)
    LOG_OLD_VALUES: Mapped[dict] = mapped_column(JSON, nullable=True)
    LOG_NEW_VALUES: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Informações de sessão para identificação de acessos
    LOG_IP_ADDRESS: Mapped[str] = mapped_column(String(45), nullable=True)  # suporta IPv4 e IPv6
    LOG_USER_AGENT: Mapped[str] = mapped_column(String(255), nullable=True)

    LOG_CREATED_AT: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    administrador = relationship('Administrador')

    @staticmethod
    def registrar(session, admin_id, acao, tabela, record_id=None, old_values=None, new_values=None, ip=None, user_agent=None):
        """
        Método utilitário para facilitar o registro de logs em qualquer parte do sistema.
        Exemplo de uso: AdminLog.registrar(session, admin_id=1, acao='update', tabela='tb_events', record_id=5, old_values={...}, new_values={...}, ip=request.remote_addr, user_agent=request.user_agent.string)
        """
        log = AdminLog(
            LOG_ADMIN_ID=admin_id,
            LOG_ACTION=acao,
            LOG_TABLE_AFFECTED=tabela,
            LOG_RECORD_ID=record_id,
            LOG_OLD_VALUES=old_values,
            LOG_NEW_VALUES=new_values,
            LOG_IP_ADDRESS=ip,
            LOG_USER_AGENT=user_agent
        )
        session.add(log)
        session.commit()
        return log