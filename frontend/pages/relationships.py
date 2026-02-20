"""
Document Relationships Visualization
Interactive graph and cluster visualization for document relationships
"""

import streamlit as st
import requests
import json
import pandas as pd
from typing import Optional, Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px

# Configuration
BACKEND_URL = st.secrets.get("backend_url", "http://localhost:8000")
API_V1_STR = "/api/v1"


def api_request(
    method: str,
    endpoint: str,
    json_data: Optional[Dict] = None,
    use_token: bool = True
) -> Optional[requests.Response]:
    """Make API request with automatic token injection"""
    headers = {}
    
    if use_token and st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        response = requests.request(
            method=method,
            url=url,
            json=json_data,
            headers=headers,
            timeout=30
        )
        return response
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


def visualize_relationship_graph(graph_data: Dict[str, Any]) -> None:
    """Visualize relationship graph using Plotly"""
    try:
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        if not nodes or not edges:
            st.warning("No relationship data to visualize")
            return
        
        # Create edge traces
        edge_x = []
        edge_y = []
        
        for edge in edges:
            x0, y0 = 0, 0  # Placeholder
            x1, y1 = 1, 1  # Placeholder
            edge_x.append(x0)
            edge_x.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            showlegend=False
        )
        
        # Create node traces
        node_x = []
        node_y = []
        node_text = []
        
        for i, node in enumerate(nodes):
            angle = (i / len(nodes)) * 2 * 3.14159  # Circle layout
            x = 10 * (1 + 0.1 * i % 10)
            y = 10 * (1 + 0.1 * (i // 10))
            
            node_x.append(x)
            node_y.append(y)
            node_text.append(node.get("id", f"Node {i}"))
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="top center",
            hoverinfo='text',
            marker=dict(
                showscale=True,
                color='#1f77b4',
                size=20,
                line=dict(width=2, color='white')
            )
        )
        
        fig = go.Figure(data=[edge_trace, node_trace])
        
        fig.update_layout(
            title="Document Relationship Network",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error visualizing graph: {str(e)}")


def visualize_clusters(clusters: List[Dict]) -> None:
    """Visualize document clusters"""
    try:
        if not clusters:
            st.info("No clusters found")
            return
        
        cluster_data = []
        for cluster in clusters:
            cluster_data.append({
                "Cluster ID": cluster.get("cluster_id"),
                "Document Count": cluster.get("size", 0),
                "Keywords": ", ".join([k[0] for k in cluster.get("keywords", [])[:3]])
            })
        
        df = pd.DataFrame(cluster_data)
        st.dataframe(df, use_container_width=True)
        
        # Visualization
        if len(cluster_data) > 0:
            cluster_sizes = [c["Document Count"] for c in cluster_data]
            cluster_ids = [f"Cluster {c['Cluster ID']}" for c in cluster_data]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=cluster_ids,
                    y=cluster_sizes,
                    marker=dict(color='indianred')
                )
            ])
            
            fig.update_layout(
                title="Document Distribution Across Clusters",
                xaxis_title="Cluster",
                yaxis_title="Document Count"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error visualizing clusters: {str(e)}")


def visualize_entity_network(network: Dict[str, Any]) -> None:
    """Visualize entity network"""
    try:
        nodes = network.get("nodes", [])
        edges = network.get("edges", [])
        
        if not nodes:
            st.info("No entities found")
            return
        
        # Create a summary table
        entity_data = []
        for node in nodes:
            entity_data.append({
                "Entity": node.get("id"),
                "Label": node.get("label", "UNKNOWN")
            })
        
        df = pd.DataFrame(entity_data)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(df, use_container_width=True)
        
        with col2:
            st.metric("Total Entities", len(nodes))
            st.metric("Total Relationships", len(edges))
    
    except Exception as e:
        st.error(f"Error visualizing entity network: {str(e)}")


def main():
    """Main relationship visualization page"""
    try:
        st.set_page_config(page_title="Relationship Analysis", layout="wide")
        
        st.header("📊 Document Relationship Analysis")
        st.markdown("Explore relationships, clusters, and entities across your documents.")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔗 Relationships",
            "📈 Clusters",
            "🏷️ Entities",
            "📄 Document Insights",
            "📊 Statistics"
        ])
        
        # ============================================
        # Relationships Tab
        # ============================================
        with tab1:
            st.subheader("Document Relationships")
        st.markdown("Analyze relationships between your documents")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            document_ids = st.text_area(
                "Enter document IDs (one per line)",
                placeholder="doc_1\ndoc_2\ndoc_3",
                height=100
            )
        
        with col2:
            update_graph = st.checkbox("Update Knowledge Graph", value=True)
            analyze_btn = st.button("Analyze Relationships", type="primary", use_container_width=True)
        
        if analyze_btn and document_ids:
            doc_list = [d.strip() for d in document_ids.split("\n") if d.strip()]
            
            with st.spinner("Analyzing relationships..."):
                response = api_request(
                    "POST",
                    f"{API_V1_STR}/relationships/analyze",
                    json_data={
                        "document_ids": doc_list,
                        "update_graphs": update_graph
                    }
                )
            
            if response and response.status_code == 200:
                data = response.json()
                
                st.success("✅ Analysis complete!")
                
                # Display statistics
                col1, col2, col3, col4 = st.columns(4)
                
                graph_stats = data.get("graph_statistics", {})
                with col1:
                    st.metric("Graph Nodes", graph_stats.get("nodes", 0))
                with col2:
                    st.metric("Graph Edges", graph_stats.get("edges", 0))
                with col3:
                    st.metric("Graph Density", f"{graph_stats.get('density', 0):.2f}")
                with col4:
                    st.metric("Components", graph_stats.get("components", 0))
                
                st.divider()
                
                # Display insights
                insights = data.get("cross_document_insights", [])
                if insights:
                    st.subheader("Cross-Document Insights")
                    
                    for insight in insights:
                        with st.expander(f"Document: {insight.get('document_id')}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Similar Documents**")
                                similar = insight.get("similar_documents", [])
                                for doc in similar:
                                    st.write(f"- {doc['id']} (Similarity: {doc['similarity']:.2%})")
                            
                            with col2:
                                st.markdown("**Keywords**")
                                keywords = insight.get("keywords", [])
                                for keyword, score in keywords[:5]:
                                    st.write(f"- {keyword} ({score:.2f})")
            else:
                st.error("Failed to analyze relationships")
        
        # ============================================
        # Clusters Tab
        # ============================================
        with tab2:
            st.subheader("Topic Clusters")
            st.markdown("Documents grouped by topic similarity")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                threshold = st.slider(
                    "Similarity Threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.05
                )
            
            with col2:
                cluster_btn = st.button("Find Clusters", type="primary", use_container_width=True)
            
            if cluster_btn:
                with st.spinner("Finding clusters..."):
                    response = api_request(
                        "POST",
                        f"{API_V1_STR}/relationships/topic-clusters",
                        json_data={"similarity_threshold": threshold}
                    )
                
                if response and response.status_code == 200:
                    data = response.json()
                    clusters = data.get("clusters", [])
                    
                    st.success(f"✅ Found {len(clusters)} clusters")
                    
                    visualize_clusters(clusters)
                else:
                    st.error("Failed to find clusters")
        
        # ============================================
        # Entities Tab
        # ============================================
        with tab3:
            st.subheader("Entity Network")
            st.markdown("Named entities and their relationships")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                entity_type = st.selectbox(
                    "Filter by Entity Type",
                    ["None", "PERSON", "ORG", "GPE", "PRODUCT"],
                    index=0
                )
            
            with col2:
                entity_btn = st.button("Load Entities", type="primary", use_container_width=True)
            
            if entity_btn:
                with st.spinner("Loading entity network..."):
                    response = api_request(
                        "GET",
                        f"{API_V1_STR}/relationships/entity-network?entity_type={entity_type if entity_type != 'None' else ''}",
                    )
                
                if response and response.status_code == 200:
                    data = response.json()
                    network = data.get("network", {})
                    
                    st.success("✅ Entity network loaded")
                    
                    visualize_entity_network(network)
                else:
                    st.error("Failed to load entity network")
            
            st.divider()
            
            # Entity connections
            st.subheader("Entity Connections")
            entity_search = st.text_input("Search entity:", placeholder="Enter entity name")
            
            if entity_search:
                with st.spinner("Searching for connections..."):
                    response = api_request(
                        "GET",
                        f"{API_V1_STR}/relationships/entity/{entity_search}/connections"
                    )
                
                if response and response.status_code == 200:
                    data = response.json()
                    connections = data.get("entity_connections", {})
                    
                    st.write(f"**Entity:** {connections.get('entity')}")
                    st.write(f"**Found in {connections.get('document_count')} documents**")
                    
                    docs = connections.get("documents", [])
                    for doc in docs:
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write(f"**Document:** {doc['document_id']}")
                        with col2:
                            st.write(f"Label: {doc['entity_label']}")
                else:
                    st.error("Entity not found")
        
        # ============================================
        # Document Insights Tab
        # ============================================
        with tab4:
            st.subheader("Document Insights")
            st.markdown("Detailed insights for a specific document")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                doc_id = st.text_input(
                    "Document ID",
                    placeholder="Enter document ID"
                )
            
            with col2:
                insights_btn = st.button("Get Insights", type="primary", use_container_width=True)
            
            if insights_btn and doc_id:
                with st.spinner("Loading insights..."):
                    response = api_request(
                        "GET",
                        f"{API_V1_STR}/relationships/document/{doc_id}/insights"
                    )
                
                if response and response.status_code == 200:
                    data = response.json()
                    insights = data.get("insights", {})
                    
                    st.success("✅ Insights loaded")
                    
                    # Display insights in tabs
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Similar Documents")
                        similar = insights.get("similar_documents", [])
                        for doc in similar:
                            st.write(f"- {doc['id']} ({doc['similarity']:.2%})")
                    
                    with col2:
                        st.subheader("Keywords")
                        keywords = insights.get("keywords", [])
                        for keyword, score in keywords[:10]:
                            st.write(f"- {keyword}")
                    
                    st.divider()
                    
                    st.subheader("Entities")
                    entities = insights.get("entities", [])
                    entity_df = pd.DataFrame(entities)
                    st.dataframe(entity_df, use_container_width=True)
                else:
                    st.error(f"Failed to get insights for document {doc_id}")
        
        # ============================================
        # Statistics Tab
        # ============================================
        with tab5:
            st.subheader("Relationship Statistics")
            
            stats_btn = st.button("Refresh Statistics", type="primary", use_container_width=True)
            
            if stats_btn:
                with st.spinner("Loading statistics..."):
                    response = api_request(
                        "GET",
                        f"{API_V1_STR}/relationships/graph-statistics"
                    )
                
                if response and response.status_code == 200:
                    data = response.json()
                    
                    # Graph statistics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    graph_stats = data.get("graph_statistics", {})
                    with col1:
                        st.metric("Total Nodes", graph_stats.get("nodes", 0))
                    with col2:
                        st.metric("Total Edges", graph_stats.get("edges", 0))
                    with col3:
                        st.metric("Density", f"{graph_stats.get('density', 0):.3f}")
                    with col4:
                        st.metric("Components", graph_stats.get("components", 0))
                    
                    st.divider()
                    
                    # Store statistics
                    st.subheader("Relationship Store Statistics")
                    store_stats = data.get("relationship_store_statistics", {})
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Relationships", store_stats.get("total_relationships", 0))
                    with col2:
                        st.metric("Unique Entities", store_stats.get("unique_entities", 0))
                    with col3:
                        st.metric("Document Clusters", store_stats.get("cluster_count", 0))
                    
                    st.divider()
                    
                    # Relationship types
                    st.subheader("Relationship Types Distribution")
                    rel_types = store_stats.get("relationship_types", {})
                    if rel_types:
                        rel_df = pd.DataFrame([
                            {"Type": k, "Count": v} for k, v in rel_types.items()
                        ])
                        st.dataframe(rel_df, use_container_width=True)
                else:
                    st.error("Failed to load statistics")
    
    except Exception as e:
        st.error(f"❌ Error loading relationship analysis: {str(e)}")
        st.info("This feature requires the relationships API endpoint. Please ensure the backend is running and try again.")


if __name__ == "__main__":
    main()
