Socket.IO API for Livelist
==========================

.. code:: json

    {
        "abc": 123,
        "xabc": "abc"
    }


.. role:: j(code)
    :language: json

.. role:: python(code)
    :language: python

In Python, :python:`def(self,x): return list(1 + 2)` is equal to :python:`3`.


Requests (client -> server)
===========================

.. code:: js

    "connect": {
        /* Server responds "connected" */
    }

    "disconnect": {
    }

    "get_playlist": {
        /* Server respons "playlists" */
    }

    "select_playlist": {
        /* Server responds "playlist_select" */
        playlist_id: int,
    }

    "activate_playlist": {
        /* Server broadcasts "playlist_activated" */
        /* This sets playlist as default for curent band */
        playlist_id: int,
    }

    "playlist": {
        "playlist_id": int,
        "name": String,
        "date": String,
        "active_item_id": int | null,
        "items": [
            {
                "id": int,
                "song_id": int,
                "position": int,
                "song": {
                    "id": int,
                    "name": String,
                    "user_id": String,
                    "bpm": int | null,
                    "notes": String,
                    "tags": [String],
                }
            }
        ]
    }

    "playlist_update": {
        /* Server broadcast "playlist_updated" */
    }

    "play_item": {
        /* Server broadcast "item_played" */
        "playlist_id": int,
        "item_id": int,
    }

    "add_song": {
        /* Server broadcast "playlist_updated" */
        "playlist_id": int,
        "item_id": int,
        "song_id": int,
        "target_id": int, /* Optional: anchor */
        "before": bool,
    }

    "move_item": {
        /* Server broadcast "playlist_updated" */
        "playlist_id": int,
        "target_id": int,
        "before": bool,
        "moved_ids": [
            int,
        ],
    }

    "move_item": {
        /* Server broadcast "playlist_updated" */
        "playlist_id": int,
        "item_id": int,
    }

    "create_playlist": {
        /* Server broadcast "playlists",
         * Server responds "playlist_created"
         **/
        "band_id": int, /* TODO? */
        "name": String,
        "date": String,
    }

    "delete_playlist": {
        /* Server broadcast "playlists",
         * Server responds "playlist_created"
         **/
        "band_id": int, /* TODO? */
        "playlist_id": int,
    }

    "save_laylist": {
        "playlist_id": int,
        "name": String,
        "date": String,
    }

    "get_songlist": {
        /* Server responds "songlist" */
    }

Responses (server -> client)
============================

.. code:: js

    "connected": {
        "band_id": int,
    }

    "item_played" {
        "playlist_id": int,
        "item_id": int,
    }
