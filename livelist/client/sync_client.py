"""Synchronous Socket.IO client for LiveList."""

from dataclasses import fields
from typing import Any, Dict, List, Optional

import socketio
from socketio.exceptions import TimeoutError as SocketTimeoutError

from .models import PlaylistInfo, PlaylistItem, PlaylistItemId, Song
from .playlist import PlaylistClient


class SyncLivelistClient(PlaylistClient):
    """Synchronous LiveList client using Socket.IO.

    Designed for scripts and simple integrations.  Use as a context manager::

        with SyncLivelistClient(
            url="http://localhost:5000",
            band="myband",
            key="secret",
        ) as client:
            songs = client.get_songlist()
            client.create_song(name="My Song")

    For long-running listeners, call ``listen()`` after ``connect()``.
    """

    def __init__(
        self,
        url: str,
        band: str,
        key: str,
        *,
        default_store: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._url = url
        self._auth: dict = {"band": band, "key": key}
        self._defstore = default_store
        self.sio = socketio.SimpleClient()

    # ---- Context manager -----------------------------------------------

    def __enter__(self) -> "SyncLivelistClient":
        self.connect()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.disconnect()

    # ---- Connection lifecycle ------------------------------------------

    def connect(self) -> None:
        """Connect to the LiveList server and fetch initial data."""
        self.sio.connect(self._url, auth=self._auth)
        _event, conn_data = self.sio.receive()  # "connected"
        self._band_id = conn_data["band_id"]
        self.get_songlist()
        self.select_playlist()

    def disconnect(self) -> None:
        """Disconnect from the server."""
        self.sio.disconnect()

    def listen(self, timeout: Optional[float] = None) -> None:
        """Block and process push events until disconnected or timed out.

        This is useful for keeping the client alive to receive real-time
        updates.  Call ``connect()`` first, then ``listen()``.
        """
        while True:
            try:
                event, data = self.sio.receive(timeout=timeout)
                self._handle_event(event, data)
            except (ConnectionError, SocketTimeoutError):
                break

    def drain_events(self, timeout: float = 1.0) -> None:
        """Process any pending incoming events, then return.

        Useful after fire-and-forget operations to ensure the server
        has processed your requests and sent back updates.
        """
        short_timeout = 0.1
        while True:
            try:
                event, data = self.sio.receive(timeout=timeout)
                self._handle_event(event, data)
                timeout = short_timeout  # Drain remaining quickly
            except SocketTimeoutError:
                break

    # ---- Internal helpers ----------------------------------------------

    def _emit_and_wait(
        self,
        event: str,
        data: Any = None,
        expected: Optional[str] = None,
    ) -> tuple:
        """Emit an event and wait for a response event.

        If *expected* is given, non-matching events are dispatched
        to their own handlers instead of being returned.
        """
        self.sio.emit(event, data or {})
        while True:
            resp_event, resp_data = self.sio.receive()
            if expected is None or resp_event == expected:
                return resp_event, resp_data
            self._handle_event(resp_event, resp_data)

    def _handle_event(self, event: str, data: Any) -> None:
        """Dispatch a single incoming event to its handler."""
        handlers = {
            "playlist_updated": self._receive_playlist,
            "playlist_select": self._receive_playlist_full,
            "item_played": self._receive_play,
        }
        handler = handlers.get(event)
        if handler:
            handler(data)

    # ---- Abstract-method implementations -------------------------------

    def playlist_item_add(
        self,
        song_id: int,
        *,
        target_id: Optional[int] = None,
        before: bool = False,
        playlist_id: Optional[int] = None,
    ) -> None:
        pid = playlist_id or self.currentPlaylistId
        self.sio.emit("add_song", {
            "song_id": song_id,
            "playlist_id": pid,
            "target_id": target_id,
            "before": before,
        })

    def playlist_item_delete(
        self,
        item_ids: List[PlaylistItemId],
        *,
        playlist_id: Optional[int] = None,
    ) -> None:
        pid = playlist_id or self.currentPlaylistId
        self.sio.emit("delete_items", {
            "item_ids": item_ids,
            "playlist_id": pid,
        })

    def playlist_item_move(
        self,
        moved_ids: List[PlaylistItemId],
        target_id: int,
        *,
        before: bool = False,
        playlist_id: Optional[int] = None,
    ) -> None:
        pid = playlist_id or self.currentPlaylistId
        self.sio.emit("move_item", {
            "moved_ids": moved_ids,
            "target_id": target_id,
            "before": before,
            "playlist_id": pid,
        })

    def playlist_item_play(
        self,
        item_id: Optional[PlaylistItemId] = None,
        off: Optional[int] = None,
        *,
        playlist_id: Optional[int] = None,
    ) -> None:
        pid = playlist_id or self.currentPlaylistId
        self.sio.emit("play_item", {
            "item_id": item_id,
            "off": off,
            "playlist_id": pid,
        })

    # ---- Request-response methods --------------------------------------

    def select_playlist(self, playlist_id: Optional[int] = None) -> None:
        """Select a playlist (defaults to the band's active playlist)."""
        data: dict = {}
        if playlist_id is not None:
            data["playlist_id"] = playlist_id
        _event, resp = self._emit_and_wait(
            "select_playlist", data, expected="playlist_select",
        )
        self._receive_playlist(resp, update_current=True)
        self._receive_playlist_current_item(resp)

    def get_songlist(self) -> Dict[int, Song]:
        """Fetch the full song list from the server."""
        _event, data = self._emit_and_wait("get_songlist", {}, expected="songlist")
        self._parse_songlist(data)
        return self.songlist

    def get_playlists(self) -> List[PlaylistInfo]:
        """Fetch all playlists for the current band."""
        _event, data = self._emit_and_wait("get_playlists", {}, expected="playlists")
        return [PlaylistInfo(**p) for p in data]

    # ---- Convenience mutation methods (fire-and-forget) ---------------

    def create_song(self, name: str, **kwargs: Any) -> None:
        """Create a new song on the server."""
        self.sio.emit("create_song", {"name": name, **kwargs})

    def save_song(self, song_id: int, **kwargs: Any) -> None:
        """Update an existing song."""
        kwargs["id"] = song_id
        self.sio.emit("save_song", kwargs)

    def create_tag(self, name: str) -> None:
        """Create a new tag for the band."""
        self.sio.emit("create_tag", {"name": name})

    def batch(self, requests: List[dict]) -> None:
        """Send a batch of operations.

        Each request is a dict with ``cmd`` and ``arg`` keys, e.g.::

            client.batch([
                {"cmd": "create_song", "arg": {"name": "Song A"}},
                {"cmd": "create_tag",   "arg": {"name": "jazz"}},
            ])
        """
        self.sio.emit("batch", {"requests": requests})

    def activate_playlist(self, playlist_id: int) -> None:
        """Set a playlist as the band's active playlist."""
        self.sio.emit("activate_playlist", {"playlist_id": playlist_id})

    def create_playlist(self, name: str, date: Optional[str] = None) -> None:
        """Create a new playlist."""
        data: dict = {"name": name}
        if date is not None:
            data["date"] = date
        self.sio.emit("create_playlist", data)

    def delete_playlist(self, playlist_id: int) -> None:
        """Delete a playlist."""
        self.sio.emit("delete_playlist", {"playlist_id": playlist_id})

    def save_playlist(
        self,
        playlist_id: int,
        name: Optional[str] = None,
        date: Optional[str] = None,
    ) -> None:
        """Update playlist metadata."""
        data: dict = {"playlist_id": playlist_id}
        if name is not None:
            data["name"] = name
        if date is not None:
            data["date"] = date
        self.sio.emit("save_playlist", data)

    # ---- Incoming event handlers ---------------------------------------

    def _receive_playlist_full(self, data: Any) -> None:
        """Handle ``playlist_select`` event."""
        self._receive_playlist(data, update_current=True)
        self._receive_playlist_current_item(data)

    def _receive_playlist(self, data: Any, update_current: bool = False) -> None:
        """Parse playlist data and notify callbacks."""
        if update_current:
            self.currentPlaylistId = data["playlist_id"]
        if self.currentPlaylistId != data["playlist_id"]:
            return

        extra_fields = [
            s.name for s in fields(PlaylistItem) if s.name not in ("id", "song")
        ]
        pli = {
            v["id"]: PlaylistItem(
                id=v["id"],
                song=self.songlist.get(int(v["song_id"])) if v.get("song_id") is not None else None,
                pos=i,
                **{k: val for k, val in v.items() if k in extra_fields},
            )
            for i, v in enumerate(data["items"])
        }
        self.playlist = pli

        for cb in self._cbs:
            cb.pe_update_playlist(list(self.playlist.values()))

    def _receive_playlist_current_item(self, data: Any) -> None:
        """Notify callbacks of the currently active item."""
        active_id = data.get("active_item_id")
        if active_id and active_id in self.playlist:
            for cb in self._cbs:
                cb.pe_play(self.playlist[active_id])

    def _receive_play(self, data: Any) -> None:
        """Handle ``item_played`` event."""
        if data["playlist_id"] != self.currentPlaylistId:
            return
        item = self.playlist.get(data["item_id"])
        if item is not None:
            for cb in self._cbs:
                cb.pe_play(item)

    # ---- Songlist parsing ----------------------------------------------

    def _parse_songlist(self, data: Any) -> None:
        """Parse raw songlist data into Song objects."""
        song_fields = [s.name for s in fields(Song)]
        songlist: Dict[int, Song] = {
            v["id"]: Song(**{k: val for k, val in v.items() if k in song_fields})
            for v in data["items"]
        }

        for song in songlist.values():
            if song.store is None:
                song.store = self._defstore

        for raw in data["items"]:
            song = songlist[raw["id"]]
            meta = raw.get("meta") or {}
            pages = meta.get("pages")
            if pages is not None:
                song.pages = [p - 1 for p in pages]

        self.songlist = songlist
        for cb in self._cbs:
            cb.pe_update_songlist(songlist)
