from typing import Any, Dict, List, Optional
from webis.core.pipeline import PipelineContext
from webis.core.plugin import ProcessorPlugin
from webis.core.schema import WebisDocument
from webis.core.llm.base import LLMFactory

class SentimentAnalysisPlugin(ProcessorPlugin):
    """
    Analyzes sentiment of the document content.
    """
    name = "sentiment_analysis"
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.llm = LLMFactory.create_llm(model_name)

    def process(self, doc: WebisDocument, context: Optional[PipelineContext] = None, **kwargs) -> WebisDocument:
        content = doc.clean_content or doc.content
        content = content[:1000]
        
        prompt = f"""
        Analyze the sentiment of the following text.
        Return a JSON object with:
        - "polarity": "positive", "negative", or "neutral"
        - "score": a float between -1.0 (negative) and 1.0 (positive)
        - "explanation": brief reason
        
        Text:
        {content}
        """
        
        try:
            response = self.llm.generate(prompt)
            import json
            import re
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                sentiment = json.loads(match.group(0))
                doc.meta.custom["sentiment"] = sentiment
        except Exception as e:
            print(f"Sentiment analysis failed: {e}")
            
        return doc
