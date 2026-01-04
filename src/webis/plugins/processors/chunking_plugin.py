"""
Chunking Processor Plugin for Webis.
"""

import logging
from typing import Optional, List

from langchain.text_splitter import RecursiveCharacterTextSplitter

from webis.core.plugin import ProcessorPlugin
from webis.core.schema import WebisDocument, PipelineContext, DocumentChunk

logger = logging.getLogger(__name__)


class ChunkingPlugin(ProcessorPlugin):
    """
    Split document content into smaller chunks.
    """
    
    name = "chunker"
    description = "Split text into chunks"
    supported_types = ["text", "html", "pdf"]
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.chunk_size = self.config.get("chunk_size", 1000)
        self.chunk_overlap = self.config.get("chunk_overlap", 200)
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )

    def process(
        self, 
        doc: WebisDocument, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Optional[WebisDocument]:
        
        content = doc.clean_content or doc.content
        if not content:
            return doc
            
        text_chunks = self.splitter.split_text(content)
        
        doc.chunks = [
            DocumentChunk(
                content=chunk,
                index=i,
                metadata={"source_doc_id": doc.id}
            )
            for i, chunk in enumerate(text_chunks)
        ]
        
        doc.add_processing_step(self.name, {"chunk_count": len(doc.chunks)})
        
        return doc
