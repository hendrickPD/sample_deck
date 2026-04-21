"""Tests for zoom_scheduler.client and auth: timezone conversion, payload shape, 401 retry."""

import json as _json
import os
from unittest import mock

import pytest
import responses

from zoom_scheduler import auth, client

TOKEN_URL = "https://zoom.us/oauth/token"
MEETINGS_URL = "https://api.zoom.us/v2/users/host@example.com/meetings"


@pytest.fixture(autouse=True)
def env_vars():
    with mock.patch.dict(
        os.environ,
        {
            "ZOOM_ACCOUNT_ID": "acc_123",
            "ZOOM_CLIENT_ID": "cid_abc",
            "ZOOM_CLIENT_SECRET": "secret_xyz",
            "ZOOM_HOST_EMAIL": "host@example.com",
        },
    ):
        yield


@pytest.fixture(autouse=True)
def reset_token_cache():
    auth._cached_token = None
    yield
    auth._cached_token = None


def test_timezone_conversion_la_to_utc():
    # 14:00 PDT (UTC-7 in April) → 21:00 UTC
    assert client.to_utc_z("2026-04-22 14:00", "America/Los_Angeles") == "2026-04-22T21:00:00Z"


def test_timezone_conversion_ny_to_utc():
    # 09:00 EDT (UTC-4 in April) → 13:00 UTC
    assert client.to_utc_z("2026-04-22 09:00", "America/New_York") == "2026-04-22T13:00:00Z"


def test_timezone_conversion_utc_passthrough():
    assert client.to_utc_z("2026-04-22 21:00", "UTC") == "2026-04-22T21:00:00Z"


def test_payload_shape_has_all_required_fields():
    p = client.build_payload("Foo", "2026-04-22T21:00:00Z", 30, "America/Los_Angeles")
    assert p["topic"] == "Foo"
    assert p["type"] == 2
    assert p["start_time"] == "2026-04-22T21:00:00Z"
    assert p["duration"] == 30
    assert p["timezone"] == "America/Los_Angeles"
    assert p["settings"] == {
        "join_before_host": False,
        "waiting_room": True,
        "mute_upon_entry": True,
    }


@responses.activate
def test_create_meeting_sends_expected_payload_and_auth():
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "tok_1", "expires_in": 3600},
        status=200,
    )
    responses.add(
        responses.POST,
        MEETINGS_URL,
        json={"id": 123, "join_url": "https://zoom.us/j/123", "password": "abc"},
        status=201,
    )

    result = client.create_meeting("Foo", "2026-04-22T21:00:00Z", 30, "America/Los_Angeles")
    assert result["id"] == 123

    meeting_req = responses.calls[1].request
    assert meeting_req.headers["Authorization"] == "Bearer tok_1"
    body = _json.loads(meeting_req.body)
    assert body["topic"] == "Foo"
    assert body["type"] == 2
    assert body["start_time"] == "2026-04-22T21:00:00Z"
    assert body["duration"] == 30
    assert body["timezone"] == "America/Los_Angeles"
    assert body["settings"]["join_before_host"] is False
    assert body["settings"]["waiting_room"] is True
    assert body["settings"]["mute_upon_entry"] is True


@responses.activate
def test_token_refresh_on_401():
    # Two token fetches: stale, then fresh
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "tok_stale", "expires_in": 3600},
        status=200,
    )
    responses.add(
        responses.POST,
        TOKEN_URL,
        json={"access_token": "tok_fresh", "expires_in": 3600},
        status=200,
    )
    # Meeting creation: first call 401s, second (with fresh token) succeeds
    responses.add(
        responses.POST,
        MEETINGS_URL,
        json={"code": 124, "message": "Invalid access token"},
        status=401,
    )
    responses.add(
        responses.POST,
        MEETINGS_URL,
        json={"id": 456, "join_url": "https://zoom.us/j/456", "password": "xyz"},
        status=201,
    )

    result = client.create_meeting("Bar", "2026-04-22T21:00:00Z", 15, "America/Los_Angeles")
    assert result["id"] == 456

    # Call order: token (stale), meeting (401), token (fresh), meeting (201)
    assert len(responses.calls) == 4
    assert responses.calls[1].request.headers["Authorization"] == "Bearer tok_stale"
    assert responses.calls[3].request.headers["Authorization"] == "Bearer tok_fresh"
