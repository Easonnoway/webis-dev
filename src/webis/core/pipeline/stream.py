from typing import Iterator, Callable, Any, Iterable
import logging
from webis.core.schema import WebisDocument, PipelineContext

logger = logging.getLogger(__name__)

class StreamPipeline:
    """
    A pipeline that processes documents one by one as they are yielded from the source,
    rather than waiting for the entire list to be fetched.
    """
    def __init__(self, processors: Iterable[Callable[[WebisDocument, PipelineContext], WebisDocument]]):
        self.processors = list(processors)

    def run(self, source_iterator: Iterator[WebisDocument], context: PipelineContext) -> Iterator[WebisDocument]:
        """
        Yields processed documents as they become available.
        """
        for doc in source_iterator:
            processed_doc = doc
            try:
                for processor in self.processors:
                    # Check for dry run or other flags in context if needed
                    if context.is_dry_run:
                        continue
                        
                    processed_doc = processor(processed_doc, context)
                    
                yield processed_doc
                
            except Exception as e:
                # Handle error for this specific document without breaking the stream
                logger.error(f"Error processing document {doc.id}: {e}", exc_info=True)
                # Optionally track errors in context if needed
                # if "errors" not in context.state: context.state["errors"] = []
                # context.state["errors"].append({"doc_id": doc.id, "error": str(e)})
