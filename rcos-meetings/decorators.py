from functools import wraps
from flask import g, redirect

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.is_user_admin:
            return redirect('/cas/login')
        return f(*args, **kwargs)
    return decorated_function