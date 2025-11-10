#!/bin/bash

# Development WebRTC Signaling Server
# HTTP/WS only - For local development and testing

echo "Starting WebRTC Signaling Server (Development Mode)..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if requirements are installed
echo "Checking dependencies..."
python3 -c "import fastapi, uvicorn, pydantic_settings, jose, passlib, slowapi, cryptography" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

# Set development environment variables
export REQUIRE_HTTPS=false
export DEBUG=true

# Start the development server (HTTP only)
echo "Starting development server with HTTP/WS..."
echo ""
echo "  HTTP endpoint: http://localhost:8080"
echo "  WS endpoint: ws://localhost:8080/ws/{room_id}"
echo "  Auth endpoint: http://localhost:8080/auth/login"
echo "  API docs: http://localhost:8080/docs"
echo ""
echo "Ensure your Postgres database contains the desired user accounts."
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --reload \
    --log-level debug

