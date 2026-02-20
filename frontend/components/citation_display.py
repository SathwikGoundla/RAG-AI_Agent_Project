"""
Citation Display Component for Streamlit
Renders citations with confidence scores and source information
"""

import streamlit as st
from typing import List, Dict, Optional


def display_citation_badge(
    confidence: float,
    similarity: float,
    size: str = "small"
) -> str:
    """
    Create HTML badge showing confidence and similarity scores
    
    Args:
        confidence: Confidence score (0-1)
        similarity: Similarity score (0-1)
        size: Badge size ("small", "medium", "large")
        
    Returns:
        HTML badge string
    """
    # Determine colors based on scores
    conf_color = get_score_color(confidence)
    sim_color = get_score_color(similarity)
    
    size_styles = {
        "small": "font-size: 0.75rem; padding: 2px 6px;",
        "medium": "font-size: 0.9rem; padding: 4px 8px;",
        "large": "font-size: 1rem; padding: 6px 10px;"
    }
    
    style = size_styles.get(size, size_styles["small"])
    
    badge = f"""
    <span style="{style} background-color: {conf_color}; color: white; border-radius: 4px; margin-right: 4px; display: inline-block;">
        Conf: {confidence:.1%}
    </span>
    <span style="{style} background-color: {sim_color}; color: white; border-radius: 4px; margin-right: 4px; display: inline-block;">
        Sim: {similarity:.1%}
    </span>
    """
    return badge


def get_score_color(score: float) -> str:
    """Get color based on score value"""
    if score >= 0.85:
        return "#27AE60"  # Green
    elif score >= 0.70:
        return "#F39C12"  # Orange
    elif score >= 0.50:
        return "#E67E22"  # Dark Orange
    else:
        return "#E74C3C"  # Red


def display_single_citation(
    citation: Dict,
    index: int,
    expanded: bool = False
) -> None:
    """
    Display a single citation in an expandable container
    
    Args:
        citation: Citation dictionary with document, page, scores, excerpt
        index: Citation number
        expanded: Whether to show expanded initially
    """
    # Build citation header
    doc_name = citation.get("document", "Unknown")
    page = citation.get("page")
    chunk_idx = citation.get("chunk_index")
    confidence = citation.get("confidence", 0)
    similarity = citation.get("similarity", 0)
    excerpt = citation.get("excerpt", "")
    
    # Location info
    location_parts = []
    if page:
        location_parts.append(f"Page {page}")
    if chunk_idx is not None:
        location_parts.append(f"Chunk {chunk_idx}")
    
    location_str = f" ({', '.join(location_parts)})" if location_parts else ""
    
    # Citation header with scores
    header = f"**{index}. {doc_name}**{location_str}"
    
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(header)
        
        with col2:
            # Confidence indicator
            conf_label = get_confidence_label(confidence)
            conf_emoji = get_confidence_emoji(confidence)
            st.caption(f"{conf_emoji} {conf_label}")
        
        # Scores
        score_col1, score_col2 = st.columns(2)
        with score_col1:
            st.metric("Confidence", f"{confidence:.1%}")
        with score_col2:
            st.metric("Similarity", f"{similarity:.1%}")
        
        # Excerpt
        if excerpt:
            st.caption("**Excerpt:**")
            st.markdown(f"> {excerpt}")


def display_citations_section(
    citations: List[Dict],
    title: str = "📚 Sources",
    collapsed: bool = True,
    show_excerpts: bool = True
) -> None:
    """
    Display citations section with expander
    
    Args:
        citations: List of citation dictionaries
        title: Section title
        collapsed: Whether to show collapsed initially
        show_excerpts: Whether to show text excerpts
    """
    if not citations:
        st.info("No sources found for this response.")
        return
    
    with st.expander(f"{title} ({len(citations)})", expanded=not collapsed):
        st.markdown("---")
        
        for i, citation in enumerate(citations, 1):
            display_single_citation(citation, i)
        
        # Summary statistics
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_confidence = sum(c.get("confidence", 0) for c in citations) / len(citations)
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        
        with col2:
            avg_similarity = sum(c.get("similarity", 0) for c in citations) / len(citations)
            st.metric("Avg Similarity", f"{avg_similarity:.1%}")
        
        with col3:
            unique_docs = len(set(c.get("document") for c in citations))
            st.metric("Unique Sources", unique_docs)


def display_citation_inline(citation: Dict) -> str:
    """
    Get inline citation string for embedding in text
    
    Args:
        citation: Citation dictionary
        
    Returns:
        Inline citation string
    """
    doc = citation.get("document", "Source")
    page = citation.get("page")
    confidence = citation.get("confidence", 0)
    
    citation_str = f"[{doc}"
    if page:
        citation_str += f", p.{page}"
    citation_str += "]"
    
    if confidence > 0:
        citation_str += f"({confidence:.0%})"
    
    return citation_str


def display_explanation_box(
    answer: str,
    citations: List[Dict],
    model_used: str = "GPT-3.5-turbo",
    tokens_used: Optional[Dict] = None
) -> None:
    """
    Display answer with full explainability information
    
    Args:
        answer: The generated answer
        citations: List of citations
        model_used: Name of model used
        tokens_used: Token usage dictionary
    """
    # Main answer
    st.markdown("### Answer")
    st.write(answer)
    
    st.divider()
    
    # Explainability section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Explanation")
        display_citations_section(citations, collapsed=False)
    
    with col2:
        st.markdown("### Response Info")
        st.caption(f"**Model:** {model_used}")
        
        if tokens_used:
            st.metric("Prompt Tokens", tokens_used.get("prompt_tokens", 0))
            st.metric("Response Tokens", tokens_used.get("completion_tokens", 0))
            st.metric("Total Tokens", tokens_used.get("total_tokens", 0))


def get_confidence_label(confidence: float) -> str:
    """Get human-readable confidence label"""
    if confidence >= 0.9:
        return "Very High"
    elif confidence >= 0.75:
        return "High"
    elif confidence >= 0.6:
        return "Medium"
    elif confidence >= 0.4:
        return "Low"
    else:
        return "Very Low"


def get_confidence_emoji(confidence: float) -> str:
    """Get emoji for confidence level"""
    if confidence >= 0.9:
        return "🟢"  # Very High
    elif confidence >= 0.75:
        return "🟡"  # High
    elif confidence >= 0.6:
        return "🟠"  # Medium
    elif confidence >= 0.4:
        return "🔴"  # Low
    else:
        return "⚫"  # Very Low


def create_citation_table(citations: List[Dict]) -> None:
    """
    Display citations as a formatted table
    
    Args:
        citations: List of citation dictionaries
    """
    if not citations:
        st.info("No citations available")
        return
    
    # Prepare table data
    table_data = []
    for i, c in enumerate(citations, 1):
        table_data.append({
            "#": i,
            "Document": c.get("document", "Unknown"),
            "Page": c.get("page") or "-",
            "Chunk": c.get("chunk_index") or "-",
            "Confidence": f"{c.get('confidence', 0):.1%}",
            "Similarity": f"{c.get('similarity', 0):.1%}",
            "Status": get_confidence_emoji(c.get("confidence", 0))
        })
    
    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn(width="small")
        }
    )


def display_confidence_gauge(
    confidence: float,
    label: str = "Overall Confidence"
) -> None:
    """
    Display confidence as a gauge/progress indicator
    
    Args:
        confidence: Confidence score (0-1)
        label: Gauge label
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.progress(
            min(1.0, max(0.0, confidence)),
            text=f"{confidence:.1%}"
        )
    
    with col2:
        st.caption(label)


def export_citations_as_text(citations: List[Dict]) -> str:
    """
    Export citations as plain text
    
    Args:
        citations: List of citation dictionaries
        
    Returns:
        Plain text citations
    """
    lines = ["SOURCES & CITATIONS", "=" * 40, ""]
    
    for i, c in enumerate(citations, 1):
        doc = c.get("document", "Unknown")
        page = c.get("page")
        chunk = c.get("chunk_index")
        conf = c.get("confidence", 0)
        sim = c.get("similarity", 0)
        excerpt = c.get("excerpt", "")
        
        lines.append(f"{i}. {doc}")
        
        if page:
            lines.append(f"   Page: {page}")
        if chunk is not None:
            lines.append(f"   Chunk: {chunk}")
        
        lines.append(f"   Confidence: {conf:.1%}")
        lines.append(f"   Similarity: {sim:.1%}")
        
        if excerpt:
            lines.append(f"   Excerpt: {excerpt[:100]}...")
        
        lines.append("")
    
    return "\n".join(lines)
