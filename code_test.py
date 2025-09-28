from models.database import SessionFactory
from models.administrador import Administrador
# Bibliotecas para realizar autenticação 2F
import pyotp
import qrcode
import time
import os
from dotenv import load_dotenv

# Cadastramento de usuário novo
"""
with SessionFactory() as session:
    adm = Administrador(ADMIN_NAME='Maria Fernanda', ADMIN_EMAIL='keven@gmail.com', ADMIN_ROLE='root', ADMIN_ACTIVE=True)
    adm.set_password('Tg7!kR@9wZ')
    session.add(adm)
    session.commit()
"""
# Carregando as variáveis do ambiente
load_dotenv()

# Definindo chave secreta para demonstração - Não é recomendado dessa forma

# Aqui ele faz uma chave aleatória para você. Você tem que ter ela para descobrir quais códigos estão sendo gerados de acordo com o tempo
# Ou seja, deve ser extremamente protegida, e escolha uma chave complexa e difícil de ser achada
key = os.environ.get('secure_AF2')

# Gerando QRCODE
"""
uri = pyotp.totp.TOTP(key).provisioning_uri(name="desenvolvimento", issuer_name='Keven')

qrcode.make(uri).save("secure_QRCODE.png")
"""

"""
# Sistema OTP baseado em? TEMPOOO
time_otp = pyotp.TOTP(key)

# Mostrando a chave
print(time_otp.now())
"""