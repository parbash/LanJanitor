#!/bin/sh
# Automated test: Environment setup and authentication for LanJanitor 0.2
# Usage: sh test_01_env_setup_and_login.sh

set -e

IMAGE=lanjanitor:0.2
CONTAINER=lanjanitor-test
PORT=8080

# 1. Build Docker image
echo "Building Docker image..."
docker build -t $IMAGE .

# 2. Run container
echo "Starting container..."
docker run --rm -d -p $PORT:5000 --name $CONTAINER $IMAGE
sleep 5

# 3. Check if app is running
echo "Checking if app is running..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/login)
if [ "$STATUS" = "200" ]; then
  echo "App is running (login page accessible)"
else
  echo "App did not start correctly (HTTP $STATUS)"; docker stop $CONTAINER; exit 1
fi

# 4. Run setupdb command to initialize the database
echo "Running setupdb command..."
docker exec $CONTAINER flask setupdb
if [ $? -ne 0 ]; then
  echo "Database setup failed"; docker stop $CONTAINER; exit 1
fi

# 5. Fetch login page to get CSRF token and cookies
echo "Fetching login page for CSRF token..."
curl -s -c cookies.txt http://localhost:$PORT/login > login.html
CSRF=$(grep csrf_token cookies.txt | awk '{print $7}')
if [ -z "$CSRF" ]; then
  # Try to extract from meta tag as fallback
  CSRF=$(grep -o 'name="csrf-token" content="[^"]*"' login.html | sed 's/.*content="\([^"]*\)"/\1/')
fi
if [ -z "$CSRF" ]; then
  echo "Failed to obtain CSRF token"; docker stop $CONTAINER; exit 1
fi

# 6. Test login with default credentials (send CSRF token)
echo "Testing login..."
LOGIN=$(curl -s -b cookies.txt -c cookies.txt -X POST -H "Content-Type: application/json" -H "X-CSRFToken: $CSRF" \
  -d '{"username":"admin","password":"admin"}' \
  http://localhost:$PORT/api/login)
echo "Login response: $LOGIN"
echo "$LOGIN" | grep '"status":' >/dev/null || { echo "Login failed"; docker stop $CONTAINER; exit 1; }

# 7. Test accessing a protected endpoint
echo "Testing access to /api/servers..."
SERVERS=$(curl -s -b cookies.txt http://localhost:$PORT/api/servers)
echo "Servers response: $SERVERS"
echo "$SERVERS" | grep '\[' >/dev/null || { echo "Failed to access /api/servers"; docker stop $CONTAINER; exit 1; }

# 8. Test logout (send CSRF token)
echo "Testing logout..."
LOGOUT=$(curl -s -b cookies.txt -X POST -H "X-CSRFToken: $CSRF" http://localhost:$PORT/api/logout)
echo "Logout response: $LOGOUT"

# 9. Test session timeout (simulate by deleting cookies)
echo "Testing session timeout (simulated by deleting cookies)..."
rm cookies.txt
TIMEOUT=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:$PORT/api/servers)
if [ "$TIMEOUT" = "401" ]; then
  echo "Session timeout/unauthorized works as expected."
else
  echo "Session timeout test failed (HTTP $TIMEOUT)"; docker stop $CONTAINER; exit 1
fi

echo "\033[0;32mAll tests passed. Stopping container.\033[0m"
docker stop $CONTAINER
