#!/bin/bash

# Set variables
IMAGE_NAME="ai_poshn"
CONTAINER_NAME="ai_poshn_container"
PORT="8000"

# Print step
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
  --env-file .env \
  --restart always \
  $IMAGE_NAME

echo "✅ Deployment complete!"