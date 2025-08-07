#!/bin/bash

# Set variables
IMAGE_NAME="ai_poshn"
CONTAINER_NAME="ai_poshn_container"
PORT="8000"
HOST_SQLITE_DIR="/home/ec2-user/AiPoshn/sqlite-data"

# Ensure host volume directory exists
mkdir -p $HOST_SQLITE_DIR

echo "🔄 Stopping and removing existing container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

echo "🧹 Removing old image..."
docker rmi $IMAGE_NAME 2>/dev/null || true

echo "⬇️ Pulling latest code from Git..."
git pull

echo "🐳 Building new Docker image..."
docker build -t $IMAGE_NAME .

echo "🚀 Running container..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:$PORT \
  -v $HOST_SQLITE_DIR:/data \
  --env-file .env \
  --restart always \
  $IMAGE_NAME

echo "✅ Deployment complete!"
