# Livelist

**Collaborative playlist management for live bands**

Livelist is a real-time web application that helps bands organize their song library and manage setlists during live performances. Multiple band members can connect simultaneously and see playlist changes instantly.

## Architecture

- **Frontend** — Vanilla JS with Bootstrap 5, Socket.IO client
- **Backend** — Flask + Flask-SocketIO (WebSocket server)
- **Database** — SQLAlchemy ORM with SQLite
- **Real-time sync** — All playlist actions are broadcast to every connected member of the same band room

## Client Interface

The main view is divided into three sections:

### Livelist (Main View)

The central area showing the current playlist as an ordered, numbered list of songs. The view operates in three modes, toggled via the **Play / Move / Edit** button group in the navbar:

- **Play mode** *(default)* — Performance mode. Tap the play button (▶) on any item to mark it as the active song; the event is broadcast to all connected clients. The anchor (⚓) is visible for adding songs at a specific position.
- **Move mode** — Reorder mode. Each item shows a drag handle (≡) and a "move to anchor" button (→⚓) on the right side. Songs can be rearranged by:
  - **Drag & Drop** — Drag the grip handle to reorder items directly
  - **Move to anchor** — Click the →⚓ button to instantly move an item to the anchor position (one click instead of scrolling + dragging)
- **Edit mode** — Management mode. Position numbers become clickable selection targets (outline style). Select multiple items to:
  - Delete selected items in bulk
  - Update item order explicitly

#### Anchor System

The anchor (⚓) determines where new songs are inserted and where items are moved when using "move to anchor". It has two states, toggled by clicking the anchor item:

- **Non-sticky** (⚓↓) — Items are inserted/moved *after* the anchor, then the anchor advances past the new item. Enables sequential workflow.
- **Sticky** (⚓↑) — Items are inserted/moved *before* the anchor, and the anchor stays in place. Enables accumulating items at a fixed position.

Click the playlist header ("Set 1") to move the anchor to the top (insert before the first item).

### Song Library (Left Offcanvas Panel)

A searchable, filterable catalog of all songs in the band's library.

- **Search** — Type-to-filter text input, plus an optional T9-style keypad for quick lookups
- **Sorting** — Sort alphabetically (A–Z), by BPM, or by ID
- **Tag filtering** — Advanced tag-based filtering system:
  - **Filter chips** — Add/remove tag chips; toggle each chip between include/exclude mode
  - **Advanced toggle** — Show/hide advanced filter options:
    - **Gate controls** — Mark certain tags as "gated" (hidden by default) with eye indicators
    - **AND/OR logic** — Switch between intersective (AND) and union (OR) filter modes
- **Add to playlist** — Click a song to add it to the current playlist; in edit mode, click to insert at a specific position relative to the selected item
- **Pin panel** — Pin the offcanvas panel open instead of auto-closing
- **Edit mode** — Switch the library to edit mode to:
  - Create new songs directly from the filter bar
  - Edit existing songs (name, BPM, tags) via a modal dialog
  - Manage tags with prefix conventions: none (normal), `!` (hidden by default), `#` (advanced-only)

### Playlist Manager (Left Offcanvas Panel)

Manage all playlists for the band.

- **Create** — Name + date form to create a new playlist
- **Select** — Click a playlist to load it into the livelist view
- **Activate** — Set a playlist as the band's active playlist (broadcast icon)
- **Edit** — Rename a playlist or change its date via a modal
- **Delete** — Remove a playlist

## Authentication

Bands authenticate via a simple password stored per-band. The auth state is kept in a cookie (`auth_data_simple`) and validated on both HTTP and WebSocket connections. Subdomain-based routing is supported (e.g. `myband.livelist.dev`) so each band gets its own URL.

## Data Model

| Model | Description |
|---|---|
| **Band** | A musical group with a subdomain identifier (`addr`), password auth, and an active playlist reference |
| **Song** | A song in the band's library — name, BPM, user identifier (`user_id`), tags, optional file reference and JSON metadata |
| **Tag** | Labels for filtering songs (e.g. genre, mood). Tags are per-band and many-to-many with songs |
| **Playlist** | A dated setlist belonging to a band — tracks an `active_item_id` for the currently playing song |
| **PlaylistItem** | A song placed at a specific position within a playlist |

## Additional Views

- **Live Sheet Screen** (`/play/<playlist_id>/`) — A clean, read-only display optimized for projection or a shared screen, showing the currently playing song in real time
- **Sheet Music** (`/sheets/<song_name>/`) — View sheet music/PDF for a song


## Setup

### Install

```bash
pip install -e ".[all]"      # server + client
pip install -e ".[server]"   # server only
```

### Configure

Optionally, set environment variables (or use a `.env` file):

| Variable | Description | Default |
|---|---|---|
| `LIVELIST_DATABASE_URI` | SQLAlchemy database URI | `sqlite:///livelist.db` |
| `LIVELIST_DOMAINS` | Colon-separated main domains for subdomain routing | *(empty)* |

### Initialize & Run

```bash
# Create database tables
flask init-db

# Create a band
flask create-band <name> <addr> <password>

# Start the server
python -m livelist.server
```
