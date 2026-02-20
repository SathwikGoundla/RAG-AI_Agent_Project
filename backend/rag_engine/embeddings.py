import logging
from typing import List
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"EmbeddingService initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Error initializing EmbeddingService: {e}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of texts."""
        if not texts:
            return []
        logger.debug(f"Generating embeddings for {len(texts)} texts.")
        embeddings = self.model.encode(texts).tolist()
        logger.debug(f"Generated {len(embeddings)} embeddings.")
        return embeddings

def get_embedding_service():
    return EmbeddingService()
