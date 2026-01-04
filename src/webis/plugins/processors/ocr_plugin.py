import logging
from typing import Optional, List, Dict, Any
from PIL import Image
import pytesseract
from webis.core.schema import WebisDocument, DocumentType
from webis.core.plugin import ProcessorPlugin, PluginRegistry

logger = logging.getLogger(__name__)

@PluginRegistry.register_processor("ocr_tesseract")
class TesseractOCRPlugin(ProcessorPlugin):
    """
    Extracts text from images using Tesseract OCR.
    """
    
    def initialize(self, context: Any) -> None:
        # Check if tesseract is installed
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            logger.warning(f"Tesseract not found or not working: {e}. OCR will fail.")

    def process(self, doc: WebisDocument, **kwargs) -> WebisDocument:
        """
        Process the document. If it's an image, extract text.
        """
        if doc.doc_type != DocumentType.IMAGE:
            return doc
            
        # Assuming doc.content is a file path to the image for now
        # In a real system, it might be bytes or a URL
        image_path = doc.content
        
        try:
            text = pytesseract.image_to_string(Image.open(image_path))
            
            # Create a new document or update the current one?
            # Usually we want to keep the original image but maybe add text to metadata
            # or return a new text document linked to the image.
            # For simplicity, let's return a new text document.
            
            new_doc = WebisDocument(
                content=text,
                doc_type=DocumentType.TEXT,
                meta=doc.meta.copy()
            )
            new_doc.meta.parent_id = doc.id
            new_doc.meta.processing_history.append({
                "plugin": "ocr_tesseract",
                "original_type": "image"
            })
            
            return new_doc
            
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            return doc

    def process_batch(self, docs: List[WebisDocument], **kwargs) -> List[WebisDocument]:
        """Process a batch of documents."""
        results = []
        for doc in docs:
            results.append(self.process(doc, **kwargs))
        return results
