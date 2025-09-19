from database import SessionFactory
from administrador import Administrador

with SessionFactory() as session:
    adm = Administrador(ADMIN_NAME='José', ADMIN_EMAIL='jose@jose', ADMIN_ROLE='editor', ADMIN_ACTIVE=True)
    adm.set_password('123')
    session.add(adm)
    session.commit()

