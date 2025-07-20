from flask import Blueprint, request, jsonify, current_app as app
import sqlite3
from common import DB_PATH, SERVERS_TABLE, login_required, dict_factory, runPlaybook, aptUpdate

updates_api = Blueprint('updates_api', __name__)

@updates_api.route("/api/updates", methods=["GET"])
@login_required
def aptUpgrade():
    """
    GET /api/updates?ip=<ip>
    Request: None
    Response: {"status": "ok", "message": str} or {"status": "error", "message": str}
    """
    try:
        output = runPlaybook('lanjanitor.yml', request.args.get("ip"), tags='update_install')
        app.logger.info(output.status)
        aptUpdate(request.args.get("ip"))
        app.logger.info(f"Updates installed for IP {request.args.get('ip')}")
        return jsonify({'status': 'ok', 'message': 'Updates installed'}), 200
    except Exception as ex:
        app.logger.error(f"Update error for IP {request.args.get('ip')}: {ex}")
        return jsonify({'status': 'error', 'message': f'Update error: {ex}'}), 500

@updates_api.route("/api/updates/all", methods=["POST"])
@login_required
def updates_all():
    """
    POST /api/updates/all
    Request: None
    Response: {"status": "ok", "message": str} or {"status": "error", "message": str}
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = dict_factory
            c = conn.cursor()
            servers = c.execute(f"SELECT server_ip, server_name FROM {SERVERS_TABLE}").fetchall()
        count = 0
        errors = []
        for server in servers:
            try:
                runPlaybook('lanjanitor.yml', server['server_ip'], tags='update_check')
                count += 1
                app.logger.info(f"Update check triggered for {server['server_name']} ({server['server_ip']})")
            except Exception as ex:
                app.logger.error(f"Update check failed for {server['server_name']} ({server['server_ip']}): {ex}")
                errors.append(f"{server['server_name']} ({server['server_ip']}): {ex}")
        msg = f"Update check triggered on {count} server{'s' if count != 1 else ''}."
        if errors:
            msg += f" Errors: {'; '.join(errors)}"
        return jsonify({'status': 'ok', 'message': msg}), 200
    except Exception as ex:
        app.logger.error(f"Failed to check updates: {ex}")
        return jsonify({'status': 'error', 'message': f'Failed to check updates: {ex}'}), 500
