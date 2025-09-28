# Isso servira para identificarmos e podermos utilizar o nosso querido novo decorador 
from functools import wraps
from flask_login import current_user
from flask import redirect, url_for, session

def adm_2af_required(f):

    @wraps(f)

    def decorate_function(*args, **kwargs):

        # Verificando se o admnistrador está logado
        if not current_user.is_authenticated:
            return redirect(url_for('auth.logar_no_sistema'))
        
        # Verificando se o admnistrador passou pela autenticação de dois fatores
        if not session.get('admin_2af_verifield', True): 
            return redirect(url_for('auth.two_factor_authentication'))
        

        return f(*args, **kwargs)
    
    return decorate_function
