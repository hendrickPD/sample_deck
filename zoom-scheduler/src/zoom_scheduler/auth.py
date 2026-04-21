"""Zoom Server-to-Server OAuth token management.

Tokens are cached in module-level state for the process lifetime. Zoom
access tokens expire after 1 hour, so we proactively refresh on 401.
"""

import base64
import os
from typing import Optional

import requests

TOKEN_URL = "https://zoom.us/oauth/token"

_cached_token: Optional[str] = None


def _fetch_token() -> str:
    account_id = os.environ["ZOOM_ACCOUNT_ID"]
    client_id = os.environ["ZOOM_CLIENT_ID"]
    client_secret = os.environ["ZOOM_CLIENT_SECRET"]

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {basic}"},
        data={"grant_type": "account_credentials", "account_id": account_id},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_token(force_refresh: bool = False) -> str:
    global _cached_token
    if force_refresh or _cached_token is None:
        _cached_token = _fetch_token()
    return _cached_token


def authed_request(method: str, url: str, **kwargs) -> requests.Response:
    """Make an authenticated Zoom API request, retrying once on 401 with a fresh token."""
    token = get_token()
    headers = dict(kwargs.pop("headers", {}) or {})
    headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, url, headers=headers, timeout=30, **kwargs)

    if response.status_code == 401:
        token = get_token(force_refresh=True)
        headers["Authorization"] = f"Bearer {token}"
        response = requests.request(method, url, headers=headers, timeout=30, **kwargs)

    return response
