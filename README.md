# Livelist

**Collaborative playlist management for live bands**

Livelist is a real-time web application that helps bands organize their song library and manage setlists during live performances. Multiple band members can connect simultaneously and see playlist changes instantly.

## Architecture

- **Frontend** — Vanilla JS with Bootstrap 5, Socket.IO client
- **Backend** — Flask + Flask-SocketIO (WebSocket server)
- **Database** — SQLAlchemy ORM with SQLite (any SQLAlchemy URI works)
- **Real-time sync** — All playlist actions are broadcast to every connected member of the same band room

## Client Interface

The main band view combines three panels:

- **Livelist** — the current playlist as a numbered list, with Play / Move / Edit modes for performance, reordering, and bulk management.
- **Song Library** *(left offcanvas)* — searchable, tag-filterable catalog of the band's songs; add songs to the playlist or insert set breaks.
- **Playlist Manager** *(left offcanvas)* — create, select, activate, edit, and delete playlists.

A full, localized guide to every mode, the anchor system, sets/breaks, and library controls is available in-app via the **Help** modal (navbar menu → Help).

## Authentication

Bands authenticate via a simple password stored per-band. The auth state is kept in a cookie (`auth_data_simple`) and validated on both HTTP and WebSocket connections. Subdomain-based routing is supported (e.g. `myband.livelist.dev`) so each band gets its own URL.

## Data Model

| Model | Description |
|---|---|
| **Band** | A musical group with a subdomain identifier (`addr`), password auth, an active playlist reference, and a per-band sheet-store config (`sheet_store`, JSON) |
| **Song** | A song in the band's library — name, BPM, user identifier (`user_id`), tags, optional file reference and JSON metadata |
| **Tag** | Labels for filtering songs (e.g. genre, mood). Tags are per-band and many-to-many with songs |
| **Playlist** | A dated setlist belonging to a band — tracks an `active_item_id` for the currently playing song |
| **PlaylistItem** | A song or break placed at a specific position within a playlist. Break items have `song_id = null` and `meta.is_break = true` |

## Sheet Music & Lyrics

- **Sheet Music** — shows sheet music as images (PDF pages are converted and cached on disk) or lyrics as plain text.

Each band has its own sheet-music layout, stored as JSON in the band's `sheet_store` field. The configuration has two parts:

- **Patterns** — where to find a file for a song. Each pattern sets a render type (`pdf` or `text`), a path template built from the `{name}` and `{instrument}` placeholders, and a display label.
- **Instruments** — the filename suffixes to try for each instrument (e.g. `-Piano`, `-Voice`) and the order in which patterns are preferred for that instrument.

Files are resolved relative to the global `LIVELIST_SHEET_STORE_PATH` directory (an optional `{band}` placeholder is replaced with the band's `addr`). See `examples/sheet-store-band.json` for a full reference layout.

## Setup

### Install

```bash
pip install -e ".[all]"      # server + client
pip install -e ".[server]"   # server only
```

### Configure

Set environment variables (or use a `.env` file). For the Flask CLI, point it at the app once per shell:

```bash
export FLASK_APP=livelist.server
```

| Variable | Description | Default |
|---|---|---|
| `LIVELIST_DATABASE_URI` | SQLAlchemy database URI | `sqlite:///livelist.db` |
| `LIVELIST_DOMAINS` | Colon-separated main domains for subdomain routing | *(empty)* |
| `LIVELIST_SHEET_STORE_PATH` | Base filesystem directory for sheet-music files (an optional `{band}` placeholder is filled with the band's `addr`) | *(empty)* |

### Initialize & Run

```bash
# Create database tables
flask init-db

# Create a band
flask create-band <name> <addr> <password>

# Configure a band's sheet store from a JSON file
flask set-sheet-store <addr> examples/sheet-store-perfecttime.json

# Start the server
python -m livelist.server
```
