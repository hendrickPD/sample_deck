"""Zoom API client for creating scheduled meetings."""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from .auth import authed_request

API_BASE = "https://api.zoom.us/v2"
LOCAL_FORMAT = "%Y-%m-%d %H:%M"


def to_utc_z(local_str: str, tz: str) -> str:
    """Parse "YYYY-MM-DD HH:MM" in the given IANA tz and return UTC ISO 8601 with Z suffix."""
    naive = datetime.strptime(local_str, LOCAL_FORMAT)
    local = naive.replace(tzinfo=ZoneInfo(tz))
    utc = local.astimezone(ZoneInfo("UTC"))
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_payload(topic: str, start_utc: str, duration_min: int, tz: str) -> dict:
    return {
        "topic": topic,
        "type": 2,
        "start_time": start_utc,
        "duration": duration_min,
        "timezone": tz,
        "settings": {
            "join_before_host": False,
            "waiting_room": True,
            "mute_upon_entry": True,
        },
    }


def create_meeting(topic: str, start_utc: str, duration_min: int, tz: str) -> dict:
    host = os.environ["ZOOM_HOST_EMAIL"]
    url = f"{API_BASE}/users/{host}/meetings"
    payload = build_payload(topic, start_utc, duration_min, tz)
    response = authed_request("POST", url, json=payload)
    response.raise_for_status()
    return response.json()
