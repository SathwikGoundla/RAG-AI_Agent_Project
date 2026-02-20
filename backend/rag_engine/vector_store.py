import chromadb
import logging
from typing import List, Dict, Any
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

from backend.config import settings

# Use ChromaDB's native embedding function
def get_embedding_function():
    """Get embedding function compatible with ChromaDB"""
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        return SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    except Exception as e:
        logger.error(f"Error loading embedding function: {e}")
        raise


class ChromaDBManager:
    def __init__(self, path: str = None):
        self.path = path or settings.CHROMA_PERSIST_DIRECTORY
        self.client = chromadb.PersistentClient(path=self.path)
        self.embedding_function = get_embedding_function()
        logger.info(f"ChromaDBManager initialized with path: {self.path}")

    def get_or_create_collection(self, collection_name: str):
        """Gets an existing collection or creates a new one with the specified embedding function."""
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function # Pass the callable instance
            )
            logger.info(f"ChromaDB collection \"{collection_name}\" retrieved or created.")
            return collection
        except Exception as e:
            logger.error(f"Error getting/creating ChromaDB collection {collection_name}: {e}")
            raise

    def get_collection(self, collection_name: str):
        """Gets an existing collection with embedding function."""
        try:
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"ChromaDB collection \"{collection_name}\" retrieved.")
            return collection
        except Exception as e:
            logger.error(f"Error getting ChromaDB collection {collection_name}: {e}")
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Collection {collection_name} not found")

    def delete_collection(self, collection_name: str):
        """Deletes a collection."""
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"ChromaDB collection \"{collection_name}\" deleted.")
        except Exception as e:
            logger.error(f"Error deleting ChromaDB collection {collection_name}: {e}")
            raise

def get_chroma_manager():
    return ChromaDBManager()
