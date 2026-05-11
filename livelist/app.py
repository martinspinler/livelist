#!/usr/bin/env python3
import click
import json
from datetime import datetime
from typing import Dict, Optional

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room

from sqlalchemy import and_, desc

from .config import load_config

from .config.settings import Config
from .models import Band, Song, Playlist, PlaylistItem, Tag, db
from .routes import api_bp, auth_bp, views_bp
from .routes.views import get_privileges, get_default_playlist


# TODO: TAGS, edit song, create song
# TODO: Play screen: do not switch played song immediately, let user to confirm

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Load YAML configuration
config_data = load_config()

# Database setup
db.init_app(app)

# SocketIO for WebSockets
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    #async_mode="eventlet" if os.environ.get("USE_EVENTLET") else "threading",
#    transports=["websocket"],
)

# Initialize sync manager
#sync_manager = PlaylistSyncManager(server_id=str(uuid.uuid4()))

# Register blueprints
app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(views_bp)
app.register_blueprint(auth_bp, url_prefix="/auth")


# Authentication middleware
@app.before_request
def before_request():
    """Check authentication and band access for each request"""
    # Skip auth for static files and login
    if request.endpoint in ("static", "auth.login", "auth.logout"):
        return

    # Get band from subdomain or URL
    #band = get_current_band()
    #if not band:
    #    return redirect(url_for("views.band_selection"))

    ## Check token for API endpoints
    #if request.endpoint and request.endpoint.startswith("api."):
    #    token = request.args.get("token") or request.headers.get("Authorization")
    #    if not validate_token(band.id, token, required_permission="view"):
    #        return jsonify({"error": "Unauthorized"}), 401

    ## Store band in request context
    #request.band = band


def get_current_band() -> Band:
    """get current band based on subdomain or url parameter"""

    return session.band
    #return db.session.query(Band).get(clients[request.sid]['band'])
    #return request.currentBand
    #from flask import request

    # try subdomain first
    host = request.host
    subdomain = host.split(".")[0] if "." in host else None

    #if band_name is None:
    #    # try url parameter
    #    band_name = request.args.get("band") or request.view_args.get("band_name")


    if subdomain:
        band = db.session.query(Band).filter_by(addr=subdomain).first()
        if band:
            return band
    raise Exception("Band not found")

    #if band_name:
    #    band = db.session.query(Band).filter_by(addr=band_name).first()
    #    if band:
    #        return band

    # default to first band if none specified (for development)
    return None
    return db.session.query(Band).first()
# Helper functions
def xget_current_band() -> Optional[Band]:
    """Get current band based on subdomain or URL parameter"""
    # Try subdomain first
    host = request.host
    subdomain = host.split(".")[0] if "." in host else None

    # Try URL parameter
    if request.args is None or request.view_args is None:
        raise Exception("")
    band_name = request.args.get("band") or request.view_args.get("band_name")
    #band_name ="testband"

    if subdomain:
        band = db.session.query(Band).filter_by(addr=subdomain).first()
        if band:
            return band

    if band_name:
        band = db.session.query(Band).filter_by(addr=band_name).first()
        if band:
            return band

    return None
    # Default to first band if none specified (for development)
    return db.session.query(Band).first()


def validate_token(band_id: int, token: str, required_permission: str = "view") -> bool:
    """Validate token for band access"""
    return True

    if not token:
        return False

    band = db.session.query(Band).get(band_id)
    if not band:
        return False

    if required_permission == "view":
        return token == band.view_token
    elif required_permission == "edit":
        return token == band.edit_token

    return False


def get_playlist_items(band, data):
    playlist_id = data.get("playlist_id")
    if playlist_id is None:
        playlist = get_default_playlist(band)
    else:
        playlist = db.session.get_one(Playlist, playlist_id)

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
                #"uuid": item.uuid,
                "song_id": item.song_id,
                "position": item.position,
                #"meta": json.loads(item.meta) if item.meta else None,
                #"song": {
                #    "id": item.song.id,
                #    "name": item.song.name,
                #    "user_id": item.song.user_id,
                #    "bpm": item.song.bpm,
                #    "notes": item.song.notes,
                #    "tags": [tag.name for tag in item.song.tags],
                #},
            } for item in items
        ],
    }


clients = {}

# WebSocket event handlers
@socketio.on("connect")
def handle_connect(auth):
    """Handle WebSocket connection"""
    #print("Connected WS", request, auth)
    if auth is None or get_privileges(auth.get("band"), auth.get("key")) is None:
        return False

    band = db.session.query(Band).filter_by(addr=auth["band"]).first()
    session.band = band
    #clients[request.sid] = auth.copy()

    if band:
        join_room(f"band_{band.id}")
        emit("connected", {"band_id": band.id})

        #playlist.active_item_id = item_id
        #    db.session.commit()
        #    # Broadcast play event
        #    emit(
        #        "item_played",
        #        {
        #            "playlist_id": playlist_id,
        #            "item_id": item_id,
        #            "timestamp": datetime.utcnow().isoformat(),
        #        },
        #        room=f"band_{band.id}",
        #    )


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection"""

    band = get_current_band()
    if band:
        leave_room(f"band_{band.id}")
    #del clients[request.sid]


@socketio.on("select_playlist")
def handle_select_playlist(data: Dict):
    """Handle playlist update from client"""
    band = get_current_band()
    if not band:
        return
    res = get_playlist_items(band, data)

    emit("playlist_select", res) #, to=f"band_{band.id}")

@socketio.on("activate_playlist")
def handle_activate_playlist(data: Dict):
    """Handle playlist update from client"""
    band = get_current_band()
    if not band:
        return

    playlist_id = data.get("playlist_id")
    if isinstance(playlist_id, int):
        playlist = db.session.get_one(Playlist, playlist_id)
        band.active_playlist_id = playlist.id

        db.session.add(band)
        db.session.commit()
        emit("playlist_activated", {"playlist_id": playlist.id}, to=f'band_{band.id}')


def get_band_playlists(data):
    """Get all playlists for a band"""
    band = get_current_band()

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
    return res

@socketio.on("get_playlists")
def on_get_band_playlists(data):
    res = get_band_playlists(data)
    emit("playlists", res)


@socketio.on("playlist_update")
def handle_playlist_update(data: Dict):
    """Handle playlist update from client"""

    band = get_current_band()
    if not band:
        return

    res = get_playlist_items(band, data)

    emit("playlist_updated", res, to=f"band_{band.id}") #, include_self=False)


@socketio.on('play_item')
def handle_play_item(data: Dict):
    """Handle play item event"""
    band = get_current_band()
    if not band:
        return

    item_id = data.get("item_id")
    playlist_id = data.get("playlist_id")

    # Update active item in playlist
    playlist = db.session.query(Playlist).get(playlist_id)
    if playlist is None or playlist.band_id != band.id:
        return

    # Relative position
    if item_id is None:
        item_id = playlist.active_item_id
        off = data.get("off")
        if off is None:
            return

        if item_id is None:
            litem = db.session.query(PlaylistItem).filter_by(playlist_id=playlist_id).order_by(desc(PlaylistItem.position)).first()
            if litem is not None and off < 0:
                pos = litem.position
            else:
                pos = 0
        else:
            act_item = db.session.query(PlaylistItem).get(item_id)
            pos = act_item.position + off
        item = db.session.query(PlaylistItem).filter_by(playlist_id=playlist_id, position=pos).first()
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
            "timestamp": datetime.utcnow().isoformat(),
        },
        to=f"band_{band.id}",
    )


@socketio.on("add_song")
def add_playlist_item(data):
    """Add a song to a playlist"""
    song_id = data.get("song_id")
    playlist_id = data.get("playlist_id")
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
    playlist_id = data.get("playlist_id")
    items = db.session.query(PlaylistItem).filter_by(playlist_id=playlist_id).order_by(PlaylistItem.position.asc()).all()
    before = data.get("before")
    moved_ids = data.get("moved_ids")
    target_id = data.get("target_id")
    moved_dict = {x: moved_ids.index(x.id) for x in items if x.id in moved_ids}
    moved = list(dict(sorted(moved_dict.items(), key=lambda item: item[1])).keys())
    target = ([x for x in items if x.id == target_id] + [None])[0]
    result = []
    if target in moved:
        #del moved[target]
        moved.remove(target)

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
    playlist_id = data.get("playlist_id")
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

    band_id = data.get("band_id")
    name = data.get("name")
    date_str = data.get("date")

    if not band_id or not name:
        return #jsonify({"error": "Missing required fields"}), 400

    try:
        date = datetime.fromisoformat(date_str) if date_str else datetime.now().date()
    except ValueError:
        return #jsonify({"error": "Invalid date format"}), 400

    playlist = Playlist(band_id=band_id, name=name, date=date)

    db.session.add(playlist)
    db.session.commit()

    res = get_band_playlists(data)
    emit("playlists", res, to=f'band_{band_id}')

    res = get_playlist_items(get_current_band(), {"playlist_id": playlist.id})
    emit("playlist_created", res) #{"playlist_id": playlist.id, "active_item_id": None})


@socketio.on("delete_playlist")
def on_delete_playlist(data):
    item = db.session.get_one(Playlist, data.get("playlist_id"))

    db.session.delete(item)
    db.session.commit()

    res = get_band_playlists(data)
    band = get_current_band()

    emit("playlists", res)
    emit("playlists", res, to=f'band_{band.id}', include_self=False)

@socketio.on("save_playlist")
def on_save_playlist(data):
    item = db.session.get_one(Playlist, data.get("playlist_id"))

    date_str = data.get("date")
    try:
        date = datetime.fromisoformat(date_str) if date_str else datetime.now().date()
    except ValueError:
        raise
        #return jsonify({"error": "Invalid date format"}), 400
    item.name = data.get("name")
    item.date = date
    db.session.add(item)
    db.session.commit()

    res = get_band_playlists(data)
    band = get_current_band()

    #emit("playlists", res)
    #emit("playlists", res, to=f'band_{band.id}', include_self=False)
    emit("playlists", res, to=f'band_{band.id}')


@socketio.on("get_songlist")
def get_songs(data):
    band = get_current_band()

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

    emit("songlist", res)


@socketio.on("create_tag")
def create_tag(data):
    """Create a new tag"""

    band = get_current_band()
    if not band:
        return

    name = data.get("name")

    tag = Tag(band_id=band.id, name=name)

    db.session.add(tag)
    db.session.commit()

    get_songs({})


@socketio.on("save_song")
def save_song(data):
    """Create a new tag"""

    band = get_current_band()
    if not band:
        return

    song = db.session.get_one(Song, data["id"])
    name = data.get("name")
    # TODO: Check filter used TAG ID's for band_id!

    tags = db.session.query(Tag).filter_by(band_id=band.id).all()#.order_by(Song.name).all()
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

    get_songs({})


@socketio.on("create_song")
def create_song(data):
    band = get_current_band()
    if not band:
        return

    song = Song(
        band_id=band.id,
        name=data.get("name"),
        user_id=data.get("user_id"),
        bpm=data.get("bpm"),
        #notes=data.get("notes"),
        #store=data.get("store"),
        meta=json.dumps(data.get("meta")) if data.get("meta") is not None else None,
    )

    db.session.add(song)
    db.session.commit()

    get_songs({})


@socketio.on("batch")
def batch(data):
    req_cnt = 0
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
        debug=app.config.get("DEBUG", True),
        allow_unsafe_werkzeug=True,
    )

if __name__ == "__main__":
    create_app()
