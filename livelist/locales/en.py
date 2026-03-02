"""English (en) translations for Livelist."""

TRANSLATIONS: dict[str, str] = {
    # ---- Navigation bar ----
    "nav_home":           "Home",
    "nav_add_song":       "Add Song",
    "nav_playlists":      "Playlists",
    "nav_live":           "Live",
    "nav_sheets":         "Sheets",
    "nav_switch_band":    "Switch band",
    "nav_collapse_all":   "Collapse all sets",
    "nav_expand_all":     "Expand all sets",
    "nav_scroll_anchor":  "Scroll to anchor",
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
    "add_break":              "Add Set",

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
    "title_delete_break":   "Delete set",
    "title_collapse_set":   "Collapse set",
    "title_copy_set":       "Copy items in set",

    # ---- Anchor system labels ----
    "anchor_label":         "Anchor",

    # ---- Numbering toggle ----
    "numbering_toggle":    "Toggle numbering: global / per-set",

    # ---- Set / break labels ----
    "set_label":            "Set {n}",

    # ---- Help modal ----
    "help_title":                         "Help",

    "help_livelist_title":                "Livelist (Main View)",
    "help_livelist_desc":                 "The central area showing the current playlist as an ordered, numbered list of songs. The view operates in three modes, toggled via the Play / Move / Edit button group in the navbar.",

    "help_play_mode":                     "Play mode (default) — Tap the play button on any item to mark it as the active song; the event is broadcast to all connected clients.",
    "help_move_mode":                     'Move mode — Reorder mode. Each item shows a drag handle and a "move to anchor" button on the right side. Songs can be rearranged by drag & drop or by moving an item to the anchor position.',
    "help_edit_mode":                     "Edit mode — Management mode. Position numbers become clickable selection targets. Select multiple items to delete them in bulk or update item order explicitly.",

    "help_set_breaks_title":              "Sets / Breaks",
    "help_set_breaks_desc":               'For better clarity, a playlist can be organized into multiple sets (e.g., to indicate a break), with every playlist containing at least one set.',
    "help_add_break":                     'Add Set — Click the "Add Set" button in the Song Library panel to insert a set separator after the current anchor position.',
    "help_set_header":                    'Set header — Each set displays: label (e.g. "Set 1"), song count, button for copying part of the playlist to the clipboard, and collapse toggle.',
    "help_collapse":                      "Collapse — Click the chevron on any set header to collapse/expand the songs in that set.",
    "help_anchor_in_set":                 "Anchor — The anchor in a set header works exactly like for individual playlist items. Click the set header to set the anchor at that position.",
    "help_reorder_delete_breaks":         "Reorder/Delete — In move mode, breaks have drag handles; in edit mode, they show delete buttons. The first set cannot be deleted.",
    "help_nav_skip_breaks":               "Navigation — Prev/next playback automatically skips breaks; breaks cannot be played.",

    "help_anchor_title":                  "Anchor System",
    "help_anchor_desc":                   'The anchor determines where new songs are inserted and where items are moved when using "move to anchor". It has two states, toggled by clicking the anchor item:',
    "help_anchor_nonsticky":              "Non-sticky (⚓↓) — Items are inserted/moved after the anchor, then the anchor advances to the new/moved item. Enables sequentially adding items AFTER.",
    "help_anchor_sticky":                 "Sticky (⚓↑) — Items are inserted/moved before the anchor, and the anchor stays on the same item. Enables sequentially adding items BEFORE.",

    "help_song_library_title":            "Song Library",
    "help_song_library_desc":             "A searchable, filterable catalog of all songs in the band's library.",
    "help_search":                        "Search — Type-to-filter text input, plus an optional T9-style keypad for quick lookups.",
    "help_sorting":                       "Sorting — Sort alphabetically (A–Z), by BPM, or by ID.",
    "help_tag_filter":                    "Tag filtering — Add/remove tag chips; toggle each chip between include/exclude mode. Advanced settings show hidden tags and an AND/OR logic switch.",
    "help_add_to_playlist":               "Add to playlist — Click a song to add it to the current playlist.",
    "help_pin_panel":                     "Pin panel — Pin the offcanvas panel so it does not close after adding a song, allowing you to add multiple songs at once.",
    "help_library_edit_mode":             "Edit mode — Switch the library to edit mode to create new songs, edit existing songs, or manage tags.",

    "help_playlist_manager_title":        "Playlist Manager",
    "help_playlist_manager_desc":         "Manage all playlists for the band.",
    "help_playlist_create":               "Create — A dialog with name and date for creating a new playlist.",
    "help_playlist_select":               "Select — Click a playlist to load it into the livelist view for yourself only.",
    "help_playlist_activate":             "Activate — Set a playlist as the band's active playlist (broadcast icon) for everyone else too.",
    "help_playlist_edit":                 "Edit — Rename a playlist or change its date.",
    "help_playlist_delete":               "Delete — Remove a playlist.",

    # ---- Index page ----
    "index_title":          "Livelist",
    "index_subtitle":       "Collaborative playlist management for bands",
    "index_features":       "Real-time web application that helps bands organize their song library and manage setlists during live performances. Multiple band members can connect simultaneously and see playlist changes instantly.",
    "index_select_band":    "Select a Band",
    "index_choose_band":    "Choose a previously visited band to view and manage playlists.",
    "index_bad_access":     "Band address or key doesn't work.",
    "index_address":        "Address",
    "index_enter_key_for":  "Enter key for {addr}:",
    "index_or_access":      "Or access existing band by address and key:",
    "index_go":             "Go",
    "index_log_out":        "Log out of {addr}",

    # ---- Index features section ----
    "feature_realtime_title":   "Real-time Collaboration",
    "feature_realtime_desc":    "All playlist changes are instantly synchronized to every connected band member.",
    "feature_modes_title":      "Three Working Modes",
    "feature_modes_desc":       "Play mode for performances, Move mode for reordering, and Edit mode for bulk management.",
    "feature_anchor_title":     "Smart Anchor System",
    "feature_anchor_desc":      "Flexible insertion point for quick reordering with Before/After behavior for Move/Add.",
    "feature_library_title":    "Searchable Song Library",
    "feature_library_desc":     "Filter by name, BPM, or tags with T9 keypad support and advanced AND/OR tag logic.",
    "feature_sets_title":       "Multiple Sets",
    "feature_sets_desc":        "Organize your playlist into sets for better clarity, with the ability to copy song names to the clipboard.",
    "feature_live_title":       "Sheets Screen",
    "feature_live_desc":        "Display the sheet document in PDF or iReal-like screen.",
}
