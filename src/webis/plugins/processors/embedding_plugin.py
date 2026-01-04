"""
Embedding Processor Plugin for Webis.
"""

import logging
import os
from typing import Optional

from langchain_openai import OpenAIEmbeddings

from webis.core.plugin import ProcessorPlugin
from webis.core.schema import WebisDocument, PipelineContext

logger = logging.getLogger(__name__)


class EmbeddingPlugin(ProcessorPlugin):
    """
    Generate embeddings for document chunks.
    """
    
    name = "embedder"
    description = "Generate embeddings for chunks"
    supported_types = ["text", "html", "pdf"]
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.model = self.config.get("model", "text-embedding-3-small")
        self.api_key = self.config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found, embedding will fail")
            
        self.embeddings = OpenAIEmbeddings(
            model=self.model,
            api_key=self.api_key
        )

    def process(
        self, 
        doc: WebisDocument, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Optional[WebisDocument]:
        
        if not doc.chunks:
            logger.warning(f"Document {doc.id} has no chunks to embed")
            return doc
            
        texts = [chunk.content for chunk in doc.chunks]
        
        try:
            vectors = self.embeddings.embed_documents(texts)
            
            for chunk, vector in zip(doc.chunks, vectors):
                chunk.embedding = vector
                
            doc.add_processing_step(self.name, {"model": self.model})
            
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            
        return doc
