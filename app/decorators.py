from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('Доступ запрещен. Требуются права администратора.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def operator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not (current_user.is_admin() or current_user.is_operator()):
            flash('Доступ запрещен. Требуются права оператора.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function 