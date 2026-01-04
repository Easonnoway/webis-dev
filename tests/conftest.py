import pytest
from webis.core.schema import WebisDocument, DocumentType, DocumentMetadata

@pytest.fixture
def sample_text_doc():
    return WebisDocument(
        content="This is a test document about AI.",
        doc_type=DocumentType.TEXT,
        meta=DocumentMetadata(
            url="http://example.com/test",
            source_plugin="test_source"
        )
    )

@pytest.fixture
def sample_html_doc():
    return WebisDocument(
        content="<html><body><h1>Title</h1><p>Content</p></body></html>",
        doc_type=DocumentType.HTML,
        meta=DocumentMetadata(
            url="http://example.com/html",
            source_plugin="test_source"
        )
    )
