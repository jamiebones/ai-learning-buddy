import uuid
import logging
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from app.core.config import settings
import datetime

# Import these modules at file level instead of in __init__
from app.services.vector_store import VectorStore
from app.services.keyword_retriever import KeywordRetriever
from app.services.api_client import LilypadClient
from app.services.document_processing import DocumentProcessor


# Initialize logging
logger = logging.getLogger(__name__)

# Text splitter for chunking
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

class RAGService:
    """RAG service implementation using Lilypad API"""

    def __init__(self, api_token=None, use_embeddings=True):
        """Initialize the RAG service with retrieval components.
        
        Args:
            api_token: Lilypad API token (uses default from config if not provided)
            use_embeddings: Whether to use vector embeddings (True) or keyword search (False)
        """
        self.use_embeddings = use_embeddings

        if use_embeddings:
            self.retriever = VectorStore()
        else:
            self.retriever = KeywordRetriever()

        # Use provided API token or default from config
        self.lilypad_client = LilypadClient(api_token or settings.LILYPAD_API_TOKEN or settings.DEFAULT_LILYPAD_API_TOKEN)
        self.initialized = False
        self._documents = []
        
    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to the retriever.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            bool: Whether the operation was successful
        """
        try:
            self._documents.extend(documents)
            
            if not self.initialized:
                logger.info("Initializing retriever with new documents...")
                success = self.retriever.initialize(documents)
                if success:
                    self.initialized = True
                return success
            else:
                logger.info("Adding documents to existing retriever...")
                return self.retriever.add_documents(documents)
                
        except Exception as e:
            logger.exception(f"Error adding documents: {e}")
            return False
            
    def retrieve_context(self, query: str) -> str:
        """Retrieve relevant context for the query"""
        try:
            logger.info(f"Retrieving context for query: '{query}'")
            
            if not self.initialized:
                logger.warning("Service not initialized yet, cannot retrieve context")
                return ""
            
            if self.use_embeddings:
                context = self.retriever.hybrid_search(query)
            else:
                context = self.retriever.retrieve(query)

            if not context or len(context) < 100:
                logger.warning("Retrieval returned insufficient content, using broader context")
                # Try to get more content or use a different retrieval method as fallback
                context = self.retriever.get_most_relevant_content()

            logger.info(f"Retrieved context length: {len(context)}")
            return context

        except Exception as e:
            logger.exception(f"Error retrieving context: {str(e)}")
            return ""

    def query(self, query: str) -> Dict[str, Any]:
        """Process user query and return answer with context
        
        Args:
            query: User query string
            
        Returns:
            Dict with 'answer' and 'source_documents' keys
        """
        logger.info(f"Processing query: {query}")

        context = self.retrieve_context(query)

        if not context:
            logger.error("Retrieval failed. No context was returned.")
            return {
                "answer": "Retrieval failed. No context available.",
                "source_documents": []
            }
        
        try:
            answer = self.lilypad_client.query(query, context)
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {
                "answer": f"API call failed: {e}",
                "source_documents": []
            }

        if not answer:
            logger.error("Lilypad API returned an empty response.")
            return {
                "answer": "Lilypad API returned an empty response.",
                "source_documents": []
            }

        # Try to determine which source documents were used in the answer
        source_docs = self.retriever.get_documents_for_context(context)
        
        return {
            "answer": answer,
            "source_documents": [
                {
                    "content": doc.page_content,
                    "note_id": doc.metadata.get("note_id")
                } for doc in source_docs
            ]
        }

    def process_note(self, note_id: uuid.UUID, user_id: uuid.UUID, content: str, title: str = "") -> bool:
        """Process a note and add to the retrieval system with proper metadata.
        
        Args:
            note_id: UUID of the note
            user_id: UUID of the user who owns the note
            content: Text content of the note
            title: Optional title of the note
            
        Returns:
            bool: Whether the operation was successful
        """
        try:
            logger.info(f"Processing note {note_id} for user {user_id}")
            
            # Create a temporary file to process with DocumentProcessor
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            # Process the document with DocumentProcessor
            processor = DocumentProcessor(temp_path)
            documents = processor.process()
            
            # Clean up the temporary file
            import os
            os.unlink(temp_path)
            
            # Add user_id and title to metadata
            for doc in documents:
                doc.metadata.update({
                    "note_id": str(note_id),
                    "user_id": str(user_id),
                    "title": title,
                    "timestamp": str(datetime.datetime.now())
                })
            
            # Add the processed documents to the retriever
            return self.add_documents(documents)
            
        except Exception as e:
            logger.exception(f"Error processing note: {e}")
            return False
    
    def query_for_user(self, user_id: uuid.UUID, query: str) -> Dict[str, Any]:
        """Process user query and return answer, filtering by user_id
        
        Args:
            user_id: User UUID to filter documents by
            query: User query string
            
        Returns:
            Dict with 'answer' and 'source_documents' keys
        """
        logger.info(f"Processing query for user {user_id}: {query}")
        
        # Set the user_id filter for retrieval
        if self.use_embeddings:
            context = self.retriever.hybrid_search(query, filter={"user_id": str(user_id)})
        else:
            # If keyword retriever doesn't support filtering, we'll filter afterward
            context = self.retriever.retrieve(query)
            # Placeholder for filtering by user_id if needed
        
        if not context:
            logger.error("Retrieval failed. No context was returned.")
            return {
                "answer": "I couldn't find any relevant information in your notes.",
                "source_documents": []
            }
        
        try:
            answer = self.lilypad_client.query(query, context)
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {
                "answer": f"Sorry, I encountered an error while processing your query.",
                "source_documents": []
            }

        if not answer:
            logger.error("Lilypad API returned an empty response.")
            return {
                "answer": "I couldn't generate an answer based on your notes.",
                "source_documents": []
            }

        # Get source documents with enhanced metadata
        source_docs = self.retriever.get_documents_for_context(context)
        
        # Format source documents with more metadata
        formatted_sources = []
        for doc in source_docs:
            formatted_sources.append({
                "content": doc.page_content,
                "note_id": doc.metadata.get("note_id"),
                "title": doc.metadata.get("title", "Untitled Note"),
                "chunk_type": doc.metadata.get("chunk_type", "unknown"),
                "source": doc.metadata.get("source", "")
            })
        
        return {
            "answer": answer,
            "source_documents": formatted_sources
        }

# Service instance
rag_service = RAGService(use_embeddings=True)

def process_user_note(user_id: uuid.UUID, note_id: uuid.UUID, content: str, title: str = "") -> bool:
    """Process a user's note and add to the retrieval system.
    
    Args:
        user_id: User's UUID
        note_id: Note's UUID
        content: Note content
        title: Note title
        
    Returns:
        bool: Success status
    """
    return rag_service.process_note(note_id, user_id, content, title)

def query_notes(user_id: uuid.UUID, query: str) -> Dict[str, Any]:
    """Query the user's notes to find relevant information and generate an answer.
    
    Args:
        user_id: User's UUID
        query: User's question
        
    Returns:
        Dict with answer and source documents
    """
    return rag_service.query_for_user(user_id, query)



