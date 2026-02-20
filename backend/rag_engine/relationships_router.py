"""
Relationship API Router
Exposes document relationships, entity networks, and topic insights
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from backend.auth.security import get_current_active_user
from backend.models import UserOut
from backend.database import get_db
from backend.rag_engine.relationship_mapper import RelationshipMapper
from backend.rag_engine.relationship_store import RelationshipStore
from backend.rag_engine.retriever import RetrieverService, get_retriever_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/relationships", tags=["relationships"])

# Global instances
relationship_mapper = RelationshipMapper()
relationship_store = RelationshipStore()


# ============================================
# Pydantic Models
# ============================================

class DocumentListRequest(BaseModel):
    """Request for document relationship analysis"""
    document_ids: List[str]
    update_graphs: bool = False


class EntityNetworkRequest(BaseModel):
    """Request for entity network"""
    entity_type: Optional[str] = None


class ClusterRequest(BaseModel):
    """Request for document clustering"""
    similarity_threshold: float = 0.5


class RelatedDocumentRequest(BaseModel):
    """Request for related documents"""
    document_id: str
    relationship_type: Optional[str] = None


# ============================================
# Helper Functions
# ============================================

def get_retriever() -> RetrieverService:
    """Get retriever service"""
    return RetrieverService()


# ============================================
# Relationship Endpoints
# ============================================

@router.post("/analyze", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def analyze_relationships(
    request: DocumentListRequest,
    current_user: UserOut = Depends(get_current_active_user),
    retriever_service: RetrieverService = Depends(get_retriever_service),
    db = Depends(get_db)
):
    """
    Analyze relationships between documents
    Builds knowledge graph and extracts relationships
    
    Args:
        request: List of document IDs to analyze
        current_user: Authenticated user
        retriever_service: Retriever service
        db: Database connection
        
    Returns:
        Dictionary with relationship analysis results
    """
    try:
        logger.info(f"Analyzing relationships for {len(request.document_ids)} documents")
        
        # Retrieve documents
        documents = []
        for doc_id in request.document_ids:
            # This is a simplified approach - in production, fetch from your vector store
            documents.append({
                "id": doc_id,
                "content": f"Document {doc_id}",
                "source_file": "unknown"
            })
        
        if request.update_graphs:
            # Build knowledge graph
            relationship_mapper.build_knowledge_graph_from_documents(documents)
        
        # Get statistics
        graph_stats = relationship_mapper.get_graph_stats()
        topic_clusters = relationship_mapper.get_topic_clusters()
        
        # Get cross-document insights
        insights = []
        for doc_id in request.document_ids:
            insight = relationship_mapper.get_cross_document_insights(doc_id)
            if insight:
                insights.append(insight)
        
        return {
            "status": "success",
            "documents_analyzed": len(request.document_ids),
            "graph_statistics": graph_stats,
            "clusters": topic_clusters,
            "cross_document_insights": insights,
            "store_statistics": relationship_store.get_stats()
        }
    
    except Exception as e:
        logger.error(f"Error analyzing relationships: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze relationships: {str(e)}"
        )


@router.get("/document/{document_id}/insights", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_document_insights(
    document_id: str,
    current_user: UserOut = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get cross-document insights for a specific document
    
    Args:
        document_id: Document ID
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Dictionary with document insights
    """
    try:
        logger.info(f"Getting insights for document {document_id}")
        
        insights = relationship_mapper.get_cross_document_insights(document_id)
        
        if not insights:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No insights found for document {document_id}"
            )
        
        return {
            "status": "success",
            "insights": insights
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting document insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insights: {str(e)}"
        )


@router.post("/related-documents", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_related_documents(
    request: RelatedDocumentRequest,
    current_user: UserOut = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get documents related to a specific document
    
    Args:
        request: Document ID and optional relationship type
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        List of related documents
    """
    try:
        logger.info(f"Finding related documents for {request.document_id}")
        
        related = relationship_store.find_related_documents(
            request.document_id,
            relationship_type=request.relationship_type
        )
        
        return {
            "status": "success",
            "document_id": request.document_id,
            "related_documents": related,
            "count": len(related)
        }
    
    except Exception as e:
        logger.error(f"Error getting related documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get related documents: {str(e)}"
        )


@router.post("/topic-clusters", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_topic_clusters(
    request: ClusterRequest,
    current_user: UserOut = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get document clusters based on topic similarity
    
    Args:
        request: Clustering parameters
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        List of document clusters
    """
    try:
        logger.info(f"Finding topic clusters with threshold {request.similarity_threshold}")
        
        clusters = relationship_mapper.get_topic_clusters(request.similarity_threshold)
        
        return {
            "status": "success",
            "cluster_count": len(clusters),
            "clusters": clusters,
            "similarity_threshold": request.similarity_threshold
        }
    
    except Exception as e:
        logger.error(f"Error getting topic clusters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get clusters: {str(e)}"
        )


@router.get("/entity-network", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_entity_network(
    entity_type: Optional[str] = None,
    current_user: UserOut = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get entity network and relationships
    
    Args:
        entity_type: Optional filter by entity type (e.g., PERSON, ORG)
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Entity network with nodes and edges
    """
    try:
        logger.info(f"Getting entity network with type filter: {entity_type}")
        
        network = relationship_mapper.get_entity_network(entity_type)
        
        return {
            "status": "success",
            "entity_type_filter": entity_type,
            "network": network
        }
    
    except Exception as e:
        logger.error(f"Error getting entity network: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get entity network: {str(e)}"
        )


@router.get("/entity/{entity_name}/connections", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_entity_connections(
    entity_name: str,
    current_user: UserOut = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get documents connected through a specific entity
    
    Args:
        entity_name: Entity name to search
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Entity connection information
    """
    try:
        logger.info(f"Finding documents connected through entity: {entity_name}")
        
        connections = relationship_store.find_entity_connections(entity_name)
        
        return {
            "status": "success",
            "entity_connections": connections
        }
    
    except Exception as e:
        logger.error(f"Error getting entity connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get entity connections: {str(e)}"
        )


@router.get("/graph-statistics", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_graph_statistics(
    current_user: UserOut = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Get overall graph and relationship statistics
    
    Args:
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Graph statistics
    """
    try:
        logger.info("Getting graph statistics")
        
        graph_stats = relationship_mapper.get_graph_stats()
        store_stats = relationship_store.get_stats()
        topic_stats = relationship_mapper.topic_similarity.get_stats()
        
        return {
            "status": "success",
            "graph_statistics": graph_stats,
            "relationship_store_statistics": store_stats,
            "topic_similarity_statistics": topic_stats
        }
    
    except Exception as e:
        logger.error(f"Error getting graph statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/export-graph", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def export_relationship_graph(
    current_user: UserOut = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Export relationship graph for visualization
    
    Args:
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Graph data with nodes and edges
    """
    try:
        logger.info("Exporting relationship graph")
        
        graph_data = relationship_store.export_relationships_graph()
        
        return {
            "status": "success",
            "graph": graph_data
        }
    
    except Exception as e:
        logger.error(f"Error exporting graph: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export graph: {str(e)}"
        )
