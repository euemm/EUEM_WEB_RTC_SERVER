"""
JWT Authentication Handler
Handles JWT token creation, validation, and user authentication
"""

import os
import csv
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security scheme
security = HTTPBearer()

class User:
    """User model for authentication"""
    def __init__(self, username: str, email: str, hashed_password: str, is_active: bool = True):
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active

class UserManager:
    """Manages user data from CSV file"""
    
    def __init__(self, csv_file: str = "users.csv"):
        self.csv_file = csv_file
        self.users: Dict[str, User] = {}
        self.load_users()
    
    def load_users(self):
        """Load users from CSV file"""
        if not os.path.exists(self.csv_file):
            # Create default users file
            self.create_default_users()
        
        with open(self.csv_file, 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                user = User(
                    username=row['username'],
                    email=row['email'],
                    hashed_password=row['hashed_password'],
                    is_active=row.get('is_active', 'true').lower() == 'true'
                )
                self.users[user.username] = user
    
    def create_default_users(self):
        """Create default users.csv file"""
        try:
            default_users = [
                {
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'hashed_password': pwd_context.hash('admin123'),
                    'is_active': 'true'
                },
                {
                    'username': 'user1',
                    'email': 'user1@example.com',
                    'hashed_password': pwd_context.hash('password123'),
                    'is_active': 'true'
                },
                {
                    'username': 'user2',
                    'email': 'user2@example.com',
                    'hashed_password': pwd_context.hash('password123'),
                    'is_active': 'true'
                }
            ]
        except Exception as e:
            print(f"Error creating password hashes: {e}")
            print("Falling back to simple hash for development...")
            # Fallback to simple hash for development
            import hashlib
            def simple_hash(password):
                return hashlib.sha256(password.encode()).hexdigest()
            
            default_users = [
                {
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'hashed_password': simple_hash('admin123'),
                    'is_active': 'true'
                },
                {
                    'username': 'user1',
                    'email': 'user1@example.com',
                    'hashed_password': simple_hash('password123'),
                    'is_active': 'true'
                },
                {
                    'username': 'user2',
                    'email': 'user2@example.com',
                    'hashed_password': simple_hash('password123'),
                    'is_active': 'true'
                }
            ]
        
        with open(self.csv_file, 'w', newline='') as file:
            fieldnames = ['username', 'email', 'hashed_password', 'is_active']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(default_users)
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.users.get(username)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== PASSWORD VERIFICATION ===")
        logger.info(f"Plain password length: {len(plain_password)}")
        logger.info(f"Hashed password length: {len(hashed_password)}")
        logger.info(f"Hashed password starts with: {hashed_password[:20]}...")
        
        try:
            logger.info("Attempting bcrypt verification")
            result = pwd_context.verify(plain_password, hashed_password)
            logger.info(f"Bcrypt verification result: {result}")
            return result
        except Exception as e:
            logger.warning(f"Bcrypt verification failed: {e}")
            logger.info("Falling back to simple hash verification")
            # Fallback for simple hash (development only)
            import hashlib
            simple_hash = hashlib.sha256(plain_password.encode()).hexdigest()
            result = simple_hash == hashed_password
            logger.info(f"Simple hash verification result: {result}")
            return result
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== USER AUTHENTICATION ===")
        logger.info(f"Looking up user: {username}")
        
        user = self.get_user(username)
        logger.info(f"User found: {user is not None}")
        
        if not user:
            logger.warning(f"User not found: {username}")
            return None
            
        if not user.is_active:
            logger.warning(f"User inactive: {username}")
            return None
            
        logger.info(f"User is active, verifying password for: {username}")
        if not self.verify_password(password, user.hashed_password):
            logger.warning(f"Password verification failed for: {username}")
            return None
            
        logger.info(f"Authentication successful for: {username}")
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
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
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
        
        user = self.user_manager.get_user(username=username)
        if user is None or not user.is_active:
            raise credentials_exception
            
        return user

# Global instances
user_manager = UserManager()
jwt_handler = JWTHandler(user_manager)

# Dependency for getting current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """FastAPI dependency to get current authenticated user"""
    return jwt_handler.get_current_user(credentials)
