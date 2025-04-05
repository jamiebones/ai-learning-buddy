import os
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.models.user import User
from app.models.note import Note
from app.services.auth import get_current_user
from app.services.file_processor import process_file
from app.services.rag_service import process_user_note
from app.schemas.note import NoteResponse

router = APIRouter()

@router.post("/upload", response_model=NoteResponse)
async def upload_note(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate file type
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="File type not supported. Upload PDF, DOCX, or TXT files."
        )
    
    # Save file temporarily
    file_path = f"temp_{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # Process file to extract text
        note_text = process_file(file_path, file.content_type)
        
        # Save to database
        note = Note(
            id=uuid.uuid4(),
            user_id=current_user.id,
            note_text=note_text,
            file_name=file.filename
        )
        db.add(note)
        await db.commit()
        
        # Process the note
        await process_user_note(current_user.id, note.id, note_text, db)
        
        return note
    
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path) 