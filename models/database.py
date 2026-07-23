from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import DeclarativeBase
import os

secret_key = os.environ.get('chave_teste_base64').encode()

class Base(DeclarativeBase):
    pass

meubanco = 'sqlite:///church.db'


#Criando minha engine
myengine = create_engine(meubanco, echo=True)

#Criando minha session
SessionFactory = sessionmaker(bind=myengine)

def init_db():

    # Importações prévias
    from models.administrador import Administrador
    from models.admnistrador_log import AdministradorLog
    from models.biblical_study import BiblicalStudy
    from models.video_message import VideoMessage
    from models.devotional import Devotional
    from models.weekly_schedule import WeeklySchedule
    from models.event import Event
    from models.department import Department
    from models.prayer_request import PrayerRequest
    from models.church_history import ChurchHistory
    from models.social_link import SocialLink
    from models.admin_log import AdminLog

    # Criando o banco de dados 
    Base.metadata.create_all(myengine)

    # Verificando a existencia de um usuário root 
    with SessionFactory() as session:
        root = session.query(Administrador).filter_by(ADMIN_ROLE='root').first()
        if not root:
            # Importando a senha de usuário root
            secret_key = os.environ.get('senha_root')
            # Importando email root
            email = os.environ.get('email_root')

            # Verificando a existencia das variáveis
            if secret_key and email:
                # Criando objeto
                user_root = Administrador(ADMIN_NAME = 'root', ADMIN_EMAIL = email, ADMIN_ROLE = 'root', ADMIN_ACTIVE = True)
                user_root.set_password(secret_key)
                session.add(user_root)
                session.commit()
            else:
                print('❌ Falha nas variáveis de usuário root, verifique se elas foram declaradas ou crie o user manualmente')

        else:
            pass
    


    