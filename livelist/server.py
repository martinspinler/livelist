#!/usr/bin/env python3
import click
import json
import locale
import datetime
from datetime import datetime as dt

from flask import Flask, render_template, session, current_app, request
from flask_socketio import SocketIO, emit, join_room, leave_room

from sqlalchemy import and_, desc
from dotenv import load_dotenv

from .config.settings import Config
from .models import Band, Song, Playlist, PlaylistItem, Tag, db
from .routes import views_bp
from .routes.views import get_privileges, get_default_playlist, find_documents_by_song
from .l10n import t as _t, get_translations, detect_language, get_supported_langs

# Language code → POSIX locale used for locale-aware sorting
_LOCALE_MAP = {
    "cs": "cs_CZ.UTF-8",
    "en": "C.UTF-8",
}

# Cached locale state: once we've set LC_COLLATE for a language,
# subsequent calls reuse it without switching again.
_collate_locale = None


def _locale_sort_key(name: str) -> str:
    """Return a sort key that respects the current request's language.

    Uses :func:`locale.strxfrm` with a per-language ``LC_COLLATE`` setting
    so that Czech characters (č, ř, š, …) sort next to their base letters.
    Falls back to plain ``str.lower`` when the locale is unavailable.
    """
    global _collate_locale
    lang = detect_language()
    loc = _LOCALE_MAP.get(lang)
    if loc and loc != _collate_locale:
        try:
            locale.setlocale(locale.LC_COLLATE, loc)
            _collate_locale = loc
        except locale.Error:
            _collate_locale = None
    if _collate_locale:
        return locale.strxfrm(name)
    return name.lower()


# TODO: TAGS, edit song, create song
# TODO: Play screen: do not switch played song immediately, let user to confirm

# Load .env file (if present) before building the app config
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


@app.context_processor
def inject_l10n():
    """Make translations available in all Jinja2 templates.

    Exposes:
    - ``_``   — shortcut for ``t(key)`` look-ups with English fallback
                  (e.g. ``{{ _('nav_help') }}``)
    - ``l10n`` — the full translations dict for the detected language
    - ``lang`` — the detected language code (e.g. ``"en"``, ``"cs"``)
    - ``supported_langs`` — list of available language codes
    - ``home_url`` — URL of the main/index page (bare domain, no subdomain)
    """
    lang = detect_language()
    translations = get_translations(lang)

    # Compute home URL: scheme + first configured bare domain
    home_url = None
    domains = current_app.config.get("DOMAINS", [])
    if domains:
        scheme = request.scheme
        host = request.host.split(":")[0]
        # If currently on a subdomain, link to the bare domain;
        # otherwise (already on bare domain) just use "/".
        if host not in domains:
            home_url = f"{scheme}://{domains[0]}"
        else:
            home_url = "/"

    return {
        "_": lambda key, **kw: _t(key, translations, **kw),
        "l10n": translations,
        "lang": lang,
        "supported_langs": get_supported_langs(),
        "home_url": home_url or "/",
    }


@app.route("/api/init.js")
def api_init():
    """Bootstrap endpoint: return all initial data as a JS global variable.

    Returns the same JSON structures that the WebSocket handlers emit,
    so the client can render immediately without waiting for WS connect.
    Auth is validated via query params (same credentials used for WS auth).
    """
    from flask import request as req
    from .routes.views import get_privileges, get_default_playlist

    band_addr = req.args.get("band")
    key = req.args.get("key")
    if not band_addr or get_privileges(band_addr, key) is None:
        return "window.__INIT__ = null;", 200, {"Content-Type": "text/javascript"}

    band = db.session.query(Band).filter_by(addr=band_addr).first()
    if not band:
        return "window.__INIT__ = null;", 200, {"Content-Type": "text/javascript"}

    # Songlist (same serialization as get_songs handler)
    songs = db.session.query(Song).filter_by(band_id=band.id).all()
    songs.sort(key=lambda s: _locale_sort_key(s.name))
    tags = db.session.query(Tag).filter_by(band_id=band.id).all()
    songlist = {
        "tags": [t.name for t in tags],
        "items": [
            {
                "id": s.id,
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

    # Playlists (reuses existing function)
    playlists = get_band_playlists_data(band)

    # Current playlist items (if active/default playlist exists)
    playlist = get_default_playlist(band)
    playlist_data = get_playlist_items(playlist) if playlist else None

    init_data = {
        "songlist": songlist,
        "playlists": playlists,
        "playlist": playlist_data,
    }

    js = f"window.__INIT__ = {json.dumps(init_data)};"
    js = js.replace("</", "<\\/")  # prevent closing </script> in HTML
    return js, 200, {"Content-Type": "text/javascript"}


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
                "meta": json.loads(item.meta) if item.meta else None,
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


def get_band_playlists_data(band):
    """Get all playlists for a band (pure data function, no session dependency)"""
    playlists = (
        db.session.query(Playlist)
        .filter_by(band_id=band.id)
        .order_by(Playlist.date.desc())
        .order_by(Playlist.id.desc())
        .all()
    )
    res = [
        {
            "id": p.id,
            "name": p.name,
            "date": p.date.isoformat(),
            "band_id": p.band_id,
            "active_item_id": p.active_item_id,
            "item_count": len(p.items),
            "song_count": sum(1 for i in p.items if i.song_id is not None),
            "set_count": sum(1 for i in p.items if i.meta and json.loads(i.meta).get("is_break")) + 1,
        }
        for p in playlists
    ]
    return res


@socketio.on("get_playlists")
def on_get_band_playlists(data):
    res = get_band_playlists_data(get_band())
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
        # Skip break items during navigation
        while item and item.meta and json.loads(item.meta).get("is_break"):
            pos += (1 if off > 0 else -1)
            item = (
                db.session.query(PlaylistItem)
                .filter_by(playlist_id=playlist_id, position=pos)
                .first()
            )
        item_id = None if item is None else item.id

    item = db.session.query(PlaylistItem).get(item_id)
    if item and item.playlist_id != playlist_id:
        return
    if item and item.meta and json.loads(item.meta).get("is_break"):
        return

    playlist.active_item_id = item_id
    db.session.commit()

    # Build documents data for the play view
    song_data = {}
    if item and item.song:
        song = item.song
        documents = find_documents_by_song(song)
        song_data = {
            'song_id': song.id,
            'song_name': song.name,
            'documents': documents,
        }

    # Broadcast play event
    emit(
        "item_played",
        {
            "playlist_id": playlist_id,
            "item_id": item_id,
            "timestamp": dt.now(datetime.timezone.utc).isoformat(),
            **song_data,
        },
        to=f"band_{band.id}",
    )


@socketio.on("add_song")
def add_playlist_item(data, broadcast=True):
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


@socketio.on("add_break")
def add_break(data, broadcast=True):
    """Add a break/pause separator to a playlist"""
    band = get_band()
    playlist = get_playlist(band, data)
    playlist_id = playlist.id

    target_id = data.get("target_id")
    before = data.get("before", False)

    label = data.get("label")

    last_item = (
        db.session.query(PlaylistItem)
        .filter_by(playlist_id=playlist_id)
        .order_by(PlaylistItem.position.desc())
        .first()
    )
    position = last_item.position + 1 if last_item else 0

    meta_dict = {"is_break": True}
    if label:
        meta_dict["label"] = label
    item = PlaylistItem(playlist_id=playlist_id, song_id=None, position=position, meta=json.dumps(meta_dict))

    db.session.add(item)
    db.session.commit()

    if target_id:
        data = dict(
            playlist_id=playlist_id,
            before=before,
            target_id=target_id,
            moved_ids=[item.id],
        )
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

    res = get_band_playlists_data(band)
    emit("playlists", res, to=f'band_{band.id}')

    res = get_playlist_items(playlist)
    emit("playlist_created", res)


@socketio.on("delete_playlist")
def on_delete_playlist(data):
    band = get_band()
    playlist = get_playlist(band, data)

    db.session.delete(playlist)
    db.session.commit()

    res = get_band_playlists_data(band)

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

    res = get_band_playlists_data(band)
    emit("playlists", res, to=f'band_{band.id}')

    res = get_playlist_items(playlist)
    emit("playlist_updated", res, to=f"band_{band.id}")


@socketio.on("get_songlist")
def get_songs(data={}):
    band = get_band()

    songs = db.session.query(Song).filter_by(band_id=band.id).all()
    songs.sort(key=lambda s: _locale_sort_key(s.name))
    tags = db.session.query(Tag).filter_by(band_id=band.id).all()

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
        # Band-level sheet-store config ({patterns, instruments}) so that
        # clients which resolve sheet files on their own filesystem (e.g.
        # gigpanel) can run the shared finder offline after connect. The
        # filesystem *prefix* is machine-specific and stays client-side.
        "sheet_store": json.loads(band.sheet_store) if band.sheet_store else {},
    }

    emit("songlist", res, to=f"band_{band.id}")


@socketio.on("create_tag")
def create_tag(data, broadcast=True):
    """Create a new tag"""

    band = get_band()

    name = data.get("name")
    if not name:
        return

    tag = Tag(band_id=band.id, name=name)

    db.session.add(tag)
    db.session.commit()

    if broadcast:
        get_songs()


@socketio.on("save_song")
def save_song(data, broadcast=True):
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

    if broadcast:
        get_songs()


@socketio.on("create_song")
def create_song(data, broadcast=True):
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

    if broadcast:
        get_songs()


@socketio.on("batch")
def batch(data):
    broadcast = data.get('broadcast', True)
    for req in data.get('requests', []):
        cmd = req.get("cmd")
        arg = req.get("arg")
        if cmd == "create_song":
            create_song(arg, broadcast=False)
        elif cmd == "create_tag":
            create_tag(arg, broadcast=False)
        elif cmd == "save_song":
            save_song(arg, broadcast=False)
        elif cmd == "add_song":
            add_playlist_item(arg, broadcast=False)

    if broadcast:
        get_songs()


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


@app.cli.command("set-sheet-store")
@click.argument("addr")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
def set_sheet_store(addr, path):
    """Set a band's sheet-store config from a JSON file.

    ADDR is the band's subdomain identifier. PATH points to a JSON file with
    the shape {"patterns": {...}, "instruments": {...}} — see
    examples/sheet-store-band.json for a reference layout.
    """
    with app.app_context():
        band = db.session.query(Band).filter_by(addr=addr).first()
        if band is None:
            print(f"No band with addr '{addr}'.")
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "patterns" not in data or "instruments" not in data:
            print("Config must be a JSON object with 'patterns' and 'instruments' keys.")
            return
        band.sheet_store = json.dumps(data)
        db.session.commit()
        print(f"Sheet store set for band '{band.name}' ({addr}).")


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
