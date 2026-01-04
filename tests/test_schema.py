from webis.core.schema import WebisDocument, DocumentType

def test_document_initialization(sample_text_doc):
    assert sample_text_doc.content == "This is a test document about AI."
    assert sample_text_doc.doc_type == DocumentType.TEXT
    assert sample_text_doc.meta.url == "http://example.com/test"

def test_document_serialization(sample_text_doc):
    json_str = sample_text_doc.json()
    assert "This is a test document about AI." in json_str
    assert "http://example.com/test" in json_str
