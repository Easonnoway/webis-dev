"""
Vector Store abstraction for Webis.
"""

import logging
import os
from typing import List, Optional, Dict, Any

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Wrapper for Vector Database (ChromaDB).
    """
    
    def __init__(self, collection_name: str = "webis_docs", persist_dir: str = "./chroma_db"):
        if chromadb is None:
            raise ImportError("chromadb is required. Install with `pip install chromadb`")
            
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
    def add_documents(
        self, 
        ids: List[str], 
        documents: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None
    ):
        """
        Add documents to the vector store.
        """
        if not ids or not documents:
            return
            
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        logger.info(f"Added {len(ids)} documents to vector store")
        
    def query(
        self, 
        query_text: str, 
        n_results: int = 5, 
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query the vector store.
        """
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
