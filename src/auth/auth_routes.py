"""
Authentication Routes
Handles login, token refresh, and user management endpoints
"""

import hmac
import hashlib
import base64
import time
from datetime import timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from .jwt_handler import user_manager, jwt_handler, get_current_user, User
from ..utils.config import get_settings

router = APIRouter(prefix="/auth", tags=["authentication"])

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserResponse(BaseModel):
    username: str
    email: str
    is_active: bool

class LoginRequest(BaseModel):
    username: str
    password: str

class TurnCredentials(BaseModel):
    username: str
    credential: str
    urls: List[str]
    ttl: int

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """Authenticate user and return JWT token"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"=== AUTH LOGIN ATTEMPT ===")
    logger.info(f"Username: {login_data.username}")
    logger.info(f"Password length: {len(login_data.password) if login_data.password else 0}")
    
    try:
        logger.info("Calling user_manager.authenticate_user()")
        user = user_manager.authenticate_user(login_data.username, login_data.password)
        logger.info(f"Authentication result: {user is not None}")
        
        if not user:
            logger.warning(f"Authentication failed for user: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Authentication successful for user: {user.username}")
        logger.info("Creating access token")
        
        access_token_expires = timedelta(minutes=30)
        access_token = jwt_handler.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        logger.info("Access token created successfully")
        logger.info(f"=== AUTH LOGIN SUCCESS ===")
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        logger.error(f"=== AUTH LOGIN ERROR ===")
        logger.error(f"Error during authentication: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token endpoint"""
    user = user_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = jwt_handler.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active
    )

@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh JWT token"""
    access_token_expires = timedelta(minutes=30)
    access_token = jwt_handler.create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    """Logout endpoint (client should discard token)"""
    return {"message": "Successfully logged out"}

@router.get("/turn-credentials", response_model=TurnCredentials)
async def get_turn_credentials(current_user: User = Depends(get_current_user)):
    """
    Generate time-limited TURN server credentials for authenticated users.
    
    Uses HMAC-SHA1 algorithm with the TURNSERVER_SECRET to generate credentials.
    The username format is: timestamp:username
    The credential is: base64(hmac-sha1(secret, username))
    
    These credentials are compatible with coturn TURN server.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    settings = get_settings()
    
    # Check if TURN server is configured
    if not settings.turnserver_secret:
        logger.error("TURN server secret not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TURN server not configured"
        )
    
    if not settings.turnserver_urls and not settings.turnserver_url:
        logger.error("TURN server URLs not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TURN server URLs not configured"
        )
    
    try:
        # Calculate expiration timestamp
        ttl = settings.turnserver_ttl
        timestamp = int(time.time()) + ttl
        
        # Create username in format: timestamp:username
        turn_username = f"{timestamp}:{current_user.username}"
        
        # Generate password using HMAC-SHA1
        secret_bytes = settings.turnserver_secret.encode('utf-8')
        username_bytes = turn_username.encode('utf-8')
        
        hmac_hash = hmac.new(secret_bytes, username_bytes, hashlib.sha1)
        turn_password = base64.b64encode(hmac_hash.digest()).decode('utf-8')
        
        # Get TURN server URLs
        turn_urls = settings.turnserver_urls if settings.turnserver_urls else [settings.turnserver_url]
        
        logger.info(f"Generated TURN credentials for user: {current_user.username}")
        logger.debug(f"TURN username: {turn_username}")
        logger.debug(f"TURN URLs: {turn_urls}")
        
        return TurnCredentials(
            username=turn_username,
            credential=turn_password,
            urls=turn_urls,
            ttl=ttl
        )
        
    except Exception as e:
        logger.error(f"Error generating TURN credentials: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate TURN credentials"
        )
