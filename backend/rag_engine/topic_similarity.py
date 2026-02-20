"""
Topic Similarity Module
Detects topic similarity and clustering between documents
Uses TF-IDF and cosine similarity for document comparison
"""

from typing import List, Dict, Tuple, Set
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


class TopicSimilarity:
    """
    Detects topic similarity between documents using TF-IDF and cosine similarity
    """
    
    def __init__(self, min_similarity: float = 0.3):
        """
        Initialize topic similarity detector
        
        Args:
            min_similarity: Minimum similarity threshold (0-1)
        """
        self.min_similarity = min_similarity
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            min_df=1,
            max_df=0.95,
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.document_texts = {}
        self.document_ids = []
        logger.info(f"TopicSimilarity initialized with min_similarity={min_similarity}")
    
    def fit(self, documents: List[Dict], text_field: str = "content") -> None:
        """
        Fit the TF-IDF vectorizer on documents
        
        Args:
            documents: List of document dictionaries
            text_field: Field name containing text content
        """
        try:
            texts = []
            self.document_ids = []
            self.document_texts = {}
            
            for doc in documents:
                doc_id = doc.get("id", doc.get("chunk_id", ""))
                text = doc.get(text_field, "")
                
                if doc_id and text:
                    texts.append(text)
                    self.document_ids.append(doc_id)
                    self.document_texts[doc_id] = text
            
            if texts:
                self.tfidf_matrix = self.vectorizer.fit_transform(texts)
                logger.info(f"Fitted TF-IDF on {len(texts)} documents")
            else:
                logger.warning("No documents provided for TF-IDF fitting")
        
        except Exception as e:
            logger.error(f"Error fitting TF-IDF: {str(e)}")
    
    def get_similar_documents(self, doc_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Get most similar documents to a given document
        
        Args:
            doc_id: Document ID
            top_k: Number of top similar documents to return
            
        Returns:
            List of (document_id, similarity_score) tuples
        """
        try:
            if self.tfidf_matrix is None or doc_id not in self.document_ids:
                return []
            
            idx = self.document_ids.index(doc_id)
            similarities = cosine_similarity(self.tfidf_matrix[idx], self.tfidf_matrix)[0]
            
            # Get top k similar documents (excluding self)
            similar_indices = np.argsort(-similarities)[1:top_k + 1]
            similar_docs = [
                (self.document_ids[i], float(similarities[i]))
                for i in similar_indices
                if similarities[i] >= self.min_similarity
            ]
            
            return similar_docs
        
        except Exception as e:
            logger.error(f"Error getting similar documents for {doc_id}: {str(e)}")
            return []
    
    def get_similarity_matrix(self) -> np.ndarray:
        """
        Get full similarity matrix for all documents
        
        Returns:
            NumPy array of similarity scores
        """
        if self.tfidf_matrix is None:
            return np.array([])
        
        return cosine_similarity(self.tfidf_matrix)
    
    def find_topic_clusters(self, similarity_threshold: float = 0.5) -> List[Set[str]]:
        """
        Find clusters of documents with similar topics
        
        Args:
            similarity_threshold: Minimum similarity for clustering
            
        Returns:
            List of document ID sets representing clusters
        """
        try:
            if self.tfidf_matrix is None or len(self.document_ids) == 0:
                return []
            
            similarity_matrix = self.get_similarity_matrix()
            
            # Union-find for clustering
            parent = {doc_id: doc_id for doc_id in self.document_ids}
            
            def find(x):
                if parent[x] != x:
                    parent[x] = find(parent[x])
                return parent[x]
            
            def union(x, y):
                px, py = find(x), find(y)
                if px != py:
                    parent[px] = py
            
            # Connect documents with similarity above threshold
            for i in range(len(self.document_ids)):
                for j in range(i + 1, len(self.document_ids)):
                    if similarity_matrix[i][j] >= similarity_threshold:
                        union(self.document_ids[i], self.document_ids[j])
            
            # Group by parent
            clusters = {}
            for doc_id in self.document_ids:
                root = find(doc_id)
                if root not in clusters:
                    clusters[root] = set()
                clusters[root].add(doc_id)
            
            logger.info(f"Found {len(clusters)} topic clusters")
            return list(clusters.values())
        
        except Exception as e:
            logger.error(f"Error finding topic clusters: {str(e)}")
            return []
    
    def get_topic_keywords(self, doc_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Extract top TF-IDF keywords for a document
        
        Args:
            doc_id: Document ID
            top_k: Number of keywords to extract
            
        Returns:
            List of (keyword, tfidf_score) tuples
        """
        try:
            if self.tfidf_matrix is None or doc_id not in self.document_ids:
                return []
            
            idx = self.document_ids.index(doc_id)
            tfidf_scores = self.tfidf_matrix[idx].toarray()[0]
            
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get top k keywords
            top_indices = np.argsort(-tfidf_scores)[:top_k]
            keywords = [
                (feature_names[i], float(tfidf_scores[i]))
                for i in top_indices
                if tfidf_scores[i] > 0
            ]
            
            return keywords
        
        except Exception as e:
            logger.error(f"Error getting topic keywords for {doc_id}: {str(e)}")
            return []
    
    def get_topic_distribution(self) -> Dict[str, float]:
        """
        Get distribution of topics across documents
        
        Returns:
            Dictionary mapping topics to prevalence
        """
        try:
            if self.tfidf_matrix is None:
                return {}
            
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Sum TF-IDF scores for each feature
            tfidf_sums = np.array(self.tfidf_matrix.sum(axis=0)).flatten()
            
            # Normalize
            total = tfidf_sums.sum()
            if total == 0:
                return {}
            
            tfidf_normalized = tfidf_sums / total
            
            # Get top topics
            top_indices = np.argsort(-tfidf_normalized)[:20]
            
            return {
                str(feature_names[i]): float(tfidf_normalized[i])
                for i in top_indices
                if tfidf_normalized[i] > 0
            }
        
        except Exception as e:
            logger.error(f"Error getting topic distribution: {str(e)}")
            return {}
    
    def compare_documents(self, doc_id1: str, doc_id2: str) -> Dict:
        """
        Compare two documents in detail
        
        Args:
            doc_id1: First document ID
            doc_id2: Second document ID
            
        Returns:
            Dictionary with comparison details
        """
        try:
            if self.tfidf_matrix is None:
                return {"error": "TF-IDF model not fitted"}
            
            if doc_id1 not in self.document_ids or doc_id2 not in self.document_ids:
                return {"error": "One or both documents not found"}
            
            idx1 = self.document_ids.index(doc_id1)
            idx2 = self.document_ids.index(doc_id2)
            
            similarity = float(cosine_similarity(
                self.tfidf_matrix[idx1],
                self.tfidf_matrix[idx2]
            )[0][0])
            
            keywords1 = self.get_topic_keywords(doc_id1, top_k=5)
            keywords2 = self.get_topic_keywords(doc_id2, top_k=5)
            
            return {
                "doc_id1": doc_id1,
                "doc_id2": doc_id2,
                "similarity_score": similarity,
                "keywords_doc1": keywords1,
                "keywords_doc2": keywords2,
                "are_similar": similarity >= self.min_similarity
            }
        
        except Exception as e:
            logger.error(f"Error comparing documents: {str(e)}")
            return {}
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the fitted model
        
        Returns:
            Dictionary with model statistics
        """
        if self.tfidf_matrix is None:
            return {"status": "not_fitted"}
        
        return {
            "documents_count": len(self.document_ids),
            "features_count": self.tfidf_matrix.shape[1],
            "matrix_shape": list(self.tfidf_matrix.shape),
            "sparsity": 1 - (self.tfidf_matrix.nnz / (self.tfidf_matrix.shape[0] * self.tfidf_matrix.shape[1]))
        }
