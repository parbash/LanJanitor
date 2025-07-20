
"""
LanJanitor Servers API
----------------------
Server CRUD, status, and reboot endpoints.
"""
from flask import Blueprint, request, jsonify, session, current_app as app
import sqlite3
from config import DB_PATH, SERVERS_TABLE
from utils.decorators import login_required
from utils.common import dict_factory, runPlaybook, get_cached_ping

servers_api = Blueprint('servers_api', __name__)

@servers_api.route("/api/servers", methods=["GET", "POST", "DELETE"])
@login_required
def servers():
    """
    GET /api/servers
    POST /api/servers {"name": str, "ip": str, "os_type": str}
    DELETE /api/servers?id=<id>
    Response: {"status": "ok", ...} or {"status": "error", "message": str}
    """
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
            app.logger.info("Server list retrieved.")
            return jsonify({'status': 'ok', 'servers': servers}), 200
        elif request.method == 'POST':
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                os_type = request.json.get('os_type', 'Ubuntu')
                name = request.json.get('name')
                ip = request.json.get('ip')
                if not name or not ip or not os_type:
                    app.logger.warning("Server add failed: missing required fields.")
                    return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
                if os_type not in ['Ubuntu', 'Windows', 'Other Linux']:
                    app.logger.warning(f"Server add failed: invalid OS type '{os_type}'.")
                    return jsonify({'status': 'error', 'message': 'Invalid OS type'}), 400
                import re
                ip_pattern = re.compile(r'^([0-9]{1,3}\.){3}[0-9]{1,3}$')
                if not ip_pattern.match(ip):
                    app.logger.warning(f"Server add failed: invalid IP address '{ip}'.")
                    return jsonify({'status': 'error', 'message': 'Invalid IP address format'}), 400
                c.execute(f"INSERT INTO {SERVERS_TABLE} (server_name,server_ip, server_updates, server_reboot, os_type) VALUES (?,?,?,?,?)", (name, ip, 0, 'false', os_type))
                server_id = c.lastrowid
                conn.commit()
            app.logger.info(f"Server '{name}' ({ip}, {os_type}) added with id {server_id}.")
            return jsonify({'status': 'ok', 'server_id': server_id}), 200
        elif request.method == 'DELETE':
            delitem = request.args.get('id')
            if not delitem:
                app.logger.warning("Server delete failed: missing server id.")
                return jsonify({'status': 'error', 'message': 'Missing server id'}), 400
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute(f'DELETE FROM {SERVERS_TABLE} WHERE server_id = ?', (delitem,))
                conn.commit()
            app.logger.info(f"Server with id {delitem} deleted.")
            return jsonify({'status': 'ok', 'message': 'Server deleted'}), 200
    except Exception as ex:
        app.logger.error(f"Servers API error: {ex}")
        return jsonify({'status': 'error', 'message': f'Servers API error: {ex}'}), 500

@servers_api.route("/api/reboot", methods=["POST"])
@login_required
def reboot_server():
    """
    POST /api/reboot
    Request: {"ip": str, "name": str}
    Response: {"status": "ok", "message": str} or {"status": "error", "message": str}
    """
    data = request.get_json()
    ip = data.get("ip")
    name = data.get("name")
    if not ip:
        app.logger.warning("Reboot failed: missing IP.")
        return jsonify({'status': 'error', 'message': 'Missing IP'}), 400
    import re
    ip_pattern = re.compile(r'^([0-9]{1,3}\.){3}[0-9]{1,3}$')
    if not ip_pattern.match(ip):
        app.logger.warning(f"Reboot failed: invalid IP address '{ip}'.")
        return jsonify({'status': 'error', 'message': 'Invalid IP address format'}), 400
    output = runPlaybook('lanjanitor.yml', ip, tags='reboot')
    app.logger.info(f"Reboot triggered for {name} ({ip}): {output.status}")
    return jsonify({'status': 'ok', 'message': 'Reboot triggered'}), 200
