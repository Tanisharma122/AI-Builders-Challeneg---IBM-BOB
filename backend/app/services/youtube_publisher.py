"""
YouTube Shorts publishing service.

Responsibilities:
  - Build Google OAuth 2.0 consent URL requesting youtube.upload scope.
  - Exchange auth code for credentials (access + refresh tokens).
  - Upload a local video file to YouTube using chunked resumable upload.
  - Refresh expired access tokens automatically.
  - Generate AI-powered title / description / viral tag suggestions from
    a clip's hook text and script commentary (no external LLM required —
    heuristic generation using the Granite analysis data already present).
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Lazy imports so the module loads even without google libs installed ────────

def _get_flow(client_id: str, client_secret: str, redirect_uri: str):
    """Return a google_auth_oauthlib Flow configured for youtube.upload."""
    from google_auth_oauthlib.flow import Flow  # type: ignore

    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
        redirect_uri=redirect_uri,
    )
    return flow


# ── OAuth helpers ─────────────────────────────────────────────────────────────


def build_auth_url(client_id: str, client_secret: str, redirect_uri: str) -> str:
    """
    Generate the Google OAuth consent URL.

    The user visits this URL, grants permission, and Google redirects them
    back to *redirect_uri* with a ``code`` query parameter.
    """
    flow = _get_flow(client_id, client_secret, redirect_uri)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # force refresh_token on every auth
    )
    return auth_url


def exchange_code_for_tokens(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> dict:
    """
    Exchange an auth *code* for access + refresh tokens.

    Returns a dict with ``access_token``, ``refresh_token``, ``token_uri``,
    ``client_id``, ``client_secret``, and ``scopes`` — everything needed to
    reconstruct a ``google.oauth2.credentials.Credentials`` object later.
    """
    flow = _get_flow(client_id, client_secret, redirect_uri)
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or []),
    }


def _build_credentials(token_data: dict):
    """Reconstruct a google.oauth2.credentials.Credentials from stored token_data."""
    from google.oauth2.credentials import Credentials  # type: ignore
    from google.auth.transport.requests import Request  # type: ignore

    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )

    # Refresh if the access token is expired
    if creds.expired and creds.refresh_token:
        logger.info("Access token expired — refreshing via refresh_token.")
        try:
            creds.refresh(Request())
        except Exception as exc:
            raise ValueError(
                "YouTube access token is expired and could not be refreshed. "
                "Please re-authenticate via /api/auth/youtube/login."
            ) from exc

    return creds


# ── Upload ────────────────────────────────────────────────────────────────────


def upload_to_youtube(
    video_path: str | Path,
    title: str,
    description: str,
    tags: list[str],
    token_data: dict,
    category_id: str = "22",
) -> str:
    """
    Upload *video_path* to YouTube using chunked resumable upload.

    Args:
        video_path:   Local path to the rendered .mp4 clip.
        title:        Video title. ``#Shorts`` is appended automatically.
        description:  Video description.
        tags:         List of tags (viral tags recommended).
        token_data:   Dict returned by :func:`exchange_code_for_tokens`.
        category_id:  YouTube category ID. Default ``"22"`` = People & Blogs.

    Returns:
        The published YouTube Shorts URL, e.g.
        ``https://youtube.com/shorts/{video_id}``.

    Raises:
        FileNotFoundError:  *video_path* does not exist.
        ValueError:         Token is expired and cannot be refreshed.
        RuntimeError:       YouTube API returned an error during upload.
    """
    from google.auth.transport.requests import AuthorizedSession  # type: ignore

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    creds = _build_credentials(token_data)

    # Use requests-based AuthorizedSession — avoids httplib2 redirect bug on Windows
    authed_session = AuthorizedSession(creds)

    # Ensure title ends with #Shorts (not duplicated)
    shorts_title = title.rstrip()
    if "#Shorts" not in shorts_title:
        shorts_title = f"{shorts_title} #Shorts"

    body = {
        "snippet": {
            "title": shorts_title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    # ── Resumable upload via requests (avoids httplib2 redirect bug on Windows) ──
    import json as _json

    file_size = video_path.stat().st_size
    upload_url_endpoint = (
        "https://www.googleapis.com/upload/youtube/v3/videos"
        f"?uploadType=resumable&part=snippet,status"
    )

    # Step 1: initiate resumable session — get upload URI
    init_headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": "video/mp4",
        "X-Upload-Content-Length": str(file_size),
    }
    init_resp = authed_session.post(
        upload_url_endpoint,
        headers=init_headers,
        data=_json.dumps(body),
    )
    if init_resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Failed to initiate upload session: {init_resp.status_code} {init_resp.text}"
        )
    upload_uri = init_resp.headers.get("Location")
    if not upload_uri:
        raise RuntimeError("YouTube did not return an upload URI in the Location header.")

    # Step 2: upload file in 5 MB chunks
    chunk_size = 5 * 1024 * 1024
    uploaded = 0
    response_data = None

    with open(video_path, "rb") as fh:
        while uploaded < file_size:
            chunk = fh.read(chunk_size)
            chunk_len = len(chunk)
            end_byte = uploaded + chunk_len - 1

            chunk_headers = {
                "Content-Length": str(chunk_len),
                "Content-Range": f"bytes {uploaded}-{end_byte}/{file_size}",
                "Content-Type": "video/mp4",
            }
            chunk_resp = authed_session.put(upload_uri, headers=chunk_headers, data=chunk)

            if chunk_resp.status_code in (200, 201):
                response_data = chunk_resp.json()
                uploaded = file_size
                logger.info("Upload complete (100%%)")
            elif chunk_resp.status_code == 308:
                # Incomplete — server accepted chunk, advance pointer
                range_header = chunk_resp.headers.get("Range", "")
                if range_header:
                    uploaded = int(range_header.split("-")[1]) + 1
                else:
                    uploaded += chunk_len
                logger.info("Upload progress: %d%%", int(uploaded / file_size * 100))
            elif chunk_resp.status_code in (401, 403):
                raise ValueError(
                    "YouTube authentication failed during upload. Please re-authenticate."
                )
            elif chunk_resp.status_code == 429:
                raise RuntimeError(
                    "YouTube API quota exceeded. Try again tomorrow."
                )
            else:
                raise RuntimeError(
                    f"YouTube upload error: {chunk_resp.status_code} {chunk_resp.text}"
                )

    video_id = (response_data or {}).get("id")
    if not video_id:
        raise RuntimeError(f"Upload succeeded but no video ID returned: {response_data}")

    logger.info("Upload complete — video ID: %s", video_id)
    return f"https://youtube.com/shorts/{video_id}"


# ── AI Suggestions ────────────────────────────────────────────────────────────


_VIRAL_TAGS: list[str] = [
    "shorts", "youtubeshorts", "viral", "trending", "fyp",
    "shortsvideo", "reels", "trendingshorts", "viralvideo", "explore",
    "shortsfeed", "shortsvideos", "viralshorts", "trending2024", "trending2025",
]

_HOOK_TEMPLATES = [
    "You won't believe {hook}",
    "Wait for it… {hook}",
    "The truth about {hook}",
    "Nobody talks about {hook}",
    "This changes everything: {hook}",
    "{hook} (watch till end)",
    "How {hook} went viral",
    "Real talk: {hook}",
]


def generate_title_suggestions(
    hook_text: str,
    script_commentary: str,
    virality_score: int,
    count: int = 5,
) -> list[str]:
    """
    Generate *count* catchy YouTube Shorts title suggestions.

    Uses heuristic templates combined with the clip's hook and commentary.
    No external API call — instant, always available.
    """
    # Clean and truncate hook text for use in titles
    clean_hook = re.sub(r"\s+", " ", hook_text.strip())[:60]
    suggestions: list[str] = []

    for template in _HOOK_TEMPLATES[:count]:
        title = template.format(hook=clean_hook)
        if len(title) > 100:
            title = title[:97] + "…"
        suggestions.append(title)

    # If virality is high, also add a direct title variant
    if virality_score >= 70 and len(suggestions) < count:
        suggestions.append(f"{clean_hook} #Shorts")

    return suggestions[:count]


def generate_description_suggestions(
    hook_text: str,
    script_commentary: str,
    virality_score: int,
    tags: list[str],
    count: int = 3,
) -> list[str]:
    """
    Generate *count* YouTube Shorts description suggestions.
    """
    tag_string = " ".join(f"#{t}" for t in tags[:20])
    clean_hook = hook_text.strip()
    clean_commentary = re.sub(r"\s+", " ", script_commentary.strip())[:300]

    templates = [
        (
            f"{clean_hook}\n\n"
            f"{clean_commentary}\n\n"
            f"Like & Subscribe for more! \n\n"
            f"{tag_string}"
        ),
        (
            f"🔥 {clean_hook} 🔥\n\n"
            f"{clean_commentary}\n\n"
            f"Follow for daily content!\n\n"
            f"{tag_string}"
        ),
        (
            f"{clean_commentary}\n\n"
            f"Drop a comment below! 👇\n\n"
            f"{tag_string}"
        ),
    ]

    return templates[:count]


def generate_viral_tags(
    hook_text: str,
    script_commentary: str,
    virality_score: int,
    max_tags: int = 30,
) -> list[str]:
    """
    Generate a curated list of viral + contextual tags for the video.
    """
    # Extract meaningful words from hook + commentary
    combined = f"{hook_text} {script_commentary}".lower()
    words = re.findall(r"\b[a-z]{4,}\b", combined)

    # Deduplicate and pick the most relevant words as contextual tags
    seen: set[str] = set(_VIRAL_TAGS)
    contextual: list[str] = []
    for word in words:
        if word not in seen and len(contextual) < 15:
            contextual.append(word)
            seen.add(word)

    all_tags = _VIRAL_TAGS + contextual
    return all_tags[:max_tags]
