import os
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.models.user import User
from app.models.note import Note
from app.models.document_chunks import DocumentChunk
from app.services.auth import get_current_user
from app.services.file_processor import process_file
from app.services.rag_service import process_user_note, delete_note_embeddings
from app.schemas.note import NoteResponse
from sqlalchemy import select

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

@router.get("", response_model=List[NoteResponse])
async def get_user_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        stmt = select(Note).where(Note.user_id == current_user.id).order_by(Note.upload_date.desc())
        result = await db.execute(stmt)
        notes = result.scalars().all()
        return notes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving notes: {str(e)}"
        )

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Verify note exists and belongs to user
        stmt = select(Note).where(
            (Note.id == note_id) &
            (Note.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        note = result.scalars().first()
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        # Delete embeddings from the vector database
        await delete_note_embeddings(note_id)
        
        # Delete note from database (this will cascade delete chunks due to relationship setting)
        await db.delete(note)
        await db.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting note: {str(e)}"
        ) 