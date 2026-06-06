"""Client-side data models for LiveList.

Plain dataclasses with no ORM dependency — suitable for use in
client applications that talk to a LiveList server over Socket.IO.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Type alias for playlist-item identifiers
PlaylistItemId = int


@dataclass
class Song:
    """A song in the LiveList system."""

    id: int
    name: str = ""
    user_id: Optional[str] = None
    bpm: Optional[int] = None
    notes: Optional[str] = None
    filename: Optional[str] = None
    store: Optional[str] = None
    meta: Optional[Dict] = None
    tags: List[str] = field(default_factory=list)
    last_playlist: Optional[Dict] = None
    pages: Optional[List[int]] = None


@dataclass
class PlaylistItem:
    """An item within a playlist, linking to a Song."""

    id: int
    song: Optional[Song] = None
    pos: int = 0


@dataclass
class PlaylistInfo:
    """Summary info about a playlist (returned by get_playlists)."""

    id: int
    name: str = ""
    date: str = ""
    band_id: Optional[int] = None
    active_item_id: Optional[int] = None
    item_count: int = 0
