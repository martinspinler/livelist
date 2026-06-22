"""Async Socket.IO client for LiveList."""

import asyncio
from dataclasses import fields
from typing import Any, Dict, List, Optional, Tuple

import socketio
from socketio.exceptions import ConnectionError as SocketConnectionError
from socketio.exceptions import TimeoutError as SocketTimeoutError

from .models import PlaylistItem, PlaylistItemId, Song
from .playlist import PlaylistClient


class AsyncLivelistClient(PlaylistClient):
    """Asynchronous LiveList client using Socket.IO.

    Usage::

        client = AsyncLivelistClient(
            url="http://localhost:5000",
            band="myband",
            key="secret",
        )
        client.register(my_callback)
        await client.run()
    """

    def __init__(
        self,
        url: Optional[str] = None,
        band: str = "",
        key: str = "",
        *,
        default_store: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._queue: asyncio.Queue[Tuple[str, Any]] = asyncio.Queue()
        self._url = url
        self._auth: dict = {"band": band, "key": key}
        self._defstore = default_store
        # Band-level sheet-store config ({patterns, instruments}) fetched
        # alongside the songlist and cached so the shared finder can run
        # offline (no server round-trip per document lookup).
        self.band_config: dict = {}
        self.sio = socketio.AsyncSimpleClient()

    # ---- Connection lifecycle ------------------------------------------

    async def connect(self) -> None:
        """Connect to the LiveList server and fetch initial data."""
        await self.sio.connect(self._url, auth=self._auth)
        _event, conn_data = await self.sio.receive()  # "connected"
        self._band_id = conn_data["band_id"]

        try:
            await self.get_songlist()
            await self.select_playlist()
        except SocketConnectionError:
            pass

    async def _disconnect(self) -> None:
        """Disconnect from the server."""
        await self.sio.disconnect()

    def disconnect(self) -> None:
        """Schedule a disconnect (safe to call from any callback)."""
        self._queue.put_nowait(("close", None))

    async def run(self) -> None:
        """Main entry point: connect with retry, then run send/recv loops."""
        while True:
            try:
                await self.connect()
                break
            except Exception:
                await asyncio.sleep(5)

        await asyncio.gather(self._run_recv(), self._run_send())

    # ---- Outgoing message queue ----------------------------------------

    def _enqueue(self, event: str, data: Any = None) -> None:
        """Queue an outgoing Socket.IO event."""
        self._queue.put_nowait((event, data or {}))

    async def _run_send(self) -> None:
        """Background loop: drain the outgoing queue and send events."""
        while True:
            msg, data = await self._queue.get()
            if msg == "close":
                await self._disconnect()
                return
            await self.sio.call(msg, data)

    async def _run_recv(self) -> None:
        """Background loop: receive and dispatch incoming push events."""
        while True:
            try:
                event, data = await self.sio.receive()
            except (SocketConnectionError, SocketTimeoutError):
                break

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
        self._enqueue("add_song", {
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
        self._enqueue("delete_items", {
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
        self._enqueue("move_item", {
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
        self._enqueue("play_item", {
            "item_id": item_id,
            "off": off,
            "playlist_id": pid,
        })

    # ---- Request-response helpers (called outside run loop) -----------

    async def select_playlist(self, playlist_id: Optional[int] = None) -> None:
        """Select a playlist (defaults to the band's active playlist)."""
        data: dict = {}
        if playlist_id is not None:
            data["playlist_id"] = playlist_id
        await self.sio.call("select_playlist", data)
        _event, resp = await self.sio.receive()
        self._receive_playlist(resp, update_current=True)
        self._receive_playlist_current_item(resp)

    async def get_songlist(self) -> Dict[int, Song]:
        """Fetch the full song list from the server."""
        await self.sio.call("get_songlist", {})
        _event, data = await self.sio.receive()
        self._parse_songlist(data)
        return self.songlist

    async def get_playlists(self) -> list:
        """Fetch all playlists for the band."""
        await self.sio.call("get_playlists", {})
        _event, data = await self.sio.receive()
        return data

    # ---- Incoming event handlers ---------------------------------------

    def _receive_playlist_full(self, data: Any) -> None:
        """Handle ``playlist_select`` push (response to select_playlist)."""
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
                song=self.songlist[int(v["song_id"])] if v.get("song_id") is not None else None,
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
        """Handle ``item_played`` push event."""
        if data["playlist_id"] != self.currentPlaylistId:
            return
        item = self.playlist.get(data["item_id"])
        if item is not None:
            for cb in self._cbs:
                cb.pe_play(item)

    # ---- Songlist parsing ----------------------------------------------

    def _parse_songlist(self, data: Any) -> None:
        """Parse raw songlist data into Song objects."""
        # Cache band-level sheet-store config carried in the same payload.
        self.band_config = data.get("sheet_store") or {}
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
