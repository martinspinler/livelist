"""English (en) translations for Livelist."""

TRANSLATIONS: dict[str, str] = {
    # ---- Navigation bar ----
    "nav_add_song":       "Add Song",
    "nav_playlists":      "Playlists",
    "nav_live":           "Live",
    "nav_help":           "Help",

    # ---- Mode toggle ----
    "mode_play":          "Play",
    "mode_move":          "Move",
    "mode_edit":          "Edit",

    # ---- Edit-mode actions ----
    "action_delete_selected": "Delete selected",
    "action_update_order":    "Update order",

    # ---- Song Library panel ----
    "song_library_title":     "Song Library",
    "song_library_search_ph": "Type or use keypad...",
    "sort_alpha":             "A-Z",
    "sort_bpm":               "BPM",
    "sort_id":                "ID",
    "tag_filter_btn":         "Tags",
    "hidden_songs":           "Hidden songs",
    "filter_and":             "AND",
    "filter_or":              "OR",
    "add_break":              "Add Break",

    # ---- Playlist panel ----
    "playlist_panel_title":   "Playlists",
    "playlist_name_ph":       "Playlist name",
    "playlist_create":        "Create",

    # ---- Edit Playlist modal ----
    "modal_edit_playlist_title": "Edit Playlist",
    "label_name":               "Name",
    "label_date":               "Date",
    "btn_cancel":               "Cancel",
    "btn_save_changes":         "Save Changes",

    # ---- Edit Song modal ----
    "modal_edit_song_title": "Edit Song",
    "label_bpm":            "BPM",
    "label_tags":           "Tags",

    # ---- Livelist item tooltips / titles ----
    "title_play":           "Play",
    "title_move_to_anchor": "Move to anchor",
    "title_delete":         "Delete",
    "title_delete_break":   "Delete break",
    "title_collapse_set":   "Collapse set",
    "title_copy_set":       "Copy set",

    # ---- Anchor system labels ----
    "anchor_label":         "Anchor",

    # ---- Set / break labels ----
    "set_label":            "Set {n}",

    # ---- Help modal ----
    "help_title":                         "Help",

    "help_livelist_title":                "Livelist (Main View)",
    "help_livelist_desc":                 "The central area showing the current playlist as an ordered, numbered list of songs. The view operates in three modes, toggled via the Play / Move / Edit button group in the navbar.",

    "help_play_mode":                     "Play mode (default) — Performance mode. Tap the play button on any item to mark it as the active song; the event is broadcast to all connected clients. The anchor is visible for adding songs at a specific position.",
    "help_move_mode":                     'Move mode — Reorder mode. Each item shows a drag handle and a "move to anchor" button on the right side. Songs can be rearranged by drag & drop or by moving an item to the anchor position.',
    "help_edit_mode":                     "Edit mode — Management mode. Position numbers become clickable selection targets. Select multiple items to delete them in bulk or update item order explicitly.",

    "help_set_breaks_title":              "Set Breaks",
    "help_set_breaks_desc":               'Break/pause items divide a playlist into sets. Every playlist starts with a "Set 1" header, and additional breaks can be inserted to create further sets.',
    "help_add_break":                     'Add Break — Click the "Add Break" button in the Song Library panel to insert a set separator after the current anchor position.',
    "help_set_header":                    'Set header — Each set displays: label (e.g. "Set 1"), song count, copy-to-clipboard button, and collapse toggle.',
    "help_collapse":                      "Collapse — Click the chevron on any set header to collapse/expand the songs in that set.",
    "help_anchor_in_set":                 "Anchor — Click a set header or its anchor icon to set the anchor at that position.",
    "help_reorder_delete_breaks":         "Reorder/Delete — In move mode, break items have drag handles; in edit mode, they show delete buttons. Set 1 cannot be deleted.",
    "help_nav_skip_breaks":               "Navigation — Prev/next playback automatically skips over break items; break items cannot be played.",

    "help_anchor_title":                  "Anchor System",
    "help_anchor_desc":                   'The anchor determines where new songs are inserted and where items are moved when using "move to anchor". It has two states, toggled by clicking the anchor item:',
    "help_anchor_nonsticky":              "Non-sticky (⚓↓) — Items are inserted/moved after the anchor, then the anchor advances past the new item. Enables sequential workflow.",
    "help_anchor_sticky":                 "Sticky (⚓↑) — Items are inserted/moved before the anchor, and the anchor stays in place. Enables accumulating items at a fixed position.",

    "help_song_library_title":            "Song Library",
    "help_song_library_desc":             "A searchable, filterable catalog of all songs in the band's library.",
    "help_search":                        "Search — Type-to-filter text input, plus an optional T9-style keypad for quick lookups.",
    "help_sorting":                       "Sorting — Sort alphabetically (A–Z), by BPM, or by ID.",
    "help_tag_filter":                    "Tag filtering — Add/remove tag chips; toggle each chip between include/exclude mode. Advanced toggle shows gate controls and AND/OR logic switch.",
    "help_add_to_playlist":               "Add to playlist — Click a song to add it to the current playlist.",
    "help_pin_panel":                     "Pin panel — Pin the offcanvas panel open instead of auto-closing.",
    "help_library_edit_mode":             "Edit mode — Switch the library to edit mode to create new songs, edit existing songs, or manage tags with prefix conventions.",

    "help_playlist_manager_title":        "Playlist Manager",
    "help_playlist_manager_desc":         "Manage all playlists for the band.",
    "help_playlist_create":               "Create — Name + date form to create a new playlist.",
    "help_playlist_select":               "Select — Click a playlist to load it into the livelist view.",
    "help_playlist_activate":             "Activate — Set a playlist as the band's active playlist (broadcast icon).",
    "help_playlist_edit":                 "Edit — Rename a playlist or change its date via a modal.",
    "help_playlist_delete":               "Delete — Remove a playlist.",

    # ---- Index page ----
    "index_title":          "Livelist",
    "index_subtitle":       "Collaborative playlist management for live bands",
    "index_features":       "Real-time web application that helps bands organize their song library and manage setlists during live performances. Multiple band members can connect simultaneously and see playlist changes instantly.",
    "index_select_band":    "Select a Band",
    "index_choose_band":    "Choose a band to view and manage playlists.",
    "index_bad_access":     "Band address or key doesn't work.",
    "index_address":        "Address",
    "index_enter_key_for":  "Enter key for {addr}:",
    "index_or_access":      "Or access by address and key:",
    "index_go":             "Go",
    "index_log_out":        "Log out of {addr}",

    # ---- Index features section ----
    "feature_realtime_title":   "Real-time Collaboration",
    "feature_realtime_desc":    "All playlist changes are instantly synchronized to every connected band member via WebSocket.",
    "feature_modes_title":      "Three Working Modes",
    "feature_modes_desc":       "Play mode for performances, Move mode for reordering, and Edit mode for bulk management.",
    "feature_anchor_title":     "Smart Anchor System",
    "feature_anchor_desc":      "Flexible insertion point that supports both sequential and fixed-position workflows.",
    "feature_library_title":    "Searchable Song Library",
    "feature_library_desc":     "Filter by name, BPM, or tags with T9 keypad support and advanced AND/OR tag logic.",
    "feature_sets_title":       "Set Breaks",
    "feature_sets_desc":        "Organize your playlist into sets with collapsible headers and per-set copy to clipboard.",
    "feature_live_title":       "Live Screen",
    "feature_live_desc":        "Clean, read-only display optimized for projection or a shared screen, showing the current song in real time.",
}
