import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    LOG_LEVEL: str = "INFO"
    FRONTEND_PORT: int = 5173

    # Usenet Settings
    USENET_SERVER: str = "news.newshosting.com"
    USENET_PORT: int = 563
    USENET_SSL: bool = True
    USENET_USERNAME: Optional[str] = None
    USENET_PASSWORD: Optional[str] = None
    USENET_CONNECTIONS: int = 50
    USENET_RETENTION: int = 1500
    USENET_RATE_LIMIT: Optional[int] = None
    USENET_MAX_RETRIES: int = 3
    USENET_MAX_CONNECTIONS: str = "50"
    USENET_RETENTION_DAYS: str = "3000"
    USENET_DOWNLOAD_RATE_LIMIT: str = "0"

    # Media Manager URLs
    SONARR_URL: str = "http://localhost:8989"
    RADARR_URL: str = "http://localhost:7878"
    LIDARR_URL: str = "http://localhost:8686"
    READARR_URL: str = "http://localhost:8787"

    # Download Settings
    DEFAULT_DOWNLOAD_PATH: str = str(Path.cwd() / "downloads")
    TEMP_DOWNLOAD_PATH: str = str(Path.cwd() / "downloads" / "temp")
    COMPLETED_PATH: str = str(Path.cwd() / "downloads" / "completed")
    FAILED_PATH: str = str(Path.cwd() / "downloads" / "failed")
    MAX_CONCURRENT_DOWNLOADS: int = 3

    # Database Settings
    DATABASE_URL: str = "sqlite:///downloads.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields from .env file

settings = Settings()

def save_settings(settings_dict: dict):
    """Save settings to .env file"""
    env_path = ".env"
    env_content = []
    
    # Read existing .env if it exists
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.readlines()
    
    # Update or add settings
    updated_keys = set()
    
    for i, line in enumerate(env_content):
        if '=' in line:
            key = line.split('=')[0].strip()
            if key in settings_dict:
                env_content[i] = f"{key}={settings_dict[key]}\n"
                updated_keys.add(key)
    
    # Add missing keys
    for key, value in settings_dict.items():
        if key not in updated_keys:
            env_content.append(f"{key}={value}\n")
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(env_content)

    # Reload settings
    load_dotenv()
