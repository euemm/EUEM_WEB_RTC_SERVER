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

# Create users.csv if it doesn't exist
if [ ! -f "users.csv" ]; then
    echo "Creating default users for development..."
    python3 -c "
from src.auth.jwt_handler import user_manager
user_manager.create_default_users()
" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Default users created successfully:"
        echo "  admin / admin123"
        echo "  user1 / password123"
        echo "  user2 / password123"
        echo ""
        echo "WARNING: These are test credentials for development only!"
        echo "         Do NOT use in production!"
        echo ""
    else
        echo "Warning: Could not create default users"
    fi
else
    echo "Using existing users.csv"
    echo ""
fi

# Load environment variables from .env file (if it exists)
if [ -f ".env" ]; then
    echo "Loading configuration from .env file..."
    set -a  # automatically export all variables
    source .env
    set +a
fi

# Set development-specific overrides (these take precedence over .env)
export REQUIRE_HTTPS=false
export DEBUG=true

# Set defaults if not defined in .env
: ${HOST:=0.0.0.0}
: ${PORT:=8000}

# Start the development server (HTTP only)
echo "Starting development server with HTTP/WS..."
echo ""
echo "  HTTP endpoint: http://localhost:${PORT}"
echo "  WS endpoint: ws://localhost:${PORT}/ws/{room_id}"
echo "  Auth endpoint: http://localhost:${PORT}/auth/login"
echo "  API docs: http://localhost:${PORT}/docs"
echo ""
echo "Test credentials:"
echo "  admin / admin123"
echo "  user1 / password123"
echo "  user2 / password123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn src.main:app \
    --host ${HOST} \
    --port ${PORT} \
    --reload \
    --log-level debug

