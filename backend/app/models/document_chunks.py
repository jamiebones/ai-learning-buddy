import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.db import Base

class DocumentChunk(Base):
    """Model for document chunks."""
    
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_type = Column(String, default="text")  # text, code, etc.
    chunk_metadata = Column(JSONB, nullable=True)
    
    # Relationship to Note model
    document = relationship("Note", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id})>" 