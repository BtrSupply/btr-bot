#!/bin/bash

# Change to parent directory where Dockerfile is located
cd ..

# Stop and remove existing container if running
docker stop btr-markets-bot 2>/dev/null || true
docker rm btr-markets-bot 2>/dev/null || true

# Build the Docker image
docker build -t btr-markets-bot .

# Run the container
docker run -d --name btr-markets-bot btr-markets-bot

# Print container ID
echo "Container ID: $(docker ps -q)"
