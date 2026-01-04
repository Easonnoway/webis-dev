"""
DuckDuckGo Source Plugin for Webis.
"""

import logging
from typing import Iterator, Optional

from webis.core.plugin import SourcePlugin
from webis.core.schema import WebisDocument, DocumentType, DocumentMetadata, PipelineContext

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

logger = logging.getLogger(__name__)


class DuckDuckGoPlugin(SourcePlugin):
    """
    Search using DuckDuckGo.
    """
    
    name = "duckduckgo"
    description = "Search using DuckDuckGo"
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.region = self.config.get("region", "wt-wt")
        self.safesearch = self.config.get("safesearch", "moderate")
        self.time = self.config.get("time", None)
        self.max_results = self.config.get("max_results", 10)

    def initialize(self, context: Optional[PipelineContext] = None) -> None:
        super().initialize(context)
        if DDGS is None:
            raise ImportError("ddgs package is required. Install with `pip install ddgs`")

    def fetch(
        self, 
        query: str, 
        limit: int = 10, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Iterator[WebisDocument]:
        if not self._initialized:
            self.initialize(context)
            
        logger.info(f"Searching DuckDuckGo for: {query}")
        
        try:
            with DDGS() as ddgs:
                results = ddgs.text(
                    query,
                    region=self.region,
                    safesearch=self.safesearch,
                    timelimit=self.time,
                    max_results=limit
                )
                
                for item in results:
                    yield WebisDocument(
                        content="", # Content to be fetched by processor
                        doc_type=DocumentType.HTML,
                        meta=DocumentMetadata(
                            url=item.get("href"),
                            title=item.get("title"),
                            source_plugin=self.name,
                            custom={"snippet": item.get("body")}
                        )
                    )
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
