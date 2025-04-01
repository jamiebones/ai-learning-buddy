import re
import logging
import numpy as np
from langchain.schema import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional

# Initialize logging
logger = logging.getLogger(__name__)

class KeywordRetriever:
    """Keyword-based document retriever using TF-IDF similarity."""

    def __init__(self):
        """Initialize keyword retriever"""
        self.documents = []
        self.chunks = []
        self.vectorizer = None
        self.vectors = None
        self.top_k = 5  # Number of top chunks to retrieve

    def initialize(self, documents: List[Document]) -> bool:
        """Initialize retriever with documents
        
        Args:
            documents: List of Document objects
            
        Returns:
            bool: Whether initialization was successful
        """
        try:
            self.documents = documents
            self._process_documents()
            logger.info(f"✅ Initialized keyword retriever with {len(documents)} documents")
            return True
        except Exception as e:
            logger.exception(f"❌ Error initializing keyword retriever: {str(e)}")
            return False

    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to the retriever
        
        Args:
            documents: List of Document objects
            
        Returns:
            bool: Whether documents were added successfully
        """
        try:
            self.documents.extend(documents)
            self._process_documents()  # Reprocess all documents
            logger.info(f"✅ Added {len(documents)} documents to keyword retriever")
            return True
        except Exception as e:
            logger.exception(f"❌ Error adding documents: {str(e)}")
            return False

    def _process_documents(self):
        """Process documents into TF-IDF vectors"""
        self.chunks = []
        
        for doc in self.documents:
            self.chunks.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "document": doc
            })
        
        if self.chunks:
            # Prepare TF-IDF vectorizer with n-grams for better phrase matching
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            doc_texts = [chunk["text"] for chunk in self.chunks]
            self.vectors = self.vectorizer.fit_transform(doc_texts)

    def retrieve(self, query: str) -> str:
        """Retrieve relevant document chunks based on query
        
        Args:
            query: Search query
            
        Returns:
            str: Concatenated relevant content
        """
        if not self.chunks:
            logger.warning("No documents available for retrieval")
            return ""

        try:
            # Transform query using existing vectorizer
            query_vector = self.vectorizer.transform([query])
            
            # Compute cosine similarity between query and document chunks
            scores = cosine_similarity(query_vector, self.vectors)[0]
            top_indices = np.argsort(scores)[-self.top_k:][::-1]  # Get top_k most relevant chunks
            
            # Filter low-confidence results
            retrieved_chunks = [self.chunks[i] for i in top_indices if scores[i] > 0.1]
            
            # Last used chunks for source tracking
            self.last_retrieved_chunks = retrieved_chunks
            
            # Merge chunks into a single context
            merged_context = "\n\n".join([chunk["text"] for chunk in retrieved_chunks])
            
            return merged_context

        except Exception as e:
            logger.exception(f"❌ Error retrieving content: {str(e)}")
            return ""

    def get_most_relevant_content(self) -> str:
        """Get most relevant content as fallback
        
        Returns:
            str: Combined content from top documents
        """
        if not self.chunks:
            return ""
            
        # Return top 3 documents by length as fallback
        sorted_chunks = sorted(self.chunks, key=lambda x: len(x["text"]), reverse=True)
        top_chunks = sorted_chunks[:3]
        self.last_retrieved_chunks = top_chunks
        
        return "\n\n".join([chunk["text"] for chunk in top_chunks])

    def get_documents_for_context(self, context: str) -> List[Document]:
        """Get the source documents used in the context
        
        Args:
            context: The context string
            
        Returns:
            List[Document]: Source documents
        """
        if not hasattr(self, 'last_retrieved_chunks'):
            return []
            
        return [chunk["document"] for chunk in self.last_retrieved_chunks]

    def hybrid_search(self, query: str) -> str:
        """Implement hybrid search for compatibility with VectorStore interface
        
        Args:
            query: Search query
            
        Returns:
            str: Retrieved context
        """
        # For keyword retriever, this is the same as regular retrieve
        return self.retrieve(query) 