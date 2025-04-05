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

class ChatResponse(BaseModel):
    """Schema for chat response including the original message and system response"""
    id: uuid.UUID
    message: str
    response: str
    timestamp: datetime
    source_documents: Optional[List[SourceDocument]] = None
    
    class Config:
        from_attributes = True 