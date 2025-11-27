#!/bin/bash

echo ""
echo "========================================"
echo "  9P Social Analytics"
echo "  Starting the application..."
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo ""
    echo "Please start Docker Desktop and try again."
    echo ""
    exit 1
fi

echo "Docker is running..."
echo ""
echo "Starting 9P Analytics (this may take a few minutes on first run)..."
echo ""

# Start the application
docker-compose up

# Clean shutdown message
echo ""
echo "Application stopped."
