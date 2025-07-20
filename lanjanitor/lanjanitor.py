"""
LanJanitor Main Application
--------------------------
Flask app entrypoint, blueprint registration, and core logic.
"""

# Standard library imports
import os
import sqlite3
from datetime import datetime
import logging

# --- Logging Setup ---
LOG_PATH = os.path.join(os.path.dirname(__file__), 'lanjanitor.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Third-party imports
from flask import Flask, render_template, make_response, session
from werkzeug.security import generate_password_hash
from flask_wtf import CSRFProtect

# Local imports
from api.auth_api import auth_api
from api.servers_api import servers_api
from api.updates_api import updates_api
from config import DB_PATH, SERVERS_TABLE, USERS_TABLE, SESSION_TIMEOUT_SECONDS


# --- Flask App Setup ---

app = Flask(__name__)
# WARNING: For production, set SECRET_KEY to a strong, random value via environment variable!
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))

# CSRF protection for all POST/PUT/DELETE requests
csrf = CSRFProtect(app)
logger.info('LanJanitor Flask app initialized.')

# --- Flask App Setup ---
app = Flask(__name__)

# WARNING: For production, set SECRET_KEY to a strong, random value via environment variable!
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))

# CSRF protection for all POST/PUT/DELETE requests
csrf = CSRFProtect(app)

# Register modular blueprints

app.register_blueprint(auth_api)
logger.info('auth_api blueprint registered.')

app.register_blueprint(servers_api)
logger.info('servers_api blueprint registered.')

#def init_user_db():
#    """Initialize user database and default admin user."""
#    with sqlite3.connect(DB_PATH) as conn:
#        c = conn.cursor()
#        c.execute(f'''CREATE TABLE IF NOT EXISTS {USERS_TABLE} (username TEXT PRIMARY KEY, password_hash TEXT)''')
#        # Insert default admin if not exists
#        c.execute(f"SELECT * FROM {USERS_TABLE} WHERE username='admin'")
#        if not c.fetchone():
#            c.execute(f"INSERT INTO {USERS_TABLE} (username, password_hash) VALUES (?, ?)", ('admin', generate_password_hash('admin')))
#        conn.commit()
#    logger.info('User DB initialized and default admin ensured.')


def init_db():
    """Ensure all required tables exist at startup."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Users table
        c.execute(f'''CREATE TABLE IF NOT EXISTS {USERS_TABLE} (username TEXT PRIMARY KEY, password_hash TEXT)''')
        c.execute(f"SELECT * FROM {USERS_TABLE} WHERE username='admin'")
        if not c.fetchone():
            c.execute(f"INSERT INTO {USERS_TABLE} (username, password_hash) VALUES (?, ?)", ('admin', generate_password_hash('admin')))
        # Servers table (add os_type column if not exists)
        c.execute(f'''CREATE TABLE IF NOT EXISTS {SERVERS_TABLE} (server_id integer primary key autoincrement, server_name text, server_ip text, server_updates integer, server_reboot text, os_type text)''')
    logger.info('All required tables ensured at startup.')

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
                logger.info('Session expired for user.')
                return make_response('Session expired', 401)
        session['last_active'] = now.isoformat()

# --- USER AUTH SETUP ---
from utils.decorators import login_required

# HTML Routes

@app.route('/login')
def login_page():
    logger.info('Login page accessed.')
    return render_template('login.html')


@app.route( '/' )
@login_required
def render_home():
    logger.info('Home page accessed.')
    return render_template("index.html")


@app.route( '/settings' )
@login_required
def render_settings():
    logger.info('Settings page accessed.')
    return render_template("settings.html")

# --- CLI Commands ---
from utils.cli import setupdb, checkupdates, genkey

app.cli.add_command(setupdb)
logger.info("setupdb CLI command registered.")

app.cli.add_command(checkupdates)
logger.info("checkupdates CLI command registered.")

app.cli.add_command(genkey)
logger.info("genkey CLI command registered.")


# --- Basic CLI Command for Testing ---
import click

@app.cli.command("hello")
def hello():
    """Test command that does nothing."""
    click.echo("Hello from LanJanitor CLI!")

app.cli.add_command(hello)


if __name__ == "__main__":
    init_db()
    logger.info('Starting LanJanitor Flask app...')
    app.run(debug=True, host='0.0.0.0', port=5000)