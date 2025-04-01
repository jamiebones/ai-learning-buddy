from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NoteBase(BaseModel):
    """Base schema for note data"""
    note_text: str
    file_name: str


class NoteCreate(NoteBase):
    """Schema for creating a new note"""
    pass


class NoteResponse(NoteBase):
    """Schema for note responses"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Configure Pydantic to work with ORM"""
        from_attributes = True 