import os
import json
from typing import Dict, Any

class Config:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        # Try to load from environment variable first
        config_json = os.getenv('APP_CONFIG')
        if config_json:
            try:
                return json.loads(config_json)
            except json.JSONDecodeError:
                pass

        # Then try to load from config file
        config_paths = [
            os.path.join(os.getcwd(), 'config.json'),
            '/etc/media-downloader/config.json',
            os.path.expanduser('~/.config/media-downloader/config.json')
        ]

        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    continue

        # Return default config if no config found
        return {
            "usenet": {
                "host": "news.newshosting.com",
                "port": 563,
                "ssl": True,
                "username": None,
                "password": None,
                "connections": 50,
                "retention": 1500
            },
            "downloads": {
                "path": "./downloads",
                "temp_path": "./downloads/temp",
                "completed_path": "./downloads/completed",
                "failed_path": "./downloads/failed"
            },
            "web": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 1
            },
            "database": {
                "url": "sqlite:///downloads.db"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by key"""
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a config value"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

# Create global config instance
config = Config()
