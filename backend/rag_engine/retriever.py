import logging
from typing import List, Dict, Any, Optional
from fastapi import Depends

logger = logging.getLogger(__name__)

from backend.rag_engine.vector_store import ChromaDBManager, get_chroma_manager
from backend.rag_engine.embeddings import EmbeddingService, get_embedding_service
from backend.models import DocumentMetadata, ChunkMetadata

class RetrieverService:
    def __init__(self, chroma_manager: ChromaDBManager = get_chroma_manager(), embedding_service: EmbeddingService = get_embedding_service()):
        self.chroma_manager = chroma_manager
        self.embedding_service = embedding_service
        logger.info("RetrieverService initialized.")

    def retrieve_chunks(self, query_text: str, user_id: str, document_ids: Optional[List[str]] = None, n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieves relevant document chunks from ChromaDB based on the query."""
        logger.info(f"Retrieving {n_results} chunks for query: \"{query_text}\" (user: {user_id})")
        
        user_collection_name = f"user_{user_id}_documents"
        try:
            collection = self.chroma_manager.get_collection(user_collection_name)
        except Exception as e:
            logger.warning(f"User collection {user_collection_name} not found or error: {e}. Returning empty chunks.")
            return []

        # Optional: Filter by specific document_ids
        where_clause = {"user_id": user_id}
        if document_ids:
            where_clause["document_id"] = {"$in": document_ids}

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause,
                include=['documents', 'metadatas', 'distances']
            )

            retrieved_chunks = []
            if results and results["documents"] and results["metadatas"]:
                distances = results.get("distances", [[]])[0]
                
                for i in range(len(results["documents"][0])):
                    chunk_content = results["documents"][0][i]
                    metadata = results["metadatas"][0][i]
                    
                    # Convert distance to similarity score (cosine distance to similarity)
                    # ChromaDB returns distances, we convert to similarity (1 - normalized_distance)
                    distance = distances[i] if i < len(distances) else 0
                    similarity_score = max(0, 1 - distance) if distance else 0.9
                    
                    retrieved_chunks.append({
                        "content": chunk_content,
                        "metadata": metadata,
                        "similarity_score": similarity_score,
                        "distance": distance
                    })
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks for query: \"{query_text}\".")
            return retrieved_chunks
        except Exception as e:
            logger.error(f"Error retrieving chunks from ChromaDB for user {user_id}: {e}")
            return []

def get_retriever_service(chroma_manager: ChromaDBManager = Depends(get_chroma_manager), embedding_service: EmbeddingService = Depends(get_embedding_service)):
    return RetrieverService(chroma_manager, embedding_service)
