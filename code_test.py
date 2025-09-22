from models.database import SessionFactory
from models.administrador import Administrador

with SessionFactory() as session:
    adm = Administrador(ADMIN_NAME='Maria Fernanda', ADMIN_EMAIL='maria@gmail.com', ADMIN_ROLE='root', ADMIN_ACTIVE=True)
    adm.set_password('123')
    session.add(adm)
    session.commit()