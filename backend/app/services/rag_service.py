import uuid
import logging
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from app.core.config import settings
import datetime
from sqlalchemy.orm import Session
from app.models.note import Note
from app.services.document_processing_service import DocumentProcessingService
from app.services.embeddings import get_embeddings
from app.services.vector_store import VectorStore
from app.services.api_client import LilypadClient

# Import these modules at file level instead of in __init__
from app.services.keyword_retriever import KeywordRetriever

# Initialize logging
logger = logging.getLogger(__name__)

# Text splitter for chunking
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

class RAGService:
    """Service for handling RAG operations using database storage and vector search."""
    
    def __init__(self, db: Session):
        """Initialize the RAG service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        if db is None:
            raise ValueError("Database session cannot be None")
            
        self.db = db
        self.document_processor = DocumentProcessingService(db)
        self.vector_store = VectorStore()
        self.lilypad_client = LilypadClient()
    
    async def process_note(self, note: Note) -> None:
        """Process a note and add it to the retrieval system."""
        try:
            # Process document into chunks and store in database
            chunks = await self.document_processor.process_document(note)
            
            # Add chunks to vector store with embeddings
            await self.vector_store.add_documents(chunks)
            
            logger.info(f"Successfully processed note {note.id}")

        except Exception as e:
            logger.error(f"Error processing note {note.id}: {str(e)}")
            raise
    
    async def get_relevant_chunks(self, query: str, user_id: uuid.UUID, limit: int = 5) -> List[Dict[str, Any]]:
        """Get relevant chunks for a query using semantic search."""
        try:
            # Get query embedding
            query_embedding = get_embeddings(query)
            
            # Search vector store for similar chunks
            # The similarity_search method now returns all needed chunk data
            similar_chunks = await self.vector_store.similarity_search(
                query_embedding,
                k=limit,
                user_id=user_id
            )
            
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Error getting relevant chunks: {str(e)}")
            raise
    
    async def query_documents(self, query: str, user_id: uuid.UUID, limit: int = 5) -> Dict[str, Any]:
        """Query documents and get response from Lilypad."""
        try:
            # Get relevant chunks
            chunks = await self.get_relevant_chunks(query, user_id, limit)
            
            if not chunks:
                logger.warning(f"No relevant chunks found for query: {query}")
                return {
                    "answer": "I couldn't find any relevant information in your notes to answer this question.",
                    "source_documents": []
                }
            
            # Format context from chunks
            context_parts = []
            for i, chunk in enumerate(chunks, 1):
                context_parts.append(f"[CHUNK {i}]\n{chunk['content']}")
            context = "\n\n".join(context_parts)
            
            # Get chat completion from Lilypad
            system_prompt = """You are a helpful AI assistant that answers questions based on the user's notes. 
Use ONLY the provided context to answer questions. If you cannot find relevant information in the context, say so.

IMPORTANT INSTRUCTIONS:
1. NEVER mention 'chunks', 'CHUNK X', or any metadata related to document retrieval in your answer
2. DO NOT show your thinking or reasoning process
3. DO NOT use phrases like "Based on the context" or "According to the chunks"
4. DO NOT output any text that starts with <think> or similar tags
5. Provide a direct, clear answer without referencing how you arrived at it
6. DO NOT include any preamble like "I'll analyze this..." or "Let me check..."
7. If you're unsure, simply state that the information isn't available in the provided context"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ]
            
            answer = await self.lilypad_client.get_chat_completion(messages)
            
            # Format source documents to include metadata properly
            formatted_chunks = []
            for chunk in chunks:
                # Convert chunk_metadata to metadata for API response validation
                chunk_metadata = chunk.get('chunk_metadata', {})
                formatted_chunk = {
                    "content": chunk['content'],
                    "metadata": chunk_metadata if chunk_metadata else {"source": "database"}
                }
                formatted_chunks.append(formatted_chunk)
            
            return {
                "answer": answer,
                "source_documents": formatted_chunks
            }
            
        except Exception as e:
            logger.error(f"Error querying documents: {str(e)}")
            raise
    
    async def delete_note(self, note_id: uuid.UUID) -> None:
        """Delete a note and its associated chunks from the retrieval system."""
        try:
            # Delete chunks from database
            await self.document_processor.delete_document_chunks(note_id)
            
            # Remove from vector store
            await self.vector_store.delete_documents(note_id)
            
            logger.info(f"Successfully deleted note {note_id}")
            
        except Exception as e:
            logger.error(f"Error deleting note {note_id}: {str(e)}")
            raise

async def process_user_note(user_id: uuid.UUID, note_id: uuid.UUID, content: str, db: Session = None) -> bool:
    """Process a user's note and add to the retrieval system."""
    if not db:
        raise ValueError("Database session is required")
        
    rag_service = RAGService(db)
    note = Note(id=note_id, user_id=user_id, note_text=content)
    await rag_service.process_note(note)
    return True

async def query_notes(user_id: uuid.UUID, query: str, db: Session = None) -> Dict[str, Any]:
    """Query the user's notes to find relevant information and generate an answer."""
    if not db:
        raise ValueError("Database session is required")
        
    rag_service = RAGService(db)
    return await rag_service.query_documents(query, user_id)



