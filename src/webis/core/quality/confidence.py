from typing import Dict, Any
from webis.core.schema import WebisDocument

class ConfidenceScorer:
    """
    Evaluates the confidence of extracted data or LLM outputs.
    """
    def calculate_score(self, doc: WebisDocument, extraction_result: Dict[str, Any]) -> float:
        """
        Calculate a confidence score between 0.0 and 1.0.
        """
        score = 1.0
        
        # 1. Check for missing fields
        if not extraction_result:
            return 0.0
            
        # 2. Heuristics: Check for "unknown" or "N/A" values
        null_values = 0
        total_values = 0
        
        def count_values(obj):
            nonlocal null_values, total_values
            if isinstance(obj, dict):
                for v in obj.values():
                    count_values(v)
            elif isinstance(obj, list):
                for v in obj:
                    count_values(v)
            else:
                total_values += 1
                if obj is None or str(obj).lower() in ["n/a", "unknown", "none", ""]:
                    null_values += 1

        count_values(extraction_result)
        
        if total_values > 0:
            completeness = 1.0 - (null_values / total_values)
            score *= completeness
            
        # 3. Source reliability (Mock)
        # if doc.meta.source_plugin == "trusted_source":
        #     score *= 1.0
        # else:
        #     score *= 0.9
            
        return round(score, 2)
