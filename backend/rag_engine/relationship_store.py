"""
Relationship Store Module
Persists and queries document relationships
Manages relationship storage and caching
"""

from typing import List, Dict, Optional, Set, Tuple
import logging
import json
from datetime import datetime
import networkx as nx

logger = logging.getLogger(__name__)


class RelationshipStore:
    """
    Stores and manages document relationships in memory and persistent storage
    """
    
    def __init__(self):
        """Initialize relationship store"""
        self.relationships = {}  # Maps document pairs to relationship data
        self.document_topics = {}  # Maps document ID to topic keywords
        self.document_entities = {}  # Maps document ID to extracted entities
        self.entity_index = {}  # Maps entity to documents containing it
        self.cluster_assignments = {}  # Maps document ID to cluster ID
        self.last_updated = None
        logger.info("RelationshipStore initialized")
    
    def store_relationship(self, doc_id1: str, doc_id2: str, relationship_data: Dict) -> None:
        """
        Store relationship between two documents
        
        Args:
            doc_id1: First document ID
            doc_id2: Second document ID
            relationship_data: Dictionary with relationship details
        """
        try:
            # Create canonical key (sorted for consistency)
            key = tuple(sorted([doc_id1, doc_id2]))
            
            self.relationships[key] = {
                **relationship_data,
                "doc_id1": doc_id1,
                "doc_id2": doc_id2,
                "timestamp": datetime.now().isoformat()
            }
            
            self.last_updated = datetime.now()
            logger.debug(f"Stored relationship between {doc_id1} and {doc_id2}")
        
        except Exception as e:
            logger.error(f"Error storing relationship: {str(e)}")
    
    def get_relationship(self, doc_id1: str, doc_id2: str) -> Optional[Dict]:
        """
        Get relationship between two documents
        
        Args:
            doc_id1: First document ID
            doc_id2: Second document ID
            
        Returns:
            Dictionary with relationship data or None
        """
        key = tuple(sorted([doc_id1, doc_id2]))
        return self.relationships.get(key)
    
    def store_document_topics(self, doc_id: str, topics: List[Tuple[str, float]]) -> None:
        """
        Store topic keywords for a document
        
        Args:
            doc_id: Document ID
            topics: List of (topic, score) tuples
        """
        self.document_topics[doc_id] = {
            "topics": topics,
            "timestamp": datetime.now().isoformat()
        }
        logger.debug(f"Stored {len(topics)} topics for document {doc_id}")
    
    def get_document_topics(self, doc_id: str) -> List[Tuple[str, float]]:
        """
        Get topics for a document
        
        Args:
            doc_id: Document ID
            
        Returns:
            List of (topic, score) tuples
        """
        return self.document_topics.get(doc_id, {}).get("topics", [])
    
    def store_document_entities(self, doc_id: str, entities: List[Dict]) -> None:
        """
        Store entities for a document
        
        Args:
            doc_id: Document ID
            entities: List of entity dictionaries
        """
        self.document_entities[doc_id] = {
            "entities": entities,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update entity index
        for entity in entities:
            entity_name = entity.get("text", "")
            if entity_name:
                if entity_name not in self.entity_index:
                    self.entity_index[entity_name] = set()
                self.entity_index[entity_name].add(doc_id)
        
        logger.debug(f"Stored {len(entities)} entities for document {doc_id}")
    
    def get_document_entities(self, doc_id: str) -> List[Dict]:
        """
        Get entities for a document
        
        Args:
            doc_id: Document ID
            
        Returns:
            List of entity dictionaries
        """
        return self.document_entities.get(doc_id, {}).get("entities", [])
    
    def get_documents_with_entity(self, entity: str) -> Set[str]:
        """
        Get all documents containing a specific entity
        
        Args:
            entity: Entity name
            
        Returns:
            Set of document IDs
        """
        return self.entity_index.get(entity, set())
    
    def store_cluster_assignment(self, doc_id: str, cluster_id: int) -> None:
        """
        Store cluster assignment for a document
        
        Args:
            doc_id: Document ID
            cluster_id: Cluster ID
        """
        self.cluster_assignments[doc_id] = cluster_id
        logger.debug(f"Assigned document {doc_id} to cluster {cluster_id}")
    
    def get_cluster_assignment(self, doc_id: str) -> Optional[int]:
        """
        Get cluster assignment for a document
        
        Args:
            doc_id: Document ID
            
        Returns:
            Cluster ID or None
        """
        return self.cluster_assignments.get(doc_id)
    
    def get_cluster_documents(self, cluster_id: int) -> Set[str]:
        """
        Get all documents in a cluster
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            Set of document IDs in cluster
        """
        return {
            doc_id for doc_id, cid in self.cluster_assignments.items()
            if cid == cluster_id
        }
    
    def find_related_documents(self, doc_id: str, relationship_type: Optional[str] = None) -> List[Dict]:
        """
        Find documents related to a given document
        
        Args:
            doc_id: Document ID
            relationship_type: Filter by relationship type (e.g., "topic_similar", "shared_entity")
            
        Returns:
            List of related document information
        """
        related = []
        
        for (d1, d2), rel_data in self.relationships.items():
            if d1 == doc_id or d2 == doc_id:
                other_doc_id = d2 if d1 == doc_id else d1
                
                if relationship_type and rel_data.get("type") != relationship_type:
                    continue
                
                related.append({
                    "document_id": other_doc_id,
                    "relationship_type": rel_data.get("type", "unknown"),
                    "similarity_score": rel_data.get("similarity_score", 0),
                    "strength": rel_data.get("strength", "weak")
                })
        
        return sorted(related, key=lambda x: x.get("similarity_score", 0), reverse=True)
    
    def find_entity_connections(self, entity: str) -> Dict:
        """
        Find connections between documents through an entity
        
        Args:
            entity: Entity name
            
        Returns:
            Dictionary with entity connection information
        """
        docs_with_entity = self.get_documents_with_entity(entity)
        
        connections = []
        for doc_id in docs_with_entity:
            doc_entities = self.get_document_entities(doc_id)
            entity_info = next(
                (e for e in doc_entities if e.get("text") == entity),
                None
            )
            
            if entity_info:
                connections.append({
                    "document_id": doc_id,
                    "entity_label": entity_info.get("label", "UNKNOWN"),
                    "entity_context": entity_info.get("context", "")
                })
        
        return {
            "entity": entity,
            "document_count": len(docs_with_entity),
            "documents": connections
        }
    
    def get_stats(self) -> Dict:
        """
        Get statistics about stored relationships
        
        Returns:
            Dictionary with store statistics
        """
        total_relationships = len(self.relationships)
        
        relationship_types = {}
        for rel_data in self.relationships.values():
            rel_type = rel_data.get("type", "unknown")
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        
        return {
            "total_relationships": total_relationships,
            "documents_with_topics": len(self.document_topics),
            "documents_with_entities": len(self.document_entities),
            "unique_entities": len(self.entity_index),
            "cluster_count": len(set(self.cluster_assignments.values())) if self.cluster_assignments else 0,
            "relationship_types": relationship_types,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
    
    def export_relationships_graph(self) -> Dict:
        """
        Export relationships as graph data
        
        Returns:
            Dictionary with nodes and edges for visualization
        """
        nodes = set()
        edges = []
        
        for (d1, d2), rel_data in self.relationships.items():
            nodes.add(d1)
            nodes.add(d2)
            
            edges.append({
                "source": d1,
                "target": d2,
                "relationship_type": rel_data.get("type", "unknown"),
                "weight": rel_data.get("similarity_score", 0.5)
            })
        
        return {
            "nodes": [{"id": node} for node in nodes],
            "edges": edges
        }
    
    def clear_store(self) -> None:
        """Clear all stored data"""
        self.relationships.clear()
        self.document_topics.clear()
        self.document_entities.clear()
        self.entity_index.clear()
        self.cluster_assignments.clear()
        self.last_updated = None
        logger.info("RelationshipStore cleared")
    
    def get_all_relationships(self, limit: int = 100) -> List[Dict]:
        """
        Get all stored relationships
        
        Args:
            limit: Maximum number of relationships to return
            
        Returns:
            List of relationship dictionaries
        """
        relationships = list(self.relationships.values())
        return relationships[:limit]
