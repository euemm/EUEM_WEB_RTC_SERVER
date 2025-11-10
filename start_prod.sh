#!/bin/bash

# WebRTC Signaling Server - Production Mode
# Runs behind Nginx (Nginx handles SSL/TLS termination)
# This script starts the server on HTTP (localhost only)

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

# Check .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Using default configuration."
    echo "For production, create .env file with proper configuration."
    echo ""
fi

# Set environment variables for production behind nginx
export REQUIRE_HTTPS=false  # Nginx handles HTTPS
export DEBUG=false

echo "============================================"
echo "Production Server Configuration:"
echo "  - Running on: http://127.0.0.1:8080"
echo "  - SSL/TLS: Handled by Nginx"
echo "  - Mode: Production"
echo "============================================"
echo ""
echo "IMPORTANT: Ensure nginx is configured to:"
echo "  - Proxy to http://127.0.0.1:8080"
echo "  - Handle SSL/TLS termination"
echo "  - Forward WebSocket connections"
echo ""
echo "Endpoints accessible through nginx:"
echo "  - Health: https://your-domain.com/health"
echo "  - Auth: https://your-domain.com/auth/login"
echo "  - WebSocket: wss://your-domain.com/ws/{room_id}"
echo ""
echo "Ensure the Postgres database contains the production user accounts necessary for authentication."
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server on localhost only (not exposed to internet)
python3 -m uvicorn src.main:app \
    --host 127.0.0.1 \
    --port 8080 \
    --log-level info
