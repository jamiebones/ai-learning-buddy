from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

class SourceDocument(BaseModel):
    """Schema for source documents returned by the RAG system"""
    content: str
    metadata: dict

class ChatRequest(BaseModel):
    """Schema for incoming chat message requests"""
    message: str
    session_id: Optional[uuid.UUID] = None  # Optional session ID, if None a new session will be created

class ChatResponse(BaseModel):
    """Schema for chat response including the original message and system response"""
    id: uuid.UUID
    message: str
    response: str
    timestamp: datetime
    session_id: uuid.UUID
    source_documents: Optional[List[SourceDocument]] = None
    
    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    name: Optional[str] = None

class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""
    id: uuid.UUID
    name: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChatSessionWithMessages(ChatSessionResponse):
    """Schema for chat session with all messages"""
    chats: List[ChatResponse]
    
    class Config:
        from_attributes = True 