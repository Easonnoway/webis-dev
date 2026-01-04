"""
Hacker News Source Plugin for Webis.
"""

import logging
from typing import Iterator, Optional

import requests

from webis.core.plugin import SourcePlugin
from webis.core.schema import WebisDocument, DocumentType, DocumentMetadata, PipelineContext

logger = logging.getLogger(__name__)


class HackerNewsPlugin(SourcePlugin):
    """
    Fetch top stories from Hacker News.
    """
    
    name = "hackernews"
    description = "Fetch top stories from Hacker News"
    
    def fetch(
        self, 
        query: str, # Query is ignored for HN top stories, or could be used to filter
        limit: int = 10, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Iterator[WebisDocument]:
        
        try:
            # 1. Get top stories IDs
            resp = requests.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                timeout=20
            )
            resp.raise_for_status()
            ids = resp.json()[:limit]
            
            # 2. Fetch details for each story
            for item_id in ids:
                item_resp = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
                    timeout=10
                )
                if not item_resp.ok:
                    continue
                    
                item = item_resp.json()
                url = item.get("url")
                
                # If no URL (e.g. Ask HN), use the HN item link
                if not url:
                    url = f"https://news.ycombinator.com/item?id={item_id}"
                
                yield WebisDocument(
                    content="", # Content to be fetched by processor
                    doc_type=DocumentType.HTML,
                    meta=DocumentMetadata(
                        url=url,
                        title=item.get("title"),
                        published_at=item.get("time"), # Need conversion
                        source_plugin=self.name,
                        custom={
                            "score": item.get("score"),
                            "by": item.get("by"),
                            "type": item.get("type")
                        }
                    )
                )
                
        except Exception as e:
            logger.error(f"Hacker News fetch failed: {e}")
