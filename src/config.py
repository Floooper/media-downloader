import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Media Downloader"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_CORS_ORIGINS: list = ["*"]
    API_RATE_LIMIT: int = 100  # requests per minute
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./data/media_downloader.db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False
    
    # Download settings
    DOWNLOAD_PATH: str = "./downloads"
    MAX_CONCURRENT_DOWNLOADS: int = 3
    CHUNK_SIZE: int = 8192
    AUTO_EXTRACT: bool = True
    
    # Usenet settings
    USENET_SERVER: Optional[str] = None
    USENET_PORT: int = 119
    USENET_SSL: bool = False
    USENET_USERNAME: Optional[str] = None
    USENET_PASSWORD: Optional[str] = None
    USENET_MAX_CONNECTIONS: int = 10
    USENET_RETENTION_DAYS: int = 1500
    USENET_DOWNLOAD_RATE_LIMIT: Optional[int] = None
    USENET_MAX_RETRIES: int = 3
    
    # Torrent settings
    ENABLE_TORRENTS: bool = True
    TORRENT_PORT: int = 6881
    TORRENT_MAX_CONNECTIONS: int = 50
    TORRENT_UPLOAD_RATE_LIMIT: int = 0  # 0 for unlimited
    TORRENT_DOWNLOAD_RATE_LIMIT: int = 0  # 0 for unlimited
    
    # Media manager settings
    SONARR_URL: Optional[str] = None
    SONARR_API_KEY: Optional[str] = None
    RADARR_URL: Optional[str] = None
    RADARR_API_KEY: Optional[str] = None
    READARR_URL: Optional[str] = None
    READARR_API_KEY: Optional[str] = None
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # WebSocket settings
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100
    WS_MESSAGE_QUEUE_SIZE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Global settings instance
settings = get_settings()

# Initialize logging configuration
import logging
import logging.config

def setup_logging():
    """Configure logging based on settings"""
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.LOG_FORMAT
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": settings.LOG_LEVEL
            }
        },
        "root": {
            "handlers": ["console"],
            "level": settings.LOG_LEVEL
        }
    }
    
    # Add file handler if LOG_FILE is specified
    if settings.LOG_FILE:
        os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "filename": settings.LOG_FILE,
            "formatter": "default",
            "level": settings.LOG_LEVEL
        }
        config["root"]["handlers"].append("file")
    
    logging.config.dictConfig(config)

# Setup logging when module is imported
setup_logging()
