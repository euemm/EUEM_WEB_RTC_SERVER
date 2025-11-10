"""
Configuration Management
Handles application configuration using environment variables
"""

from __future__ import annotations

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # WebSocket Configuration
    websocket_timeout: int = 30
    max_connections_per_room: int = 10

    # CORS Configuration
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True

    # Logging Configuration
    log_level: str = "INFO"

    # Database Configuration
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "euem_db"
    db_user: str = "euem"
    db_password: str = ""
    db_pool_min_size: int = 1
    db_pool_max_size: int = 10

    # Security Configuration
    secret_key: str = "your-secret-key-here"
    jwt_secret_key: str = "your-jwt-secret-key-change-this-in-production"
    allowed_rooms: List[str] = Field(default_factory=list)  # Empty means all rooms allowed
    require_https: bool = True

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Health Check
    health_check_interval: int = 30

    # TURN Server Configuration
    turnserver_secret: str = ""
    turnserver_url: str = ""
    turnserver_urls: List[str] = Field(default_factory=list)
    turnserver_ttl: int = 86400  # 24 hours default


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings
