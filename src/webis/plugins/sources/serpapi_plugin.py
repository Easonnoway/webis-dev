"""
SerpApi Source Plugin for Webis.
"""

import logging
import os
from typing import Iterator, Optional

import requests

from webis.core.plugin import SourcePlugin
from webis.core.schema import WebisDocument, DocumentType, DocumentMetadata, PipelineContext

logger = logging.getLogger(__name__)


class SerpApiPlugin(SourcePlugin):
    """
    Search using SerpApi (Google, Bing, etc.).
    """
    
    name = "serpapi"
    description = "Search using SerpApi"
    required_env_vars = ["SERPAPI_API_KEY"]
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.engine = self.config.get("engine", "google")
        self.api_key = os.environ.get("SERPAPI_API_KEY")

    def fetch(
        self, 
        query: str, 
        limit: int = 10, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Iterator[WebisDocument]:
        
        if not self.api_key:
            logger.error("Missing SERPAPI_API_KEY")
            return
            
        params = {
            "engine": self.engine,
            "q": query,
            "api_key": self.api_key,
            "num": limit
        }
        
        try:
            resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            organic_results = data.get("organic_results", [])
            
            for item in organic_results:
                yield WebisDocument(
                    content="", # Content to be fetched
                    doc_type=DocumentType.HTML,
                    meta=DocumentMetadata(
                        url=item.get("link"),
                        title=item.get("title"),
                        source_plugin=self.name,
                        custom={
                            "snippet": item.get("snippet"),
                            "position": item.get("position")
                        }
                    )
                )
                
        except Exception as e:
            logger.error(f"SerpApi search failed: {e}")
