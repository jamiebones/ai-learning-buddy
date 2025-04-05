import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.note import Note
from app.models.document_chunks import DocumentChunk
from app.services.document_processing import TextDocumentProcessor
import uuid

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """Service for processing documents and storing their chunks."""
    
    def __init__(self, db: Session):
        """Initialize the document processing service.
        
        Args:
            db: SQLAlchemy database session
        """
        if db is None:
            raise ValueError("Database session cannot be None")
            
        self.db = db
        self.document_processor = TextDocumentProcessor()
    
    async def process_document(self, note: Note) -> List[DocumentChunk]:
        """Process a document into chunks and store them."""
        try:
            # Process document into chunks
            chunks = self.document_processor.process(note.note_text)
            
            if not chunks:
                logger.warning(f"No chunks created for note {note.id}")
                return []
            
            # Create document chunks
            document_chunks = []
            for chunk in chunks:
                # Create document chunk
                doc_chunk = DocumentChunk(
                    document_id=note.id,
                    content=chunk.page_content,
                    chunk_type=chunk.metadata.get("chunk_type", "text"),
                    chunk_metadata=chunk.metadata
                )
                self.db.add(doc_chunk)
                document_chunks.append(doc_chunk)
            
            # Flush to get chunk IDs without committing transaction
            await self.db.flush()
            
            # Log success
            logger.info(f"Successfully processed document {note.id} into {len(document_chunks)} chunks")
            return document_chunks
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error processing document {note.id}: {str(e)}")
            raise
    
    async def get_document_chunks(self, chunk_ids: List[uuid.UUID]) -> List[Dict[str, Any]]:
        """Get document chunks by their IDs."""
        try:
            if not chunk_ids:
                return []
                
            chunks = []
            for chunk_id in chunk_ids:
                result = await self.db.execute(
                    self.db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id)
                )
                chunk = result.scalar_one_or_none()
                if chunk:
                    chunks.append({
                        "id": str(chunk.id),
                        "document_id": str(chunk.document_id),
                        "content": chunk.content,
                        "chunk_type": chunk.chunk_type,
                        "metadata": chunk.chunk_metadata
                    })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error getting document chunks: {str(e)}")
            raise
    
    async def delete_document_chunks(self, note_id: uuid.UUID) -> None:
        """Delete all chunks for a document."""
        try:
            # Delete chunks
            await self.db.execute(
                self.db.query(DocumentChunk).filter(DocumentChunk.document_id == note_id).delete()
            )
            # Let the calling function handle commit
            
            logger.info(f"Deleted all chunks for document {note_id}")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting document chunks: {str(e)}")
            raise 