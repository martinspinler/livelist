"""
HTML views for Livelist
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Any, Optional, TypedDict

import flask.json

from flask import redirect, render_template, request, url_for, make_response, send_file, abort, current_app
from datetime import date



from ..models import Band, Playlist, PlaylistItem, Song, db
from ..songfind import (
    Store,
    build_store,
    find_documents as _find_documents,
    resolve_document as _resolve_document_path,
)
from . import views_bp


# --- Sheet music / lyrics helpers ---

IMG_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')

RENDERING_LABELS = {'pdf': 'Sheet', 'text': 'Lyrics', 'ireal': 'iReal'}


def _get_store(band: Band) -> Store:
    """Build a Store from the band's per-band sheet_store config.

    The band.sheet_store column holds a JSON string of the form
    {"patterns": {...}, "instruments": {...}} (or NULL). When unset, an
    empty store is returned so the app degrades gracefully instead of
    crashing — bands simply show no documents until configured.
    """
    _prefix = current_app.config.get("SHEET_STORE_PATH")
    store = json.loads(band.sheet_store) if band.sheet_store else {}
    prefix: str = "" if _prefix is None else str(_prefix).format(band=band.addr)
    return build_store(store, prefix)


def _name_candidates(song: Song) -> list[str]:
    """Name candidates for a song: prefer song.filename (covers case-sensitive
    variants like "All Of Me" vs "All of Me"), fall back to song.name."""
    name_candidates = [song.filename] if song.filename else []
    if song.name not in name_candidates:
        name_candidates.append(song.name)
    return name_candidates


def find_documents_by_song(song: Song) -> list:
    """Find all unique documents for a song by iterating patterns × instruments.

    Thin wrapper around the shared :mod:`livelist.songfind` module; the
    server always probes without orientation (``None``) — orientation-aware
    probing is a client concern.
    """
    st = _get_store(song.band)
    return _find_documents(_name_candidates(song), st, orientation=None)


def resolve_document(song: Song, pattern_id: str, instr_id: str) -> Optional[str]:
    """Resolve a specific document file for serving.

    Given a pattern_id and instr_id, tries that instrument's suffixes with
    the pattern template until an existing file is found. Returns the
    absolute file path, or None.
    """
    st = _get_store(song.band)
    return _resolve_document_path(_name_candidates(song), st, pattern_id, instr_id)


def get_privileges(band_name, key):
    band = (
        db.session.query(Band)
        .filter_by(addr=band_name)
        .first()
    )
    if band:
        if key == band.pwd:
            return "edit"
    return None


def check_privileges(band):
    auth_cookie = flask.json.loads(request.cookies.get('auth_data_simple', "{}"))
    for band_name, key in auth_cookie.items():
        if band == band_name and get_privileges(band_name, key):
            return key
    return None


def _get_domains() -> list[str]:
    """Return the app's main domain from config (e.g. 'livelist.org').

    Falls back to empty list when DOMAINS is not configured.
    """
    return current_app.config.get("DOMAINS", [])


def _get_subdomain():
    """Extract the subdomain from the request host, or None if there isn't one.

    Uses the DOMAIN config setting to reliably distinguish between
    the main domain (e.g. livelist.org → None) and a subdomain
    (e.g. myband.livelist.org → 'myband').
    """
    host = request.host.split(":")[0]  # strip port
    domains = _get_domains()

    for domain in domains:
        if host.endswith("." + domain):
            return host[: -(len(domain) + 1)]

    return None


def _get_cookie_domain():
    """Determine the domain attribute for the auth cookie.
    """

    host = request.host.split(":")[0]  # strip port
    domains = _get_domains()

    if host in domains:
        return host

    subdomain = _get_subdomain()
    if subdomain is None:
        return host
    for domain in domains:
        if host == (subdomain + "." + domain):
            return domain

    return None


def _set_auth_cookie(response, auth_cookie):
    """Set the shared auth cookie on a response."""
    domain = _get_cookie_domain()
    kwargs: dict[str, Any] = {"max_age": 60 * 60 * 24 * 365 * 2}
    if domain:
        kwargs["domain"] = domain
    response.set_cookie('auth_data_simple', flask.json.dumps(auth_cookie), **kwargs)
    return response


def _get_instr_pref(band_addr: str) -> Optional[str]:
    """Read the preferred instrument for a band from the cookie."""
    prefs = flask.json.loads(request.cookies.get('instr_pref', '{}'))
    return prefs.get(band_addr)


def _set_instr_cookie(response, band_addr: str, instr_id: str):
    """Set the instrument preference cookie (per-band)."""
    prefs = flask.json.loads(request.cookies.get('instr_pref', '{}'))
    prefs[band_addr] = instr_id
    domain = _get_cookie_domain()
    kwargs: dict[str, Any] = {"max_age": 60 * 60 * 24 * 365 * 2}
    if domain:
        kwargs["domain"] = domain
    response.set_cookie('instr_pref', flask.json.dumps(prefs), **kwargs)
    return response


@views_bp.route("/")
def index():
    subdomain = _get_subdomain()
    force_login = request.args.get("force_login") is not None

    auth_cookie = flask.json.loads(request.cookies.get('auth_data_simple', "{}"))
    auth_bands = []
    for band_name, key in auth_cookie.items():
        if get_privileges(band_name, key):
            auth_bands.append(band_name)

    # On subdomain, if authenticated for that band and not forcing login, show band view directly
    if not force_login and subdomain is not None and subdomain in auth_bands:
        return view_band_noredirect(subdomain)

    bands = (
        db.session.query(Band)
        .filter(Band.addr.in_(auth_bands))
        .all()
    )
    return render_template(
        "index.html",
        bands=bands,
        bad_access=(request.args.get("auth_failed") is not None),
        subdomain=subdomain,
    )


@views_bp.route("/login", methods=["GET", "POST"])
def login():
    subdomain = _get_subdomain()

    if request.method == "GET":
        # GET /login handles logout: remove the subdomain band from the auth cookie,
        # then redirect back to index (which will show login form since band is gone).
        auth_cookie = flask.json.loads(request.cookies.get('auth_data_simple', "{}"))

        # If on a subdomain, log out only that band
        if subdomain and subdomain in auth_cookie:
            del auth_cookie[subdomain]

        # Determine redirect target based on remaining auth
        auth_bands = [b for b, k in auth_cookie.items() if get_privileges(b, k)]
        if subdomain and subdomain in auth_bands:
            # Still authenticated (shouldn't happen after delete, but safety)
            target = "/"
        else:
            # Not authenticated for subdomain anymore — index will show login form
            target = "/?force_login"

        response = make_response(redirect(target))
        _set_auth_cookie(response, auth_cookie)
        return response

    # POST: process login form
    auth_cookie = flask.json.loads(request.cookies.get('auth_data_simple', "{}"))
    band_name = request.form.get("band_name")
    key = request.form.get("band_access_key")

    if get_privileges(band_name, key):
        auth_cookie[band_name] = key
        # If logging into the same band as the current subdomain, stay on subdomain root
        if subdomain == band_name:
            target = "/"
        else:
            target = f'/band/{band_name}'
        response = make_response(redirect(target))
        _set_auth_cookie(response, auth_cookie)
        return response

    response = make_response(redirect('/?auth_failed'))
    return response


@views_bp.route("/band/<band>/")
def view_band(band):
    bands = (
        db.session.query(Band)
        .filter_by(addr=band)
        .all()
    )
    # FIXME: Check only for ALLOWED subdomains
    if bands and request.host in ["localhost"]:
        return redirect(request.scheme + "://" + band + "." + request.host)
    return view_band_noredirect(band)

def get_default_playlist(band) -> Optional[Playlist]:
    # Get active playlist
    playlist = None
    if band.active_playlist_id:
        playlist = db.session.query(Playlist).get(band.active_playlist_id)

    # If no active playlist, get the most recent one
    if not playlist:
        playlist = (
            db.session.query(Playlist)
            .filter_by(band_id=band.id)
            .order_by(Playlist.date.desc())
            .first()
        )
    return playlist

def view_band_noredirect(band):
    """Main playlist interface"""
    # Get band from subdomain or default
    key = check_privileges(band)
    if key is None:
        return make_response(redirect('/?auth_failed'))

    band = _get_current_band(band)
    if band is None:
        return make_response(redirect('/?auth_failed'))
        return render_template("404.html")
        return redirect(url_for("views.band_selection"))

    playlist = get_default_playlist(band)

    date_today = date.today().isoformat()
    jinja_script = f"""<script>
        function jinja_update(state) {{
            state.currentBand = {band.id};
            state.currentPlaylist = { playlist.id if playlist else 'null' };
            state.activePlaylist = { playlist.id if playlist else 'null' };
            state.socket_auth = {{auth: {{band: "{band.addr}", key: "{key}"}}}};
        }}
        </script>
    """
    return render_template(
        "band.html", band=band, playlist=playlist, date_today=date_today, jinja_script=jinja_script, auth_key=key
    )


@views_bp.route("/play/<int:playlist_id>/")
def play_view(playlist_id: int):
    """Live play view for a playlist — reacts to ``item_played`` via Socket.IO.

    Bootstraps the page with the currently active item so the user sees
    something immediately, then hands over to the Socket.IO client which
    updates in real-time when the server broadcasts ``item_played``.
    """
    playlist = db.session.get_one(Playlist, playlist_id)
    band = playlist.band

    # Auth key for Socket.IO connection (same as band view)
    key = check_privileges(band.addr)
    if key is None:
        return make_response(redirect('/?auth_failed'))

    # Instrument definitions from store config (for instrument selector)
    st = _get_store(band)

    # Build a list of song-carrying items (skip breaks) for navigation
    items = (
        db.session.query(PlaylistItem)
        .filter_by(playlist_id=playlist_id)
        .order_by(PlaylistItem.position)
        .all()
    )
    song_items = []
    for item in items:
        if item.song_id is None:
            continue
        song = item.song
        if song is None:
            continue
        documents = find_documents_by_song(song)

        song_items.append({
            'id': item.id,
            'song_id': song.id,
            'song_name': song.name,
            'position': item.position,
            'documents': documents,
        })

    # Resolve the currently active item
    active_item_id = playlist.active_item_id
    active_song = None
    active_documents = []
    if active_item_id:
        pli = db.session.get(PlaylistItem, active_item_id)
        if pli and pli.song:
            active_song = pli.song
            # Reuse documents from song_items if already probed
            existing = next((s for s in song_items if s['id'] == active_item_id), None)
            active_documents = existing['documents'] if existing else find_documents_by_song(active_song)

    store_instruments = {i.id: i.name for i in st.instruments.values()}
    instr_pref = _get_instr_pref(band.addr) or ''

    return render_template(
        "play.html",
        band=band,
        playlist=playlist,
        song_items=song_items,
        active_item_id=active_item_id,
        active_song=active_song,
        active_documents=active_documents,
        store_instruments=store_instruments,
        rendering_labels=RENDERING_LABELS,
        auth_key=key,
        instr_pref=instr_pref,
    )


@views_bp.route("/band-selection/")
def band_selection():
    """Band selection page"""
    bands = db.session.query(Band).all()
    return render_template("band_selection.html", bands=bands)


@views_bp.route("/api/instr-pref/<band_addr>", methods=["POST"])
def set_instr_pref(band_addr: str):
    """Save the preferred instrument for a band into a cookie."""
    instr_id = request.form.get("instr_id", "")
    resp = make_response("ok", 200)
    return _set_instr_cookie(resp, band_addr, instr_id)


@views_bp.route("/select-band/<int:band_id>/")
def select_band(band_id: int):
    """Select a band and redirect to main interface"""
    band = db.session.get_one(Band, band_id)
    # In a real app, you might set a session cookie or subdomain redirect
    # For simplicity, we'll redirect with a query parameter
    return redirect(url_for("views.index", band=band.addr))


@views_bp.route("/sheets/<int:song_id>/<pattern_id>/<instr_id>/<int:page>.jpg")
@views_bp.route("/sheets/<int:song_id>/<pattern_id>/<instr_id>/<int:page>")
def sheet_view(song_id: int, pattern_id: str, instr_id: str, page: int):
    """Serve a single sheet-music page as JPEG.

    URL pattern: ``/sheets/<song_id>/<pattern_id>/<instr_id>/<page>.jpg``

    Locates the source PDF via ``resolve_document``, converts the requested
    page to JPEG (caching the result on disk), and returns the image.
    """
    song = db.session.get(Song, song_id)
    if song is None:
        abort(404)

    filename = resolve_document(song, pattern_id, instr_id)
    if not filename:
        abort(404)

    # Ensure cache directory exists
    os.makedirs(IMG_CACHE_PATH, exist_ok=True)
    cache_key = f'{song_id}-{pattern_id}-{instr_id}-{page}'
    cache_prefix = os.path.join(IMG_CACHE_PATH, cache_key)
    cached_file = f'{cache_prefix}.jpg'

    # Convert the requested PDF page to JPEG (cached)
    if not Path(cached_file).is_file():
        try:
            cmd = f'pdftoppm -jpeg -singlefile -f {page} -l {page} "{filename}" {cache_prefix}'
            subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError:
            abort(500)

    if not Path(cached_file).is_file():
        abort(404)

    return send_file(cached_file, mimetype='image/jpeg')


@views_bp.route("/lyrics/<int:song_id>/<pattern_id>/<instr_id>")
def lyrics_view(song_id: int, pattern_id: str, instr_id: str):
    """Serve lyrics for a song as an HTML fragment.

    Locates a .txt file via ``resolve_document``, splits it into paragraphs
    on blank lines, and renders each paragraph (preserving intra-paragraph
    line breaks) as HTML.
    """
    song = db.session.get(Song, song_id)
    if song is None:
        abort(404)

    filename = resolve_document(song, pattern_id, instr_id)
    if not filename:
        abort(404)

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except OSError:
        abort(500)

    # Split on blank lines into paragraphs; preserve line breaks within
    paragraphs = []
    for raw_para in content.split('\n\n'):
        lines = [line for line in raw_para.splitlines() if line.strip()]
        if lines:
            paragraphs.append(lines)

    return render_template("lyrics.html", paragraphs=paragraphs)


# Helper function to get current band (duplicated from app.py for views)
def _get_current_band(band_name=None):
    """Get current band based on subdomain or URL parameter"""
    #from flask import request

    # Try subdomain first
    host = request.host
    subdomain = host.split(".")[0] if "." in host else None

    if band_name is not None:
        band = db.session.query(Band).filter_by(addr=band_name).first()
        if band:
            return band

    if subdomain is not None:
        band = db.session.query(Band).filter_by(addr=subdomain).first()
        if band:
            return band

    return None
