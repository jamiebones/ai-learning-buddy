from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.user import User
from app.models.chat import Chat, ChatSession
from app.services.auth import get_current_user
from app.services.rag_service import query_notes
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionCreate, ChatSessionResponse, ChatSessionWithMessages
from typing import List
import logging
from sqlalchemy import select
import uuid
from datetime import datetime

# Initialize logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/session", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session"""
    try:
        # Create new chat session
        session = ChatSession(
            id=uuid.uuid4(),
            user_id=current_user.id,
            name=session_data.name or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return session
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the chat session."
        )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all chat sessions for the current user"""
    try:
        stmt = select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(ChatSession.updated_at.desc())
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        return sessions
    except Exception as e:
        logger.error(f"Error fetching chat sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching chat sessions."
        )

@router.get("/session/{session_id}", response_model=ChatSessionWithMessages)
async def get_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific chat session with all messages"""
    try:
        stmt = select(ChatSession).where(
            (ChatSession.id == session_id) & 
            (ChatSession.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        session = result.scalars().first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the chat session."
        )

@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session"""
    try:
        stmt = select(ChatSession).where(
            (ChatSession.id == session_id) & 
            (ChatSession.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        session = result.scalars().first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        await db.delete(session)
        await db.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the chat session."
        )

@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Get or create session
        session_id = chat_request.session_id
        if session_id:
            # Verify session belongs to user
            stmt = select(ChatSession).where(
                (ChatSession.id == session_id) & 
                (ChatSession.user_id == current_user.id)
            )
            result = await db.execute(stmt)
            session = result.scalars().first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )
        else:
            # Create new chat session
            session = ChatSession(
                id=uuid.uuid4(),
                user_id=current_user.id,
                name=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            session_id = session.id
        
        # Update session timestamp
        session.updated_at = datetime.now()
        await db.commit()
        
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
            session_id=session_id,
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
            "session_id": chat.session_id,
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
            
            # Create session if needed
            if not chat_request.session_id:
                session = ChatSession(
                    id=uuid.uuid4(),
                    user_id=current_user.id,
                    name=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)
                session_id = session.id
            else:
                session_id = chat_request.session_id
            
            # Save the conversation with error response
            chat = Chat(
                user_id=current_user.id,
                session_id=session_id,
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
                "session_id": chat.session_id,
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
    session_id: uuid.UUID = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        logger.info(f"Fetching chat history for user {current_user.id}")
        
        if session_id:
            # Verify session belongs to user
            stmt = select(ChatSession).where(
                (ChatSession.id == session_id) & 
                (ChatSession.user_id == current_user.id)
            )
            result = await db.execute(stmt)
            session = result.scalars().first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )
            
            # Get chats for specific session
            stmt = select(Chat).where(Chat.session_id == session_id).order_by(Chat.timestamp.asc())
        else:
            # Get all chats for user
            stmt = select(Chat).where(Chat.user_id == current_user.id).order_by(Chat.timestamp.asc())
        
        result = await db.execute(stmt)
        chats = result.scalars().all()
        return chats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching chat history."
        ) 