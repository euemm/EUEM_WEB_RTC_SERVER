"""
Authentication Routes
Handles login, token refresh, and user management endpoints
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from .jwt_handler import user_manager, jwt_handler, get_current_user, User

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
