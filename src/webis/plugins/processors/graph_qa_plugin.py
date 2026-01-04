from typing import Any, Dict, List
from webis.core.plugin import ProcessorPlugin
from webis.core.schema import WebisDocument, PipelineContext
from webis.core.memory.graph_store import GraphStore

class GraphQAPlugin(ProcessorPlugin):
    """
    Performs Question Answering using the Knowledge Graph.
    """
    name = "graph_qa"

    def __init__(self, graph_store: GraphStore):
        self.graph_store = graph_store

    def process(self, doc: WebisDocument, context: PipelineContext) -> WebisDocument:
        # This plugin doesn't transform the document content directly,
        # but it might attach QA results to metadata or be used as a standalone tool.
        # Here we assume the document content IS the question.
        
        question = doc.content
        
        # 1. Entity Linking (Mock)
        # Extract entities from question to find starting nodes in graph
        entities = self._extract_entities(question)
        
        # 2. Subgraph Retrieval
        # Get neighbors of these entities
        context_triples = []
        for entity in entities:
            # This is a simplified query
            query = f"MATCH (n)-[r]-(m) WHERE n.name = '{entity}' RETURN n, r, m LIMIT 10"
            results = self.graph_store.query(query)
            context_triples.extend(results)
            
        # 3. Answer Generation (Mock)
        # In a real system, we'd pass context_triples + question to an LLM
        answer = f"Based on the graph context {context_triples}, the answer to '{question}' is..."
        
        doc.meta.extra["graph_qa_answer"] = answer
        doc.meta.extra["graph_context"] = context_triples
        
        return doc

    def _extract_entities(self, text: str) -> List[str]:
        # Mock entity extraction
        # In reality, use an NER model or LLM
        return [word for word in text.split() if word[0].isupper()]
