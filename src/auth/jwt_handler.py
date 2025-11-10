"""
JWT Authentication Handler
Handles JWT token creation, validation, and user authentication
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..utils.db import get_db_pool

# Password hashing (bcrypt cost factor 10)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__default_rounds=10)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security scheme
security = HTTPBearer()

logger = logging.getLogger(__name__)


class User:
    """User model for authentication"""

    def __init__(
        self,
        user_id: str,
        email: str,
        hashed_password: str,
        is_verified: bool,
        is_enabled: bool,
    ) -> None:
        self.id = user_id
        self.email = email
        self.username = email  # maintain backwards compatibility with existing code
        self.hashed_password = hashed_password
        self.is_verified = is_verified
        self.is_enabled = is_enabled

    @property
    def is_active(self) -> bool:
        return self.is_enabled and self.is_verified


class UserManager:
    """Manages user data from PostgreSQL"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    async def get_user(self, email: str) -> Optional[User]:
        """Fetch a user by email from the database."""
        pool = await get_db_pool()
        query = """
            SELECT id, email::text AS email, password, is_verified, is_enabled
            FROM users
            WHERE email = $1
        """
        row = await pool.fetchrow(query, email)
        if row is None:
            return None
        return User(
            user_id=str(row["id"]),
            email=row["email"],
            hashed_password=row["password"],
            is_verified=row["is_verified"],
            is_enabled=row["is_enabled"],
        )

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against stored bcrypt hash."""
        self.logger.info("=== PASSWORD VERIFICATION ===")
        self.logger.info("Plain password length: %s", len(plain_password))
        self.logger.info("Hashed password starts with: %s", hashed_password[:20])
        return pwd_context.verify(plain_password, hashed_password)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials against the database."""
        self.logger.info("=== USER AUTHENTICATION ===")
        self.logger.info("Looking up user: %s", email)

        user = await self.get_user(email)
        self.logger.info("User found: %s", user is not None)

        if user is None:
            self.logger.warning("User not found: %s", email)
            return None

        if not user.is_enabled:
            self.logger.warning("User disabled: %s", email)
            return None

        if not user.is_verified:
            self.logger.warning("User not verified: %s", email)
            return None

        self.logger.info("User is active, verifying password for: %s", email)
        if not await self.verify_password(password, user.hashed_password):
            self.logger.warning("Password verification failed for: %s", email)
            return None

        self.logger.info("Authentication successful for: %s", email)
        return user


class JWTHandler:
    """Handles JWT token operations"""

    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return payload
        except JWTError:
            return None

    async def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> User:
        """Get current authenticated user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            token = credentials.credentials
            payload = self.verify_token(token)
            if payload is None:
                raise credentials_exception

            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception

        except JWTError:
            raise credentials_exception

        user = await self.user_manager.get_user(email=username)
        if user is None or not user.is_active:
            raise credentials_exception

        return user


# Global instances
user_manager = UserManager()
jwt_handler = JWTHandler(user_manager)


# Dependency for getting current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """FastAPI dependency to get current authenticated user"""
    return await jwt_handler.get_current_user(credentials)
