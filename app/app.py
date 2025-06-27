# Lanjanitor - A simple Ansible based server management tool
import os
import sys
import sqlite3
from io import StringIO
from flask import Flask, render_template, jsonify, request, make_response, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from Crypto.PublicKey import RSA
import ansible_runner
import click # command line parameters
import subprocess
import platform
import time
from flask_wtf import CSRFProtect
from datetime import timedelta, datetime
#from app.api import api
from blueprint_api import api

# --- Constants ---
DB_PATH = '/app/lanjanitor.db'
PRIVATE_KEY_PATH = '/app/private.pem'
PUBLIC_KEY_PATH = '/app/public.pem'
SERVERS_TABLE = 'servers'
USERS_TABLE = 'users'
DEFAULT_SERVER_IP = '192.168.0.100'
DEFAULT_SERVER_NAME = 'server1'
PING_CACHE_TTL = 30  # seconds
SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes
API_SERVERS = "api/servers"

# --- Flask App Setup ---
app = Flask(__name__)
# WARNING: For production, set SECRET_KEY to a strong, random value via environment variable!
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))

# CSRF protection for all POST/PUT/DELETE requests
csrf = CSRFProtect(app)

# Initialize user DB at startup
def init_user_db():
    """Initialize user database and default admin user."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(f'''CREATE TABLE IF NOT EXISTS {USERS_TABLE} (username TEXT PRIMARY KEY, password_hash TEXT)''')
        # Insert default admin if not exists
        c.execute(f"SELECT * FROM {USERS_TABLE} WHERE username='admin'")
        if not c.fetchone():
            c.execute(f"INSERT INTO {USERS_TABLE} (username, password_hash) VALUES (?, ?)", ('admin', generate_password_hash('admin')))
        conn.commit()

def init_db():
    """Ensure all required tables exist at startup."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Users table
        c.execute(f'''CREATE TABLE IF NOT EXISTS {USERS_TABLE} (username TEXT PRIMARY KEY, password_hash TEXT)''')
        c.execute(f"SELECT * FROM {USERS_TABLE} WHERE username='admin'")
        if not c.fetchone():
            c.execute(f"INSERT INTO {USERS_TABLE} (username, password_hash) VALUES (?, ?)", ('admin', generate_password_hash('admin')))
        # Servers table
        c.execute(f'''CREATE TABLE IF NOT EXISTS {SERVERS_TABLE} (server_id integer primary key autoincrement, server_name text, server_ip text, server_updates integer, server_reboot text)''')
        c.execute(f"SELECT * FROM {SERVERS_TABLE} WHERE server_ip = ?", (DEFAULT_SERVER_IP,))
        if not c.fetchone():
            c.execute(f"INSERT INTO {SERVERS_TABLE} (server_name,server_ip, server_updates, server_reboot) VALUES (?,?,?,?)", (DEFAULT_SERVER_NAME,DEFAULT_SERVER_IP,0,'false'))
        conn.commit()

# Call this at startup
init_db()

# Register blueprints
app.register_blueprint(api)

# --- Session Timeout Setup ---
@app.before_request
def session_timeout_check():
    """Expire session after timeout."""
    if 'user' in session:
        now = datetime.utcnow()
        last_active = session.get('last_active')
        if last_active:
            last_active = datetime.fromisoformat(last_active)
            if (now - last_active).total_seconds() > SESSION_TIMEOUT_SECONDS:
                session.clear()
                return make_response('Session expired', 401)
        session['last_active'] = now.isoformat()

# --- USER AUTH SETUP ---
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# HTML Routes
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route( '/' )
@login_required
def render_home():
    return render_template("index.html")

@app.route( '/settings' )
@login_required
def render_settings():
    return render_template("settings.html")

# --- Ping Cache Setup ---
_ping_cache = {}

def ping_host(ip):
    # Use system ping, 1 packet, short timeout
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    timeout = '-w' if platform.system().lower() == 'windows' else '-W'
    try:
        result = subprocess.run([
            'ping', param, '1', timeout, '1', ip
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception as ex:
        print(f'[Ping] Error pinging {ip}: {ex}')
        return False

def get_cached_ping(ip: str) -> bool:
    """Return cached ping status or ping and cache result."""
    now = time.time()
    entry = _ping_cache.get(ip)
    if entry and now - entry['timestamp'] < PING_CACHE_TTL:
        return entry['status']
    # Not cached or expired
    status = ping_host(ip)
    _ping_cache[ip] = {'status': status, 'timestamp': now}
    return status

# CLI Commands
@app.cli.command()
def setupdb():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(f'''CREATE TABLE IF NOT EXISTS {SERVERS_TABLE} (server_id integer primary key autoincrement, server_name text, server_ip text, server_updates integer, server_reboot text)''')
        # Only insert default server if it does not already exist
        c.execute(f"SELECT * FROM {SERVERS_TABLE} WHERE server_ip = ?", (DEFAULT_SERVER_IP,))
        if not c.fetchone():
            c.execute(f"INSERT INTO {SERVERS_TABLE} (server_name,server_ip, server_updates, server_reboot) VALUES (?,?,?,?)", (DEFAULT_SERVER_NAME,DEFAULT_SERVER_IP,0,'false'))
        conn.commit()
    return 'ok'

@app.cli.command()
def checkupdates():
    print("Starting check updates...")
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = dict_factory
        c = conn.cursor()
        servers = c.execute("SELECT * FROM servers").fetchall()
    for server in servers:
        aptUpdate(server['server_ip'])
                  
def aptUpdate(ip: str):
    """Check for updates and reboot status, update DB."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = dict_factory
        c = conn.cursor()
        try:
            output = runPlaybook('update_check.yml', ip)
            # Parse updates
            updates = output.status.split("{")[1].split('}')[0].split(':')[1].split(';')[0].replace(' ','').replace('"','')
            updates = int(updates)
        except Exception as ex:
            updates = -1
            print(f'[CheckUpdates] Error parsing updates: {ex}')

        # Parse reboot-required status from Ansible output
        reboot_required = 'false'
        try:
            # Look for the debug output line for reboot_file.stat.exists
            for line in output.status.splitlines():
                if '"reboot_file.stat.exists": true' in line or "'reboot_file.stat.exists': True" in line:
                    reboot_required = 'true'
                    break
                if '"reboot_file.stat.exists": false' in line or "'reboot_file.stat.exists': False" in line:
                    reboot_required = 'false'
                    break
        except Exception as ex:
            print(f'[CheckUpdates] Error parsing reboot status: {ex}')

        try:
            print(f'Updates: {updates}, Reboot required: {reboot_required}')
            c.execute(f'UPDATE {SERVERS_TABLE} SET server_updates = ?, server_reboot = ? WHERE server_ip = ?', (updates, reboot_required, ip))
        except Exception as ex:
            print(f'[CheckUpdates] Error updating db...{ex}')
        conn.commit()

@app.cli.command()
def genkey():
    if not os.path.isfile(PRIVATE_KEY_PATH):
        key = RSA.generate(2048)
        f = open(PRIVATE_KEY_PATH, "wb")
        f.write(key.exportKey('PEM'))
        f.close()

        pubkey = key.publickey()
        f = open(PUBLIC_KEY_PATH, "wb")
        f.write(pubkey.exportKey('OpenSSH'))
        f.close()
    else:
        print('key already exists')

# Return DB queries with column names
def dict_factory(cursor, row):
    """Return DB queries with column names as dict."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def runPlaybook(_playbook, _ip):
    # Change STDOUT to grab the playbook output
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result

    # Run the playbook
    _inventory = f'"{_ip}"'
    r = ansible_runner.run(private_data_dir='/app/ansible', playbook=_playbook, inventory=_inventory, extravars={ 'target' :_ip})
    
    # Reset STDOUT
    sys.stdout = old_stdout

    # Change playbook status for actual output
    r.status = result.getvalue()
    return r

# Remove API routes now handled by blueprint

# Add back the reboot_server route, now in the correct place and protected
@app.route("/api/reboot", methods=["POST"])
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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)