"""
Document Upload & Management Page for Advanced RAG System
Handles document uploads, displays uploaded documents, and manages document lifecycle.
"""

import streamlit as st
import requests
from datetime import datetime
import json
from typing import Optional, Dict, Any
import os

# ============================================
# Configuration
# ============================================

BACKEND_URL = st.secrets.get("backend_url", "http://localhost:8000")
API_V1_STR = "/api/v1"
ALLOWED_EXTENSIONS = ["pdf", "docx", "txt", "jpg", "jpeg", "png"]
MAX_FILE_SIZE_MB = 50

# ============================================
# API Helper Functions
# ============================================

def api_request(
    method: str,
    endpoint: str,
    json_data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    use_token: bool = True,
    files: Optional[Dict] = None
) -> Optional[requests.Response]:
    """Make API request with automatic token injection and error handling."""
    if headers is None:
        headers = {}
    
    # Add JWT token if authenticated
    if use_token and st.session_state.get("access_token"):
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        if files:
            # For file uploads, don't set Content-Type; requests will set it with boundary
            response = requests.request(
                method=method,
                url=url,
                data=json_data,
                params=params,
                headers=headers,
                files=files,
                timeout=120  # Longer timeout for large files
            )
        else:
            response = requests.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                headers=headers,
                timeout=10
            )
        return response
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Is the server running on http://localhost:8000?")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timeout. Please try again.")
        return None
    except Exception as e:
        st.error(f"❌ Request error: {str(e)}")
        return None

# ============================================
# Document Management Functions
# ============================================

def upload_document(file):
    """Upload a document to the backend."""
    # Validate file
    file_name = file.name
    file_ext = file_name.split('.')[-1].lower()
    file_size_mb = file.size / (1024 * 1024)
    
    if file_ext not in ALLOWED_EXTENSIONS:
        st.error(f"❌ File type '{file_ext}' not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}")
        return None
    
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(f"❌ File size ({file_size_mb:.2f} MB) exceeds maximum allowed ({MAX_FILE_SIZE_MB} MB)")
        return None
    
    # Upload file
    files = {"file": (file_name, file, f"application/{file_ext}")}
    
    with st.spinner(f"📤 Uploading {file_name}..."):
        response = api_request(
            "POST",
            f"{API_V1_STR}/documents/upload",
            files=files
        )
    
    if response and response.status_code == 201:
        doc_data = response.json()
        st.success(f"✅ Document '{file_name}' uploaded successfully!")
        st.session_state.show_upload_success = True
        st.session_state.last_uploaded_doc = doc_data
        return doc_data
    elif response:
        error_msg = response.json().get("detail", "Unknown error")
        st.error(f"❌ Upload failed: {error_msg}")
        return None
    else:
        st.error("❌ Upload failed: No response from server")
        return None

def fetch_user_documents():
    """Fetch list of documents for the current user."""
    response = api_request(
        "GET",
        f"{API_V1_STR}/documents/user_documents"
    )
    
    if response and response.status_code == 200:
        return response.json()
    elif response and response.status_code == 401:
        st.error("❌ Unauthorized: Please log in again")
        return []
    elif response and response.status_code == 404:
        return []  # No documents yet
    else:
        if response:
            st.error(f"❌ Error fetching documents: {response.json().get('detail', 'Unknown error')}")
        return []

def delete_document(document_id: str, filename: str):
    """Delete a document."""
    response = api_request(
        "DELETE",
        f"{API_V1_STR}/documents/{document_id}"
    )
    
    if response and response.status_code == 204:
        st.success(f"✅ Document '{filename}' deleted successfully!")
        st.session_state.show_delete_success = True
        return True
    elif response:
        error_msg = response.json().get("detail", "Unknown error")
        st.error(f"❌ Delete failed: {error_msg}")
        return False
    else:
        st.error("❌ Delete failed: No response from server")
        return False

def get_file_size_display(size_bytes: Optional[int]) -> str:
    """Convert bytes to human-readable format."""
    if not size_bytes:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_status_badge(status: str) -> str:
    """Get badge HTML for document status."""
    status_colors = {
        "completed": "🟢 Completed",
        "processing": "🟡 Processing",
        "failed": "🔴 Failed"
    }
    return status_colors.get(status, f"⚪ {status}")

# ============================================
# Page Content
# ============================================

def show_upload_section():
    """Display document upload section."""
    st.subheader("📤 Upload Documents")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Upload documents (PDF, DOCX, TXT, JPG, PNG) to build your knowledge base.")
    
    with col2:
        st.info(f"Max file size: {MAX_FILE_SIZE_MB} MB")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a document to upload",
        type=ALLOWED_EXTENSIONS,
        help="Supported formats: PDF (with OCR for scanned pages), DOCX, TXT, JPG, PNG"
    )
    
    if uploaded_file is not None:
        st.write(f"**File:** {uploaded_file.name}")
        st.write(f"**Size:** {get_file_size_display(uploaded_file.size)}")
        
        if st.button("🚀 Upload & Process", use_container_width=True, key="upload_btn"):
            doc_data = upload_document(uploaded_file)
            if doc_data:
                st.rerun()

def show_documents_section():
    """Display list of uploaded documents."""
    st.subheader("📚 Your Documents")
    
    documents = fetch_user_documents()
    
    if not documents:
        st.info("📭 No documents uploaded yet. Start by uploading a document above!")
        return
    
    st.write(f"**Total documents:** {len(documents)}")
    
    # Create tabs for different views
    view_type = st.radio("View as:", ["List", "Cards"], horizontal=True, key="doc_view")
    
    if view_type == "List":
        # Table view
        for doc in documents:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{doc.get('filename', 'Unknown')}**")
                    file_type = doc.get('file_type', 'unknown').upper()
                    chunk_count = doc.get('chunk_count', 0)
                    st.caption(f"{file_type} • {chunk_count} chunks • {get_file_size_display(doc.get('file_size'))}")
                
                with col2:
                    st.markdown(get_status_badge(doc.get('status', 'unknown')))
                
                with col3:
                    created_at = doc.get('created_at', '')
                    if created_at:
                        st.caption(created_at.split('T')[0])  # Date only
                
                with col4:
                    if st.button("🗑️ Delete", key=f"delete_{doc['id']}", use_container_width=True):
                        if st.session_state.get("confirm_delete") == doc['id']:
                            delete_document(doc['id'], doc.get('filename', 'Unknown'))
                            if st.session_state.show_delete_success:
                                st.session_state.show_delete_success = False
                                st.rerun()
                        else:
                            st.session_state.confirm_delete = doc['id']
                            st.warning("⚠️ Click again to confirm deletion")
    
    else:
        # Cards view
        cols = st.columns(3)
        for idx, doc in enumerate(documents):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### {doc.get('filename', 'Unknown')[:20]}...")
                    
                    file_type = doc.get('file_type', 'unknown').upper()
                    chunk_count = doc.get('chunk_count', 0)
                    file_size = get_file_size_display(doc.get('file_size'))
                    status = get_status_badge(doc.get('status', 'unknown'))
                    
                    st.markdown(f"**Type:** {file_type}")
                    st.markdown(f"**Chunks:** {chunk_count}")
                    st.markdown(f"**Size:** {file_size}")
                    st.markdown(f"**Status:** {status}")
                    
                    if doc.get('text_content_summary'):
                        st.markdown("**Preview:**")
                        st.caption(doc['text_content_summary'][:100] + "...")
                    
                    st.markdown("---")
                    if st.button("🗑️ Delete", key=f"delete_card_{doc['id']}", use_container_width=True):
                        if delete_document(doc['id'], doc.get('filename', 'Unknown')):
                            st.rerun()

def show_stats_section():
    """Display document statistics."""
    st.subheader("📊 Upload Statistics")
    
    documents = fetch_user_documents()
    
    if not documents:
        st.info("No documents uploaded yet.")
        return
    
    # Calculate stats
    total_docs = len(documents)
    total_chunks = sum(doc.get('chunk_count', 0) for doc in documents)
    total_size = sum(doc.get('file_size', 0) or 0 for doc in documents)
    completed_docs = sum(1 for doc in documents if doc.get('status') == 'completed')
    processing_docs = sum(1 for doc in documents if doc.get('status') == 'processing')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documents", total_docs)
    
    with col2:
        st.metric("Total Chunks", total_chunks)
    
    with col3:
        st.metric("Total Size", get_file_size_display(total_size))
    
    with col4:
        st.metric("Processing", processing_docs)
    
    # File type distribution
    st.markdown("**File Type Distribution:**")
    file_types = {}
    for doc in documents:
        file_type = doc.get('file_type', 'unknown').upper()
        file_types[file_type] = file_types.get(file_type, 0) + 1
    
    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(file_types)
    
    with col2:
        status_counts = {}
        for doc in documents:
            status = doc.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        st.bar_chart(status_counts)

# ============================================
# Main Page
# ============================================

def main():
    """Main Knowledge Base page."""
    st.header("📁 Knowledge Base")
    st.markdown("Upload and manage your documents for the AI to learn from.")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "📚 Documents", "📊 Statistics"])
    
    with tab1:
        show_upload_section()
    
    with tab2:
        show_documents_section()
    
    with tab3:
        show_stats_section()

if __name__ == "__main__":
    # Initialize session state
    if "show_delete_success" not in st.session_state:
        st.session_state.show_delete_success = False
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = None
    
    main()
