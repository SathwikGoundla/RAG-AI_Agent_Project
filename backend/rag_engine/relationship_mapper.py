"""
Relationship Mapper Module
Maps relationships between documents and entities
Builds knowledge graphs from document content
Integrates topic similarity for cross-document reasoning
"""

from typing import List, Dict, Set, Tuple, Optional
import logging
import spacy
from spacy import displacy
import networkx as nx
from backend.rag_engine.topic_similarity import TopicSimilarity

logger = logging.getLogger(__name__)


class RelationshipMapper:
    """
    Extract and map relationships between documents and entities
    """
    
    def __init__(self):
        """Initialize relationship mapper"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded")
        except Exception as e:
            logger.warning(f"SpaCy model not loaded: {str(e)}. Some features will be limited.")
            self.nlp = None
        
        self.knowledge_graph = nx.DiGraph()
        self.topic_similarity = TopicSimilarity(min_similarity=0.3)
        self.documents = []
        logger.info("RelationshipMapper initialized")
    
    def extract_entities(self, text: str) -> List[Dict]:
        """
        Extract named entities from text
        
        Args:
            text: Input text
            
        Returns:
            List of entities with labels
        """
        if not self.nlp:
            logger.warning("SpaCy model not available")
            return []
        
        try:
            doc = self.nlp(text)
            entities = []
            
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
            
            logger.info(f"Extracted {len(entities)} entities")
            return entities
        
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return []
    
    def extract_relationships(self, text: str) -> List[Dict]:
        """
        Extract relationships between entities
        
        Args:
            text: Input text
            
        Returns:
            List of relationships
        """
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            relationships = []
            
            # Simple relationship extraction using dependency parsing
            for token in doc:
                if token.dep_ == "SUBJECT":
                    # Find object
                    for child in token.head.children:
                        if child.dep_ == "OBJECT":
                            relationships.append({
                                "subject": token.text,
                                "predicate": token.head.text,
                                "object": child.text,
                                "relation_type": "subject-verb-object"
                            })
            
            logger.info(f"Extracted {len(relationships)} relationships")
            return relationships
        
        except Exception as e:
            logger.error(f"Error extracting relationships: {str(e)}")
            return []
    
    def build_knowledge_graph_from_documents(self, documents: List[Dict]) -> nx.DiGraph:
        """
        Build knowledge graph from documents
        Includes entity extraction, relationships, and topic similarity
        
        Args:
            documents: List of document chunks
            
        Returns:
            NetworkX directed graph
        """
        graph = nx.DiGraph()
        self.documents = documents
        
        try:
            # Fit topic similarity model
            self.topic_similarity.fit(documents, text_field="content")
            
            for doc in documents:
                source_file = doc.get("source_file", "unknown")
                content = doc.get("content", "")
                chunk_id = doc.get("id", doc.get("chunk_id", ""))
                
                if not chunk_id:
                    continue
                
                # Add document node with metadata
                graph.add_node(
                    chunk_id,
                    type="document",
                    source=source_file,
                    content=content[:200],
                    chunk_index=doc.get("chunk_index", 0),
                    page_number=doc.get("page_number")
                )
                
                # Extract entities
                entities = self.extract_entities(content)
                
                # Add entity nodes and links
                for entity in entities:
                    entity_node = f"{entity['label']}:{entity['text']}"
                    graph.add_node(
                        entity_node,
                        type="entity",
                        label=entity['label'],
                        name=entity['text'],
                        document_id=chunk_id
                    )
                    graph.add_edge(chunk_id, entity_node, relation="contains_entity", weight=1.0)
                
                # Extract relationships
                relationships = self.extract_relationships(content)
                
                for rel in relationships:
                    subject = f"ENTITY:{rel['subject']}"
                    obj = f"ENTITY:{rel['object']}"
                    
                    if subject not in graph:
                        graph.add_node(subject, type="entity")
                    if obj not in graph:
                        graph.add_node(obj, type="entity")
                    
                    graph.add_edge(subject, obj, relation=rel['predicate'], weight=1.0)
            
            # Add topic similarity edges between documents
            for doc_id in [d.get("id", d.get("chunk_id")) for d in documents if d.get("id") or d.get("chunk_id")]:
                similar_docs = self.topic_similarity.get_similar_documents(doc_id, top_k=5)
                
                for similar_id, similarity_score in similar_docs:
                    if similar_id in graph and doc_id in graph:
                        graph.add_edge(
                            doc_id,
                            similar_id,
                            relation="topic_similar",
                            weight=similarity_score
                        )
            
            self.knowledge_graph = graph
            logger.info(f"Built knowledge graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
            
            return graph
        
        except Exception as e:
            logger.error(f"Error building knowledge graph: {str(e)}")
            return graph
    
    def find_related_documents(self, document_id: str, max_depth: int = 2) -> List[str]:
        """
        Find documents related to a given document
        
        Args:
            document_id: ID of reference document
            max_depth: Maximum depth for relationship search
            
        Returns:
            List of related document IDs
        """
        try:
            if document_id not in self.knowledge_graph:
                return []
            
            related = set()
            queue = [(document_id, 0)]
            
            while queue:
                node, depth = queue.pop(0)
                
                if depth > max_depth:
                    continue
                
                # Get connected nodes
                for successor in self.knowledge_graph.successors(node):
                    if successor not in related:
                        if self.knowledge_graph.nodes[successor].get("type") == "document":
                            related.add(successor)
                        queue.append((successor, depth + 1))
            
            return list(related)
        
        except Exception as e:
            logger.error(f"Error finding related documents: {str(e)}")
            return []
    
    def get_relationship_summary(self, document_id: str) -> Dict:
        """
        Get summary of relationships for a document
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with relationship summary
        """
        try:
            if document_id not in self.knowledge_graph:
                return {"error": "Document not found"}
            
            related_docs = self.find_related_documents(document_id)
            
            # Get entities in this document
            successors = list(self.knowledge_graph.successors(document_id))
            entities = [node for node in successors if self.knowledge_graph.nodes[node].get("type") == "entity"]
            
            return {
                "document_id": document_id,
                "related_documents": related_docs,
                "entities": entities,
                "entity_count": len(entities),
                "relationship_count": len(successors)
            }
        
        except Exception as e:
            logger.error(f"Error getting relationship summary: {str(e)}")
            return {}
    
    def get_graph_stats(self) -> Dict:
        """
        Get knowledge graph statistics
        
        Returns:
            Dictionary with graph stats
        """
        return {
            "nodes": self.knowledge_graph.number_of_nodes(),
            "edges": self.knowledge_graph.number_of_edges(),
            "density": nx.density(self.knowledge_graph),
            "components": nx.number_weakly_connected_components(self.knowledge_graph)
        }
    
    def get_topic_clusters(self, similarity_threshold: float = 0.5) -> List[Dict]:
        """
        Get document clusters based on topic similarity
        
        Args:
            similarity_threshold: Minimum similarity for clustering
            
        Returns:
            List of cluster dictionaries
        """
        try:
            clusters = self.topic_similarity.find_topic_clusters(similarity_threshold)
            
            return [
                {
                    "cluster_id": i,
                    "document_ids": list(cluster),
                    "size": len(cluster),
                    "keywords": self._extract_cluster_keywords(list(cluster))
                }
                for i, cluster in enumerate(clusters)
            ]
        
        except Exception as e:
            logger.error(f"Error getting topic clusters: {str(e)}")
            return []
    
    def get_cross_document_insights(self, document_id: str) -> Dict:
        """
        Get cross-document insights and relationships
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with cross-document insights
        """
        try:
            # Get similar documents by topic
            similar_docs = self.topic_similarity.get_similar_documents(document_id, top_k=5)
            
            # Get entities in this document
            successors = list(self.knowledge_graph.successors(document_id))
            entities = [
                {
                    "name": node,
                    "label": self.knowledge_graph.nodes[node].get("label", "UNKNOWN")
                }
                for node in successors
                if self.knowledge_graph.nodes[node].get("type") == "entity"
            ]
            
            # Get topic keywords
            keywords = self.topic_similarity.get_topic_keywords(document_id, top_k=10)
            
            # Find documents sharing same entities
            shared_entity_docs = set()
            for entity_node in [n for n in successors if self.knowledge_graph.nodes[n].get("type") == "entity"]:
                for pred in self.knowledge_graph.predecessors(entity_node):
                    if self.knowledge_graph.nodes[pred].get("type") == "document" and pred != document_id:
                        shared_entity_docs.add(pred)
            
            return {
                "document_id": document_id,
                "similar_documents": [
                    {"id": doc_id, "similarity": score}
                    for doc_id, score in similar_docs
                ],
                "shared_entity_documents": list(shared_entity_docs),
                "entities": entities,
                "entity_count": len(entities),
                "keywords": keywords,
                "related_documents": self.find_related_documents(document_id, max_depth=2)
            }
        
        except Exception as e:
            logger.error(f"Error getting cross-document insights: {str(e)}")
            return {}
    
    def get_entity_network(self, entity_type: Optional[str] = None) -> Dict:
        """
        Get network of entities and their relationships
        
        Args:
            entity_type: Filter by entity type (e.g., "PERSON", "ORG")
            
        Returns:
            Dictionary with entity network
        """
        try:
            nodes = []
            edges = []
            
            for node in self.knowledge_graph.nodes():
                if self.knowledge_graph.nodes[node].get("type") == "entity":
                    node_data = self.knowledge_graph.nodes[node]
                    label = node_data.get("label", "UNKNOWN")
                    
                    if entity_type and label != entity_type:
                        continue
                    
                    nodes.append({
                        "id": node,
                        "label": label,
                        "name": node_data.get("name", node)
                    })
            
            # Get relationships between entities
            for source in [n["id"] for n in nodes]:
                for target in self.knowledge_graph.successors(source):
                    if self.knowledge_graph.nodes[target].get("type") == "entity":
                        edges.append({
                            "source": source,
                            "target": target,
                            "relation": self.knowledge_graph[source][target].get("relation", "related")
                        })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "entity_count": len(nodes),
                "relationship_count": len(edges)
            }
        
        except Exception as e:
            logger.error(f"Error getting entity network: {str(e)}")
            return {"nodes": [], "edges": []}
    
    def _extract_cluster_keywords(self, document_ids: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Extract keywords for a cluster of documents
        
        Args:
            document_ids: List of document IDs in cluster
            top_k: Number of keywords to extract
            
        Returns:
            List of (keyword, score) tuples
        """
        try:
            if not document_ids:
                return []
            
            # Get keywords for each document and aggregate
            keyword_scores = {}
            
            for doc_id in document_ids:
                keywords = self.topic_similarity.get_topic_keywords(doc_id, top_k=10)
                for keyword, score in keywords:
                    keyword_scores[keyword] = keyword_scores.get(keyword, 0) + score
            
            # Sort by aggregated score and return top k
            sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_keywords[:top_k]
        
        except Exception as e:
            logger.error(f"Error extracting cluster keywords: {str(e)}")
            return []

