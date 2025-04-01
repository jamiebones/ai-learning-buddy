import os
import shutil
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.core.logging import logger
from langchain.docstore.document import Document
from typing import List

print(f"VECTOR_STORE_DIR: {settings.VECTOR_STORE_DIR}")

class VectorStore:
    """Handles document embeddings and vector store operations"""

    def __init__(self, persist_directory=None, embedding_model=None):
        self.persist_directory = persist_directory or settings.VECTOR_STORE_DIR
        self.embedding_model = embedding_model or settings.DEFAULT_EMBEDDING_MODEL
        self.store = None

    def initialize(self, documents):
        """Initialize embedding model and vector store"""
        try:
            logger.info(f"Initializing embedding model: {self.embedding_model}")
            
            # Load embeddings
            self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model)

            if not documents:
                logger.error("❌ No documents provided for vector store.")
                return False

            # Clean up existing vector store if present
            if os.path.exists(self.persist_directory):
                logger.info(f"Removing existing vector store at {self.persist_directory}")
                shutil.rmtree(self.persist_directory)

            # Create vector store
            logger.info("Creating vector store")
            self.store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )

            logger.info("✅ Vector store initialized successfully")
            return True

        except Exception as e:
            logger.exception(f"❌ Vector store initialization failed: {e}")
            return False

    def hybrid_search(self, query: str, mmr_k: int = 5, mmr_fetch_k: int = 15, similarity_k: int = 3) -> str:
        """Retrieve relevant context using hybrid search approach"""
        if not self.store:
            logger.error("❌ Vector store not initialized")
            return ""

        try:
            retrieved_docs = []
            
            # MMR search for diverse results
            mmr_docs = self.store.max_marginal_relevance_search(query=query, k=mmr_k, fetch_k=mmr_fetch_k)
            retrieved_docs.extend(mmr_docs)
            logger.info(f"📌 Retrieved {len(mmr_docs)} chunks using MMR search")
            
            # Also get top similar chunks
            similar_docs = self.store.similarity_search(query=query, k=similarity_k)
            
            # Combine results (avoiding duplicates)
            seen_content = set(doc.page_content for doc in retrieved_docs)
            for doc in similar_docs:
                if doc.page_content not in seen_content:
                    retrieved_docs.append(doc)
                    seen_content.add(doc.page_content)

            logger.info(f"📌 Retrieved {len(retrieved_docs)} total unique chunks")
            
            if not retrieved_docs:
                logger.warning("⚠️ No relevant context found")
                return ""

            # Log first few chunks
            for i, doc in enumerate(retrieved_docs[:3]):
                logger.info(f"🔹 Chunk {i+1}: {doc.page_content[:500]}...")

            return self._format_context(retrieved_docs)

        except Exception as e:
            logger.exception(f"❌ Error in hybrid search: {str(e)}")
            return ""

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