"""
Analytics & Insights Dashboard
Track your learning progress and RAG system usage
"""

import streamlit as st
import requests
from typing import Optional, Dict
from datetime import datetime, timedelta

# ============================================
# Configuration
# ============================================

BACKEND_URL = st.secrets.get("backend_url", "http://localhost:8000")
API_V1_STR = "/api/v1"

# ============================================
# API Functions
# ============================================

def api_request(
    method: str,
    endpoint: str,
    json_data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    use_token: bool = True
) -> Optional[requests.Response]:
    """Make API request with automatic token injection."""
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
        st.error("❌ Cannot connect to backend.")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timeout.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def get_user_analytics() -> Optional[Dict]:
    """Get user analytics."""
    response = api_request(
        "GET",
        f"{API_V1_STR}/analytics/summary"
    )
    
    if response and response.status_code == 200:
        return response.json()
    return None


def get_document_stats() -> Optional[Dict]:
    """Get document statistics."""
    response = api_request(
        "GET",
        f"{API_V1_STR}/documents/stats"
    )
    
    if response and response.status_code == 200:
        return response.json()
    return None


# ============================================
# Page Layout
# ============================================

def main():
    """Main analytics page."""
    st.header("📊 Analytics & Insights")
    st.markdown("Track your learning progress and RAG system usage.")
    
    # Load analytics data with fallback
    try:
        with st.spinner("Loading analytics..."):
            user_analytics = get_user_analytics()
            doc_stats = get_document_stats()
        
        # Use default values if API returns None
        if user_analytics is None:
            user_analytics = {
                "total_queries": 0,
                "total_quiz_attempts": 0,
                "total_sessions": 0
            }
        
        if doc_stats is None:
            doc_stats = {
                "total_documents": 0,
                "total_chunks": 0,
                "total_tokens": 0
            }
    except Exception as e:
        st.warning(f"⚠️ Analytics data unavailable: {str(e)}")
        user_analytics = {
            "total_queries": 0,
            "total_quiz_attempts": 0,
            "total_sessions": 0
        }
        doc_stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "total_tokens": 0
        }
    
    # ============================================
    # Key Metrics
    # ============================================
    
    st.markdown("## 📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📚 Documents",
            doc_stats.get("total_documents", 0)
        )
    
    with col2:
        st.metric(
            "🔍 Queries",
            user_analytics.get("total_queries", 0)
        )
    
    with col3:
        st.metric(
            "📝 Quizzes",
            user_analytics.get("total_quiz_attempts", 0)
        )
    
    with col4:
        st.metric(
            "⏱️ Sessions",
            user_analytics.get("total_sessions", 0)
        )
    
    st.divider()
    
    # ============================================
    # Document Statistics
    # ============================================
    
    st.markdown("## 📚 Document Library")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Chunks",
            f"{doc_stats.get('total_chunks', 0):,}"
        )
    
    with col2:
        st.metric(
            "Total Tokens",
            f"{doc_stats.get('total_tokens', 0):,}"
        )
    
    with col3:
        st.metric(
            "Storage Used",
            f"{doc_stats.get('storage_size_mb', 0):.2f} MB"
        )
    
    # Document breakdown
    st.markdown("**Document Types:**")
    
    file_types = doc_stats.get("file_types_breakdown", {})
    if file_types:
        for file_type, count in file_types.items():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.caption(file_type.upper())
            with col2:
                st.metric("Count", count)
    else:
        st.info("No document type data available")
    
    st.divider()
    
    # ============================================
    # Usage Statistics
    # ============================================
    
    st.markdown("## 🎯 Usage Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Queries & Chat**")
        
        queries_col1, queries_col2 = st.columns(2)
        with queries_col1:
            st.metric(
                "Total Queries",
                user_analytics.get("total_queries", 0)
            )
        with queries_col2:
            st.metric(
                "Avg Response Time",
                f"{user_analytics.get('avg_response_time_ms', 0):.0f}ms"
            )
        
        st.metric(
            "Tokens Used",
            f"{user_analytics.get('total_tokens_used', 0):,}"
        )
    
    with col2:
        st.markdown("**Quiz Performance**")
        
        quiz_col1, quiz_col2 = st.columns(2)
        with quiz_col1:
            st.metric(
                "Quizzes Taken",
                user_analytics.get("total_quiz_attempts", 0)
            )
        with quiz_col2:
            accuracy = user_analytics.get("quiz_accuracy_percent", 0)
            st.metric(
                "Average Accuracy",
                f"{accuracy:.1f}%"
            )
    
    st.divider()
    
    # ============================================
    # Activity Timeline
    # ============================================
    
    st.markdown("## 📅 Activity Timeline")
    
    activity = user_analytics.get("recent_activity", [])
    
    if activity:
        for item in activity[:10]:
            col1, col2, col3 = st.columns([1, 2, 1])
            
            activity_type = item.get("type", "unknown")
            
            # Icon based on type
            icon_map = {
                "query": "🔍",
                "chat": "💬",
                "quiz": "📝",
                "upload": "📤",
                "search": "🔎"
            }
            icon = icon_map.get(activity_type, "📌")
            
            with col1:
                st.caption(icon)
            
            with col2:
                description = item.get("description", "Activity")
                timestamp = item.get("timestamp", "")
                st.caption(description)
                if timestamp:
                    st.caption(f"*{timestamp}*")
            
            with col3:
                status = item.get("status", "")
                if status == "success":
                    st.caption("✅")
                elif status == "error":
                    st.caption("❌")
    else:
        st.info("No recent activity")
    
    st.divider()
    
    # ============================================
    # Session Information
    # ============================================
    
    st.markdown("## ℹ️ Session Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Account Status:**")
        st.caption(f"User ID: {st.session_state.get('user_id', 'Unknown')}")
        st.caption(f"Username: {st.session_state.get('username', 'Unknown')}")
    
    with col2:
        st.markdown("**Session Details:**")
        st.caption(f"Total Sessions: {user_analytics.get('total_sessions', 0)}")
        st.caption(f"Last Active: {user_analytics.get('last_active', 'Never')}")
    
    st.divider()
    
    # ============================================
    # Export Options
    # ============================================
    
    st.markdown("## 📥 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Analytics", use_container_width=True):
            st.info("📊 Analytics export feature coming soon!")
    
    with col2:
        if st.button("📝 Export Chat History", use_container_width=True):
            st.info("📝 Chat history export feature coming soon!")
    
    with col3:
        if st.button("📈 Export Quiz Results", use_container_width=True):
            st.info("📈 Quiz results export feature coming soon!")


# ============================================
# Main Execution
# ============================================

if __name__ == "__main__":
    main()
