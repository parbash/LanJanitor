"""
LanJanitor Decorators
--------------------
Reusable Flask decorators for authentication and session management.
"""
from flask import session, redirect
from functools import wraps


from flask import request, make_response

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            # If API endpoint, return 401 Unauthorized
            if request.path.startswith('/api/'):
                return make_response('Unauthorized', 401)
            # Otherwise, redirect to login page
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function
