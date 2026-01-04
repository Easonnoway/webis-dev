import pytest
from webis.core.pipeline import Pipeline
from webis.core.plugin import ProcessorPlugin, SourcePlugin, PluginRegistry
from webis.core.schema import WebisDocument

class MockSource(SourcePlugin):
    name = "mock_source"
    def fetch(self, query, **kwargs):
        yield WebisDocument(content="test content")

class MockPlugin(ProcessorPlugin):
    name = "mock_plugin"
    def process(self, doc, context=None, **kwargs):
        context.set("status", "ok")
        return doc

def test_pipeline_basic():
    registry = PluginRegistry()
    registry.register(MockSource())
    registry.register(MockPlugin())
    
    pipeline = Pipeline(registry=registry)
    pipeline.add_source("mock_source")
    pipeline.add_processor("mock_plugin")
    
    # Pipeline.run takes a query or input dict
    result = pipeline.run("test")
    
    # Result is PipelineResult object
    assert result.success
    assert result.context.get("status") == "ok"
    assert len(result.documents) == 1
    assert result.documents[0].content == "test content"
