"""
Semantic Scholar Source Plugin for Webis.
"""

import logging
from typing import Iterator, Optional

import requests

from webis.core.plugin import SourcePlugin
from webis.core.schema import WebisDocument, DocumentType, DocumentMetadata, PipelineContext

logger = logging.getLogger(__name__)


class SemanticScholarPlugin(SourcePlugin):
    """
    Search academic papers on Semantic Scholar.
    """
    
    name = "semantic_scholar"
    description = "Search academic papers on Semantic Scholar"
    
    API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    def fetch(
        self, 
        query: str, 
        limit: int = 10, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Iterator[WebisDocument]:
        
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,abstract,year,authors,url,openAccessPdf"
        }
        
        try:
            resp = requests.get(self.API_URL, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            papers = data.get("data", [])
            
            for paper in papers:
                url = paper.get("url")
                pdf_info = paper.get("openAccessPdf")
                if pdf_info and pdf_info.get("url"):
                    url = pdf_info.get("url")
                    doc_type = DocumentType.PDF
                else:
                    doc_type = DocumentType.HTML
                
                if not url:
                    continue
                    
                yield WebisDocument(
                    content="", # Content to be fetched
                    doc_type=doc_type,
                    meta=DocumentMetadata(
                        url=url,
                        title=paper.get("title"),
                        author=", ".join([a["name"] for a in paper.get("authors", [])]),
                        source_plugin=self.name,
                        custom={
                            "abstract": paper.get("abstract"),
                            "year": paper.get("year")
                        }
                    )
                )
                
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
