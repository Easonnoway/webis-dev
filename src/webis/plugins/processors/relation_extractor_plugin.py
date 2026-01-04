from typing import Any, Dict, List, Optional
import json
from webis.core.pipeline import PipelineContext
from webis.core.plugin import ExtractorPlugin
from webis.core.schema import WebisDocument, StructuredResult, Lineage
from webis.core.llm.base import LLMFactory

class RelationExtractorPlugin(ExtractorPlugin):
    """
    Extracts entity relations (Subject -> Relation -> Object) from documents.
    """
    name = "relation_extractor"
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.llm = LLMFactory.create_llm(model_name)

    def extract(
        self,
        docs: List[WebisDocument],
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> StructuredResult:
        
        all_relations = []
        
        for doc in docs:
            content = doc.clean_content or doc.content
            # Limit content length for demo
            content = content[:2000]
            
            prompt = f"""
            Extract relationships from the following text.
            Return a JSON list of objects with 'subject', 'relation', and 'object' fields.
            
            Text:
            {content}
            
            Output:
            """
            
            try:
                response = self.llm.generate(prompt)
                # Simple JSON parsing
                import re
                match = re.search(r"\[.*\]", response, re.DOTALL)
                if match:
                    relations = json.loads(match.group(0))
                    for r in relations:
                        r["source_doc_id"] = doc.id
                    all_relations.extend(relations)
            except Exception as e:
                print(f"Relation extraction failed for doc {doc.id}: {e}")

        return StructuredResult(
            schema_id="relation_triples",
            data=all_relations,
            lineage=Lineage(
                source_doc_ids=[d.id for d in docs],
                model_name=self.llm.model_name
            )
        )
