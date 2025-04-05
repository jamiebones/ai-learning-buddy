import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import settings
from app.core.logging import logger
from app.services.embeddings import get_embeddings

class VectorStore:
    """Handles document embeddings and vector store operations using singleton pattern with Chroma"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db=None):
        """Initialize Chroma vector store if not already initialized.
        
        Args:
            db: SQLAlchemy session (kept for API compatibility, not used)
        """
        if not self._initialized:
            self._initialize_store()
            self._initialized = True
    
    def _initialize_store(self):
        """Initialize the Chroma vector store with persistence"""
        try:
            # Ensure the persist directory exists
            os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
            
            # Create the embedding function using sentence transformers
            embedding_function = HuggingFaceEmbeddings(
                model_name=settings.DEFAULT_EMBEDDING_MODEL
            )
            
            # Initialize Chroma with persistence
            self.store = Chroma(
                persist_directory=settings.VECTOR_STORE_DIR,
                embedding_function=embedding_function,
                collection_name="document_chunks"
            )
            
            logger.info(f"Initialized Chroma vector store at {settings.VECTOR_STORE_DIR}")
            
        except Exception as e:
            logger.error(f"Error initializing Chroma vector store: {str(e)}")
            raise
    
    async def add_documents(self, chunks: List[Any]) -> None:
        """Add document chunks to the vector store.
        
        Args:
            chunks: List of DocumentChunk objects
        """
        try:
            # Convert DocumentChunk objects to LangChain Document objects
            documents = []
            for chunk in chunks:
                # Get embedding for the content
                embedding = get_embeddings(chunk.content)
                
                # Get user_id from the note
                try:
                    # Try to get note from database to get user_id
                    user_id = str(chunk.document.user_id) if hasattr(chunk, 'document') and chunk.document else None
                except:
                    user_id = None
                
                # Create a LangChain Document
                doc = Document(
                    page_content=chunk.content,
                    metadata={
                        "chunk_id": str(chunk.id),
                        "document_id": str(chunk.document_id),
                        "user_id": user_id,  # Add user_id to metadata
                        "chunk_type": chunk.chunk_type,
                        **(chunk.chunk_metadata or {})
                    }
                )
                documents.append(doc)
            
            # Add documents to Chroma
            if documents:
                self.store.add_documents(documents)
                self.store.persist()  # Save to disk
                logger.info(f"Successfully added {len(documents)} chunks to Chroma vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to Chroma vector store: {str(e)}")
            raise
    
    async def similarity_search(self, query_embedding: List[float], k: int = 5, user_id: uuid.UUID = None) -> List[Dict[str, Any]]:
        """Search for similar chunks using cosine similarity.
        
        Args:
            query_embedding: The embedding vector of the query
            k: Maximum number of results to return
            user_id: Filter results by user ID (via document metadata)
            
        Returns:
            List of dictionaries containing document chunk information
        """
        try:
            # Use Chroma's similarity search with embeddings
            filter_dict = None
            if user_id:
                # Use $eq operator with user_id field
                filter_dict = {"user_id": {"$eq": str(user_id)}}
            
            results = self.store.similarity_search_by_vector(
                query_embedding,
                k=k,
                filter=filter_dict
            )
            
            # Convert results to a compatible format
            chunks = []
            for doc in results:
                chunks.append({
                    "id": doc.metadata.get("chunk_id"),
                    "document_id": doc.metadata.get("document_id"),
                    "content": doc.page_content,
                    "chunk_type": doc.metadata.get("chunk_type", "text"),
                    "chunk_metadata": {k: v for k, v in doc.metadata.items() 
                                    if k not in ["chunk_id", "document_id", "chunk_type", "user_id"]}
                })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}")
            raise
    
    async def delete_documents(self, note_id: uuid.UUID) -> None:
        """Delete all chunks for a document.
        
        Args:
            note_id: UUID of the note to delete chunks for
        """
        try:
            # Delete documents by filtering on document_id
            self.store.delete(
                filter={"document_id": {"$eq": str(note_id)}}
            )
            
            # Persist changes to disk
            self.store.persist()
            
            logger.info(f"Successfully deleted chunks for document {note_id} from Chroma")
            
        except Exception as e:
            logger.error(f"Error deleting chunks for document {note_id}: {str(e)}")
            raise
    
    async def hybrid_search(self, query: str, mmr_k: int = 5, mmr_fetch_k: int = 15, similarity_k: int = 3) -> str:
        """Retrieve relevant context using hybrid search approach"""
        try:
            retrieved_docs = []
            
            # MMR search for diverse results
            mmr_docs = self.store.max_marginal_relevance_search(query=query, k=mmr_k, fetch_k=mmr_fetch_k)
            retrieved_docs.extend(mmr_docs)
            logger.info(f"Retrieved {len(mmr_docs)} chunks using MMR search")
            
            # Also get top similar chunks
            similar_docs = self.store.similarity_search(query=query, k=similarity_k)
            
            # Combine results (avoiding duplicates)
            seen_content = set(doc.page_content for doc in retrieved_docs)
            for doc in similar_docs:
                if doc.page_content not in seen_content:
                    retrieved_docs.append(doc)
                    seen_content.add(doc.page_content)

            logger.info(f"Retrieved {len(retrieved_docs)} total unique chunks")
            
            if not retrieved_docs:
                logger.warning("No relevant context found")
                return ""

            # Log first few chunks
            for i, doc in enumerate(retrieved_docs[:3]):
                logger.info(f"Chunk {i+1}: {doc.page_content[:500]}...")

            return self._format_context(retrieved_docs)

        except Exception as e:
            logger.exception(f"Error in hybrid search: {str(e)}")
            return ""
    
    async def get_documents_for_context(self, context: str) -> List[Document]:
        """Get the documents that were used to generate the context."""
        try:
            # Split context into chunks and search for each
            chunks = context.split("\n\n---\n\n")
            documents = []
            
            for chunk in chunks:
                # Remove the header if present
                if "[" in chunk and "]" in chunk:
                    chunk = chunk[chunk.find("]") + 1:].strip()
                
                # Search for this chunk in the vector store
                docs = self.store.similarity_search(chunk, k=1)
                if docs:
                    documents.extend(docs)
            
            return documents

        except Exception as e:
            logger.exception(f"Error getting documents for context: {str(e)}")
            return []
    
    def _format_context(self, docs: List[Document]) -> str:
        """Format retrieved documents into context string"""
        context_parts = []
        for i, doc in enumerate(docs):
            chunk_type = doc.metadata.get("chunk_type", "unknown")

            if chunk_type == "line" and "start_line" in doc.metadata:
                header = f"[CHUNK {i+1} - LINES {doc.metadata['start_line']}-{doc.metadata['end_line']}]"
            else:
                header = f"[CHUNK {i+1} - TYPE: {chunk_type}]"

            context_parts.append(f"{header}\n{doc.page_content}")

        return "\n\n---\n\n".join(context_parts)
    
    async def close(self):
        """Properly close the Chroma client"""
        try:
            if hasattr(self, 'store') and self.store:
                self.store.persist()  # Save any changes
                logger.info("Vector store closed and persisted successfully")
        except Exception as e:
            logger.exception(f"Error closing vector store: {e}")

# Create a singleton instance
vector_store = VectorStore() 