Socket.IO API for Livelist
==========================

All real-time communication uses Socket.IO events.
Clients connect to the WebSocket and authenticate with their band credentials.
Events are split into **requests** (client → server) and **responses/emissions** (server → client).

Authentication
--------------

On connection, the client must pass an ``auth`` object containing:

.. code:: json

    {
        "band": "<band_addr>",
        "key": "<access_key>"
    }

If authentication fails the connection is rejected.


Requests (client → server)
==========================

connect
-------

.. code:: js

    /* Auth payload passed via Socket.IO connect auth param */
    {
        "band": String,   // band address/subdomain
        "key": String,    // access key
    }

Server responds **connected**.


disconnect
----------

No payload. Server cleans up the room membership.


get_playlists
-------------

.. code:: js

    {}

Server responds **playlists**.


select_playlist
---------------

.. code:: js

    {
        "playlist_id": int,  // optional; omit to use the band's default playlist
    }

Server responds **playlist_select** with full playlist item data.


activate_playlist
-----------------

.. code:: js

    {
        "playlist_id": int,
    }

Sets the playlist as the active (default) playlist for the current band.
Server broadcasts **playlist_activated** to the band room.


playlist_update
---------------

.. code:: js

    {
        "playlist_id": int,  // optional; omit to use the band's default playlist
    }

Server broadcasts **playlist_updated** to the band room with full playlist item data.


play_item
---------

Play (activate) an item in a playlist. Supports absolute or relative navigation.

.. code:: js

    {
        "playlist_id": int,
        "item_id": int | null,  // absolute: set this item as active
        // — OR relative navigation —
        "off": int,             // relative offset from current active item
                                // (used only when item_id is null)
    }

If ``item_id`` is ``null`` and ``off`` is provided, the server resolves the
new active item by offsetting from the currently active item.
Server broadcasts **item_played** to the band room.


add_song
--------

Add a song to a playlist. Optionally anchor it relative to an existing item.

.. code:: js

    {
        "playlist_id": int,
        "song_id": int,
        "target_id": int | null,  // optional: anchor item id
        "before": bool,           // optional (default false): insert before target
    }

When ``target_id`` is provided, the new item is moved to the anchor position
(via the ``move_item`` logic). Server broadcasts **playlist_updated** to the
band room.


move_item
---------

Reorder items within a playlist by moving one or more items next to a target.

.. code:: js

    {
        "playlist_id": int,
        "target_id": int,       // anchor item id
        "before": bool,         // true = place before target, false = after
        "moved_ids": [int],     // ids of items to move
    }

Server broadcasts **playlist_updated** to the band room.


delete_items
------------

Remove one or more items from a playlist.

.. code:: js

    {
        "playlist_id": int,
        "item_ids": [int],
    }

If the deleted item was the active item, the playlist's ``active_item_id`` is
set to ``null``. Positions are re-indexed after deletion.
Server broadcasts **playlist_updated** to the band room.


create_playlist
---------------

.. code:: js

    {
        "band_id": int,
        "name": String,
        "date": String,  // ISO date string; defaults to today if omitted
    }

Server broadcasts **playlists** to the band room, and responds with
**playlist_created** to the sender with full playlist item data.


delete_playlist
---------------

.. code:: js

    {
        "playlist_id": int,
    }

Server emits **playlists** to the sender and also broadcasts **playlists** to
the rest of the band room (excluding sender).


save_playlist
-------------

Update the name and/or date of an existing playlist.

.. code:: js

    {
        "playlist_id": int,
        "name": String,   // new name
        "date": String,   // ISO date string; defaults to today if omitted
    }

Server broadcasts **playlists** to the band room.


get_songlist
------------

.. code:: js

    {}

Server responds **songlist** with the full song catalog for the current band.


create_tag
----------

Create a new tag for the current band.

.. code:: js

    {
        "name": String,
    }

Server responds **songlist** (refreshed) to the sender.


save_song
---------

Update an existing song's metadata.

.. code:: js

    {
        "id": int,              // song id
        "name": String,         // optional: new name
        "bpm": int | null,      // optional: new BPM
        "tags": [String],       // tag names to assign (others are removed)
        "meta": Object | null,  // optional: arbitrary JSON metadata
    }

Server responds **songlist** (refreshed) to the sender.


create_song
-----------

Create a new song in the current band.

.. code:: js

    {
        "name": String,
        "user_id": String,          // optional
        "bpm": int | null,          // optional
        "meta": Object | null,      // optional: arbitrary JSON metadata
    }

Server responds **songlist** (refreshed) to the sender.


batch
-----

Execute multiple requests in sequence.

.. code:: js

    {
        "requests": [
            {
                "cmd": String,  // event name, e.g. "create_song"
                "arg": Object,  // payload for the event
            },
            ...
        ]
    }

Each request is dispatched to the matching handler in order.


Responses (server → client)
===========================

connected
---------

Emitted to the connecting client on successful authentication.

.. code:: js

    {
        "band_id": int,
    }


playlists
---------

List of all playlists for the band.

.. code:: js

    [
        {
            "id": int,
            "name": String,
            "date": String,           // ISO date string
            "band_id": int,
            "active_item_id": int | null,
            "item_count": int,
        }
    ]


playlist_select
---------------

Full playlist with items, emitted in response to ``select_playlist``.
(Uses the same item-data format as **playlist_updated**.)

.. code:: js

    {
        "playlist_id": int,
        "name": String,
        "date": String,           // formatted as YYYY-MM-DD
        "active_item_id": int | null,
        "items": [
            {
                "id": int,
                "song_id": int,
                "position": int,
            }
        ],
    }


playlist_activated
------------------

Broadcast when a playlist is set as the band's active playlist.

.. code:: js

    {
        "playlist_id": int,
    }


playlist_updated
----------------

Broadcast when a playlist's items change (add, move, delete, update).
Uses the same data format as **playlist_select**.

.. code:: js

    {
        "playlist_id": int,
        "name": String,
        "date": String,
        "active_item_id": int | null,
        "items": [
            {
                "id": int,
                "song_id": int,
                "position": int,
            }
        ],
    }


playlist_created
----------------

Emitted to the creator after a new playlist is created.
Uses the same data format as **playlist_select**.

.. code:: js

    {
        "playlist_id": int,
        "name": String,
        "date": String,
        "active_item_id": int | null,
        "items": [],
    }


item_played
-----------

Broadcast when a playlist item is activated/played.

.. code:: js

    {
        "playlist_id": int,
        "item_id": int | null,
        "timestamp": String,      // ISO 8601 UTC timestamp
    }


songlist
--------

Full song catalog for the band, including tags.

.. code:: js

    {
        "tags": [String],
        "items": [
            {
                "id": int,
                "name": String,
                "user_id": String,
                "bpm": int | null,
                "notes": String,
                "filename": String | null,
                "store": String | null,
                "meta": Object | null,
                "tags": [String],
            }
        ],
    }
