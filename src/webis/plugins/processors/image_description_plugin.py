import logging
from typing import List, Any
from webis.core.schema import WebisDocument, DocumentType
from webis.core.plugin import ProcessorPlugin, PluginRegistry
from webis.core.llm import get_default_router, ModelConfig

logger = logging.getLogger(__name__)

@PluginRegistry.register_processor("image_description")
class ImageDescriptionPlugin(ProcessorPlugin):
    """
    Generates descriptions for images using a Vision LLM.
    """
    
    def initialize(self, context: Any) -> None:
        self.router = get_default_router()

    def process(self, doc: WebisDocument, **kwargs) -> WebisDocument:
        if doc.doc_type != DocumentType.IMAGE:
            return doc
            
        image_url = doc.meta.url or doc.content # Assuming content is URL or path
        
        # Construct message for Vision model
        # Note: This assumes the LLM provider supports image URLs in this format
        # OpenAI format: content: [{"type": "text", "text": ...}, {"type": "image_url", "image_url": {"url": ...}}]
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in detail."},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        
        try:
            # Use a vision-capable model
            # We need to ensure the router has one. 
            # For now, let's assume 'gpt-4o' or 'claude-sonnet' is configured.
            response = self.router.chat(messages, model="gpt-4o")
            
            description = response.content
            
            # Update metadata with description
            doc.meta.meta_custom["description"] = description
            doc.meta.processing_history.append({
                "plugin": "image_description",
                "model": response.model
            })
            
            return doc
            
        except Exception as e:
            logger.error(f"Image description failed: {e}")
            return doc

    def process_batch(self, docs: List[WebisDocument], **kwargs) -> List[WebisDocument]:
        results = []
        for doc in docs:
            results.append(self.process(doc, **kwargs))
        return results
