"""
YouTube OAuth 2.0 authentication endpoints.

Routes
------
GET  /api/auth/youtube/login      — return Google consent URL
GET  /api/auth/youtube/callback   — exchange auth code for tokens
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/youtube", tags=["youtube-auth"])


@router.get("/login")
async def youtube_login() -> JSONResponse:
    """
    Return the Google OAuth consent URL.

    The frontend should redirect the user (or open a popup) to the returned
    ``auth_url``. After the user grants permission Google will redirect to
    the configured ``YOUTUBE_REDIRECT_URI`` with a ``code`` query parameter.

    Requires ``YOUTUBE_CLIENT_ID``, ``YOUTUBE_CLIENT_SECRET``, and
    ``YOUTUBE_REDIRECT_URI`` to be set in the environment.
    """
    if not settings.youtube_client_id or not settings.youtube_client_secret:
        raise HTTPException(
            status_code=503,
            detail=(
                "YouTube OAuth is not configured. "
                "Set YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and "
                "YOUTUBE_REDIRECT_URI in your .env file."
            ),
        )

    try:
        from app.services.youtube_publisher import build_auth_url

        auth_url = build_auth_url(
            client_id=settings.youtube_client_id,
            client_secret=settings.youtube_client_secret,
            redirect_uri=settings.youtube_redirect_uri,
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail=(
                "google-auth-oauthlib is not installed. "
                "Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
            ),
        )
    except Exception as exc:
        logger.exception("Failed to build YouTube auth URL.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return JSONResponse({"auth_url": auth_url})


@router.get("/callback")
async def youtube_callback(
    code: str = Query(..., description="Auth code returned by Google"),
    error: str | None = Query(default=None, description="OAuth error from Google"),
) -> JSONResponse:
    """
    Exchange the Google OAuth *code* for access + refresh tokens.

    In a production app you would store these server-side (encrypted, per-user).
    Here we return them directly to the frontend so the client can pass them
    back on the publish request — acceptable for a single-user / demo deployment.

    The returned ``token_data`` object should be stored securely (e.g.
    ``localStorage`` with appropriate XSS mitigations or an HttpOnly cookie).
    """
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Google OAuth error: {error}. The user may have denied access.",
        )

    if not settings.youtube_client_id or not settings.youtube_client_secret:
        raise HTTPException(
            status_code=503,
            detail="YouTube OAuth is not configured on the server.",
        )

    try:
        from app.services.youtube_publisher import exchange_code_for_tokens

        token_data = exchange_code_for_tokens(
            code=code,
            client_id=settings.youtube_client_id,
            client_secret=settings.youtube_client_secret,
            redirect_uri=settings.youtube_redirect_uri,
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="google-auth-oauthlib is not installed.",
        )
    except Exception as exc:
        logger.exception("Token exchange failed.")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange code for tokens: {exc}",
        ) from exc

    return JSONResponse(
        {
            "token_data": token_data,
            "message": "Authentication successful. Store token_data securely.",
        }
    )
