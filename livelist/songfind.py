"""Pure-stdlib sheet-music document discovery.

Shared by the LiveList server and by clients that resolve sheet files on
their own filesystem (e.g. gigpanel). This module has no framework
dependencies — no Flask, no SQLAlchemy, no Qt — so it can be imported
anywhere. Callers build a :class:`Store` (from wherever their config comes
from) and pass name candidates; this module enumerates which
pattern x instrument combinations resolve to existing files on disk via
``os.path.isfile``.

The two main entry points are :func:`find_documents` (enumerate all
matching documents for a song) and :func:`resolve_document` (resolve one
specific pattern/instrument pair, e.g. for serving a chosen file).
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Pattern:
    id: str
    render: str
    pattern: str
    label: str
    instr: list[str] = field(default_factory=list)


@dataclass
class Instrument:
    id: str
    name: str
    patterns: list[str]
    prio: Optional[list[str]] = None


@dataclass
class Store:
    patterns: dict[str, Pattern]
    instruments: dict[str, Instrument]
    prefix: str


def build_store(config: dict, prefix: str = "") -> Store:
    """Build a :class:`Store` from a raw ``{"patterns": ..., "instruments": ...}``
    config dict and a filesystem prefix.

    An empty/missing config yields an empty store so callers degrade
    gracefully instead of crashing.
    """
    patterns = {k: Pattern(id=k, **v) for k, v in config.get('patterns', {}).items()}
    instruments = {k: Instrument(id=k, **v) for k, v in config.get('instruments', {}).items()}
    return Store(patterns, instruments, prefix)


def _effective_suffix_idx(
    suffix_idx: int,
    instr_suffixes: list,
    template: str,
    has_instr_placeholder: bool,
    pat_instr: Optional[list],
    instr_id: str,
    patterns: dict[str, Pattern],
    prio: Optional[list[str]],
    pat: Pattern
) -> int:
    """Compute the effective suffix index for auto-select priority.

    The returned integer determines how the client ranks this document for
    a given instrument (lower = higher priority).

    Three cases:

    1. Pattern HAS ``{instrument}`` placeholder -> the suffix was actually
       used in the filename, so its real position (suffix_idx) is the
       priority.

    2. Pattern LACKS ``{instrument}`` AND has an explicit ``instr`` list
       in the pattern config (e.g. ``["voc"]`` on a lyrics PDF):
       - If instr_id IS in that list -> eff_idx = 0 (high priority for
         this instrument; pattern order among equal indices resolves
         specific-vs-generic ties since specific patterns are listed
         earlier in the config).
       - If instr_id is NOT in that list -> eff_idx = len(suffixes)
         (low priority fallback).

    3. Pattern LACKS ``{instrument}`` AND has NO ``instr`` list ->
       heuristic: scan all suffixes and check if any stripped suffix
       string appears in the template path (e.g. suffix ' - Lyrics'
       matches ``0_Lyrics/{name}.pdf``).  If found, use that suffix's
       index; otherwise fall back to len(suffixes).
    """
    if prio:
        for i, p in enumerate(prio):
            if p == pat.id:
                return i

    if has_instr_placeholder:
        return suffix_idx

    # Generic pattern — check explicit instr list first
    if pat_instr is not None:
        if instr_id in pat_instr:
            return 0
        return len(instr_suffixes)

    # No explicit instr: heuristic — match suffix keywords against path
    for si, sfx in enumerate(instr_suffixes):
        stripped = sfx.lstrip(' -')
        if stripped and stripped in template:
            return si

    return len(instr_suffixes)


def _probe_suffixes(instr: Instrument, orientation: Optional[str]) -> list[str]:
    """Return the suffix list to probe for an instrument, optionally
    prepending orientation variants (``-L``/``-P``) so they are tried first.

    Mirrors the gigpanel's historical behaviour: when the screen is
    landscape/portrait, ``<suffix>-L``/``<suffix>-P`` variants are
    preferred over the bare suffix. The server passes ``orientation=None``
    (no expansion).
    """
    base = list(instr.patterns)
    if orientation in ('L', 'P'):
        otag = f"-{orientation}"
        return [s + otag for s in base] + base
    return base


def find_documents(
    name_candidates: list[str],
    store: Store,
    orientation: Optional[str] = None,
) -> list:
    """Find all unique documents for a song by iterating patterns x instruments.

    ``name_candidates`` is the ordered list of names to try (callers usually
    pass ``[song.filename, song.name]``, skipping falsy entries).

    ``orientation`` may be ``'L'`` or ``'P'`` to prefer landscape/portrait
    instrument-suffix variants (prepended, highest priority); ``None`` keeps
    the configured suffixes as-is.

    Returns a list of document dicts, each with:
      pattern_id          - id of the pattern that produced this file
      render              - render type ("pdf", "text")
      path                - file path relative to the store prefix
      instruments_matched - {instr_id: suffix_index} mapping; the suffix_index
                            determines auto-select priority on the client
                            (lower = higher priority).  See _effective_suffix_idx.
      label               - human-readable label from the pattern config

    Documents are deduplicated by absolute file path.  When two pattern x
    instrument combinations resolve to the same file, their matched
    instruments are merged and the first pattern's id/label is kept.
    """
    seen = {}  # abs_path -> document dict

    for pat in store.patterns.values():
        template = pat.pattern
        label = pat.label
        has_instr_placeholder = '{instrument}' in template

        for instr in store.instruments.values():
            suffixes = _probe_suffixes(instr, orientation)
            for suffix_idx, suffix in enumerate(suffixes):
                matched_rel = None
                matched_abs = None
                for name in name_candidates:
                    candidate_rel = template.format(name=name, instrument=suffix)
                    candidate_abs = store.prefix + candidate_rel
                    if os.path.isfile(candidate_abs):
                        matched_rel = candidate_rel
                        matched_abs = candidate_abs
                        break
                if matched_abs is None:
                    continue
                eff_idx = _effective_suffix_idx(
                    suffix_idx, suffixes, template,
                    has_instr_placeholder, pat.instr, instr.id, store.patterns, instr.prio, pat
                )
                if matched_abs not in seen:
                    seen[matched_abs] = {
                        'pattern_id': pat.id,
                        'render': pat.render,
                        'path': matched_rel,
                        'instruments_matched': {instr.id: eff_idx},
                        'label': label or pat.id,
                    }
                else:
                    doc = seen[matched_abs]
                    if instr.id not in doc['instruments_matched']:
                        doc['instruments_matched'][instr.id] = eff_idx
                break  # first matching suffix per instrument is enough

    return list(seen.values())


def pick_best_for_instrument(documents: list, instr_id: Optional[str]) -> Optional[dict]:
    """Pick the highest-priority document for a given instrument.

    Selects the document whose ``instruments_matched`` contains ``instr_id``
    with the lowest effective index (highest priority). If ``instr_id`` is
    None or no document matches it, falls back to the first document of
    any instrument. Returns None if there are no documents at all.

    This is the "set instrument X and pick the first one" selector used by
    clients like gigpanel that show a single document without a dialog.
    """
    if not documents:
        return None

    if instr_id:
        matching = [d for d in documents if instr_id in d.get('instruments_matched', {})]
        if matching:
            return min(matching, key=lambda d: d['instruments_matched'][instr_id])

    return documents[0]


def resolve_document(
    name_candidates: list[str],
    store: Store,
    pattern_id: str,
    instr_id: str,
) -> Optional[str]:
    """Resolve a specific document file for serving.

    Given a pattern_id and instr_id, tries that instrument's suffixes with
    the pattern template until an existing file is found. Returns the
    absolute file path, or None.
    """
    pat = store.patterns.get(pattern_id)
    instr = store.instruments.get(instr_id)

    if pat is None or instr is None:
        return None

    template = pat.pattern
    for suffix in instr.patterns:
        for name in name_candidates:
            candidate_rel = template.format(name=name, instrument=suffix)
            candidate_abs = store.prefix + candidate_rel
            if os.path.isfile(candidate_abs):
                return candidate_abs

    return None
