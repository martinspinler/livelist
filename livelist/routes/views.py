"""
HTML views for Livelist
"""

import flask.json
from flask import redirect, render_template, request, url_for, make_response, current_app
from datetime import date

from ..models import Band, Playlist, db
from . import views_bp


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


@views_bp.route("/")
def index():
    subdomain = request.host.split(".")[0] if "." in request.host else None
    if subdomain is not None and request.host in ["localhost"]:
        return view_band_noredirect(subdomain)

    auth_cookie = flask.json.loads(request.cookies.get('auth_data_simple', "{}"))
    auth_bands = []
    for band_name, key in auth_cookie.items():
        if get_privileges(band_name, key):
            auth_bands.append(band_name)

    #print(data)
    #b = _get_current_band()
    #if b is not None:
    #    return view_band(b.name)
    bands = (
        db.session.query(Band)
        .filter(Band.addr.in_(auth_bands))
        .all()
    )
    return render_template("index.html", bands=bands, bad_access=(request.args.get("auth_failed") is not None))


@views_bp.route("/login", methods=["POST"])
def login():
    auth_cookie = flask.json.loads(request.cookies.get('auth_data_simple', "{}"))
    band_name = request.form.get("band_name")
    key = request.form.get("band_access_key")
    if get_privileges(band_name, key):
        response = make_response(redirect(f'/band/{band_name}'))
        auth_cookie[band_name] = key
        response.set_cookie('auth_data_simple', flask.json.dumps(auth_cookie), max_age=60*60*24*365*2)
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

def get_default_playlist(band):
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
        "band.html", band=band, playlist=playlist, date_today=date_today, jinja_script=jinja_script
    )


@views_bp.route("/play/<int:playlist_id>/")
def play_view(playlist_id: int):
    """Live view for a playlist"""
    playlist = db.session.get_one(Playlist, playlist_id)
    band = playlist.band

    return render_template("play.html", band=band, playlist=playlist)


@views_bp.route("/band-selection/")
def band_selection():
    """Band selection page"""
    bands = db.session.query(Band).all()
    return render_template("band_selection.html", bands=bands)


@views_bp.route("/select-band/<int:band_id>/")
def select_band(band_id: int):
    """Select a band and redirect to main interface"""
    band = db.session.get_one(Band, band_id)
    # In a real app, you might set a session cookie or subdomain redirect
    # For simplicity, we'll redirect with a query parameter
    return redirect(url_for("views.index", band=band.addr))


@views_bp.route("/sheets/<path:song_name>/")
def sheet_view(song_name: str):
    """View sheet music for a song"""
    band = _get_current_band()
    if not band:
        return redirect(url_for("views.band_selection"))

    # This is a simplified version - in the original, it served PDF files
    return render_template("sheet.html", band=band, song_name=song_name)


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
