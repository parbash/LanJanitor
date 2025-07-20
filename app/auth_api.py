from flask import Blueprint, request, jsonify, session, current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from common import DB_PATH, PUBLIC_KEY_PATH, login_required

auth_api = Blueprint('auth_api', __name__)

@auth_api.route('/api/login', methods=['POST'])
def login():
    """
    POST /api/login
    Request: {"username": str, "password": str}
    Response: {"status": "ok"} or {"status": "error", "message": str}
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            app.logger.warning("Login failed: missing username or password")
            return jsonify({'status': 'error', 'message': 'Missing username or password'}), 400
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('SELECT password_hash FROM users WHERE username=?', (username,))
            row = c.fetchone()
            if row and check_password_hash(row[0], password):
                app.logger.info(f"User '{username}' logged in successfully.")
                session['user'] = username
                return jsonify({'status': 'ok'}), 200
        app.logger.warning(f"Login failed for user '{username}': invalid credentials.")
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    except Exception as ex:
        app.logger.error(f"Login error for user '{username if 'username' in locals() else ''}': {ex}")
        return jsonify({'status': 'error', 'message': f'Login error: {ex}'}), 500

@auth_api.route('/api/logout', methods=['POST'])
def logout():
    """
    POST /api/logout
    Request: None
    Response: {"status": "ok", "message": "Logged out"}
    """
    session.pop('user', None)
    app.logger.info("User logged out.")
    return jsonify({'status': 'ok', 'message': 'Logged out'}), 200

@auth_api.route('/api/set_password', methods=['POST'])
@login_required
def set_password():
    """
    POST /api/set_password
    Request: {"old_password": str, "new_password": str}
    Response: {"status": "ok", "message": str} or {"status": "error", "message": str}
    """
    try:
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        if not old_password or not new_password:
            app.logger.warning("Password change failed: missing old or new password.")
            return jsonify({'status': 'error', 'message': 'Missing old or new password'}), 400
        username = session.get('user')
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('SELECT password_hash FROM users WHERE username=?', (username,))
            row = c.fetchone()
            if not row or not check_password_hash(row[0], old_password):
                app.logger.warning(f"Password change failed for user '{username}': incorrect current password.")
                return jsonify({'status': 'error', 'message': 'Current password incorrect'}), 400
            c.execute('UPDATE users SET password_hash=? WHERE username=?', (generate_password_hash(new_password), username))
            conn.commit()
        app.logger.info(f"Password changed for user '{username}'.")
        return jsonify({'status': 'ok', 'message': 'Password changed successfully'}), 200
    except Exception as ex:
        app.logger.error(f"Password change error for user '{username if 'username' in locals() else ''}': {ex}")
        return jsonify({'status': 'error', 'message': f'Password change error: {ex}'}), 500

@auth_api.route("/api/key", methods=["GET"])
@login_required
def getkey():
    """
    GET /api/key
    Request: None
    Response: {"status": "ok", "key": str} or {"status": "error", "message": str}
    """
    try:
        with open(PUBLIC_KEY_PATH, 'r') as file:
            data = file.read().replace('\n', '<br />')
        app.logger.info("Public key retrieved.")
        return jsonify({'status': 'ok', 'key': data}), 200
    except Exception:
        app.logger.warning("Public key retrieval failed: No key generated.")
        return jsonify({'status': 'error', 'message': 'No key has been generated...'}), 404
