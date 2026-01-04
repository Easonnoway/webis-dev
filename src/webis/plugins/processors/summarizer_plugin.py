"""
Summarizer Processor Plugin for Webis.
"""

import logging
from typing import Optional, List, Dict

from webis.core.plugin import ProcessorPlugin
from webis.core.schema import WebisDocument, PipelineContext
from webis.core.llm import LLMRouter

logger = logging.getLogger(__name__)


class SummarizerPlugin(ProcessorPlugin):
    """
    Summarize document content using LLM.
    """
    
    name = "summarizer"
    description = "Summarize document content using LLM"
    supported_types = ["html", "pdf", "text"]
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.model_name = self.config.get("model", "gpt-4o-mini")
        self.max_tokens = self.config.get("max_tokens", 500)
        self.prompt_template = self.config.get(
            "prompt", 
            "Please summarize the following text in a concise manner:\n\n{text}"
        )
        
        # Initialize LLM Router
        self.llm = LLMRouter()
        # Add the requested model if it's a builtin one, or assume it's configured elsewhere
        try:
            self.llm.add_model(self.model_name, primary=True)
        except ValueError:
            # If model is not builtin, we might need more config. 
            # For now, let's assume the user will configure the router if using custom models.
            # Or we fallback to a safe default if add_model fails.
            logger.warning(f"Model {self.model_name} not found in builtins. Using gpt-4o-mini as fallback.")
            self.llm.add_model("gpt-4o-mini", primary=True)

    def process(
        self, 
        doc: WebisDocument, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Optional[WebisDocument]:
        
        if not doc.content:
            return doc
            
        # Skip if already summarized
        if doc.meta.custom.get("summary"):
            return doc
            
        # Truncate content if too long (simple truncation for now)
        # In a real app, we'd use token counting
        text = doc.content[:10000] 
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that summarizes web content."},
            {"role": "user", "content": self.prompt_template.format(text=text)}
        ]
        
        try:
            logger.info(f"Summarizing document: {doc.meta.title}")
            response = self.llm.chat(messages)
            doc.meta.custom["summary"] = response.content
            doc.meta.custom["summary_model"] = response.model
        except Exception as e:
            logger.error(f"Summarization failed for {doc.meta.url}: {e}")
            
        return doc
