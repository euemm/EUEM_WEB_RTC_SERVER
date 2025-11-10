"""
WebRTC Signaling Server
Main server file for handling WebRTC signaling between clients
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager

from .handlers.websocket_handler import WebSocketHandler
from .models.signal_data import SignalData
from .utils.config import get_settings
from .auth.auth_routes import router as auth_router
from .auth.jwt_handler import get_current_user, User
from .security.rate_limiter import get_rate_limiter, get_ddos_protection, custom_rate_limit_handler
from .security.ssl_config import get_ssl_context, verify_ssl_setup
from .utils.db import close_db_pool

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log')
    ]
)
logger = logging.getLogger(__name__)

# Set uvicorn logging to DEBUG for more detailed HTTP request info
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        await close_db_pool()


# Initialize FastAPI app with rate limiting
app = FastAPI(
    title="WebRTC Signaling Server",
    description="A secure signaling server for WebRTC peer-to-peer connections",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiting
limiter = get_rate_limiter()
app.state.limiter = limiter
app.add_exception_handler(Exception, custom_rate_limit_handler)

# Add CORS middleware with security restrictions
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Add detailed request logging middleware
@app.middleware("http")
async def detailed_logging_middleware(request: Request, call_next):
    """Detailed request logging and security middleware"""
    
    # Get client information
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    origin = request.headers.get("origin", "none")
    referer = request.headers.get("referer", "none")
    
    # Log detailed request information
    logger.info(f"=== INCOMING REQUEST ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url.scheme}://{request.url.netloc}{request.url.path}")
    logger.info(f"Query params: {dict(request.query_params)}")
    logger.info(f"Client IP: {client_ip}")
    logger.info(f"User-Agent: {user_agent}")
    logger.info(f"Origin: {origin}")
    logger.info(f"Referer: {referer}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Log request body for debugging (be careful with sensitive data)
    # NOTE: We don't read the body here to avoid consuming it before FastAPI can process it
    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length", "unknown")
        logger.info(f"Request body length: {content_length}")
        if "/auth/login" in str(request.url.path):
            logger.info("Request body: [AUTH ENDPOINT - BODY HIDDEN]")
        else:
            logger.info("Request body: [WILL BE LOGGED AFTER PROCESSING]")
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Log response information
        logger.info(f"=== RESPONSE ===")
        logger.info(f"Status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        # Add security headers to all responses
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add HSTS header only for HTTPS requests
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        logger.info(f"=== REQUEST COMPLETED ===")
        return response
        
    except Exception as e:
        logger.error(f"=== REQUEST ERROR ===")
        logger.error(f"Error processing request: {e}")
        logger.error(f"Request details: {request.method} {request.url}")
        logger.error(f"Client IP: {client_ip}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

# Initialize WebSocket handler and DDoS protection
websocket_handler = WebSocketHandler()
ddos_protection = get_ddos_protection()

# Include authentication routes
app.include_router(auth_router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "WebRTC Signaling Server is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "active_connections": len(websocket_handler.active_connections),
        "rooms": len(websocket_handler.rooms)
    }

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for WebRTC signaling (supports both WS and WSS)"""
    
    # Get client IP for DDoS protection
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    # Log detailed WebSocket connection information
    logger.info(f"=== WEBSOCKET CONNECTION ATTEMPT ===")
    logger.info(f"Room ID: {room_id}")
    logger.info(f"URL: {websocket.url.scheme}://{websocket.url.netloc}{websocket.url.path}")
    logger.info(f"Client IP: {client_ip}")
    logger.info(f"Headers: {dict(websocket.headers)}")
    logger.info(f"Query params: {dict(websocket.query_params)}")
    
    # Check if IP is blocked
    if ddos_protection.is_ip_blocked(client_ip):
        await websocket.close(code=1008, reason="IP blocked due to security violations")
        return
    
    # Generate unique connection ID
    connection_id = str(uuid.uuid4())
    
    # Track connection
    ddos_protection.add_connection(client_ip, connection_id)
    
    # Track if connection was established (for cleanup in finally block)
    connected = False
    client_id = None
    
    try:
        # Accept WebSocket connection
        await websocket.accept()
        
        # Send authentication challenge
        await websocket.send_text(json.dumps({
            "type": "auth_required",
            "message": "Authentication required. Send JWT token."
        }))
        
        # Wait for authentication
        auth_data = await websocket.receive_text()
        auth_message = json.loads(auth_data)
        
        if auth_message.get("type") != "auth_token":
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Validate JWT token
        token = auth_message.get("token")
        client_id = auth_message.get("clientId")  # Get client ID from auth message
        if not token:
            ddos_protection.record_auth_failure(client_ip)
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Verify token and get user
        try:
            from .auth.jwt_handler import jwt_handler
            payload = jwt_handler.verify_token(token)
            if not payload:
                ddos_protection.record_auth_failure(client_ip)
                await websocket.close(code=1008, reason="Invalid token")
                return
            
            username = payload.get("sub")
            from .auth.jwt_handler import user_manager
            user = await user_manager.get_user(username)
            if not user or not user.is_active:
                ddos_protection.record_auth_failure(client_ip)
                await websocket.close(code=1008, reason="User not found or inactive")
                return
            
            # Clear auth failures on successful login
            ddos_protection.clear_auth_failures(client_ip)
            
            # Send authentication success with assigned client_id
            # If client didn't provide ID, generate one
            if not client_id:
                client_id = str(uuid.uuid4())
            
            await websocket.send_text(json.dumps({
                "type": "auth_success",
                "user": username,
                "client_id": client_id,
                "message": "Authentication successful"
            }))
            
        except Exception as e:
            ddos_protection.record_auth_failure(client_ip)
            logger.error(f"Authentication error: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
        
        # Connect to room with user context and client_id
        await websocket_handler.connect(websocket, room_id, user.username, client_id)
        connected = True  # Mark connection as established
        
        # Main message loop
        while True:
            # Check message rate
            if not ddos_protection.check_message_rate(client_ip):
                await websocket.close(code=1008, reason="Rate limit exceeded")
                break
            
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different types of signaling messages
            await websocket_handler.handle_message(room_id, websocket, message)
            
    except WebSocketDisconnect as e:
        logger.info(f"=== WEBSOCKET DISCONNECT ===")
        logger.info(f"Room ID: {room_id}")
        logger.info(f"Client IP: {client_ip}")
        logger.info(f"Client ID: {client_id}")
        logger.info(f"Close code: {e.code}")
        logger.info(f"Close reason: {e.reason}")
    except Exception as e:
        logger.error(f"=== WEBSOCKET ERROR ===")
        logger.error(f"Room ID: {room_id}")
        logger.error(f"Client IP: {client_ip}")
        logger.error(f"Client ID: {client_id}")
        logger.error(f"Error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        # CRITICAL: Always disconnect and cleanup, even on error
        logger.info(f"=== WEBSOCKET CLEANUP ===")
        logger.info(f"Room ID: {room_id}, Client ID: {client_id}, Connection ID: {connection_id}")
        
        # Only disconnect if connection was successfully established
        if connected:
            try:
                await websocket_handler.disconnect(websocket, room_id)
                logger.info(f"Successfully disconnected client {client_id} from room {room_id}")
            except Exception as disconnect_error:
                logger.error(f"Error during disconnect: {disconnect_error}")
        
        # Always remove DDoS protection tracking
        ddos_protection.remove_connection(client_ip, connection_id)
        logger.info(f"Removed connection tracking for IP: {client_ip}")

@app.post("/api/rooms/{room_id}/info")
async def get_room_info(room_id: str):
    """Get information about a specific room"""
    room_info = websocket_handler.get_room_info(room_id)
    if room_info is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room_info

@app.get("/api/rooms")
async def list_rooms():
    """List all active rooms"""
    return websocket_handler.list_rooms()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
