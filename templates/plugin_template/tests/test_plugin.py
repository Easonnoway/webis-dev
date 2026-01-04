import pytest
from webis.core.schema import WebisDocument, DocumentType, PipelineContext
from webis_plugin_{{cookiecutter.plugin_slug}}.plugin import {{cookiecutter.plugin_class_name}}

def test_plugin_processing():
    plugin = {{cookiecutter.plugin_class_name}}(config_param="test")
    doc = WebisDocument(content="hello world", doc_type=DocumentType.TEXT)
    context = PipelineContext(run_id="test")
    
    result = plugin.process(doc, context)
    
    assert result.content == "hello world"
    # Add more assertions based on your logic
