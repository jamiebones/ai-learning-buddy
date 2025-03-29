from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.user import User
from app.models.chat import Chat
from app.services.auth import get_current_user
from app.services.rag_service import query_notes
from app.schemas.chat import ChatRequest, ChatResponse
from typing import List

router = APIRouter()

@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Query the RAG system
    rag_response = query_notes(current_user.id, chat_request.message)
    
    # Save the conversation
    chat = Chat(
        user_id=current_user.id,
        message=chat_request.message,
        response=rag_response["answer"]
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    
    return {
        "id": chat.id,
        "message": chat.message,
        "response": chat.response,
        "timestamp": chat.timestamp,
        "source_documents": rag_response["source_documents"]
    }

@router.get("/history", response_model=List[ChatResponse])
async def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chats = db.query(Chat).filter(Chat.user_id == current_user.id).order_by(Chat.timestamp.asc()).all()
    return chats 