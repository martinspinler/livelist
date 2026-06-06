#!/usr/bin/env python3
"""Example: Create songs for a band on a LiveList server.

Usage:
    python examples/create_songs.py --url https://livelist.cz --band myband --key secret

The song list is defined at the bottom of this file — edit it to suit.
"""

import argparse

from livelist.client import SyncLivelistClient


# ---------------------------------------------------------------------------
# Song data — edit this list to define the songs you want to create.
# Each entry is a dict with at least a "name" key.
# Optional keys match the server's create_song handler:
#   user_id, bpm, meta (dict)
# ---------------------------------------------------------------------------

SONGS = [
    {"name": "Fly Me To The Moon", "user_id": "46"},
    {"name": "Sing, Sing, Sing", "user_id": "77"},
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create songs on a LiveList server")
    parser.add_argument(
        "--url", default="http://localhost:5000",
        help="LiveList server URL (default: http://localhost:5000)",
    )
    parser.add_argument("--band", required=True, help="Band address (subdomain)")
    parser.add_argument("--key", required=True, help="Band access key / password")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be sent without connecting",
    )
    args = parser.parse_args()

    # Build batch requests
    requests = [
        {"cmd": "create_song", "arg": {k: v for k, v in song.items() if v is not None}}
        for song in SONGS
    ]

    if args.dry_run:
        print(f"Would send {len(requests)} create_song requests to {args.url}:")
        for req in requests:
            print(f"  {req['arg']['name']}")
        return

    with SyncLivelistClient(url=args.url, band=args.band, key=args.key) as client:
        print(f"Connected to {args.url} (band={args.band})")

        # Show current song count
        existing = len(client.songlist)
        print(f"Existing songs: {existing}")

        # Send the batch
        client.batch(requests)
        client.drain_events(timeout=2)

        # Verify by re-fetching
        updated = client.get_songlist()
        new_count = len(updated) - existing
        print(f"Created {new_count} song(s) — total now {len(updated)}")


if __name__ == "__main__":
    main()
