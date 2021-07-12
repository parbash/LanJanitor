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
@app.route( '/' )
def render_home():
    return render_template("index.html")

@app.route( '/settings' )
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
            output = runPlaybook('update_check.yml', _ip )
            updates = output.status.split("{")[1].split('}')[0].split(':')[1].split(';')[0].replace(' ','').replace('"','')
            updates = int(updates)
        except:
            updates = -1
        try:
            print(updates)
            c.execute(f'UPDATE servers SET server_updates = {updates} WHERE server_ip = "{_ip}"')
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
def getkey():
    try:
        with open('/app/public.pem', 'r') as file:
            data = file.read().replace('\n', '<br />')
    except:
        data = "No key has been generated..."
    return data 

@app.route("/api/updates", methods=["GET"])
def aptUpgrade():
    output = runPlaybook( 'update_install.yml', request.args.get("ip") )
    app.logger.info(output.status)
    aptUpdate(request.args.get("ip"))
    return make_response("ok", 200)

@app.route("/api/servers",methods=["GET","POST","DELETE"])
def servers():
    if request.method == 'GET':
        with sqlite3.connect('/app/lanjanitor.db') as conn:
            conn.row_factory = dict_factory
            c = conn.cursor()
            servers = c.execute("SELECT * FROM servers").fetchall()
        return jsonify( servers )
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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)