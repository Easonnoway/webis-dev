import pytest
from webis.core.plugin import ProcessorPlugin
from webis.core.schema import WebisDocument, PipelineContext

class MockProcessor(ProcessorPlugin):
    name = "mock_processor"
    
    def process(self, doc: WebisDocument, context: PipelineContext) -> WebisDocument:
        doc.content += " [Processed]"
        return doc

def test_processor_plugin(sample_text_doc):
    processor = MockProcessor()
    context = PipelineContext(run_id="test_run")
    
    processed_doc = processor.process(sample_text_doc, context)
    
    assert " [Processed]" in processed_doc.content
    assert processed_doc.meta.url == "http://example.com/test"
