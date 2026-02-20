"""
Google OAuth 2.0 Authentication for Advanced RAG System.
Handles Google Sign-In / Sign-Up and secure token issuance.
"""

import logging
import re
import secrets
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from backend.config import settings
from backend.database import User, get_db
from backend.models import UserOut

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication - Google OAuth"])


# ============================================================================
# Google OAuth Configuration
# ============================================================================

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI = settings.GOOGLE_REDIRECT_URI
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


# ============================================================================
# Models
# ============================================================================

class GoogleTokenResponse(BaseModel):
    """Google OAuth callback success payload."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserOut
    expires_in: int


class GoogleExchangeRequest(BaseModel):
    """One-time code exchange request after frontend redirect."""

    exchange_code: str


# ============================================================================
# State Management for CSRF Protection
# ============================================================================

# NOTE: In production, use Redis/shared cache instead of memory.
_oauth_states: dict[str, float] = {}
STATE_TTL_SECONDS = 600  # 10 minutes
MAX_STORED_STATES = 5000

_oauth_exchange_codes: dict[str, dict] = {}
EXCHANGE_CODE_TTL_SECONDS = 180  # 3 minutes


def generate_state() -> str:
    """Generate random state for OAuth CSRF protection."""
    return secrets.token_urlsafe(32)


def cleanup_expired_states() -> None:
    """Remove expired OAuth states from memory."""
    now = time.time()
    expired = [
        state
        for state, created_at in _oauth_states.items()
        if now - created_at > STATE_TTL_SECONDS
    ]
    for state in expired:
        _oauth_states.pop(state, None)


def store_state(state: str) -> None:
    """Store OAuth state with timestamp and bounded map size."""
    cleanup_expired_states()

    if len(_oauth_states) >= MAX_STORED_STATES:
        oldest_state = min(_oauth_states.items(), key=lambda item: item[1])[0]
        _oauth_states.pop(oldest_state, None)

    _oauth_states[state] = time.time()


def verify_state(state: str) -> bool:
    """Verify OAuth state (CSRF protection)."""
    cleanup_expired_states()
    return state in _oauth_states


def clear_state(state: str) -> None:
    """Clear OAuth state after successful validation (one-time use)."""
    _oauth_states.pop(state, None)


def _cleanup_expired_exchange_codes() -> None:
    """Remove expired one-time exchange codes from memory."""
    now = time.time()
    expired_codes = [
        code
        for code, data in _oauth_exchange_codes.items()
        if now - data["created_at"] > EXCHANGE_CODE_TTL_SECONDS
    ]
    for code in expired_codes:
        _oauth_exchange_codes.pop(code, None)


def _store_exchange_payload(payload: GoogleTokenResponse) -> str:
    """Store OAuth result as one-time exchange payload and return code."""
    _cleanup_expired_exchange_codes()

    exchange_code = secrets.token_urlsafe(32)
    _oauth_exchange_codes[exchange_code] = {
        "created_at": time.time(),
        "payload": payload,
    }
    return exchange_code


def _consume_exchange_payload(exchange_code: str) -> Optional[GoogleTokenResponse]:
    """Consume one-time exchange payload. Returns None if invalid/expired."""
    _cleanup_expired_exchange_codes()
    data = _oauth_exchange_codes.pop(exchange_code, None)
    if not data:
        return None
    return data.get("payload")


def _frontend_redirect_url(success: bool, **params) -> str:
    """Build redirect URL to frontend app with status params."""
    base = str(settings.FRONTEND_URL).rstrip("/")
    query_params = {"oauth_success": "true" if success else "false", **params}
    return f"{base}/?{urlencode(query_params)}"


# ============================================================================
# Internal Helpers
# ============================================================================

def _sanitize_username(base_username: str) -> str:
    """Sanitize and normalize a username candidate for local account creation."""
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", base_username).strip("_-")
    if not sanitized:
        sanitized = "user"
    if len(sanitized) < 3:
        sanitized = f"{sanitized}_usr"
    return sanitized[:50]


def _generate_unique_username(db: Session, email: str) -> str:
    """Generate a unique username from email local-part."""
    base = _sanitize_username(email.split("@")[0])

    if not db.query(User).filter(User.username == base).first():
        return base

    for attempt in range(1, 1000):
        candidate = f"{base}_{attempt}"[:50]
        if not db.query(User).filter(User.username == candidate).first():
            return candidate

    return f"{base[:43]}_{secrets.token_hex(3)}"[:50]


def _to_user_out(user: User) -> UserOut:
    """Convert SQLAlchemy user model to API response model safely."""
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at or datetime.utcnow(),
    )


# ============================================================================
# Google OAuth Endpoints
# ============================================================================

@router.get("/google")
async def google_login():
    """Redirect user to Google OAuth consent screen."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured. Contact administrator.",
        )

    state = generate_state()
    store_state(state)

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    logger.info("Redirecting to Google OAuth consent screen")
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = Query(None),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Handle Google OAuth callback, issue local JWTs, and return user profile."""

    if not verify_state(state):
        logger.warning("Invalid OAuth state - potential CSRF attack")
        return RedirectResponse(
            url=_frontend_redirect_url(False, reason="invalid_state"),
            status_code=status.HTTP_302_FOUND,
        )

    clear_state(state)

    if error:
        logger.warning("Google OAuth returned error: %s", error)
        return RedirectResponse(
            url=_frontend_redirect_url(False, reason="google_error"),
            status_code=status.HTTP_302_FOUND,
        )

    if not code:
        return RedirectResponse(
            url=_frontend_redirect_url(False, reason="missing_code"),
            status_code=status.HTTP_302_FOUND,
        )

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                },
            )

            if token_response.status_code != 200:
                logger.error("Google token exchange failed: %s", token_response.text)
                return RedirectResponse(
                    url=_frontend_redirect_url(False, reason="token_exchange_failed"),
                    status_code=status.HTTP_302_FOUND,
                )

            google_tokens = token_response.json()
            google_access_token = google_tokens.get("access_token")
            if not google_access_token:
                logger.error("Google token response missing access_token")
                return RedirectResponse(
                    url=_frontend_redirect_url(False, reason="token_missing"),
                    status_code=status.HTTP_302_FOUND,
                )

            user_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {google_access_token}"},
            )

            if user_response.status_code != 200:
                logger.error("Failed to get Google user info: %s", user_response.text)
                return RedirectResponse(
                    url=_frontend_redirect_url(False, reason="userinfo_failed"),
                    status_code=status.HTTP_302_FOUND,
                )

            google_user = user_response.json()

    except httpx.RequestError as exc:
        logger.error("Google OAuth network error: %s", exc)
        return RedirectResponse(
            url=_frontend_redirect_url(False, reason="network_error"),
            status_code=status.HTTP_302_FOUND,
        )

    google_id = google_user.get("id")
    email = (google_user.get("email") or "").strip().lower()
    name = (google_user.get("name") or "").strip()

    if not google_id or not email:
        logger.error("Missing required Google user information")
        return RedirectResponse(
            url=_frontend_redirect_url(False, reason="missing_user_info"),
            status_code=status.HTTP_302_FOUND,
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        try:
            user = User(
                email=email,
                username=_generate_unique_username(db, email),
                full_name=name or email.split("@")[0],
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                is_active=True,
                is_verified=True,
                oauth_provider="google",
                oauth_id=google_id,
                last_login=datetime.utcnow(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("New user created via Google OAuth: %s", email)
        except Exception:
            db.rollback()
            logger.exception("Error creating user from Google OAuth")
            return RedirectResponse(
                url=_frontend_redirect_url(False, reason="user_create_failed"),
                status_code=status.HTTP_302_FOUND,
            )
    else:
        if user.oauth_provider and user.oauth_provider != "google":
            logger.warning(
                "OAuth provider mismatch for %s: expected %s, got google",
                email,
                user.oauth_provider,
            )
            return RedirectResponse(
                url=_frontend_redirect_url(False, reason="provider_mismatch"),
                status_code=status.HTTP_302_FOUND,
            )

        if user.oauth_provider == "google" and user.oauth_id and user.oauth_id != google_id:
            logger.warning("OAuth ID mismatch for existing Google user: %s", email)
            return RedirectResponse(
                url=_frontend_redirect_url(False, reason="oauth_id_mismatch"),
                status_code=status.HTTP_302_FOUND,
            )

        try:
            if not user.oauth_provider:
                user.oauth_provider = "google"
            if not user.oauth_id:
                user.oauth_id = google_id
            if name and not user.full_name:
                user.full_name = name
            user.is_verified = True
            user.last_login = datetime.utcnow()
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            logger.exception("Error updating user OAuth info")
            return RedirectResponse(
                url=_frontend_redirect_url(False, reason="user_update_failed"),
                status_code=status.HTTP_302_FOUND,
            )

    if not user.is_active:
        return RedirectResponse(
            url=_frontend_redirect_url(False, reason="inactive_user"),
            status_code=status.HTTP_302_FOUND,
        )

    try:
        access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
        refresh_token = create_refresh_token(data={"sub": user.username, "user_id": user.id})

        logger.info("User authenticated via Google: %s", user.email)
        payload = GoogleTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=_to_user_out(user),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        exchange_code = _store_exchange_payload(payload)
        return RedirectResponse(
            url=_frontend_redirect_url(True, exchange_code=exchange_code),
            status_code=status.HTTP_302_FOUND,
        )
    except Exception:
        logger.exception("Error creating JWT tokens")
        return RedirectResponse(
            url=_frontend_redirect_url(False, reason="token_create_failed"),
            status_code=status.HTTP_302_FOUND,
        )


@router.post("/google/exchange", response_model=GoogleTokenResponse)
async def exchange_google_oauth_result(request: GoogleExchangeRequest) -> GoogleTokenResponse:
    """Exchange a one-time OAuth exchange code for tokens and user profile."""
    payload = _consume_exchange_payload(request.exchange_code)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired exchange code",
        )
    return payload
