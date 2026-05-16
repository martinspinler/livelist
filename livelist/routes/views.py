"""
HTML views for Livelist
"""

import flask.json
from typing import Any
from flask import redirect, render_template, request, url_for, make_response
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


def _get_domains() -> list[str]:
    """Return the app's main domain from config (e.g. 'livelist.org').

    Falls back to empty list when DOMAINS is not configured.
    """
    from flask import current_app
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

def get_default_playlist(band) -> Playlist | None:
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
