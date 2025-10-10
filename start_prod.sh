#!/bin/bash

# Production WebRTC Signaling Server
# HTTPS/WSS only - Secure production deployment

echo "Starting WebRTC Signaling Server (Production Mode)..."
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

# Check for SSL certificates
if [ ! -f "ssl/server.crt" ] || [ ! -f "ssl/server.key" ]; then
    echo "Error: SSL certificates not found in ssl/ directory"
    echo ""
    echo "For production deployment, you must provide valid SSL certificates:"
    echo "  1. Obtain certificates from a trusted CA (e.g., Let's Encrypt)"
    echo "  2. Place cert.pem in ssl/server.crt"
    echo "  3. Place privkey.pem in ssl/server.key"
    echo ""
    echo "For testing only, you can generate self-signed certificates:"
    echo "  python3 -c 'from src.security.ssl_config import ssl_manager; ssl_manager.generate_self_signed_cert()'"
    echo ""
    exit 1
fi

# Verify SSL certificates are readable
if [ ! -r "ssl/server.crt" ] || [ ! -r "ssl/server.key" ]; then
    echo "Error: SSL certificates exist but are not readable"
    echo "Check file permissions: chmod 644 ssl/server.crt && chmod 600 ssl/server.key"
    exit 1
fi

# Check if users.csv exists
if [ ! -f "users.csv" ]; then
    echo "Error: users.csv not found"
    echo "Please create users.csv with your production user credentials"
    echo ""
    echo "To create users.csv with default users (NOT RECOMMENDED FOR PRODUCTION):"
    echo "  python3 -c 'from src.auth.jwt_handler import user_manager; user_manager.create_default_users()'"
    echo ""
    exit 1
fi

# Check .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Using default configuration."
    echo "For production, create .env file with proper configuration."
    echo ""
fi

# Set production environment variables
export REQUIRE_HTTPS=true
export DEBUG=false

# Start the production server with SSL/TLS
echo "Starting production server with HTTPS/WSS..."
echo ""
echo "  HTTPS endpoint: https://0.0.0.0:8000"
echo "  WSS endpoint: wss://0.0.0.0:8000/ws/{room_id}"
echo "  Auth endpoint: https://0.0.0.0:8000/auth/login"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 -m uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-keyfile ssl/server.key \
    --ssl-certfile ssl/server.crt \
    --log-level info

