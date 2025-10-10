"""
Configuration Management
Handles application configuration using environment variables
"""

import os
from typing import List
from pydantic import Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # WebSocket Configuration
    websocket_timeout: int = Field(default=30, env="WEBSOCKET_TIMEOUT")
    max_connections_per_room: int = Field(default=10, env="MAX_CONNECTIONS_PER_ROOM")
    
    # CORS Configuration
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Security Configuration
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    jwt_secret_key: str = Field(default="your-jwt-secret-key-change-this-in-production", env="JWT_SECRET_KEY")
    allowed_rooms: List[str] = Field(default_factory=list)  # Empty means all rooms allowed
    require_https: bool = Field(default=True, env="REQUIRE_HTTPS")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Health Check
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # TURN Server Configuration
    turnserver_secret: str = Field(default="", env="TURNSERVER_SECRET")
    turnserver_url: str = Field(default="", env="TURNSERVER_URL")
    turnserver_urls: List[str] = Field(default_factory=list)
    turnserver_ttl: int = Field(default=86400, env="TURNSERVER_TTL")  # 24 hours default
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
_settings: Settings = None

def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reload_settings():
    """Reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings
