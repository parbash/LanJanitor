"""
LanJanitor Decorators
--------------------
Reusable Flask decorators for authentication and session management.
"""
from flask import session, redirect
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function
