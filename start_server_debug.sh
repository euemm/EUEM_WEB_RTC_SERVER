#!/bin/bash

# Debug WebRTC Signaling Server Startup Script
# Enables maximum logging for debugging HTTP request issues

echo "Starting WebRTC Signaling Server in DEBUG mode..."

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
fi

# Check SSL certificate (optional)
if [ ! -f "ssl/server.crt" ] || [ ! -f "ssl/server.key" ]; then
    echo "Generating SSL certificates..."
    python3 -c "
from src.security.ssl_config import ssl_manager
ssl_manager.generate_self_signed_cert()
" 2>/dev/null
fi

# Create users.csv if it doesn't exist
if [ ! -f "users.csv" ]; then
    echo "Creating default users..."
    python3 -c "
from src.auth.jwt_handler import user_manager
user_manager.create_default_users()
"
fi

# Set debug environment variables
export REQUIRE_HTTPS=false
export LOG_LEVEL=DEBUG
export DEBUG=true

echo "Starting server with maximum logging enabled..."
echo "Server logs will be written to: server.log"
echo "Press Ctrl+C to stop the server"
echo ""

# Start with maximum verbosity
python3 -m uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level debug \
    --access-log \
    --reload \
    --reload-dir src \
    --reload-include "*.py"
