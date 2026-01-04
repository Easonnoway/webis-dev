import hashlib
from typing import Optional
from sqlmodel import Session, select
from webis.core.memory.models import DocumentModel
from webis.core.schema import WebisDocument

class Deduplicator:
    """
    Handles document deduplication logic.
    """
    
    def __init__(self, session: Session):
        self.session = session

    def compute_hash(self, content: str) -> str:
        """Compute MD5 hash of content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def is_duplicate(self, doc: WebisDocument) -> bool:
        """
        Check if document already exists based on URL or content hash.
        """
        # Check by URL if available
        if doc.meta.url:
            statement = select(DocumentModel).where(DocumentModel.url == doc.meta.url)
            result = self.session.exec(statement).first()
            if result:
                return True

        # Check by content hash
        content_hash = self.compute_hash(doc.content)
        statement = select(DocumentModel).where(DocumentModel.content_hash == content_hash)
        result = self.session.exec(statement).first()
        
        if result:
            return True
            
        return False

    def get_existing_doc(self, doc: WebisDocument) -> Optional[DocumentModel]:
        """
        Retrieve existing document if it exists.
        """
        if doc.meta.url:
            statement = select(DocumentModel).where(DocumentModel.url == doc.meta.url)
            result = self.session.exec(statement).first()
            if result:
                return result

        content_hash = self.compute_hash(doc.content)
        statement = select(DocumentModel).where(DocumentModel.content_hash == content_hash)
        result = self.session.exec(statement).first()
        
        return result
