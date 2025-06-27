"""
API Blueprint for LanJanitor
"""
from flask import Blueprint, request, jsonify, make_response, session, current_app as app
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from common import (
    DB_PATH, PUBLIC_KEY_PATH, SERVERS_TABLE, login_required, dict_factory, runPlaybook, aptUpdate, get_cached_ping
)

api = Blueprint('api', __name__)

@api.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('SELECT password_hash FROM users WHERE username=?', (username,))
            row = c.fetchone()
            if row and check_password_hash(row[0], password):
                session['user'] = username
                return jsonify({'status': 'ok'}), 200
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as ex:
        return jsonify({'error': f'Login error: {ex}'}), 500

@api.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return make_response('ok', 200)

@api.route('/api/set_password', methods=['POST'])
@login_required
def set_password():
    try:
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        username = session.get('user')
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('SELECT password_hash FROM users WHERE username=?', (username,))
            row = c.fetchone()
            if not row or not check_password_hash(row[0], old_password):
                return jsonify({'error': 'Current password incorrect'}), 400
            c.execute('UPDATE users SET password_hash=? WHERE username=?', (generate_password_hash(new_password), username))
            conn.commit()
        return jsonify({'status': 'ok'}), 200
    except Exception as ex:
        return jsonify({'error': f'Password change error: {ex}'}), 500

@api.route("/api/key", methods=["GET"])
@login_required
def getkey():
    try:
        with open(PUBLIC_KEY_PATH, 'r') as file:
            data = file.read().replace('\n', '<br />')
    except Exception:
        data = "No key has been generated..."
    return data

@api.route("/api/updates", methods=["GET"])
@login_required
def aptUpgrade():
    try:
        output = runPlaybook('update_install.yml', request.args.get("ip"))
        app.logger.info(output.status)
        aptUpdate(request.args.get("ip"))
        return jsonify({'status': 'ok'}), 200
    except Exception as ex:
        return jsonify({'error': f'Update error: {ex}'}), 500

@api.route(f"/api/servers", methods=["GET", "POST", "DELETE"])
@login_required
def servers():
    try:
        if request.method == 'GET':
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = dict_factory
                c = conn.cursor()
                servers = c.execute(f"SELECT * FROM {SERVERS_TABLE}").fetchall()
                if not servers:
                    servers = []
                for server in servers:
                    server['ping_status'] = 'online' if get_cached_ping(server['server_ip']) else 'offline'
            return jsonify(servers)
        elif request.method == 'POST':
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                os_type = request.json.get('os_type', 'Ubuntu')
                c.execute(f"INSERT INTO {SERVERS_TABLE} (server_name,server_ip, server_updates, server_reboot, os_type) VALUES (?,?,?,?,?)", (request.json['name'], request.json['ip'], 0, 'false', os_type))
                server_id = c.lastrowid
                conn.commit()
            return jsonify({'status': 'ok', 'server_id': server_id})
        elif request.method == 'DELETE':
            delitem = request.args.get('id')
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute(f'DELETE FROM {SERVERS_TABLE} WHERE server_id = ?', (delitem,))
                conn.commit()
            return jsonify({'status': 'ok'})
    except Exception as ex:
        return jsonify({'error': f'Servers API error: {ex}'}), 500

@api.route("/api/reboot", methods=["POST"])
@login_required
def reboot_server():
    data = request.get_json()
    ip = data.get("ip")
    name = data.get("name")
    if not ip:
        return make_response("Missing IP", 400)
    output = runPlaybook('reboot_server.yml', ip)
    app.logger.info(f"Reboot triggered for {name} ({ip}): {output.status}")
    return make_response("ok", 200)

@api.route("/api/updates/all", methods=["POST"])
@login_required
def updates_all():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = dict_factory
            c = conn.cursor()
            servers = c.execute(f"SELECT server_ip, server_name FROM {SERVERS_TABLE}").fetchall()
        count = 0
        errors = []
        for server in servers:
            try:
                # Trigger update check (can be async in future)
                aptUpdate(server['server_ip'])
                count += 1
            except Exception as ex:
                errors.append(f"{server['server_name']} ({server['server_ip']}): {ex}")
        msg = f"Update check triggered on {count} server{'s' if count != 1 else ''}."
        if errors:
            msg += f" Errors: {'; '.join(errors)}"
        return jsonify({'status': 'ok', 'message': msg}), 200
    except Exception as ex:
        return jsonify({'status': 'error', 'message': f'Failed to check updates: {ex}'}), 500
