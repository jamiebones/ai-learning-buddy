import uuid
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
from langchain.llms import OpenAI  # or HuggingFacePipeline for local models
from langchain.chains import RetrievalQA
from app.core.config import settings

# Initialize embeddings model
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize ChromaDB
persist_directory = "chroma_db"
vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

# Text splitter for chunking
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

def add_to_vector_store(note_id: uuid.UUID, text: str) -> None:
    """Process text and add to vector store with metadata."""
    # Split text into chunks
    chunks = text_splitter.split_text(text)
    
    # Create documents with metadata
    documents = [
        Document(page_content=chunk, metadata={"note_id": str(note_id), "chunk_id": i})
        for i, chunk in enumerate(chunks)
    ]
    
    # Add to vector store
    vectorstore.add_documents(documents)
    vectorstore.persist()

def query_notes(user_id: uuid.UUID, query: str) -> Dict[str, Any]:
    """Query the vector store to find relevant chunks and generate an answer."""
    # Initialize retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    # Initialize LLM
    llm = OpenAI(temperature=0, api_key=settings.OPENAI_API_KEY)
    
    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    
    # Run query
    result = qa_chain({"query": query})
    
    return {
        "answer": result["result"],
        "source_documents": [
            {
                "content": doc.page_content,
                "note_id": doc.metadata.get("note_id")
            } for doc in result["source_documents"]
        ]
    } 