from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from webis.core.memory.vector_store import VectorStore

class SearchResult(BaseModel):
    document_id: str
    content: str
    metadata: Dict[str, Any]
    score: float

class HybridRetriever:
    """
    Retriever that combines vector search with metadata filtering.
    """
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def search(
        self, 
        query: str, 
        top_k: int = 5, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Perform a search with vector similarity and metadata filtering.
        
        Args:
            query: The search query text.
            top_k: Number of results to return.
            filters: Metadata filters (e.g., {"source_plugin": "google", "author": "John"}).
        """
        # Construct ChromaDB where clause
        where_clause = filters if filters else None
        
        results = self.vector_store.query(
            query_text=query,
            n_results=top_k,
            where=where_clause
        )
        
        search_results = []
        if results and results['ids']:
            # ChromaDB returns lists of lists for queries
            ids = results['ids'][0]
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            
            for i in range(len(ids)):
                # Convert distance to similarity score (approx)
                # ChromaDB default is L2 distance, lower is better. 
                # We can just return distance or try to invert it.
                # For now, let's just return the distance as score (or 1/(1+d))
                score = 1.0 / (1.0 + distances[i]) if distances[i] is not None else 0.0
                
                search_results.append(SearchResult(
                    document_id=ids[i],
                    content=documents[i] if documents[i] else "",
                    metadata=metadatas[i] if metadatas and metadatas[i] else {},
                    score=score
                ))
                
        return search_results
