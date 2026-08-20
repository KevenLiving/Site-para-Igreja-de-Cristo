# Isso servira para identificarmos e podermos utilizar o nosso querido novo decorador 
from functools import wraps
from flask_login import current_user
from flask import redirect, url_for, session, flash

def login_already_required(f):
    # Somente usuário deslogado ou que passou pela etapa um de autenticação pode acessar a rota de login diretamente. Quem estiver logado, tem que acessar pela rota de acesso disposta na própria página para deslogar.
    @wraps(f)
    def decorate_function(*args, **kwargs):
        # Se o usuário está logado
        if current_user.is_authenticated:
            # Verifica se já passou pela autenticação de 2 fatores (etapa completa)
            if session.get('admin_2af_verifield', False):
                # Se já completou as duas etapas, NÃO pode acessar login
                flash('Você já está completamente logado no sistema.', 'info')
                return redirect(url_for('administrador.index'))
            # Se NÃO passou pelo 2FA (só passou pela 1ª etapa), PERMITE acesso ao login
            # Ele pode voltar para a página de login se quiser
        
        # Permite acesso à rota (para não logados ou só com 1ª etapa)
        return f(*args, **kwargs)
    
    return decorate_function