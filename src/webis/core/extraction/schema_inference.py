from typing import List, Dict, Any
import json
from webis.core.llm.base import LLMFactory

class SchemaInferencer:
    """
    Infers JSON schema from sample data.
    """
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.llm = LLMFactory.create_llm(model_name)

    def infer(self, samples: List[str]) -> Dict[str, Any]:
        samples_text = "\n---\n".join(samples[:3]) # Use first 3 samples
        prompt = f"""
        You are a data engineer. Infer a JSON Schema that describes the structure of the information in the following text samples.
        The schema should be robust and cover the common fields found in the samples.
        Return ONLY the JSON Schema.

        Samples:
        {samples_text}
        """
        
        response = self.llm.generate(prompt)
        
        import re
        try:
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
            
        return {}
