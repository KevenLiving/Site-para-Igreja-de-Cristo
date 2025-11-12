# Isso servira para identificarmos e podermos utilizar o nosso querido novo decorador de identificador de root
from functools import wraps
from flask_login import current_user
from flask import redirect, url_for, session

def root_permission(f):

    @wraps(f)

    def decorate_function(*args, **kwargs):

        # Verificando se o admnistrador é usuário root
        if not current_user.ADMIN_ROLE == "root":
            return redirect(url_for('administrador.index'))
        
        return f(*args, **kwargs)
    
    return decorate_function