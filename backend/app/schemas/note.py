from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class NoteBase(BaseModel):
    """Base schema for note data"""
    note_text: str
    file_name: str


class NoteCreate(NoteBase):
    """Schema for creating a new note"""
    pass


class NoteResponse(BaseModel):
    """Schema for note responses"""
    id: UUID
    user_id: UUID
    note_text: str
    file_name: str
    upload_date: datetime

    class Config:
        """Configure Pydantic to work with ORM"""
        from_attributes = True 