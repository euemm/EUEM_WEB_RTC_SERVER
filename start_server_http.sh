#!/bin/bash

# HTTP-only WebRTC Signaling Server Startup Script
# Runs on HTTP/WS only (no SSL/TLS)

echo "Starting HTTP-only WebRTC Signaling Server..."

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

# Create users.csv if it doesn't exist
if [ ! -f "users.csv" ]; then
    echo "Creating default users..."
    python3 -c "
from src.auth.jwt_handler import user_manager
user_manager.create_default_users()
" 2>/dev/null
    echo "Default users created:"
    echo "  admin / admin123"
    echo "  user1 / password123"
    echo "  user2 / password123"
    echo ""
fi

# Set environment to disable HTTPS requirement
export REQUIRE_HTTPS=false

# Start the HTTP-only server
echo "Starting HTTP-only server on http://localhost:8000"
echo "WebSocket endpoint: ws://localhost:8000/ws/{room_id}"
echo "Authentication endpoint: http://localhost:8000/auth/login"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
