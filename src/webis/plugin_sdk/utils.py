import logging
import requests
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_logger(name: str) -> logging.Logger:
    """
    Get a standardized logger for plugins.
    """
    logger = logging.getLogger(f"webis.plugins.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

class HttpClient:
    """
    A robust HTTP client for plugins with built-in retries and timeout defaults.
    """
    def __init__(self, 
                 retries: int = 3, 
                 backoff_factor: float = 0.3, 
                 timeout: int = 30,
                 headers: Optional[Dict[str, str]] = None):
        self.timeout = timeout
        self.session = requests.Session()
        
        if headers:
            self.session.headers.update(headers)
            
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        return self.session.post(url, **kwargs)
