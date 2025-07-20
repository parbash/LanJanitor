import os
import sqlite3
import click
from Crypto.PublicKey import RSA
from config import DB_PATH, SERVERS_TABLE, DEFAULT_SERVER_IP, DEFAULT_SERVER_NAME, PRIVATE_KEY_PATH, PUBLIC_KEY_PATH
from utils.common import dict_factory, runPlaybook

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


import logging
logger = logging.getLogger("lanjanitor.cli")

@click.command('setupdb')
def setupdb():
    """Setup the database tables and default server."""
    logger.info("setupdb CLI command executed.")
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(f'''CREATE TABLE IF NOT EXISTS {SERVERS_TABLE} (server_id integer primary key autoincrement, server_name text, server_ip text, server_updates integer, server_reboot text, os_type text)''')
        c.execute(f"SELECT * FROM {SERVERS_TABLE} WHERE server_ip = ?", (DEFAULT_SERVER_IP,))
        if not c.fetchone():
            c.execute(f"INSERT INTO {SERVERS_TABLE} (server_name,server_ip, server_updates, server_reboot, os_type) VALUES (?,?,?,?,?)", (DEFAULT_SERVER_NAME,DEFAULT_SERVER_IP,0,'false','Ubuntu'))
        conn.commit()
    click.echo('Database setup complete.')


@click.command('checkupdates')
def checkupdates():
    """Check updates for all servers."""
    logger.info("checkupdates CLI command executed.")
    click.echo("Starting check updates...")
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = dict_factory
        c = conn.cursor()
        servers = c.execute("SELECT * FROM servers").fetchall()
    for server in servers:
        aptUpdate(server['server_ip'])


@click.command('genkey')
def genkey():
    """Generate SSH key pair if not exists."""
    logger.info("genkey CLI command executed.")
    if not os.path.isfile(PRIVATE_KEY_PATH):
        key = RSA.generate(2048)
        f = open(PRIVATE_KEY_PATH, "wb")
        f.write(key.exportKey('PEM'))
        f.close()
        pubkey = key.publickey()
        f = open(PUBLIC_KEY_PATH, "wb")
        f.write(pubkey.exportKey('OpenSSH'))
        f.close()
        click.echo('Key generated.')
    else:
        click.echo('Key already exists.')
