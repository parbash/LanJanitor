#!/bin/sh
# start.sh - Build and start the LanJanitor container

IMAGE=lanjanitor:0.3
CONTAINER=lanjanitor
PORT=8080

# Build the Docker image
echo "Building Docker image $IMAGE..."
docker build -t $IMAGE . || { echo "Docker build failed"; exit 1; }

# Stop and remove any existing container with the same name
docker rm -f $CONTAINER 2>/dev/null || true

echo "Starting LanJanitor container..."
docker run -d \
  --name $CONTAINER \
  -p $PORT:5000 \
  $IMAGE

echo "LanJanitor is running at http://localhost:$PORT"
