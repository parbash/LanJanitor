# Lanjanitor - A simple Ansible based server management tool
from flask import Flask, render_template, jsonify, request, make_response, session
from Crypto.PublicKey import RSA
from io import StringIO
import ansible_runner
import sqlite3
import sys
import os
import click # command line parameters
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')

# --- USER AUTH SETUP ---
def init_user_db():
    with sqlite3.connect('/app/lanjanitor.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT)''')
        # Insert default admin if not exists
        c.execute("SELECT * FROM users WHERE username='admin'")
        if not c.fetchone():
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ('admin', generate_password_hash('admin')))
        conn.commit()

@app.before_first_request
def ensure_user_db():
    init_user_db()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            return make_response('Unauthorized', 401)
        return f(*args, **kwargs)
    return decorated_function

# --- AUTH API ENDPOINTS ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    with sqlite3.connect('/app/lanjanitor.db') as conn:
        c = conn.cursor()
        c.execute('SELECT password_hash FROM users WHERE username=?', (username,))
        row = c.fetchone()
        if row and check_password_hash(row[0], password):
            session['user'] = username
            return make_response('ok', 200)
    return make_response('Invalid credentials', 401)

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return make_response('ok', 200)

@app.route('/api/set_password', methods=['POST'])
@login_required
def set_password():
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    username = session.get('user')
    with sqlite3.connect('/app/lanjanitor.db') as conn:
        c = conn.cursor()
        c.execute('SELECT password_hash FROM users WHERE username=?', (username,))
        row = c.fetchone()
        if not row or not check_password_hash(row[0], old_password):
            return make_response('Current password incorrect', 400)
        c.execute('UPDATE users SET password_hash=? WHERE username=?', (generate_password_hash(new_password), username))
        conn.commit()
    return make_response('ok', 200)
from flask import Flask, render_template, jsonify,request, make_response
from Crypto.PublicKey import RSA
from io import StringIO
import ansible_runner
import sqlite3
import sys
import os
import click # command line parameters

app = Flask(__name__)

# Return DB queries with column names
def dict_factory(cursor, row):
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

# CLI Commands
@app.cli.command()
def setupdb():
    with sqlite3.connect('/app/lanjanitor.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE servers (server_id integer primary key autoincrement, server_name text, server_ip text, server_updates integer, server_reboot text)''')
        c.execute("INSERT INTO servers (server_name,server_ip, server_updates, server_reboot) VALUES ('server1','192.168.0.100',0,'false')")
        conn.commit()
    return 'ok'

@app.cli.command()
def checkupdates():
    print("Starting check updates...")
    with sqlite3.connect('/app/lanjanitor.db') as conn:
        conn.row_factory = dict_factory
        c = conn.cursor()
        servers = c.execute("SELECT * FROM servers").fetchall()
    for server in servers:
        aptUpdate(server['server_ip'])
                  
def aptUpdate(_ip):
    with sqlite3.connect('/app/lanjanitor.db') as conn:
        conn.row_factory = dict_factory
        c = conn.cursor()
        try:
            output = runPlaybook('update_check.yml', _ip)
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
            c.execute(f'UPDATE servers SET server_updates = {updates}, server_reboot = "{reboot_required}" WHERE server_ip = "{_ip}"')
        except Exception as ex:
            print(f'[CheckUpdates] Error updating db...{ex}')
        conn.commit()

@app.cli.command()
def genkey():
    if not os.path.isfile('/app/private.pem'):
        key = RSA.generate(2048)
        f = open("/app/private.pem", "wb")
        f.write(key.exportKey('PEM'))
        f.close()

        pubkey = key.publickey()
        f = open("/app/public.pem", "wb")
        f.write(pubkey.exportKey('OpenSSH'))
        f.close()
    else:
        print('key already exists')

# HTML API Routes
@app.route("/api/key",methods=["GET"])
@login_required
def getkey():
    try:
        with open('/app/public.pem', 'r') as file:
            data = file.read().replace('\n', '<br />')
    except:
        data = "No key has been generated..."
    return data 

@app.route("/api/updates", methods=["GET"])
@login_required
def aptUpgrade():
    output = runPlaybook( 'update_install.yml', request.args.get("ip") )
    app.logger.info(output.status)
    aptUpdate(request.args.get("ip"))
    return make_response("ok", 200)

@app.route("/api/servers",methods=["GET","POST","DELETE"])
@login_required
def servers():

    import subprocess
    import platform
    def ping_host(ip):
        # Use system ping, 1 packet, short timeout
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout = '-w' if platform.system().lower() == 'windows' else '-W'
        try:
            result = subprocess.run([
                'ping', param, '1', timeout, '1', ip
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return result.returncode == 0
        except Exception:
            return False

    if request.method == 'GET':
        with sqlite3.connect('/app/lanjanitor.db') as conn:
            conn.row_factory = dict_factory
            c = conn.cursor()
            servers = c.execute("SELECT * FROM servers").fetchall()
            # Add ping status to each server
            for server in servers:
                server['ping_status'] = 'online' if ping_host(server['server_ip']) else 'offline'
        return jsonify(servers)
    elif request.method == 'POST':
        with sqlite3.connect('/app/lanjanitor.db') as conn:
            c = conn.cursor()
            c.execute(f"INSERT INTO servers (server_name,server_ip, server_updates, server_reboot) VALUES ('{request.json['name']}','{request.json['ip']}',0,'false')")
            conn.commit()
        return 'ok'
    elif request.method == 'DELETE':
        delitem = request.args.get('id')
        with sqlite3.connect('/app/lanjanitor.db') as conn:
            c = conn.cursor()
            c.execute(f'DELETE FROM servers WHERE server_id = "{ delitem }"')
            conn.commit()
        return make_response( "ok", 200 )

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