"""
HTML Fetcher Processor Plugin for Webis.
"""

import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from webis.core.plugin import ProcessorPlugin
from webis.core.schema import WebisDocument, DocumentType, PipelineContext

logger = logging.getLogger(__name__)


class HtmlFetcherPlugin(ProcessorPlugin):
    """
    Fetches content for documents that have a URL but no content.
    """
    
    name = "html_fetcher"
    description = "Fetch HTML content from URLs"
    supported_types = ["html", "pdf"] # Can fetch both
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.timeout = self.config.get("timeout", 30)
        self.headers = self.config.get("headers", {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def process(
        self, 
        doc: WebisDocument, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Optional[WebisDocument]:
        
        # If content is already present, skip fetching
        if doc.content and len(doc.content) > 100:
            return doc
            
        if not doc.meta.url:
            logger.warning(f"Document {doc.id} has no URL, skipping fetch")
            return doc
            
        try:
            logger.info(f"Fetching URL: {doc.meta.url}")
            resp = requests.get(
                doc.meta.url, 
                headers=self.headers, 
                timeout=self.timeout,
                verify=False # Sometimes needed for scraping, use with caution
            )
            resp.raise_for_status()
            
            # Update content
            doc.content = resp.text
            
            # Update doc type if it was unknown or generic HTML but we got a PDF
            content_type = resp.headers.get("Content-Type", "").lower()
            if "application/pdf" in content_type:
                doc.doc_type = DocumentType.PDF
                # For PDF, content might be binary bytes, but WebisDocument.content is str
                # We might need to handle binary storage or immediate text extraction
                # For now, let's store it as latin-1 decoded string to preserve bytes if needed
                # Or better, just mark it and let a PDF processor handle the download/extraction
                # Re-assigning content to empty and letting PDF processor handle it might be better
                # But for simplicity in this v1, let's assume text-based content mostly.
                pass
            
            doc.add_processing_step(self.name, {"status": "fetched", "status_code": resp.status_code})
            return doc
            
        except Exception as e:
            logger.error(f"Failed to fetch {doc.meta.url}: {e}")
            doc.add_processing_step(self.name, {"status": "failed", "error": str(e)})
            # Return the doc anyway, maybe other processors can handle metadata
            return doc
