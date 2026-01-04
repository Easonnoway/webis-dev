"""
Configuration management for Webis.
"""

import os
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel

class WebisConfig(BaseModel):
    """Global configuration schema."""
    env: str = "development"
    log_level: str = "INFO"
    
    # Database
    database_url: str = "sqlite:///webis.db"
    
    # Vector Store
    vector_store_path: str = "./chroma_db"
    
    # API Keys (loaded from env usually, but can be in config)
    openai_api_key: Optional[str] = None
    serpapi_api_key: Optional[str] = None
    
    # Pipeline defaults
    default_timeout: int = 30
    max_retries: int = 3

class ConfigManager:
    """
    Singleton configuration manager.
    """
    _instance = None
    _config: WebisConfig = WebisConfig()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        # 1. Load from default config.yaml if exists
        config_path = os.environ.get("WEBIS_CONFIG", "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)
                # Update _config with data
                # This is a simplified loading, in production use Dynaconf
                pass
        
        # 2. Override with env vars
        if os.environ.get("WEBIS_ENV"):
            self._config.env = os.environ["WEBIS_ENV"]
            
    @property
    def config(self) -> WebisConfig:
        return self._config

settings = ConfigManager().config
