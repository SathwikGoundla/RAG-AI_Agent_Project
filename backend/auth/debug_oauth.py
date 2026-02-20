from fastapi import APIRouter
from backend.config import settings

router = APIRouter()


@router.get("/debug_google")
async def debug_google_oauth():
    """Returns whether Google OAuth credentials are present (does not return secrets)."""
    configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    return {"google_oauth_configured": configured}
