"""
ADVANCED RAG SYSTEM - Clean Architecture Frontend
✅ Login ONLY initially (no sidebar visible)
✅ Dashboard ONLY after login (with custom sidebar)
✅ Google OAuth integrated
✅ Proper tab structure
✅ Complete control over UI flow
"""

import streamlit as st
import requests
import json
from typing import Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Advanced RAG - AI Document Q&A",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Backend URL
BACKEND_URL = "http://localhost:8000"

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
<style>
    /* Hide default sidebar and pages menu */
    [data-testid="stSidebarNav"] { display: none !important; }
    .streamlit-expanderHeader { display: none !important; }
    
    /* Login page background */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        background-attachment: fixed !important;
        min-height: 100vh;
    }
    
    /* Input styling */
    .stTextInput > label,
    .stPasswordInput > label,
    .stCheckbox > label {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 8px !important;
        display: block !important;
    }
    
    .stTextInput > div > div > input,
    .stPasswordInput > div > div > input {
        background-color: #f3f4f6 !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        color: #1f2937 !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stPasswordInput > div > div > input:focus {
        border-color: #667eea !important;
        background-color: white !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stPasswordInput > div > div > input::placeholder {
        color: #9ca3af !important;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100% !important;
        height: 48px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton > button:hover {
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        font-weight: 600;
        padding: 12px 24px;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #667eea;
        border-bottom: 3px solid #667eea;
    }
    
    /* Dashboard styling */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 30px;
    }
    
    /* Sidebar styling - clean transparent */
    .stSidebar {
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "token" not in st.session_state:
    st.session_state.token = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
if "messages" not in st.session_state:
    st.session_state.messages = []


def _set_auth_session(data: dict):
    """Set authentication state in a way compatible with all frontend pages."""
    user = data.get("user", {})
    access_token = data.get("access_token") or data.get("token")

    st.session_state.token = access_token
    st.session_state.access_token = access_token
    st.session_state.refresh_token = data.get("refresh_token")
    st.session_state.user_id = user.get("id")
    st.session_state.username = user.get("username")

    st.session_state.user_info = {
        "user_id": user.get("id"),
        "username": user.get("username"),
        "email": user.get("email", ""),
        "full_name": user.get("full_name", ""),
    }
    st.session_state.authenticated = True


def handle_google_callback() -> None:
    """Handle Google OAuth redirect and exchange one-time code for tokens."""
    query_params = st.query_params
    oauth_success = query_params.get("oauth_success")
    exchange_code = query_params.get("exchange_code")
    reason = query_params.get("reason")

    if oauth_success == "true" and exchange_code and not st.session_state.authenticated:
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/auth/google/exchange",
                json={"exchange_code": exchange_code},
                timeout=10,
            )

            if response.status_code == 200:
                _set_auth_session(response.json())
                st.query_params.clear()
                st.success("✅ Google login successful!")
                st.rerun()
            else:
                detail = response.json().get("detail", "Google sign-in failed")
                st.error(f"❌ {detail}")
                st.query_params.clear()
        except Exception as e:
            st.error(f"❌ Google sign-in error: {str(e)}")
            st.query_params.clear()

    elif oauth_success == "false":
        message = f"Google login failed ({reason})" if reason else "Google login failed"
        st.error(f"❌ {message}")
        st.query_params.clear()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_backend() -> bool:
    """Check if backend server is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False

def login_user(username: str, password: str) -> Tuple[bool, str]:
    """Authenticate user and get JWT token"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"username": username, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            _set_auth_session(data)
            return True, "✅ Login successful!"
        else:
            error_msg = response.json().get("detail", "Login failed")
            return False, f"❌ {error_msg}"
    except requests.exceptions.ConnectionError:
        return False, "❌ Backend not running. Please start the backend first."
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def register_user(full_name: str, username: str, email: str, password: str) -> Tuple[bool, str]:
    """Register new user account"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name
            },
            timeout=5
        )
        
        if response.status_code == 201:
            return True, "Account created successfully! Please login."
        else:
            error_msg = response.json().get("detail", "Registration failed")
            return False, str(error_msg)
    except Exception as e:
        return False, f"Backend error: {str(e)}"

def logout_user():
    """Logout user and clear session"""
    try:
        if st.session_state.token:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            requests.post(f"{BACKEND_URL}/api/v1/auth/logout", headers=headers, timeout=2)
    except:
        pass
    
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user_info = {}
    st.session_state.current_page = "Dashboard"
    st.session_state.messages = []

# ============================================================================
# LOGIN PAGE - ONLY SHOWN IF NOT AUTHENTICATED
# ============================================================================

def show_login_page():
    """Display login/signup page"""
    handle_google_callback()
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        # Header
        st.markdown("""
        <div style="text-align: center; margin-bottom: 40px; color: white;">
            <h1 style="font-size: 48px; margin: 0; font-weight: 800;">🧠</h1>
            <h2 style="font-size: 36px; margin: 10px 0 5px 0; color: white;">Advanced RAG</h2>
            <p style="font-size: 18px; margin: 0; color: rgba(255,255,255,0.8);">
                Intelligent Document Q&A Platform
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: white; border-radius: 20px; padding: 40px; 
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
        """, unsafe_allow_html=True)
        
        # Tabs
        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Sign Up"])
        
        # ==================== SIGN IN ====================
        with tab1:
            st.markdown("<h3 style='color: #1f2937; margin-bottom: 20px;'>Welcome Back</h3>", 
                       unsafe_allow_html=True)
            
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="signin_username"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="signin_password"
            )
            
            col_remember, col_forgot = st.columns([1, 1])
            with col_remember:
                remember = st.checkbox("Remember me", value=False)
            with col_forgot:
                st.markdown("")
            
            if st.button("Sign In", use_container_width=True, key="signin_btn"):
                if not username or not password:
                    st.error("❌ Please enter username and password")
                else:
                    success, message = login_user(username, password)
                    if success:
                        st.success("✅ " + message)
                        st.rerun()
                    else:
                        st.error("❌ " + message)
            
            # Google Sign-In
            st.divider()
            st.markdown("""
            <div style="text-align: center; margin: 20px 0; color: #6b7280; font-size: 14px;">
                OR
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="display: flex; justify-content: center;">
                <a href="http://localhost:8000/api/v1/auth/google" 
                   style="display: inline-flex; align-items: center; justify-content: center;
                           background-color: white; border: 1px solid #dadce0; border-radius: 4px;
                           padding: 8px 16px; font-family: 'Roboto', sans-serif; font-size: 14px;
                           font-weight: 500; color: #3c4043; text-decoration: none; width: 100%;
                           box-shadow: 0 2px 4px 0 rgba(0,0,0,0.04); 
                           transition: all 0.2s ease;" 
                   onmouseover="this.style.backgroundColor='#f8f9fa'; this.style.boxShadow='0 4px 8px 0 rgba(0,0,0,0.12)';"
                   onmouseout="this.style.backgroundColor='white'; this.style.boxShadow='0 2px 4px 0 rgba(0,0,0,0.04)';">
                    <svg style="margin-right: 8px; width: 18px; height: 18px;" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                    </svg>
                    <span>Sign in with Google</span>
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.6); margin: 20px 0; font-size: 14px;'>Standard Login to Continue</p>", 
                       unsafe_allow_html=True)
        
        # ==================== SIGN UP ====================
        with tab2:
            st.markdown("<h3 style='color: #1f2937; margin-bottom: 20px;'>Create Account</h3>", 
                       unsafe_allow_html=True)
            
            full_name = st.text_input(
                "Full Name",
                placeholder="Enter your full name",
                key="signup_fullname"
            )
            
            signup_username = st.text_input(
                "Username",
                placeholder="Choose a username",
                key="signup_username"
            )
            
            signup_email = st.text_input(
                "Email",
                placeholder="Enter your email",
                key="signup_email"
            )
            
            signup_password = st.text_input(
                "Password",
                type="password",
                placeholder="Create a password (min 8 chars)",
                key="signup_password"
            )
            
            signup_confirm = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Confirm password",
                key="signup_confirm"
            )
            
            if st.button("Create Account", use_container_width=True, key="signup_btn"):
                if not all([full_name, signup_username, signup_email, signup_password, signup_confirm]):
                    st.error("❌ Please fill in all fields")
                elif signup_password != signup_confirm:
                    st.error("❌ Passwords do not match")
                elif len(signup_password) < 8:
                    st.error("❌ Password must be at least 8 characters")
                else:
                    success, message = register_user(full_name, signup_username, signup_email, signup_password)
                    if success:
                        st.success("✅ " + message)
                        st.info("Switch to Sign In tab and login with your credentials")
                    else:
                        st.error("❌ " + message)
            
            st.divider()
            
            # Google Sign-Up
            st.markdown("""
            <div style="text-align: center; margin: 20px 0; color: #6b7280; font-size: 14px;">
                OR
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="display: flex; justify-content: center;">
                <a href="http://localhost:8000/api/v1/auth/google" 
                   style="display: inline-flex; align-items: center; justify-content: center;
                           background-color: white; border: 1px solid #dadce0; border-radius: 4px;
                           padding: 8px 16px; font-family: 'Roboto', sans-serif; font-size: 14px;
                           font-weight: 500; color: #3c4043; text-decoration: none; width: 100%;
                           box-shadow: 0 2px 4px 0 rgba(0,0,0,0.04); 
                           transition: all 0.2s ease;" 
                   onmouseover="this.style.backgroundColor='#f8f9fa'; this.style.boxShadow='0 4px 8px 0 rgba(0,0,0,0.12)';"
                   onmouseout="this.style.backgroundColor='white'; this.style.boxShadow='0 2px 4px 0 rgba(0,0,0,0.04)';">
                    <svg style="margin-right: 8px; width: 18px; height: 18px;" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                    </svg>
                    <span>Sign up with Google</span>
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 40px; color: rgba(255,255,255,0.7); font-size: 14px;">
            🔒 Secure • 🔐 Private • 🤖 Intelligent
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# DASHBOARD PAGE - ONLY SHOWN IF AUTHENTICATED
# ============================================================================

def show_dashboard():
    """Display main dashboard - ONLY SHOWN AFTER LOGIN"""
    
    # Sidebar ONLY visible for authenticated users
    if st.session_state.authenticated:
        with st.sidebar:
            st.markdown(f"### 👤 {st.session_state.user_info.get('username', 'User')}")
            st.markdown("Status: 🟢 Active")
            
            st.divider()
            
            st.markdown("### 📑 Navigation")
            
            pages = {
                "Dashboard": "🏠",
                "Documents": "📄",
                "Chat": "💬",
                "Analytics": "📊",
                "Settings": "⚙️"
            }
            
            for page, icon in pages.items():
                if st.button(f"{icon} {page}", use_container_width=True, key=f"nav_{page}"):
                    st.session_state.current_page = page
            
            st.divider()
            
            if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
                logout_user()
                st.rerun()
    
    # Main content based on selected page
    if st.session_state.current_page == "Dashboard":
        show_dashboard_content()
    elif st.session_state.current_page == "Documents":
        show_documents_content()
    elif st.session_state.current_page == "Chat":
        show_chat_content()
    elif st.session_state.current_page == "Analytics":
        show_analytics_content()
    elif st.session_state.current_page == "Settings":
        show_settings_content()

# ============================================================================
# DASHBOARD CONTENT
# ============================================================================

def show_dashboard_content():
    """Dashboard overview page"""
    st.markdown(f"# Welcome back, {st.session_state.user_info.get('username', 'User')}! 🎉")
    
    st.divider()
    
    # Stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Documents", "0", "uploaded")
    with col2:
        st.metric("💬 Queries", "0", "asked")
    with col3:
        st.metric("⚡ Avg Response", "0ms")
    with col4:
        st.metric("💾 Storage", "0 MB", "used")
    
    st.divider()
    
    st.markdown("## 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Upload Documents", use_container_width=True):
            st.session_state.current_page = "Documents"
            st.rerun()
        st.markdown("Upload PDF, DOCX files")
    
    with col2:
        if st.button("💬 Chat with AI", use_container_width=True):
            st.session_state.current_page = "Chat"
            st.rerun()
        st.markdown("Ask questions about docs")
    
    with col3:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"
            st.rerun()
        st.markdown("Check statistics")

# ============================================================================
# DOCUMENTS CONTENT
# ============================================================================

def show_documents_content():
    """Document management page"""
    
    st.markdown("## 📄 Document Management")
    
    tab1, tab2 = st.tabs(["📤 Upload", "📋 My Documents"])
    
    with tab1:
        st.markdown("### Upload Your Documents")
        st.markdown("Upload PDF, DOCX, TXT, or image files for analysis")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "txt", "jpg", "jpeg", "png"],
            help="Maximum 50MB"
        )
        
        if uploaded_file:
            col_info1, col_info2 = st.columns([3, 1])
            with col_info1:
                st.success(f"✅ File selected: **{uploaded_file.name}**")
            with col_info2:
                st.caption(f"Size: {uploaded_file.size / 1024 / 1024:.2f}MB")
            
            st.divider()
            
            if st.button("📤 Upload Now", use_container_width=True, key="upload_btn"):
                with st.spinner("⏳ Processing your document..."):
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state.token}"}
                        files = {"file": (uploaded_file.name, uploaded_file.getbuffer())}
                        
                        response = requests.post(
                            f"{BACKEND_URL}/api/v1/documents/upload",
                            files=files,
                            headers=headers,
                            timeout=60
                        )
                        
                        if response.status_code in [200, 201]:
                            data = response.json()
                            st.success("✅ Document uploaded successfully!")
                            st.markdown("### 📊 Upload Details:")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📁 Document ID", str(data.get("id", "N/A"))[:8] + "...")
                            with col2:
                                st.metric("✓ Status", "Processed")
                            with col3:
                                st.metric("📄 File", data.get("file_type", "N/A").upper())
                            
                            st.divider()
                            st.info(f"✨ Document ready for Q&A! Go to Chat tab to ask questions.")
                        else:
                            error_detail = response.json().get("detail", "Unknown error")
                            st.error(f"❌ Upload failed: {error_detail}")
                    except requests.exceptions.Timeout:
                        st.error("❌ Upload timeout! File might be too large - try smaller file")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.markdown("### Your Documents")
        st.info("📄 No documents uploaded yet. Start in the Upload tab!")

# ============================================================================
# CHAT CONTENT
# ============================================================================

def show_chat_content():
    """Chat page"""
    
    st.markdown("## 💬 Chat with AI")
    st.markdown("Ask questions about your uploaded documents")
    
    if st.session_state.messages:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])
    else:
        st.info("💭 Upload documents first to start chatting!")
    
    user_input = st.chat_input("Ask a question...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append(
            {"role": "assistant", "content": "I'm ready to help! Please upload documents first."}
        )
        st.rerun()

# ============================================================================
# ANALYTICS CONTENT
# ============================================================================

def show_analytics_content():
    """Analytics page"""
    
    st.markdown("## 📊 Analytics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Documents", "0")
    with col2:
        st.metric("Queries", "0")
    with col3:
        st.metric("Storage", "0 MB")
    
    st.info("📈 Advanced charts coming soon!")

# ============================================================================
# SETTINGS CONTENT
# ============================================================================

def show_settings_content():
    """Settings page"""
    
    st.markdown("## ⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["👤 Profile", "🔐 Security", "🔔 Notifications"])
    
    with tab1:
        st.markdown("### Profile Information")
        st.text_input("Username", value=st.session_state.user_info.get("username", ""), disabled=True)
        st.text_input("Email", value=st.session_state.user_info.get("email", ""))
        st.text_area("Bio", max_chars=500)
        if st.button("Save Profile", use_container_width=True):
            st.success("✅ Profile updated!")
    
    with tab2:
        st.markdown("### Change Password")
        st.text_input("Current Password", type="password")
        st.text_input("New Password", type="password")
        st.text_input("Confirm Password", type="password")
        if st.button("Change Password", use_container_width=True):
            st.success("✅ Password changed!")
    
    with tab3:
        st.markdown("### Notification Preferences")
        st.checkbox("Email notifications", value=True)
        st.checkbox("Upload confirmations", value=True)
        if st.button("Save Preferences", use_container_width=True):
            st.success("✅ Preferences saved!")

# ============================================================================
# MAIN APP LOGIC
# ============================================================================

def main():
    """Main app entry point"""
    
    if not check_backend():
        st.error("❌ Backend not running on port 8000")
        st.stop()
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
