"""
HTML Cleaner Processor Plugin for Webis.
"""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from webis.core.plugin import ProcessorPlugin
from webis.core.schema import WebisDocument, DocumentType, PipelineContext

logger = logging.getLogger(__name__)


class HtmlCleanerPlugin(ProcessorPlugin):
    """
    Extracts clean text from HTML content.
    """
    
    name = "html_cleaner"
    description = "Extract clean text from HTML"
    supported_types = ["html"]
    
    def process(
        self, 
        doc: WebisDocument, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Optional[WebisDocument]:
        
        if not doc.content:
            return doc
            
        try:
            soup = BeautifulSoup(doc.content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            doc.clean_content = text
            doc.add_processing_step(self.name)
            return doc
            
        except Exception as e:
            logger.error(f"HTML cleaning failed for {doc.id}: {e}")
            return doc
