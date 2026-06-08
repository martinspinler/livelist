"""Lightweight localization / i18n package for Livelist.

Translation data lives in ``livelist.locales.<lang>`` modules, each
exposing a ``TRANSLATIONS`` dict.  New languages are picked up
automatically — just drop a new ``<lang>.py`` file in the ``locales``
directory.

Usage in Jinja2 templates (via the Flask context processor)::

    {{ _('nav_help') }}               → translated string
    {{ _('index_log_out', addr='foo') }} → with format interpolation
"""

from __future__ import annotations

import importlib
from pathlib import Path

from flask import request

# ---------------------------------------------------------------------------
# Auto-discover available languages from livelist/locales/*.py
# ---------------------------------------------------------------------------

_LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
DEFAULT_LANG = "en"

_discovered: dict[str, dict[str, str]] = {}


def _discover_languages() -> dict[str, dict[str, str]]:
    """Import every ``<lang>.py`` in the locales directory and collect
    their ``TRANSLATIONS`` dicts.
    """
    result: dict[str, dict[str, str]] = {}
    if not _LOCALES_DIR.is_dir():
        return result
    for py_file in sorted(_LOCALES_DIR.glob("*.py")):
        lang_code = py_file.stem
        if lang_code.startswith("_"):
            continue
        module_name = f"livelist.locales.{lang_code}"
        try:
            mod = importlib.import_module(module_name)
            if hasattr(mod, "TRANSLATIONS"):
                result[lang_code] = mod.TRANSLATIONS
        except ImportError:
            pass
    return result


def _get_all_translations() -> dict[str, dict[str, str]]:
    """Return the cached translation map, lazy-loading on first call."""
    if not _discovered:
        _discovered.update(_discover_languages())
    return _discovered


# ---------------------------------------------------------------------------
# Supported languages
# ---------------------------------------------------------------------------

def get_supported_langs() -> list[str]:
    """Return available language codes (always includes ``en`` first)."""
    langs = list(_get_all_translations().keys())
    # Ensure English is always present and listed first
    if "en" in langs:
        langs.remove("en")
    return ["en"] + sorted(langs)


SUPPORTED_LANGS: list[str] = []  # populated lazily; use get_supported_langs()


def _ensure_supported_langs() -> list[str]:
    global SUPPORTED_LANGS
    if not SUPPORTED_LANGS:
        SUPPORTED_LANGS = get_supported_langs()
    return SUPPORTED_LANGS


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------


def _parse_accept_language(header: str | None) -> list[str]:
    """Parse an Accept-Language header into an ordered list of language codes.

    Only the primary subtag (e.g. ``en`` from ``en-US``) is kept, and
    duplicates are removed while preserving order.
    """
    if not header:
        return []
    langs: list[str] = []
    for part in header.split(","):
        code = part.split(";")[0].strip().split("-")[0].lower()
        if code and code not in langs:
            langs.append(code)
    return langs


def detect_language() -> str:
    """Detect the preferred language from the current Flask request.

    Resolution order:
    1. ``?lang=`` query parameter
    2. Best match from ``Accept-Language`` header
    3. Fallback to :data:`DEFAULT_LANG`

    Returns :data:`DEFAULT_LANG` when called outside a request context.
    """
    supported = _ensure_supported_langs()
    try:
        # 1. Explicit query param wins
        lang_param = request.args.get("lang")
        if lang_param and lang_param.lower() in supported:
            return lang_param.lower()

        # 2. Accept-Language header
        for code in _parse_accept_language(request.headers.get("Accept-Language")):
            if code in supported:
                return code
    except RuntimeError:
        pass

    # 3. Default
    return DEFAULT_LANG


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_translations(lang: str | None = None) -> dict[str, str]:
    """Return a ``key -> translated string`` dict for *lang*.

    If *lang* is ``None`` the language is auto-detected from the current
    request (see :func:`detect_language`).  If the requested language is
    not supported, the English translations are returned.
    """
    all_tr = _get_all_translations()
    if lang is None:
        lang = detect_language()
    return all_tr.get(lang, all_tr.get(DEFAULT_LANG, {}))


def t(key: str, translations: dict[str, str] | None = None, **kwargs) -> str:
    """Look up *key* with English fallback.

    Resolution order:
    1. The key in the provided/requested translations dict
    2. The key in the English (fallback) translations
    3. The raw key itself (last resort)

    Any extra keyword arguments are used for simple string formatting
    (e.g. ``t("set_label", n=2)`` → ``"Set 2"``).
    """
    all_tr = _get_all_translations()

    if translations is None:
        translations = get_translations()

    value = translations.get(key)

    # Fallback to English if key missing in the target language
    if value is None and lang_of(translations) != DEFAULT_LANG:
        value = all_tr.get(DEFAULT_LANG, {}).get(key)

    # Last resort: return the key itself
    if value is None:
        value = key

    if kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass
    return value


def lang_of(translations: dict[str, str]) -> str | None:
    """Best-effort reverse-lookup: which language does this dict belong to?

    Used internally by :func:`t` to decide whether a fallback is needed.
    """
    all_tr = _get_all_translations()
    for code, tr in all_tr.items():
        if tr is translations:
            return code
    return None
