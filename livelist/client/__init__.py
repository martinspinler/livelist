"""LiveList client library.

Provides synchronous and asynchronous Socket.IO clients for connecting
to a LiveList server, plus shared data models and an abstract base class.

Quick start (sync)::

    from livelist.client import SyncLivelistClient

    with SyncLivelistClient(url="...", band="...", key="...") as client:
        songs = client.get_songlist()

Quick start (async)::

    from livelist.client import AsyncLivelistClient

    client = AsyncLivelistClient(url="...", band="...", key="...")
    await client.run()
"""

from .models import PlaylistInfo, PlaylistItem, PlaylistItemId, Song
from .playlist import PlaylistCallback, PlaylistClient

# Lazy imports — python-socketio is only needed when instantiating a client,
# not when using the data models or ABC alone.


def AsyncLivelistClient(*args, **kwargs):
    """Create an async Socket.IO LiveList client."""
    from .async_client import AsyncLivelistClient as _AsyncLivelistClient
    return _AsyncLivelistClient(*args, **kwargs)


def SyncLivelistClient(*args, **kwargs):
    """Create a sync Socket.IO LiveList client."""
    from .sync_client import SyncLivelistClient as _SyncLivelistClient
    return _SyncLivelistClient(*args, **kwargs)


__all__ = [
    "Song",
    "PlaylistItem",
    "PlaylistItemId",
    "PlaylistInfo",
    "PlaylistCallback",
    "PlaylistClient",
    "AsyncLivelistClient",
    "SyncLivelistClient",
]
