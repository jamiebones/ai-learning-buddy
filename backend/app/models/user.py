import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    chats = relationship(
        "Chat", 
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Chat.timestamp)"
    )
    
    notes = relationship(
        "Note", 
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Note.upload_date)"
    )