#!/bin/bash

# Flexible WebRTC Signaling Server Startup Script
# Supports both HTTP/WS and HTTPS/WSS connections

echo "Starting Flexible WebRTC Signaling Server..."

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

# Check SSL certificate (optional for flexible mode)
if [ ! -f "ssl/server.crt" ] || [ ! -f "ssl/server.key" ]; then
    echo "Generating SSL certificates for HTTPS/WSS support..."
    python3 -c "
from src.security.ssl_config import ssl_manager
ssl_manager.generate_self_signed_cert()
" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Warning: Could not generate SSL certificates. HTTPS/WSS will not be available."
    fi
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

# Start the flexible server
echo "Starting flexible server:"
echo "  HTTP endpoint: http://localhost:8000"
echo "  HTTPS endpoint: https://localhost:8000 (if SSL available)"
echo "  WebSocket endpoint: ws://localhost:8000/ws/{room_id}"
echo "  Secure WebSocket endpoint: wss://localhost:8000/ws/{room_id}"
echo "  Authentication endpoint: http://localhost:8000/auth/login or https://localhost:8000/auth/login"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Check if SSL certificates exist for HTTPS support
if [ -f "ssl/server.crt" ] && [ -f "ssl/server.key" ]; then
    echo "Starting servers with both HTTP and HTTPS support..."
    echo "  HTTP server: http://localhost:8000"
    echo "  HTTPS server: https://localhost:8001"
    echo ""
    
    # Start HTTP server in background
    python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
    HTTP_PID=$!
    
    # Start HTTPS server in background  
    python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --ssl-keyfile ssl/server.key --ssl-certfile ssl/server.crt --reload &
    HTTPS_PID=$!
    
    echo "HTTP server PID: $HTTP_PID"
    echo "HTTPS server PID: $HTTPS_PID"
    echo ""
    echo "Press Ctrl+C to stop both servers"
    
    # Wait for both processes
    wait $HTTP_PID $HTTPS_PID
else
    echo "Starting server with HTTP support only (no SSL certificates found)..."
    echo "  HTTP server: http://localhost:8000"
    python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
fi
