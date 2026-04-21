"""CLI entry point for zoom-schedule."""

import json
import sys

import click
from dotenv import load_dotenv

from .client import build_payload, create_meeting, to_utc_z


@click.command()
@click.option("--topic", required=True, help="Meeting topic/title.")
@click.option("--start", "start", required=True, help='Start time "YYYY-MM-DD HH:MM" in --tz.')
@click.option("--duration", required=True, type=int, help="Duration in minutes.")
@click.option("--tz", default="America/Los_Angeles", show_default=True, help="IANA timezone for --start.")
@click.option("--dry-run", is_flag=True, help="Print the request payload and exit without calling Zoom.")
def main(topic: str, start: str, duration: int, tz: str, dry_run: bool) -> None:
    load_dotenv()

    try:
        start_utc = to_utc_z(start, tz)
    except ValueError as e:
        click.echo(f"Error parsing --start (expected 'YYYY-MM-DD HH:MM'): {e}", err=True)
        sys.exit(1)

    payload = build_payload(topic, start_utc, duration, tz)

    if dry_run:
        click.echo("DRY RUN — would POST this payload:")
        click.echo(json.dumps(payload, indent=2))
        return

    meeting = create_meeting(topic, start_utc, duration, tz)
    click.echo("Meeting created")
    click.echo(f"Topic: {meeting.get('topic', topic)}")
    click.echo(f"Start: {start} ({tz})")
    click.echo(f"Join URL: {meeting.get('join_url', '')}")
    click.echo(f"Meeting ID: {meeting.get('id', '')}")
    click.echo(f"Passcode: {meeting.get('password') or '(none)'}")


if __name__ == "__main__":
    main()
