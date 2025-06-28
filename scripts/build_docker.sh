#!/usr/bin/env bash

# Usage: ./build_docker.sh /path/to/docker-directory image_name

set -e

DOCKER_DIR="$1"
IMAGE_NAME="$2"

if [[ -z "$DOCKER_DIR" || -z "$IMAGE_NAME" ]]; then
  echo "Usage: $0 /path/to/docker-directory image_name"
  exit 1
fi

# Check that Dockerfile exists
if [[ ! -f "$DOCKER_DIR/Dockerfile" ]]; then
  echo "Error: No Dockerfile found in $DOCKER_DIR"
  exit 1
fi

# Build the image
cd "$DOCKER_DIR"
docker build -t "$IMAGE_NAME" .

echo "Docker image '$IMAGE_NAME' built successfully from directory '$DOCKER_DIR'"
