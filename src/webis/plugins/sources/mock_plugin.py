from typing import Any, Dict, Iterator, List, Optional
from webis.core.plugin import SourcePlugin
from webis.core.schema import WebisDocument, DocumentType, DocumentMetadata

class MockSourcePlugin(SourcePlugin):
    """
    Mock source plugin for testing and development.
    Returns predefined documents.
    """
    name = "mock_source"
    
    def __init__(self, documents: List[Dict[str, Any]] = None):
        self.documents = documents or []

    def initialize(self, context):
        # Load from config if not provided in init
        if not self.documents:
            self.documents = context.config.get("mock_documents", [])

    def fetch(self, query: str, **kwargs) -> Iterator[WebisDocument]:
        count = 0
        limit = kwargs.get("limit", 10)
        
        for doc_data in self.documents:
            if count >= limit:
                break
                
            content = doc_data.get("content", "Mock content")
            if query.lower() in content.lower() or query == "*":
                yield WebisDocument(
                    content=content,
                    doc_type=DocumentType(doc_data.get("type", "text")),
                    meta=DocumentMetadata(
                        url=doc_data.get("url", "http://mock.local"),
                        title=doc_data.get("title", "Mock Document"),
                        source_plugin=self.name
                    )
                )
                count += 1
