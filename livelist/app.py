#!/usr/bin/env python3
import click
import json
import datetime
from datetime import datetime as dt

from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit, join_room, leave_room

from sqlalchemy import and_, desc

from .config.settings import Config
from .models import Band, Song, Playlist, PlaylistItem, Tag, db
from .routes import views_bp
from .routes.views import get_privileges, get_default_playlist


# TODO: TAGS, edit song, create song
# TODO: Play screen: do not switch played song immediately, let user to confirm

# Load .env file (if present) before building the app config
from dotenv import load_dotenv
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)


# Database setup
db.init_app(app)

# SocketIO for WebSockets
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    #async_mode="eventlet" if os.environ.get("USE_EVENTLET") else "threading",
#    transports=["websocket"],
)

# Register blueprints
app.register_blueprint(views_bp)


def get_band() -> Band:
    """get current band based on session variable (authentised) """

    band = session.get("band")
    if not isinstance(band, Band):
        raise ValueError("No band")
    return band


def get_playlist(band: Band, data):
    """Get playlist specified in data request and check if belongs to the band"""
    playlist_id = data.get("playlist_id")
    playlist = db.session.get_one(Playlist, playlist_id)
    if playlist is None or band.id != playlist.band_id:
        raise ValueError()

    return playlist


def get_playlist_items(playlist: Playlist):
    items = (
        db.session.query(PlaylistItem)
        .filter_by(playlist_id=playlist.id)
        .order_by(PlaylistItem.position)
        .all()
    )

    return {
        "playlist_id": playlist.id,
        "name": playlist.name,
        "date": playlist.date.strftime('%Y-%m-%d'),
        "active_item_id": playlist.active_item_id,
        "items": [
            {
                "id": item.id,
                "song_id": item.song_id,
                "position": item.position,
            } for item in items
        ],
    }


# WebSocket event handlers
@socketio.on("connect")
def handle_connect(auth):
    """Handle WebSocket connection"""

    if auth is None or get_privileges(auth.get("band"), auth.get("key")) is None:
        return False

    band = db.session.query(Band).filter_by(addr=auth["band"]).first()
    session["band"] = band

    if band:
        join_room(f"band_{band.id}")
        emit("connected", {"band_id": band.id})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection"""

    leave_room(f"band_{get_band().id}")


@socketio.on("select_playlist")
def handle_select_playlist(data: dict):
    """Handle playlist update from client"""
    band = get_band()
    try:
        playlist = get_playlist(band, data)
    except Exception:
        playlist = get_default_playlist(band)
        if playlist is None:
            return

    res = get_playlist_items(playlist)

    emit("playlist_select", res) #, to=f"band_{band.id}")


@socketio.on("activate_playlist")
def handle_activate_playlist(data: dict):
    """Handle playlist update from client"""
    band = get_band()
    playlist = get_playlist(band, data)

    band.active_playlist_id = playlist.id

    db.session.add(band)
    db.session.commit()

    emit("playlist_activated", {"playlist_id": playlist.id}, to=f'band_{band.id}')


def get_band_playlists(band):
    """Get all playlists for a band"""
    band = get_band()

    playlists = (
        db.session.query(Playlist)
        .filter_by(band_id=band.id)
        .order_by(Playlist.date.desc())
        .order_by(Playlist.id.desc())
        .all()
    )
    res = (
        [
            {
                "id": p.id,
                "name": p.name,
                "date": p.date.isoformat(),
                "band_id": p.band_id,
                "active_item_id": p.active_item_id,
                "item_count": len(p.items),
            }
            for p in playlists
        ]
    )
    return res


@socketio.on("get_playlists")
def on_get_band_playlists(data):
    res = get_band_playlists(get_band())
    emit("playlists", res)


@socketio.on("playlist_update")
def handle_playlist_update(data: dict):
    """Handle playlist update from client"""

    band = get_band()
    playlist = get_playlist(band, data)
    res = get_playlist_items(playlist)

    emit("playlist_updated", res, to=f"band_{band.id}") #, include_self=False)


@socketio.on('play_item')
def handle_play_item(data: dict):
    """Handle play item event"""
    band = get_band()
    playlist = get_playlist(band, data)

    playlist_id = playlist.id
    item_id = data.get("item_id")

    # Relative position
    if item_id is None:
        item_id = playlist.active_item_id
        off = data.get("off")
        if off is None:
            return

        if item_id is None:
            litem = (
                db.session.query(PlaylistItem)
                .filter_by(playlist_id=playlist_id)
                .order_by(desc(PlaylistItem.position))
                .first()
            )
            if litem is not None and off < 0:
                pos = litem.position
            else:
                pos = 0
        else:
            act_item = db.session.get_one(PlaylistItem, item_id)
            pos = act_item.position + off

        item = (
            db.session.query(PlaylistItem)
            .filter_by(playlist_id=playlist_id, position=pos)
            .first()
        )
        item_id = None if item is None else item.id

    item = db.session.query(PlaylistItem).get(item_id)
    if item and item.playlist_id != playlist_id:
        return

    playlist.active_item_id = item_id
    db.session.commit()

    # Broadcast play event
    emit(
        "item_played",
        {
            "playlist_id": playlist_id,
            "item_id": item_id,
            "timestamp": dt.now(datetime.timezone.utc).isoformat(),
        },
        to=f"band_{band.id}",
    )


@socketio.on("add_song")
def add_playlist_item(data):
    """Add a song to a playlist"""
    band = get_band()
    playlist = get_playlist(band, data)
    playlist_id = playlist.id

    song_id = data.get("song_id")
    target_id = data.get("target_id")
    before = data.get("before", False)

    if not song_id:
        return

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

    # TODO: add metadata with added id (result)
    if target_id:
        data = dict(
            playlist_id=playlist_id,
            before=before,
            target_id=target_id,
            moved_ids=[item.id],
        )
        # handle_playlist_update is called inside
        on_move(data)
    else:
        handle_playlist_update({"playlist_id": playlist_id})


@socketio.on("move_item")
def on_move(data):
    band = get_band()
    playlist = get_playlist(band, data)
    playlist_id = playlist.id

    items = (
        db.session.query(PlaylistItem)
        .filter_by(playlist_id=playlist_id)
        .order_by(PlaylistItem.position.asc())
        .all()
    )
    before = data.get("before")
    moved_ids = data.get("moved_ids")
    target_id = data.get("target_id")
    moved_dict = {x: moved_ids.index(x.id) for x in items if x.id in moved_ids}
    moved = list(dict(sorted(moved_dict.items(), key=lambda item: item[1])).keys())
    target = ([x for x in items if x.id == target_id] + [None])[0]
    if target in moved:
        moved.remove(target)

    result = []
    for i, item in enumerate(items):
        if item == target and before:
            result.extend(moved)
        if item not in moved:
            result.append(item)
        if item == target and not before:
            result.extend(moved)

    for i, item in enumerate(result):
        if i != item.position:
            item.position = i
            db.session.add(item)

    db.session.commit()
    handle_playlist_update({"playlist_id": playlist_id})


@socketio.on("delete_items")
def on_delete_item(data):
    band = get_band()
    playlist = get_playlist(band, data)
    playlist_id = playlist.id

    items = (
        db.session.query(PlaylistItem)
        .filter(and_(
            PlaylistItem.id.in_(data.get("item_ids")),
            PlaylistItem.playlist_id==playlist_id,
        ))
        .all()
    )

    for item in items:
        db.session.delete(item)
        if item.id == playlist.active_item_id:
            playlist.active_item_id = None
            db.session.add(playlist)
    db.session.commit()

    items = (
        db.session.query(PlaylistItem)
        .filter_by(playlist_id=playlist_id)
        .order_by(PlaylistItem.position.asc())
        .all()
    )
    for i in range(len(items)):
        items[i].position = i
        db.session.add(items[i])
    db.session.commit()
    handle_playlist_update({"playlist_id": playlist_id})


@socketio.on("create_playlist")
def create_playlist(data):
    """Create a new playlist"""

    band = get_band()
    date_str = data.get("date")

    try:
        date = dt.fromisoformat(date_str) if date_str else dt.now().date()
    except ValueError:
        return

    playlist = Playlist(band_id=band.id, name=data.get("name"), date=date)

    db.session.add(playlist)
    db.session.commit()

    res = get_band_playlists(band)
    emit("playlists", res, to=f'band_{band.id}')

    res = get_playlist_items(playlist)
    emit("playlist_created", res)


@socketio.on("delete_playlist")
def on_delete_playlist(data):
    band = get_band()
    playlist = get_playlist(band, data)

    db.session.delete(playlist)
    db.session.commit()

    res = get_band_playlists(band)

    emit("playlists", res)
    emit("playlists", res, to=f'band_{band.id}', include_self=False)


@socketio.on("save_playlist")
def on_save_playlist(data):
    band = get_band()
    playlist = get_playlist(band, data)

    date_str = data.get("date")
    try:
        date = dt.fromisoformat(date_str) if date_str else dt.now().date()
    except ValueError:
        raise

    playlist.name = data.get("name")
    playlist.date = date
    db.session.add(playlist)
    db.session.commit()

    res = get_band_playlists(band)
    emit("playlists", res, to=f'band_{band.id}')

    res = get_playlist_items(playlist)
    emit("playlist_updated", res, to=f"band_{band.id}")


@socketio.on("get_songlist")
def get_songs(data={}):
    band = get_band()

    songs = db.session.query(Song).filter_by(band_id=band.id).order_by(Song.name).all()
    tags = db.session.query(Tag).filter_by(band_id=band.id).all()#.order_by(Song.name).all()

    res = {
        "tags": [
            t.name for t in tags
        ],
        "items": [
            {
                "id": s.id,
                #"uuid": s.uuid,
                "name": s.name,
                "user_id": s.user_id,
                "bpm": s.bpm,
                "notes": s.notes,
                "filename": s.filename,
                "store": s.store,
                "meta": json.loads(s.meta) if s.meta else None,
                "tags": [tag.name for tag in s.tags],
            }
            for s in songs
        ],
    }

    emit("songlist", res, to=f"band_{band.id}")


@socketio.on("create_tag")
def create_tag(data):
    """Create a new tag"""

    band = get_band()

    name = data.get("name")
    if not name:
        return

    tag = Tag(band_id=band.id, name=name)

    db.session.add(tag)
    db.session.commit()

    get_songs()


@socketio.on("save_song")
def save_song(data):
    """Update song"""

    band = get_band()

    song = db.session.get_one(Song, data.get("id"))
    # TODO: Check filter used TAG ID's for band_id!

    tags = db.session.query(Tag).filter_by(band_id=band.id).all()
    for t in tags:
        if t.name not in data.get("tags", []):
            if t in song.tags:
                song.tags.remove(t)
        else:
            if t not in song.tags:
                song.tags.append(t)

    song.name = data.get("name", song.name)
    song.bpm = data.get("bpm", song.bpm)
    if data.get("meta") is not None:
        try:
            song.meta = json.dumps(data.get("meta"))
        except Exception:
            pass

    db.session.add(song)
    db.session.commit()

    get_songs()


@socketio.on("create_song")
def create_song(data):
    band = get_band()
    name = data.get("name")
    if not name:
        return

    song = Song(
        band_id=band.id,
        name=name,
        user_id=data.get("user_id"),
        bpm=data.get("bpm"),
        #notes=data.get("notes"),
        #store=data.get("store"),
        meta=json.dumps(data.get("meta")) if data.get("meta") is not None else None,
    )

    db.session.add(song)
    db.session.commit()

    get_songs()


@socketio.on("batch")
def batch(data):
    for req in data.get('requests', []):
        cmd = req.get("cmd")
        arg = req.get("arg")
        if cmd == "create_song":
            create_song(arg)


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("500.html"), 500


# CLI commands
@app.cli.command("init-db")
def init_db_command():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized.")


@app.cli.command("create-band")
@click.argument("name")
@click.argument("addr")
@click.argument("password")
def create_band(name, addr, password):
    """Create a new band"""
    with app.app_context():
        db.create_all()
        band = Band(name=name, addr=addr, pwd=password)
        db.session.add(band)
        db.session.commit()
        print("Band created.")


def create_app():
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    # Run the application
    socketio.run(
        app,
        host=app.config.get("HOST", "127.0.0.1"),
        port=app.config.get("PORT", 5000),
        allow_unsafe_werkzeug=True,
    )

if __name__ == "__main__":
    create_app()
