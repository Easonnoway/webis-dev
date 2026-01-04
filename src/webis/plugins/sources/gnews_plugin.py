"""
GNews Source Plugin for Webis.
"""

import logging
from typing import Iterator, Optional

from webis.core.plugin import SourcePlugin
from webis.core.schema import WebisDocument, DocumentType, DocumentMetadata, PipelineContext

try:
    from gnews import GNews
except ImportError:
    GNews = None

logger = logging.getLogger(__name__)


class GNewsPlugin(SourcePlugin):
    """
    Fetch news articles using GNews (Google News).
    """
    
    name = "gnews"
    description = "Search Google News for articles"
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.language = self.config.get("language", "en")
        self.country = self.config.get("country", "US")
        self.period = self.config.get("period", "7d")
        self.max_results = self.config.get("max_results", 10)
        self.exclude_websites = self.config.get("exclude_websites", [])
        
        self._client = None

    def initialize(self, context: Optional[PipelineContext] = None) -> None:
        super().initialize(context)
        if GNews is None:
            raise ImportError("gnews package is required. Install with `pip install gnews`")
        
        self._client = GNews(
            language=self.language,
            country=self.country,
            period=self.period,
            max_results=self.max_results,
            exclude_websites=self.exclude_websites
        )

    def fetch(
        self, 
        query: str, 
        limit: int = 10, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Iterator[WebisDocument]:
        if not self._initialized:
            self.initialize(context)
            
        logger.info(f"Searching GNews for: {query}")
        
        # GNews.get_news returns a list of dicts
        # [{'title': ..., 'description': ..., 'published date': ..., 'url': ..., 'publisher': ...}]
        try:
            results = self._client.get_news(query)
        except Exception as e:
            logger.error(f"GNews search failed: {e}")
            return

        count = 0
        for item in results:
            if count >= limit:
                break
            
            url = item.get("url")
            if not url:
                continue
                
            # GNews tool usually just gives metadata, we might need to fetch full content
            # But for now, let's create a document with what we have.
            # Ideally, a separate "Downloader" processor would fetch the full HTML.
            # Or we can use GNews.get_full_article if configured.
            
            # For this v1 migration, let's assume we just pass the URL and metadata
            # and let a downstream processor handle the fetching if content is empty.
            
            # However, the original GNewsTool might have fetched content. 
            # Let's check the original implementation if needed. 
            # But for a "Source Plugin", returning the URL and metadata is often enough 
            # if we have a "Fetcher" processor. 
            # To be safe and useful, let's try to get the full article if possible, 
            # or just return the metadata.
            
            # Let's stick to the "Source" responsibility: finding the resource.
            
            yield WebisDocument(
                content="", # Content to be fetched by a processor
                doc_type=DocumentType.HTML,
                meta=DocumentMetadata(
                    url=url,
                    title=item.get("title"),
                    published_at=item.get("published date"), # Need parsing
                    source_plugin=self.name,
                    custom={
                        "publisher": item.get("publisher"),
                        "description": item.get("description")
                    }
                )
            )
            count += 1

