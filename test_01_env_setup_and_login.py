import requests
import time
import sys
import json

IMAGE = "lanjanitor:0.2"
CONTAINER = "lanjanitor-test"
PORT = 8080
BASE_URL = f"http://localhost:{PORT}"

# Helper to print and flush
print_flush = lambda msg: print(msg, flush=True)

def main():
    session = requests.Session()

    # 1. Check if app is running
    print_flush("Checking if app is running...")
    try:
        resp = session.get(f"{BASE_URL}/login")
        if resp.status_code != 200:
            print_flush(f"App did not start correctly (HTTP {resp.status_code})")
            sys.exit(1)
        print_flush("App is running (login page accessible)")
    except Exception as e:
        print_flush(f"Error connecting to app: {e}")
        sys.exit(1)

    # 2. Get CSRF token from meta tag
    print_flush("Fetching CSRF token from login page...")
    csrf_token = None
    if 'csrf-token' in resp.text:
        import re
        m = re.search(r'name="csrf-token" content="([^"]+)"', resp.text)
        if m:
            csrf_token = m.group(1)
    if not csrf_token:
        print_flush("Failed to obtain CSRF token")
        sys.exit(1)
    print_flush(f"CSRF token: {csrf_token}")

    # 3. Login
    print_flush("Testing login...")
    login_resp = session.post(f"{BASE_URL}/api/login", json={"username": "admin", "password": "admin"}, headers={"X-CSRFToken": csrf_token})
    print_flush(f"Login response: {login_resp.text}")
    if 'status' not in login_resp.text:
        print_flush("Login failed")
        sys.exit(1)

    # 4. Test /api/servers GET
    print_flush("Testing access to /api/servers...")
    servers_resp = session.get(f"{BASE_URL}/api/servers")
    print_flush(f"Servers response: {servers_resp.text}")
    if not servers_resp.ok or not servers_resp.text.startswith('['):
        print_flush("Failed to access /api/servers")
        sys.exit(1)

    # 5. Add a server
    print_flush("Testing add server...")
    add_server_resp = session.post(f"{BASE_URL}/api/servers", json={"name": "testserver", "ip": "192.168.56.123"}, headers={"X-CSRFToken": csrf_token})
    print_flush(f"Add server response: {add_server_resp.text}")
    if 'status' not in add_server_resp.text:
        print_flush("Add server failed")
        sys.exit(1)

    # 6. Confirm server is in list
    servers_after_add = session.get(f"{BASE_URL}/api/servers").json()
    print_flush(f"Servers after add: {servers_after_add}")
    testserver = next((s for s in servers_after_add if s.get('server_name') == 'testserver'), None)
    if not testserver:
        print_flush("Added server not found in list")
        sys.exit(1)
    server_id = testserver.get('server_id')
    print_flush(f"Extracted server_id: {server_id}")

    # 7. Delete the server
    print_flush(f"Testing delete server (id={server_id})...")
    del_server_resp = session.delete(f"{BASE_URL}/api/servers", params={"id": server_id}, headers={"X-CSRFToken": csrf_token})
    print_flush(f"Delete server response: {del_server_resp.text}")
    if 'status' not in del_server_resp.text:
        print_flush("Delete server failed")
        sys.exit(1)

    # 8. Confirm server is deleted
    servers_after_del = session.get(f"{BASE_URL}/api/servers").json()
    print_flush(f"Servers after delete: {servers_after_del}")
    if any(s.get('server_name') == 'testserver' for s in servers_after_del):
        print_flush("Server was not deleted")
        sys.exit(1)
    print_flush("Server deleted successfully.")

    # 9. Logout
    print_flush("Testing logout...")
    logout_resp = session.post(f"{BASE_URL}/api/logout", headers={"X-CSRFToken": csrf_token})
    print_flush(f"Logout response: {logout_resp.text}")

    # 10. Test session timeout (simulate by clearing cookies)
    print_flush("Testing session timeout (simulated by clearing cookies)...")
    session.cookies.clear()
    timeout_resp = session.get(f"{BASE_URL}/api/servers")
    if timeout_resp.status_code == 401:
        print_flush("Session timeout/unauthorized works as expected.")
    else:
        print_flush(f"Session timeout test failed (HTTP {timeout_resp.status_code})")
        sys.exit(1)

    print_flush("All tests passed.")

if __name__ == "__main__":
    main()
