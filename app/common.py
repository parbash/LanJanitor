"""
Common constants, decorators, and utility functions for LanJanitor
"""
import os
import sys
import sqlite3
import subprocess
import platform
import time
from io import StringIO
from flask import session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import ansible_runner
from Crypto.PublicKey import RSA

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

# --- Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            return make_response('Unauthorized', 401)
        return f(*args, **kwargs)
    return decorated_function

# --- Utility Functions ---

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

_ping_cache = {}

def ping_host(ip):
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
    now = time.time()
    entry = _ping_cache.get(ip)
    if entry and now - entry['timestamp'] < PING_CACHE_TTL:
        return entry['status']
    status = ping_host(ip)
    _ping_cache[ip] = {'status': status, 'timestamp': now}
    return status

def runPlaybook(_playbook, _ip):
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    _inventory = f'"{_ip}"'
    r = ansible_runner.run(private_data_dir='/app/ansible', playbook=_playbook, inventory=_inventory, extravars={ 'target' :_ip})
    sys.stdout = old_stdout
    r.status = result.getvalue()
    return r

def aptUpdate(ip: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = dict_factory
        c = conn.cursor()
        try:
            output = runPlaybook('update_check.yml', ip)
            updates = output.status.split("{")[1].split('}')[0].split(':')[1].split(';')[0].replace(' ','').replace('"','')
            updates = int(updates)
        except Exception as ex:
            updates = -1
            print(f'[CheckUpdates] Error parsing updates: {ex}')
        reboot_required = 'false'
        try:
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
