import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base

class Note(Base):
    """Model for storing user notes."""
    
    __tablename__ = "notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    note_text = Column(Text, nullable=False)
    file_name = Column(String, nullable=True)
    upload_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="notes")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan") 