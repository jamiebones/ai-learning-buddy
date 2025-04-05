import logging
from typing import List
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize the model once as a module-level variable
_model = None

def get_model() -> SentenceTransformer:
    """Get or initialize the sentence transformer model."""
    global _model
    if _model is None:
        try:
            _model = SentenceTransformer(settings.DEFAULT_EMBEDDING_MODEL)
            logger.info(f"Initialized embedding model: {settings.DEFAULT_EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            raise
    return _model

def get_embeddings(text: str) -> List[float]:
    """Generate embeddings for a given text using sentence transformers.
    
    Args:
        text: The text to generate embeddings for
        
    Returns:
        List of floats representing the text embedding
    """
    try:
        model = get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        
        # Convert to list for JSON serialization
        embedding_list = embedding.tolist()
        
        logger.debug(f"Successfully generated embedding for text of length {len(text)}")
        return embedding_list
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise 