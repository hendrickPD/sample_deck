# zoom-scheduler

A standalone Python CLI for creating scheduled Zoom meetings via the Zoom REST API,
authenticated with a Server-to-Server OAuth app. Single-user, local use.

## Zoom Marketplace setup

1. Go to <https://marketplace.zoom.us/> → **Develop** → **Build App** → **Server-to-Server OAuth**.
2. Give it a name (e.g. `zoom-scheduler`) and create it.
3. Under **App Credentials**, note the **Account ID**, **Client ID**, and **Client Secret**.
4. Under **Scopes**, add the scope that lets you create meetings on behalf of a user. Depending
   on account structure one of these will apply:
   - `meeting:write:meeting:admin` (granular scope, newer apps) — admin-level create on any user
   - `meeting:write:admin` / `meeting:write` (classic scope) — same intent, older naming
   Add the one your Marketplace UI offers. If unsure, add both.
5. **Activate** the app. On a managed Zoom account, this may require an account admin to
   approve the app before you can get tokens.

The `ZOOM_HOST_EMAIL` you use must be a **licensed** Zoom user who has logged into Zoom at
least once (see Known issues below).

## Install

```bash
git clone <this repo>
cd zoom-scheduler
cp .env.example .env
# edit .env and fill in the four values

python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv venv
source .venv/bin/activate
uv pip install -e .[dev]
```

## Usage

```bash
# Dry run first — prints the payload, does not call Zoom
zoom-schedule --dry-run --topic "Design review" --start "2026-04-22 14:00" --duration 30

# For real, in your local timezone (default America/Los_Angeles)
zoom-schedule --topic "Design review" --start "2026-04-22 14:00" --duration 30

# Override the timezone
zoom-schedule --topic "EU sync" --start "2026-04-22 15:00" --duration 45 --tz Europe/Berlin
```

On success, prints:

```
Meeting created
Topic: Design review
Start: 2026-04-22 14:00 (America/Los_Angeles)
Join URL: https://zoom.us/j/...
Meeting ID: 12345678901
Passcode: abc123
```

## Timezone convention

`--start` is parsed as a **naive local time** in the `--tz` timezone, then converted to UTC
internally and sent to Zoom with a `Z` suffix (e.g. `2026-04-22T21:00:00Z`). The `timezone`
field in the Zoom payload is sent for display purposes only — when `start_time` ends in `Z`,
Zoom treats the time as UTC regardless of what `timezone` says. This tool picks one
convention (local-in → UTC-out) and sticks with it so the round-trip is unambiguous.

## Tests

```bash
pytest
```

Tests mock HTTP with [`responses`](https://github.com/getsentry/responses) and do not hit
real Zoom.

## Known issues

- **`ZOOM_HOST_EMAIL` must be licensed and have logged into Zoom at least once.** Freshly
  provisioned users and Basic (free) users will return `404 User not found` or similar from
  the create-meeting endpoint even when your OAuth app is working. Log in once via the web
  client to materialize the user, and confirm the license in the Zoom admin panel.
- Tokens are cached per process. The CLI exits after one call, so caching only matters if
  you import `zoom_scheduler` as a library. On 401, the cached token is refreshed once.

## Scope (v1)

In: scheduled meeting creation. Out: Google Calendar sync, MCP wrapper, recurring meetings,
update/delete, multi-user hosting.
