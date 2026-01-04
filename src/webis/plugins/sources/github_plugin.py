"""
GitHub Source Plugin for Webis.
"""

import logging
import os
from typing import Iterator, Optional

import requests

from webis.core.plugin import SourcePlugin
from webis.core.schema import WebisDocument, DocumentType, DocumentMetadata, PipelineContext

logger = logging.getLogger(__name__)


class GitHubSearchPlugin(SourcePlugin):
    """
    Search GitHub repositories.
    """
    
    name = "github"
    description = "Search GitHub repositories"
    
    def fetch(
        self, 
        query: str, 
        limit: int = 10, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Iterator[WebisDocument]:
        
        url = "https://api.github.com/search/repositories"
        params = {"q": query, "per_page": limit}
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        # Optional: Use GITHUB_TOKEN if available to avoid rate limits
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
            
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=20)
            resp.raise_for_status()
            items = resp.json().get("items", [])
            
            for repo in items:
                yield WebisDocument(
                    content="", # Content (README/Page) to be fetched by processor
                    doc_type=DocumentType.HTML,
                    meta=DocumentMetadata(
                        url=repo.get("html_url"),
                        title=repo.get("full_name"),
                        source_plugin=self.name,
                        custom={
                            "description": repo.get("description"),
                            "stars": repo.get("stargazers_count"),
                            "language": repo.get("language")
                        }
                    )
                )
                
        except Exception as e:
            logger.error(f"GitHub search failed: {e}")
