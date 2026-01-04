from typing import List, Dict, Any
import re
from datetime import datetime
from webis.core.plugin import ProcessorPlugin
from webis.core.schema import WebisDocument, PipelineContext

class TemporalExtractorPlugin(ProcessorPlugin):
    """
    Extracts temporal events from text and normalizes timestamps.
    Identifies (Event, Timestamp) pairs to build timelines.
    """
    name = "temporal_extractor"

    def __init__(self, date_formats: List[str] = None):
        self.date_formats = date_formats or ["%Y-%m-%d", "%Y年%m月%d日"]
        # Simple regex for demonstration. In production, use a library like dateparser or an LLM.
        self.date_pattern = re.compile(r'(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{2}-\d{2})')

    def process(self, doc: WebisDocument, context: PipelineContext) -> WebisDocument:
        
        text = doc.content
        events = self._extract_events(text)
        
        # Store extracted events in metadata
        if "events" not in doc.meta.extra:
            doc.meta.extra["events"] = []
        doc.meta.extra["events"].extend(events)
        
        return doc

    def _extract_events(self, text: str) -> List[Dict[str, Any]]:
        events = []
        # Split by sentences to associate dates with immediate context
        sentences = re.split(r'[。！？.!?]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            matches = self.date_pattern.finditer(sentence)
            for match in matches:
                date_str = match.group(1)
                # The event is roughly the rest of the sentence
                # A real implementation would use Dependency Parsing to find the root verb associated with the time
                event_desc = sentence.replace(date_str, "").strip()
                
                events.append({
                    "date_raw": date_str,
                    "description": event_desc,
                    "context": sentence
                })
        
        return events
