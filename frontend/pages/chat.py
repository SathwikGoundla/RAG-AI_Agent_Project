"""
Chat & Query Interface for Advanced RAG System
Real-time conversation with AI about your documents
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List

# Import citation display components
import sys
sys.path.append(".")
try:
    from frontend.components.citation_display import (
        display_citations_section,
        display_single_citation,
        get_confidence_emoji,
        get_confidence_label,
        create_citation_table
    )
except ImportError:
    # Fallback if import fails
    display_citations_section = None

# ============================================
# Configuration
# ============================================

BACKEND_URL = st.secrets.get("backend_url", "http://localhost:8000")
API_V1_STR = "/api/v1"
MAX_MESSAGE_LENGTH = 5000

# ============================================
# API Helper Functions
# ============================================

def api_request(
    method: str,
    endpoint: str,
    json_data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    use_token: bool = True
) -> Optional[requests.Response]:
    """Make API request with automatic token injection and error handling."""
    if headers is None:
        headers = {}
    
    if use_token and st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        response = requests.request(
            method=method,
            url=url,
            json=json_data,
            params=params,
            headers=headers,
            timeout=30
        )
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Is the server running?")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timeout. Please try again.")
        return None
    except Exception as e:
        st.error(f"❌ Request error: {str(e)}")
        return None

# ============================================
# Chat Functions
# ============================================

def send_chat_message(message: str, language: str = "english") -> Optional[Dict]:
    """Send a chat message and get response."""
    response = api_request(
        "POST",
        f"{API_V1_STR}/rag/chat",
        json_data={
            "message": message,
            "language": language,
            "include_context": True
        }
    )
    
    if response and response.status_code == 200:
        return response.json()
    elif response:
        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        return None
    return None


def query_documents(question: str, language: str = "english", n_results: int = 5) -> Optional[Dict]:
    """Query documents without chat history."""
    response = api_request(
        "POST",
        f"{API_V1_STR}/rag/query",
        json_data={
            "question": question,
            "language": language,
            "n_results": n_results
        }
    )
    
    if response and response.status_code == 200:
        return response.json()
    elif response:
        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        return None
    return None


def search_documents(query: str, language: str = "english", n_results: int = 5) -> Optional[List[Dict]]:
    """Search documents without generating answer with bilingual support."""
    response = api_request(
        "POST",
        f"{API_V1_STR}/rag/search",
        json_data={
            "question": query,
            "language": language,
            "n_results": n_results
        }
    )
    
    if response and response.status_code == 200:
        return response.json()
    elif response:
        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        return None
    return None


# ============================================
# Display Helper Functions
# ============================================

def display_search_results(results: List[Dict]):
    """Display search results with language metadata and similarity scores."""
    if not results:
        st.info("No results found")
        return
    
    for i, result in enumerate(results, 1):
        with st.container(border=True):
            # Header with document info
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                filename = result.get("filename", "Unknown document")
                chunk_id = result.get("chunk_id", "")
                header = f"**{i}. {filename}**"
                if chunk_id:
                    header += f" (ID: {chunk_id})"
                st.markdown(header)
            
            with col2:
                if "similarity_score" in result:
                    similarity = result.get("similarity_score", 0)
                    similarity_emoji = "🟢" if similarity >= 0.8 else "🟡" if similarity >= 0.6 else "🟠"
                    st.metric("Relevance", f"{similarity:.0%}", f"{similarity_emoji}")
            
            with col3:
                query_lang = result.get("query_language", "english")
                lang_emoji = "🇺🇸" if query_lang == "english" else "🇮🇳"
                st.metric("Query Lang", query_lang[:3].upper(), f"{lang_emoji}")
            
            # Display page and chunk info
            page_info = []
            if "page_number" in result and result["page_number"]:
                page_info.append(f"Page {result['page_number']}")
            if "chunk_type" in result:
                page_info.append(f"Type: {result['chunk_type']}")
            
            if page_info:
                st.caption(" | ".join(page_info))
            
            # Display content preview
            content = result.get("content", "")
            if content:
                st.markdown("**Content Preview:**")
                # Limit preview to 300 chars
                preview = content[:300] + ("..." if len(content) > 300 else "")
                st.markdown(f"> {preview}")
            
            st.divider()


# ============================================
# Main Chat Page
# ============================================

def display_message(role: str, content: str, sources: Optional[List[Dict]] = None):
    """Display a chat message with enhanced citations and confidence scores."""
    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(content)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.write(content)
            
            if sources and len(sources) > 0:
                # Display citations section
                st.divider()
                st.markdown("### 📚 Sources & Citations")
                
                # Show summary statistics
                col1, col2, col3 = st.columns(3)
                
                avg_confidence = sum(s.get("confidence", 0) for s in sources) / len(sources)
                avg_similarity = sum(s.get("similarity", 0) for s in sources) / len(sources)
                
                with col1:
                    emoji = get_confidence_emoji(avg_confidence) if 'get_confidence_emoji' in dir() else "📊"
                    st.metric("Avg Confidence", f"{avg_confidence:.1%}", f"{emoji}")
                
                with col2:
                    st.metric("Avg Similarity", f"{avg_similarity:.1%}")
                
                with col3:
                    st.metric("Sources", len(sources))
                
                st.divider()
                
                # Display individual citations
                with st.expander(f"Show Citation Details ({len(sources)} sources)", expanded=False):
                    for i, source in enumerate(sources, 1):
                        doc_name = source.get("document", source.get("filename", "Unknown"))
                        page = source.get("page")
                        chunk_idx = source.get("chunk_index")
                        confidence = source.get("confidence", 0)
                        similarity = source.get("similarity", 0)
                        excerpt = source.get("excerpt", "")
                        
                        # Citation header
                        with st.container(border=True):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                # Document name with location
                                header = f"**{i}. {doc_name}**"
                                if page:
                                    header += f" (Page {page})"
                                if chunk_idx is not None:
                                    header += f" [Chunk {chunk_idx}]"
                                st.markdown(header)
                            
                            with col2:
                                # Confidence badge
                                conf_emoji = "🟢" if confidence >= 0.85 else "🟡" if confidence >= 0.7 else "🟠" if confidence >= 0.5 else "🔴"
                                conf_label = "High" if confidence >= 0.85 else "Med" if confidence >= 0.6 else "Low"
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
            else:
                st.caption("ℹ️ No sources used for this response")


def display_search_results(results: List[Dict]):
    """Display search results with confidence and similarity badges."""
    if not results:
        st.info("No documents found matching your search.")
        return
    
    for idx, result in enumerate(results, 1):
        with st.container(border=True):
            # Header with document name and badges
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                doc_name = result.get("document", result.get("filename", "Unknown"))
                st.markdown(f"**{idx}. {doc_name}**")
                
                # Location info
                if result.get("page"):
                    st.caption(f"📄 Page {result['page']}")
                if result.get("chunk_index") is not None:
                    st.caption(f"📍 Chunk {result['chunk_index']}")
            
            # Confidence badge
            with col2:
                confidence = result.get("confidence", result.get("relevance_score", 0))
                if isinstance(confidence, str):
                    confidence = float(confidence.rstrip('%')) / 100 if '%' in confidence else 0
                
                conf_emoji = "🟢" if confidence >= 0.85 else "🟡" if confidence >= 0.7 else "🟠" if confidence >= 0.5 else "🔴"
                st.metric("Confidence", f"{confidence:.0%}", f"{conf_emoji}")
            
            # Similarity badge
            with col3:
                similarity = result.get("similarity", result.get("distance", 0))
                if isinstance(similarity, str):
                    try:
                        similarity = float(similarity)
                    except:
                        similarity = 0
                
                # Convert distance to similarity if needed
                if similarity < 1:  # Likely a distance value
                    similarity = max(0, 1 - similarity)
                
                st.metric("Similarity", f"{similarity:.0%}")
            
            # Chunk type
            with col4:
                chunk_type = result.get("chunk_type", "text").upper()
                st.metric("Type", chunk_type)
            
            st.divider()
            
            # Content preview
            content = result.get("content", result.get("excerpt", ""))
            if content:
                st.caption("**Content Preview:**")
                st.markdown(f"> {content[:250]}{'...' if len(content) > 250 else ''}")


# ============================================
# Page Layout
# ============================================

def main():
    """Main chat page."""
    st.header("💬 AI Chat")
    st.markdown("Ask questions about your uploaded documents. The AI will search your knowledge base and provide answers with sources.")
    
    # Initialize session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_mode" not in st.session_state:
        st.session_state.chat_mode = "chat"  # "chat", "query", "search"
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "english"
    
    # Create tabs
    chat_tab, query_tab, search_tab = st.tabs(["💬 Chat", "❓ Single Query", "🔍 Search"])
    
    # ============================================
    # Chat Tab
    # ============================================
    with chat_tab:
        st.subheader("Conversation with AI")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("Have a multi-turn conversation. The AI will remember context.")
        with col2:
            language = st.selectbox(
                "Language",
                ["english", "telugu"],
                key="chat_language",
                label_visibility="collapsed"
            )
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
        
        st.divider()
        
        # Display chat history
        for message in st.session_state.chat_messages:
            if message["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(message["content"])
                    
                    # Display citations if available
                    if message.get("sources") and len(message["sources"]) > 0:
                        sources = message["sources"]
                        st.divider()
                        st.markdown("### 📚 Sources & Citations")
                        
                        # Calculate averages
                        avg_confidence = sum(s.get("confidence", 0) for s in sources) / len(sources)
                        avg_similarity = sum(s.get("similarity", 0) for s in sources) / len(sources)
                        
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            conf_emoji = "🟢" if avg_confidence >= 0.85 else "🟡" if avg_confidence >= 0.7 else "🟠" if avg_confidence >= 0.5 else "🔴"
                            st.metric("Avg Confidence", f"{avg_confidence:.0%}", f"{conf_emoji}")
                        with col2:
                            st.metric("Avg Similarity", f"{avg_similarity:.0%}")
                        with col3:
                            st.metric("Sources", len(sources))
                        
                        st.divider()
                        
                        # Display citations
                        with st.expander(f"Show Citation Details ({len(sources)} sources)", expanded=False):
                            for i, source in enumerate(sources, 1):
                                doc_name = source.get("document", source.get("filename", "Unknown"))
                                page = source.get("page")
                                chunk_idx = source.get("chunk_index")
                                confidence = source.get("confidence", 0)
                                similarity = source.get("similarity", 0)
                                excerpt = source.get("excerpt", "")
                                
                                with st.container(border=True):
                                    col1, col2 = st.columns([3, 1])
                                    
                                    with col1:
                                        header = f"**{i}. {doc_name}**"
                                        if page:
                                            header += f" (Page {page})"
                                        if chunk_idx is not None:
                                            header += f" [Chunk {chunk_idx}]"
                                        st.markdown(header)
                                    
                                    with col2:
                                        conf_emoji = "🟢" if confidence >= 0.85 else "🟡" if confidence >= 0.7 else "🟠" if confidence >= 0.5 else "🔴"
                                        conf_label = "High" if confidence >= 0.85 else "Med" if confidence >= 0.6 else "Low"
                                        st.caption(f"{conf_emoji} {conf_label}")
                                    
                                    # Scores
                                    score_col1, score_col2 = st.columns(2)
                                    with score_col1:
                                        st.metric("Confidence", f"{confidence:.0%}")
                                    with score_col2:
                                        st.metric("Similarity", f"{similarity:.0%}")
                                    
                                    # Excerpt
                                    if excerpt:
                                        st.caption("**Excerpt:**")
                                        st.markdown(f"> {excerpt}")
        
        # Chat input
        if user_input := st.chat_input(
            "Ask a question about your documents...",
            max_chars=MAX_MESSAGE_LENGTH
        ):
            # Add user message
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Display user message
            with st.chat_message("user", avatar="👤"):
                st.write(user_input)
            
            # Get AI response
            with st.spinner("🤔 Thinking..."):
                response = send_chat_message(user_input, language=language)
            
            if response:
                # Extract sources/citations from response
                sources = response.get("sources", response.get("citations", []))
                
                assistant_message = {
                    "role": "assistant",
                    "content": response.get("message", "No response"),
                    "sources": sources
                }
                st.session_state.chat_messages.append(assistant_message)
                
                # Display response with citations
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(response.get("message", ""))
                    
                    # Display citations
                    if sources and len(sources) > 0:
                        st.divider()
                        st.markdown("### 📚 Sources & Citations")
                        
                        # Calculate averages
                        avg_confidence = sum(s.get("confidence", 0) for s in sources) / len(sources)
                        avg_similarity = sum(s.get("similarity", 0) for s in sources) / len(sources)
                        
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            conf_emoji = "🟢" if avg_confidence >= 0.85 else "🟡" if avg_confidence >= 0.7 else "🟠" if avg_confidence >= 0.5 else "🔴"
                            st.metric("Avg Confidence", f"{avg_confidence:.0%}", f"{conf_emoji}")
                        with col2:
                            st.metric("Avg Similarity", f"{avg_similarity:.0%}")
                        with col3:
                            st.metric("Sources", len(sources))
                        
                        st.divider()
                        
                        # Display citations
                        with st.expander(f"Show Citation Details ({len(sources)} sources)", expanded=False):
                            for i, source in enumerate(sources, 1):
                                doc_name = source.get("document", source.get("filename", "Unknown"))
                                page = source.get("page")
                                chunk_idx = source.get("chunk_index")
                                confidence = source.get("confidence", 0)
                                similarity = source.get("similarity", 0)
                                excerpt = source.get("excerpt", "")
                                
                                with st.container(border=True):
                                    col1, col2 = st.columns([3, 1])
                                    
                                    with col1:
                                        header = f"**{i}. {doc_name}**"
                                        if page:
                                            header += f" (Page {page})"
                                        if chunk_idx is not None:
                                            header += f" [Chunk {chunk_idx}]"
                                        st.markdown(header)
                                    
                                    with col2:
                                        conf_emoji = "🟢" if confidence >= 0.85 else "🟡" if confidence >= 0.7 else "🟠" if confidence >= 0.5 else "🔴"
                                        conf_label = "High" if confidence >= 0.85 else "Med" if confidence >= 0.6 else "Low"
                                        st.caption(f"{conf_emoji} {conf_label}")
                                    
                                    # Scores
                                    score_col1, score_col2 = st.columns(2)
                                    with score_col1:
                                        st.metric("Confidence", f"{confidence:.0%}")
                                    with score_col2:
                                        st.metric("Similarity", f"{similarity:.0%}")
                                    
                                    # Excerpt
                                    if excerpt:
                                        st.caption("**Excerpt:**")
                                        st.markdown(f"> {excerpt}")
    
    # ============================================
    # Query Tab
    # ============================================
    with query_tab:
        st.subheader("Single Query (No History)")
        st.caption("Ask a one-off question without conversation history.")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            question = st.text_area(
                "Your question",
                max_chars=MAX_MESSAGE_LENGTH,
                height=100,
                label_visibility="collapsed",
                placeholder="Ask a question..."
            )
        
        with col2:
            language = st.selectbox(
                "Language",
                ["english", "telugu"],
                key="query_language"
            )
        
        with col3:
            n_results = st.number_input(
                "Sources",
                min_value=1,
                max_value=10,
                value=5,
                key="query_results"
            )
        
        if st.button("📤 Submit Query", use_container_width=True, type="primary"):
            if not question or len(question.strip()) == 0:
                st.error("❌ Please enter a question")
            else:
                with st.spinner("🤔 Processing..."):
                    response = query_documents(question, language=language, n_results=n_results)
                
                if response:
                    st.success("✅ Query processed successfully!")
                    
                    # Main answer display
                    st.markdown("### 📝 Answer")
                    st.write(response.get("answer", ""))
                    
                    # Statistics
                    st.divider()
                    st.markdown("### 📊 Response Statistics")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    usage = response.get("tokens_used", {})
                    with col1:
                        st.metric("Tokens Used", usage.get("total_tokens", 0))
                    with col2:
                        st.metric("Sources Used", response.get("context_count", 0))
                    with col3:
                        model = response.get("model", "Phi3 (Local Ollama)")
                        st.metric("Model", model.split("-")[-1])
                    with col4:
                        language_used = response.get("language", "en").upper()
                        st.metric("Language", language_used)
                    
                    st.divider()
                    
                    # Display sources with citations and confidence
                    sources = response.get("sources", response.get("citations", []))
                    if sources:
                        st.markdown(f"### 📚 Sources & Citations ({len(sources)} sources)")
                        
                        # Calculate averages
                        avg_confidence = sum(s.get("confidence", 0) for s in sources) / len(sources)
                        avg_similarity = sum(s.get("similarity", 0) for s in sources) / len(sources)
                        
                        # Summary metrics
                        summ_col1, summ_col2 = st.columns(2)
                        with summ_col1:
                            conf_emoji = "🟢" if avg_confidence >= 0.85 else "🟡" if avg_confidence >= 0.7 else "🟠" if avg_confidence >= 0.5 else "🔴"
                            st.metric("Average Confidence", f"{avg_confidence:.1%}", f"{conf_emoji}")
                        with summ_col2:
                            st.metric("Average Similarity", f"{avg_similarity:.1%}", "📈")
                        
                        st.divider()
                        
                        # Detailed citations
                        for i, source in enumerate(sources, 1):
                            doc_name = source.get("document", source.get("filename", "Unknown"))
                            page = source.get("page")
                            chunk_idx = source.get("chunk_index")
                            confidence = source.get("confidence", 0)
                            similarity = source.get("similarity", 0)
                            excerpt = source.get("excerpt", "")
                            
                            with st.container(border=True):
                                # Header with confidence badge
                                col1, col2, col3 = st.columns([2, 1, 1])
                                
                                with col1:
                                    header = f"**{i}. {doc_name}**"
                                    if page:
                                        header += f" — Page {page}"
                                    if chunk_idx is not None:
                                        header += f" [Chunk {chunk_idx}]"
                                    st.markdown(header)
                                
                                with col2:
                                    conf_emoji = "🟢" if confidence >= 0.85 else "🟡" if confidence >= 0.7 else "🟠" if confidence >= 0.5 else "🔴"
                                    st.metric("Confidence", f"{confidence:.0%}")
                                
                                with col3:
                                    st.metric("Similarity", f"{similarity:.0%}")
                                
                                # Excerpt
                                if excerpt:
                                    st.caption("**Relevant Excerpt:**")
                                    st.markdown(f"> *{excerpt}*")
    
    # ============================================
    # Search Tab (Bilingual)
    # ============================================
    with search_tab:
        st.subheader("Document Search")
        st.caption("Search your documents without generating an answer. Supports English and Telugu.")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_query = st.text_input(
                "Search query",
                max_chars=500,
                placeholder="Enter search terms in English or Telugu...",
                label_visibility="collapsed"
            )
        
        with col2:
            search_language = st.selectbox(
                "Language",
                ["english", "telugu"],
                key="search_language"
            )
        
        with col3:
            n_results = st.number_input(
                "Results",
                min_value=1,
                max_value=20,
                value=5,
                key="search_results"
            )
        
        if st.button("🔍 Search", use_container_width=True, type="primary"):
            if not search_query or len(search_query.strip()) == 0:
                st.error("❌ Please enter a search query")
            else:
                with st.spinner("🔍 Searching..."):
                    results = search_documents(search_query, language=search_language, n_results=n_results)
                
                if results is not None:
                    st.success(f"✅ Found {len(results)} matching chunks")
                    
                    # Display with enhanced metrics
                    if len(results) > 0:
                        st.divider()
                        st.markdown(f"### 📊 Search Results ({search_language} Query)")
                        
                        # Calculate stats
                        similarities = [r.get("similarity_score", 0) for r in results if "similarity_score" in r]
                        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Results Found", len(results))
                        with col2:
                            if avg_similarity > 0:
                                st.metric("Avg Relevance", f"{avg_similarity:.1%}")
                        with col3:
                            lang_emoji = "🇺🇸" if search_language == "english" else "🇮🇳"
                            st.metric("Query Language", search_language, f"{lang_emoji}")
                        
                        st.divider()
                    
                    # Display results with bilingual metadata
                    display_search_results(results)


# ============================================
# Main Execution
# ============================================

if __name__ == "__main__":
    main()
