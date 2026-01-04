import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SecretManager:
    """
    Manages access to sensitive information like API keys.
    Supports reading from environment variables, .env files, and potentially external vaults.
    """
    def __init__(self):
        self._load_dotenv()

    def _load_dotenv(self):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            logger.warning("python-dotenv not installed. Skipping .env loading.")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret by key.
        """
        # 1. Try Environment Variable
        value = os.getenv(key)
        if value is not None:
            return value
        
        # 2. Try Docker Secret (common pattern: /run/secrets/<key>)
        docker_secret_path = f"/run/secrets/{key}"
        if os.path.exists(docker_secret_path):
            try:
                with open(docker_secret_path, "r") as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning(f"Failed to read Docker secret {key}: {e}")

        # 3. Return default
        return default

    def require(self, key: str) -> str:
        """
        Retrieve a secret or raise an error if missing.
        """
        value = self.get(key)
        if value is None:
            raise ValueError(f"Missing required secret: {key}")
        return value

# Global instance
secrets = SecretManager()
