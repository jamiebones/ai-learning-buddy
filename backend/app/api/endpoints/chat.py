from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.user import User
from app.models.chat import Chat
from app.services.auth import get_current_user
from app.services.rag_service import query_notes
from app.schemas.chat import ChatRequest, ChatResponse
from typing import List
import logging
from sqlalchemy import select

# Initialize logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Query the RAG system
        logger.info(f"Querying RAG system for user {current_user.id}")
        rag_response = await query_notes(current_user.id, chat_request.message, db)
        
        if not rag_response or not isinstance(rag_response, dict):
            logger.error(f"Invalid response from RAG system: {rag_response}")
            raise ValueError("Invalid response from RAG system")
            
        answer = rag_response.get("answer", "")
        source_documents = rag_response.get("source_documents", [])
        
        if not answer:
            logger.warning("Empty response from RAG system")
            answer = "I'm sorry, I couldn't generate a response based on the available information."
        
        # Save the conversation
        chat = Chat(
            user_id=current_user.id,
            message=chat_request.message,
            response=answer
        )
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
        logger.info(f"Successfully processed chat message for user {current_user.id}")
        return {
            "id": chat.id,
            "message": chat.message,
            "response": chat.response,
            "timestamp": chat.timestamp,
            "source_documents": source_documents
        }
        
    except ValueError as e:
        logger.error(f"Value error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except TypeError as e:
        # Handle the specific error about the filter parameter
        if "got an unexpected keyword argument 'filter'" in str(e):
            logger.error(f"Filter parameter error in RAG service: {str(e)}")
            error_message = "Sorry, there was an issue with the search functionality. Our team has been notified."
            
            # Save the conversation with error response
            chat = Chat(
                user_id=current_user.id,
                message=chat_request.message,
                response=error_message
            )
            db.add(chat)
            await db.commit()
            await db.refresh(chat)
            
            return {
                "id": chat.id,
                "message": chat.message,
                "response": error_message,
                "timestamp": chat.timestamp,
                "source_documents": []
            }
        # Re-raise other TypeError exceptions
        logger.error(f"Type error in chat endpoint: {str(e)}")
        raise
        
    except Exception as e:
        # Handle any other exceptions
        logger.error(f"Unexpected error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        )

@router.get("/history", response_model=List[ChatResponse])
async def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"Fetching chat history for user {current_user.id}")
        stmt = select(Chat).where(Chat.user_id == current_user.id).order_by(Chat.timestamp.asc())
        result = await db.execute(stmt)
        chats = result.scalars().all()
        return chats
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching chat history."
        ) 