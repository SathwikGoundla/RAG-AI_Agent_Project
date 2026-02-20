import streamlit as st
import requests
import json
from datetime import datetime
import time


def _set_auth_session(data: dict):
    """Set authentication state for all frontend pages consistently."""
    user = data.get('user', {})

    access_token = data.get('access_token') or data.get('token')
    refresh_token = data.get('refresh_token', '')

    # Backward-compatible keys
    st.session_state.token = access_token
    st.session_state.refresh_token = refresh_token

    # Keys used by feature pages
    st.session_state.access_token = access_token
    st.session_state.user_id = user.get('id')
    st.session_state.username = user.get('username')

    st.session_state.user_info = {
        'id': user.get('id'),
        'username': user.get('username'),
        'email': user.get('email'),
        'full_name': user.get('full_name'),
        'is_active': user.get('is_active', True),
        'login_time': datetime.now().isoformat()
    }
    st.session_state.authenticated = True


def handle_google_callback():
    """Handle Google OAuth callback redirect by exchanging one-time code."""
    query_params = st.query_params
    oauth_success = query_params.get("oauth_success")
    exchange_code = query_params.get("exchange_code")
    reason = query_params.get("reason")

    if oauth_success == "true" and exchange_code:
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/auth/google/exchange",
                json={"exchange_code": exchange_code},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                _set_auth_session(data)
                st.query_params.clear()
                st.success("✅ Google login successful!")
                time.sleep(0.4)
                st.switch_page("pages/chat.py")
            else:
                detail = response.json().get("detail", "Google sign-in failed")
                st.error(f"❌ {detail}")

        except Exception as e:
            st.error(f"❌ Google sign-in error: {str(e)}")
        finally:
            # Prevent one-time code reuse if page refresh happens
            st.query_params.clear()

    elif oauth_success == "false":
        message = f"Google login failed ({reason})" if reason else "Google login failed"
        st.error(f"❌ {message}")
        st.query_params.clear()

# Page configuration
st.set_page_config(
    page_title="Advanced RAG System - Login",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Redirect if already authenticated
if 'authenticated' in st.session_state and st.session_state.authenticated:
    st.switch_page("pages/chat.py")

# Hide sidebar for login page
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="collapsedControl"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

# Custom CSS for modern Instagram-style design
st.markdown("""
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
        }
        
        .login-container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 14px 28px rgba(0, 0, 0, 0.2);
            width: 100%;
            max-width: 400px;
            padding: 40px;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo-text {
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            font-family: 'Segoe UI', sans-serif;
        }
        
        .tagline {
            font-size: 14px;
            color: #666;
            margin-bottom: 30px;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        .form-label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
            font-weight: 600;
            color: #1f2937;
        }
        
        .input-field {
            width: 100%;
            padding: 12px 16px;
            border: 1.5px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s ease;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .input-field:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .btn-login {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        }
        
        .btn-login:active {
            transform: translateY(0);
        }
        
        .divider {
            display: flex;
            align-items: center;
            margin: 24px 0;
        }
        
        .divider-line {
            flex: 1;
            height: 1px;
            background-color: #e5e7eb;
        }
        
        .divider-text {
            margin: 0 12px;
            color: #9ca3af;
            font-size: 14px;
            font-weight: 500;
        }
        
        .btn-google {
            width: 100%;
            padding: 12px;
            background: white;
            color: #1f2937;
            border: 1.5px solid #e5e7eb;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .btn-google:hover {
            background: #f9fafb;
            border-color: #d1d5db;
        }
        
        .footer-text {
            text-align: center;
            margin-top: 20px;
            font-size: 14px;
            color: #6b7280;
        }
        
        .footer-link {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            cursor: pointer;
        }
        
        .footer-link:hover {
            text-decoration: underline;
        }
        
        .error-message {
            background-color: #fee2e2;
            border-left: 4px solid #ef4444;
            color: #991b1b;
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 16px;
            font-size: 14px;
        }
        
        .success-message {
            background-color: #dcfce7;
            border-left: 4px solid #22c55e;
            color: #166534;
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 16px;
            font-size: 14px;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            font-size: 14px;
        }
        
        .checkbox-group input {
            margin-right: 8px;
            cursor: pointer;
        }
        
        .forgot-password {
            text-align: right;
            margin-bottom: 20px;
        }
        
        .forgot-password a {
            font-size: 14px;
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        
        .forgot-password a:hover {
            text-decoration: underline;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

# Backend API URL
BACKEND_URL = "http://localhost:8000"

def login_user(username, password):
    """Authenticate user with backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            _set_auth_session(data)
            return True, "✅ Login successful!"
        else:
            error_msg = response.json().get('detail', 'Invalid credentials')
            return False, f"❌ {error_msg}"
    except requests.exceptions.ConnectionError:
        return False, "❌ Backend server not running. Please start the backend first.\n\nRun: python -m uvicorn main:app --reload"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def register_user(username, email, password, full_name):
    """Register new user with backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name
            },
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 201:
            return True, "✅ Registration successful! Please log in."
        else:
            error_detail = response.json().get('detail', 'Registration failed')
            return False, f"❌ {error_detail}"
    except requests.exceptions.ConnectionError:
        return False, "❌ Backend server not running. Please start the backend first.\n\nRun: python -m uvicorn main:app --reload"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

# Main login UI
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    handle_google_callback()

    # Logo and Title
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 48px; margin-bottom: 16px;">🚀</div>
            <h1 style="
                font-size: 32px;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 8px;
            ">Advanced RAG System</h1>
            <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                Intelligent Document Q&A Platform
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Tabs for Login and Sign Up
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
    
    with tab1:
        st.markdown("### Welcome Back!")
        st.markdown("Enter your credentials to continue")
        
        # Display any previous error messages
        if 'login_error' in st.session_state and st.session_state.login_error:
            st.markdown(f"<div class='error-message'>{st.session_state.login_error}</div>", unsafe_allow_html=True)
            st.session_state.login_error = None
        
        # Login form
        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            key="login_username",
            label_visibility="collapsed"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password",
            label_visibility="collapsed"
        )
        
        # Remember me & Forgot password
        col_check, col_forgot = st.columns([1, 1])
        with col_check:
            remember_me = st.checkbox("Remember me", key="remember_me")
        with col_forgot:
            st.markdown("""
                <div style="text-align: right; margin-top: 8px;">
                    <a href="#" style="font-size: 12px; color: #667eea; text-decoration: none; font-weight: 600;">
                        Forgot password?
                    </a>
                </div>
            """, unsafe_allow_html=True)
        
        # Login button
        if st.button("Sign In", use_container_width=True, type="primary", key="btn_login"):
            if not username or not password:
                st.error("❌ Please enter both username and password")
            else:
                with st.spinner("Signing in..."):
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                        time.sleep(0.5)
                        st.switch_page("pages/chat.py")
                    else:
                        st.error(message)
        

        
        # Sign up link
        st.markdown("""
            <div style="text-align: center; margin-top: 20px; font-size: 14px; color: #6b7280;">
                Don't have an account? 
                <span style="color: #667eea; font-weight: 600; cursor: pointer;">
                    Create one now!
                </span>
            </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Create New Account")
        st.markdown("Join our community today")
        
        # Display any previous error messages
        if 'signup_error' in st.session_state and st.session_state.signup_error:
            st.markdown(f"<div class='error-message'>{st.session_state.signup_error}</div>", unsafe_allow_html=True)
            st.session_state.signup_error = None
        
        # Sign up form
        signup_fullname = st.text_input(
            "Full Name",
            placeholder="Enter your full name",
            key="signup_fullname",
            label_visibility="collapsed"
        )
        
        signup_username = st.text_input(
            "Username",
            placeholder="Choose a username",
            key="signup_username",
            label_visibility="collapsed"
        )
        
        signup_email = st.text_input(
            "Email",
            placeholder="Enter your email address",
            key="signup_email",
            label_visibility="collapsed"
        )
        
        signup_password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a strong password",
            key="signup_password",
            label_visibility="collapsed"
        )
        
        signup_password_confirm = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Confirm your password",
            key="signup_password_confirm",
            label_visibility="collapsed"
        )
        
        # Terms
        agree_terms = st.checkbox(
            "I agree to the Terms and Conditions",
            key="agree_terms"
        )
        
        # Sign up button
        if st.button("Create Account", use_container_width=True, type="primary", key="btn_signup"):
            if not all([signup_fullname, signup_username, signup_email, signup_password]):
                st.error("❌ Please fill in all fields")
            elif signup_password != signup_password_confirm:
                st.error("❌ Passwords do not match")
            elif len(signup_password) < 6:
                st.error("❌ Password must be at least 6 characters")
            elif not agree_terms:
                st.error("❌ Please agree to the Terms and Conditions")
            else:
                with st.spinner("Creating account..."):
                    success, message = register_user(
                        signup_username,
                        signup_email,
                        signup_password,
                        signup_fullname
                    )
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
        
        # Sign in link
        st.markdown("""
            <div style="text-align: center; margin-top: 20px; font-size: 14px; color: #6b7280;">
                Already have an account? 
                <span style="color: #667eea; font-weight: 600;">
                    Sign in here!
                </span>
            </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
        <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
            <p style="font-size: 12px; color: #9ca3af; margin: 0;">
                Advanced RAG System v2.0 | © 2026
            </p>
            <p style="font-size: 11px; color: #d1d5db; margin-top: 8px;">
                Secure • Private • Intelligent
            </p>
        </div>
    """, unsafe_allow_html=True)
