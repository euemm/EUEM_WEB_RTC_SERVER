#!/bin/bash

# Secure WebRTC Signaling Server Startup Script

echo "Starting Secure WebRTC Signaling Server..."

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

# Check SSL certificate
if [ ! -f "ssl/server.crt" ] || [ ! -f "ssl/server.key" ]; then
    echo "Generating SSL certificates..."
    python3 -c "
from src.security.ssl_config import ssl_manager
ssl_manager.generate_self_signed_cert()
" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Error generating SSL certificates. Please check your Python environment."
        exit 1
    fi
fi

# Verify SSL certificates exist
if [ ! -f "ssl/server.crt" ] || [ ! -f "ssl/server.key" ]; then
    echo "Error: SSL certificates not found after generation attempt"
    exit 1
fi

# Create users.csv if it doesn't exist
if [ ! -f "users.csv" ]; then
    echo "Creating default users..."
    python3 -c "
from src.auth.jwt_handler import user_manager
user_manager.create_default_users()
"
    echo "Default users created:"
    echo "  admin / admin123"
    echo "  user1 / password123"
    echo "  user2 / password123"
    echo ""
fi

# Start the secure server with SSL
echo "Starting secure server on https://localhost:8000"
echo "WebSocket endpoint: wss://localhost:8000/ws/{room_id}"
echo "Authentication endpoint: https://localhost:8000/auth/login"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile ssl/server.key --ssl-certfile ssl/server.crt --reload