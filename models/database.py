from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import DeclarativeBase



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
    


    Base.metadata.create_all(myengine)