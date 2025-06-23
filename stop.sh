#!/bin/sh
# Stop and remove the LanJanitor container
CONTAINER_NAME="lanjanitor"

docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME
