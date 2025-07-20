# LanJanitor Common Utilities
# Constants, decorators, and utility functions shared across modules.
# Common helpers for DB, Ansible, and ping operations.

# --- Ping Cache ---
_ping_cache = {}

# Imports
import sys
import platform
import time
import subprocess
from io import StringIO
import ansible_runner

PING_CACHE_TTL = 30  # seconds

def dict_factory(cursor, row):
    """Return DB queries with column names as dict."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def runPlaybook(_playbook, _ip, tags=None):
    """Run an Ansible playbook and return the result object."""
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    _inventory = f'"{_ip}"'
    runner_args = {
        'private_data_dir': '/app/ansible',
        'playbook': _playbook,
        'inventory': _inventory,
        'extravars': { 'target': _ip }
    }
    if tags:
        runner_args['tags'] = tags
    r = ansible_runner.run(**runner_args)
    sys.stdout = old_stdout
    r.status = result.getvalue()
    return r

def ping_host(ip):
    """Ping a host and return True if reachable."""
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
    status = ping_host(ip)
    _ping_cache[ip] = {'status': status, 'timestamp': now}
    return status