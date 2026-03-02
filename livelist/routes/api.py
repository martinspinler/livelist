import json
from datetime import datetime

from flask import jsonify, request

from ..models import Playlist, PlaylistItem, Song, Tag, TagManager, db

from . import api_bp


@api_bp.route("/bands/<int:band_id>/playlists/", methods=["GET"])
def get_band_playlists(band_id: int):
    """Get all playlists for a band"""
    playlists = (
        db.session.query(Playlist)
        .filter_by(band_id=band_id)
        .order_by(Playlist.date.desc())
        .all()
    )
    return jsonify(
        [
            {
                "id": p.id,
                #"uuid": p.uuid,
                "name": p.name,
                "date": p.date.isoformat(),
                "band_id": p.band_id,
                "active_item_id": p.active_item_id,
                "item_count": len(p.items),
            }
            for p in playlists
        ]
    )


@api_bp.route("/playlists/", methods=["POST"])
def create_playlist():
    """Create a new playlist"""
    data = request.get_json()

    band_id = data.get("band_id")
    name = data.get("name")
    date_str = data.get("date")

    if not band_id or not name:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        date = datetime.fromisoformat(date_str) if date_str else datetime.now().date()
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    playlist = Playlist(band_id=band_id, name=name, date=date)

    db.session.add(playlist)
    db.session.commit()

    return jsonify(
        {
            "id": playlist.id,
            #"uuid": playlist.uuid,
            "name": playlist.name,
            "date": playlist.date.isoformat(),
            "band_id": playlist.band_id,
        }
    ), 201


@api_bp.route("/playlists/<int:playlist_id>/", methods=["GET"])
def get_playlist(playlist_id: int):
    """Get playlist details"""
    playlist = db.session.get_one(Playlist, playlist_id)

    return jsonify(
        {
            "id": playlist.id,
            #"uuid": playlist.uuid,
            "name": playlist.name,
            "date": playlist.date.isoformat(),
            "band_id": playlist.band_id,
            "active_item_id": playlist.active_item_id,
            "items": [
                {
                    "id": item.id,
                   # "uuid": item.uuid,
                    "song_id": item.song_id,
                    "position": item.position,
                    "meta": json.loads(item.meta) if item.meta else None,
                }
                for item in playlist.items
            ],
        }
    )


@api_bp.route("/playlists/<int:playlist_id>/items/", methods=["GET"])
def get_playlist_items(playlist_id: int):
    """Get items in a playlist"""

    playlist = db.session.get_one(Playlist, playlist_id)
    items = (
        db.session.query(PlaylistItem)
        .filter_by(playlist_id=playlist_id)
        .order_by(PlaylistItem.position)
        .all()
    )

    return jsonify(
        {
            "id": playlist.id,
            "name": playlist.name,
            "date": playlist.date.strftime("%Y-%m-%d"),
            "items": [
                {
                    "id": item.id,
                    #"uuid": item.uuid,
                    "song_id": item.song_id,
                    "position": item.position,
                    "meta": json.loads(item.meta) if item.meta else None,
                    "song": {
                        "id": item.song.id,
                        "name": item.song.name,
                        "user_id": item.song.user_id,
                        "bpm": item.song.bpm,
                        "notes": item.song.notes,
                        "tags": [tag.name for tag in item.song.tags],
                    },
                }
                for item in items
            ],
        },
    )


@api_bp.route("/playlists/<int:playlist_id>/items/", methods=["POST"])
def add_playlist_item(playlist_id: int):
    """Add a song to a playlist"""
    data = request.get_json()
    song_id = data.get("song_id")

    if not song_id:
        return jsonify({"error": "Missing song_id"}), 400

    # Get the last position in the playlist
    last_item = (
        db.session.query(PlaylistItem)
        .filter_by(playlist_id=playlist_id)
        .order_by(PlaylistItem.position.desc())
        .first()
    )
    position = last_item.position + 1 if last_item else 0

    item = PlaylistItem(playlist_id=playlist_id, song_id=song_id, position=position)

    db.session.add(item)
    db.session.commit()

    return jsonify(
        {
            "id": item.id,
            #"uuid": item.uuid,
            "song_id": item.song_id,
            "position": item.position,
            "playlist_id": item.playlist_id,
        }
    ), 201


@api_bp.route("/playlists/<int:playlist_id>/items/<int:item_id>/", methods=["DELETE"])
def delete_playlist_item(playlist_id: int, item_id: int):
    """Delete an item from a playlist"""
    item = db.session.get_one(PlaylistItem, item_id)

    if item.playlist_id != playlist_id:
        return jsonify({"error": "Item not in specified playlist"}), 400

    db.session.delete(item)
    db.session.commit()

    return jsonify({"success": True})




@api_bp.route("/songs/", methods=["GET"])
def get_songs():
    """Get songs with optional filtering"""
    band_id = request.args.get("band_id", type=int)
    tag = request.args.get("tag")

    query = db.session.query(Song)

    if band_id:
        query = query.filter_by(band_id=band_id)

    if tag:
        query = query.join(Song.tags).filter(Tag.name == tag)

    songs = query.order_by(Song.name).all()

    # Apply keypad filter if provided
    #if keypad_filter:
    #    songs = filter_songs_by_keypad(songs, keypad_filter)

    return jsonify(
        [
            {
                "id": s.id,
                #"uuid": s.uuid,
                "name": s.name,
                "user_id": s.user_id,
                "bpm": s.bpm,
                "notes": s.notes,
                "filename": s.filename,
                "store": s.store,
                #"meta": json.loads(s.meta) if s.meta else None,
                "tags": [tag.name for tag in s.tags],
            }
            for s in songs
        ]
    )


@api_bp.route("/songs/", methods=["POST"])
def create_song():
    """Create a new song"""
    data = request.get_json()

    band_id = data.get("band_id")
    name = data.get("name")

    if not band_id or not name:
        return jsonify({"error": "Missing band_id or name"}), 400

    song = Song(
        band_id=band_id,
        name=name,
        user_id=data.get("user_id"),
        bpm=data.get("bpm"),
        notes=data.get("notes"),
        store=data.get("store"),
        meta=json.dumps(data.get("meta")) if data.get("meta") else None,
    )

    db.session.add(song)
    db.session.commit()

    # Add tags if provided
    tags = data.get("tags", [])
    for tag_name in tags:
        TagManager.add_tag_to_song(song.id, tag_name)

    return jsonify(
        {
            "id": song.id,
            #"uuid": song.uuid,
            "name": song.name,
            "band_id": song.band_id,
            "tags": tags,
        }
    ), 201


@api_bp.route("/songs/<int:song_id>/", methods=["GET"])
def get_song(song_id: int):
    """Get song details"""
    song = db.session.get_one(Song, song_id)

    return jsonify(
        {
            "id": song.id,
            #"uuid": song.uuid,
            "name": song.name,
            "user_id": song.user_id,
            "bpm": song.bpm,
            "notes": song.notes,
            "filename": song.filename,
            "store": song.store,
            "meta": json.loads(song.meta) if song.meta else None,
            "tags": [tag.name for tag in song.tags],
        }
    )


@api_bp.route("/songs/<int:song_id>/", methods=["PUT"])
def update_song(song_id: int):
    """Update song details"""
    song = db.session.get_one(Song, song_id)
    data = request.get_json()

    if "name" in data:
        song.name = data["name"]
    if "user_id" in data:
        song.user_id = data["user_id"]
    if "bpm" in data:
        song.bpm = data["bpm"]
    if "notes" in data:
        song.notes = data["notes"]
    if "store" in data:
        song.store = data["store"]
    if "meta" in data:
        song.meta = json.dumps(data["meta"]) if data["meta"] else None

    # Update tags if provided
    if "tags" in data:
        # Remove all existing tags
        song.tags.clear()
        # Add new tags
        for tag_name in data["tags"]:
            TagManager.add_tag_to_song(song.id, tag_name)

    db.session.commit()

    return jsonify({"success": True})


@api_bp.route("/tags/", methods=["GET"])
def get_tags():
    """Get all tags"""
    band_id = request.args.get("band_id", type=int)
    tags = TagManager.get_all_tags(band_id)

    return jsonify(
        [
            {"name": tag.name, "color": tag.color, "song_count": len(tag.songs)}
            for tag in tags
        ]
    )


@api_bp.route("/tags/<string:tag_name>/", methods=["GET"])
def get_tag(tag_name: str):
    """Get tag details"""
    tag = db.session.query(Tag).filter_by(name=tag_name).first_or_404()

    return jsonify(
        {
            "name": tag.name,
            "color": tag.color,
            "songs": [
                {"id": song.id, "name": song.name, "band_id": song.band_id}
                for song in tag.songs
            ],
        }
    )


@api_bp.route("/play/<int:playlist_id>/<int:item_id>/", methods=["POST"])
def play_item(playlist_id: int, item_id: int):
    """Set an item as currently playing"""
    playlist = db.session.query(Playlist).get_or_404(playlist_id)
    item = db.session.query(PlaylistItem).get_or_404(item_id)

    if item.playlist_id != playlist_id:
        return jsonify({"error": "Item not in playlist"}), 400

    playlist.active_item_id = item_id
    db.session.commit()

    return jsonify(
        {"playlist_id": playlist_id, "item_id": item_id, "song_id": item.song_id}
    )
