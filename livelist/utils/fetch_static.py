"""Download third-party frontend assets into the static directory.

Replaces the former ``get_static.sh`` shell script with a pure-stdlib,
cross-platform implementation (no ``wget``/``unzip`` dependency). Invoked
explicitly via the ``flask fetch-static`` CLI command — it is **not** run
automatically at startup, so installs stay offline-safe and predictable.

Static directory resolution
---------------------------
By default assets land in the package's own ``livelist/static/`` folder, which
is what Flask serves via ``url_for('static', ...)``. This is correct for
editable installs (``pip install -e .``): the source tree is writable and
persists across reinstalls.

Set the ``LIVELIST_STATIC_DIR`` environment variable to redirect *both* the
download target and Flask's static folder to an external directory. This is
useful for non-editable installs where ``site-packages`` is read-only or where
you want fetched assets to survive ``pip install --upgrade``. When set,
``flask fetch-static`` populates that directory as a *complete* static root:
it copies the committed bundled files (custom CSS/JS, favicon, …) out of the
package **and** downloads the third-party libraries, so everything the
templates reference via ``url_for('static', ...)`` is served from one place.

Assets fetched
  - Bootstrap 5 CSS + JS bundle (+ source map)
  - Bootstrap Icons 1.13.1 CSS + web fonts
  - Socket.IO 3.1.3 client (+ source map)
"""

from __future__ import annotations

import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

# The package's bundled static dir — always the package location, used as the
# source of committed files to copy when LIVELIST_STATIC_DIR overrides the
# destination.
_PACKAGE_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Single-file downloads: (url, destination relative to the static dir)
_SINGLE_FILES = [
    (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css",
        "css/bootstrap.min.css",
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js",
        "js/bootstrap.bundle.min.js",
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js.map",
        "js/bootstrap.bundle.min.js.map",
    ),
    (
        "https://cdn.socket.io/3.1.3/socket.io.min.js",
        "js/socket.io.min.js",
    ),
    (
        "https://cdn.socket.io/3.1.3/socket.io.min.js.map",
        "js/socket.io.min.js.map",
    ),
]

# Zip downloads: (url, handler_name)
_ZIP_ASSETS = [
    (
        "https://github.com/twbs/icons/releases/download/v1.13.1/bootstrap-icons-1.13.1.zip",
        "_extract_bootstrap_icons",
    ),
]

# Files/dirs produced by fetching (excluded when copying committed files, so a
# previously-fetched source tree doesn't drag third-party libs into an override
# dir — those get re-downloaded into the override instead).
_FETCHED_FILES = {
    "css/bootstrap.min.css",
    "css/bootstrap-icons.min.css",
    "js/bootstrap.bundle.min.js",
    "js/bootstrap.bundle.min.js.map",
    "js/socket.io.min.js",
    "js/socket.io.min.js.map",
}
_FETCHED_DIRS = {"css/fonts"}


def get_static_dir() -> Path:
    """Return the static directory: ``$LIVELIST_STATIC_DIR`` if set, else the
    package's bundled ``static/`` folder."""
    override = os.environ.get("LIVELIST_STATIC_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _PACKAGE_STATIC_DIR


def is_overridden() -> bool:
    """True when ``LIVELIST_STATIC_DIR`` redirects static files outside the
    package."""
    return bool(os.environ.get("LIVELIST_STATIC_DIR", "").strip())


def _download(url: str, dest: Path) -> None:
    """Stream ``url`` to ``dest``, creating parent dirs as needed."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  fetching {url}")
    with urllib.request.urlopen(url) as response, open(dest, "wb") as out:
        shutil.copyfileobj(response, out)


def _extract_bootstrap_icons(zip_path: Path, static_dir: Path) -> None:
    """Pull bootstrap-icons.min.css and its fonts/ out of the release zip."""
    css_dir = static_dir / "css"
    fonts_dir = css_dir / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            base = name.rsplit("/", 1)[-1]
            if base == "bootstrap-icons.min.css":
                with zf.open(name) as src, open(css_dir / base, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            elif "/fonts/" in name:
                # Preserve only the filename, flatten into css/fonts/
                fname = name.rsplit("/fonts/", 1)[-1]
                if fname:
                    with zf.open(name) as src, open(fonts_dir / fname, "wb") as dst:
                        shutil.copyfileobj(src, dst)


_HANDLERS = {
    "_extract_bootstrap_icons": _extract_bootstrap_icons,
}


def _is_fetched(rel: str) -> bool:
    """True if a packaged static path belongs to a fetched (third-party)
    asset rather than a committed project file."""
    if rel in _FETCHED_FILES:
        return True
    for d in _FETCHED_DIRS:
        if rel == d or rel.startswith(d + "/"):
            return True
    return False


def _copy_committed(static_dir: Path) -> None:
    """Copy committed (non-fetched) static files from the package into the
    override directory so it becomes a complete static root."""
    if not _PACKAGE_STATIC_DIR.is_dir():
        print("  no bundled static dir found; skipping committed-file copy")
        return
    copied = 0
    for src in _PACKAGE_STATIC_DIR.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(_PACKAGE_STATIC_DIR).as_posix()
        if "__pycache__" in rel or rel.startswith("."):
            continue
        if _is_fetched(rel):
            continue
        dest = static_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied += 1
    print(f"  copied {copied} committed file(s) from package")


def is_present(static_dir: Path | None = None) -> bool:
    """Return True iff every fetched asset already exists in ``static_dir``."""
    if static_dir is None:
        static_dir = get_static_dir()
    for _, rel in _SINGLE_FILES:
        if not (static_dir / rel).exists():
            return False
    return (static_dir / "css" / "bootstrap-icons.min.css").exists()


def fetch(force: bool = False) -> None:
    """Download all frontend assets into the resolved static directory.

    When ``LIVELIST_STATIC_DIR`` is set, the destination is also populated
    with the package's committed static files so Flask can serve everything
    from that one directory. Idempotent unless ``force`` is True.
    """
    static_dir = get_static_dir()
    static_dir.mkdir(parents=True, exist_ok=True)

    # When redirecting outside the package, mirror the committed bundled files
    # in first so the override dir is a complete static root. Done unconditionally
    # (cheap, idempotent) so a half-populated dir self-heals.
    if is_overridden():
        print(f"Populating {static_dir} as the static root ...")
        _copy_committed(static_dir)

    if not force and is_present(static_dir):
        print("Static assets already present — nothing to download.")
        print("Use 'flask fetch-static' with --force to re-download.")
        return

    tmp_dir = static_dir / ".fetch-tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        print("Downloading single-file assets...")
        for url, rel in _SINGLE_FILES:
            _download(url, static_dir / rel)

        for url, handler_name in _ZIP_ASSETS:
            print(f"Downloading {url}...")
            zip_path = tmp_dir / Path(url).name
            _download(url, zip_path)
            _HANDLERS[handler_name](zip_path, static_dir)
    except Exception as exc:  # noqa: BLE001 - re-raise with context
        raise RuntimeError(f"Failed to fetch static assets: {exc}") from exc
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print("Static assets ready in:", static_dir)


if __name__ == "__main__":
    fetch(force=True)
