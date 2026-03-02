"""Abstract base class for LiveList playlist clients."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Protocol, runtime_checkable

from .models import PlaylistItem, PlaylistItemId, Song


@runtime_checkable
class PlaylistCallback(Protocol):
    """Protocol for objects that receive playlist push events."""

    def pe_update_playlist(self, items: List[PlaylistItem]) -> None:
        """Called when the playlist contents change."""
        ...

    def pe_play(self, item: PlaylistItem) -> None:
        """Called when a playlist item is activated (played)."""
        ...

    def pe_add(self, item: PlaylistItem) -> None:
        """Called when an item is added to the playlist."""
        ...

    def pe_update_songlist(self, songs: dict) -> None:
        """Called when the song list is updated."""
        ...


class PlaylistClient(ABC):
    """Abstract base for LiveList playlist clients.

    Subclass this to implement a concrete transport (e.g. Socket.IO).
    Register callback objects via ``register()`` to receive push events.
    """

    def __init__(self) -> None:
        self._cbs: List[Any] = []
        self.songlist: dict[int, Song] = {}
        self.playlist: dict[int, PlaylistItem] = {}
        self.currentPlaylistId: Optional[int] = None

    def register(self, cb: Any) -> None:
        """Register a callback object (should satisfy PlaylistCallback)."""
        self._cbs.append(cb)

    def unregister(self, cb: Any) -> None:
        """Unregister a previously registered callback object."""
        self._cbs.remove(cb)

    # --- Abstract playlist-item operations ---

    @abstractmethod
    def playlist_item_add(
        self,
        song_id: int,
        *,
        target_id: Optional[int] = None,
        before: bool = False,
        playlist_id: Optional[int] = None,
    ) -> None:
        """Add a song to a playlist (defaults to the current playlist)."""
        ...

    @abstractmethod
    def playlist_item_delete(
        self,
        item_ids: List[PlaylistItemId],
        *,
        playlist_id: Optional[int] = None,
    ) -> None:
        """Delete items from a playlist."""
        ...

    @abstractmethod
    def playlist_item_move(
        self,
        moved_ids: List[PlaylistItemId],
        target_id: int,
        *,
        before: bool = False,
        playlist_id: Optional[int] = None,
    ) -> None:
        """Move items to before/after a target (drag-and-drop style)."""
        ...

    @abstractmethod
    def playlist_item_play(
        self,
        item_id: Optional[PlaylistItemId] = None,
        off: Optional[int] = None,
        *,
        playlist_id: Optional[int] = None,
    ) -> None:
        """Activate a playlist item, or shift by *off* positions."""
        ...


