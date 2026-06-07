"use strict";

function initApplication() {
    const socket = state.io(window.Location.host, state.socket_auth);

    Object.assign(state, {
        editMode: false,
        moveMode: false,
        selectedItems: new Set(),
        socket: socket,

        selectionMode: "none",
        selection: new Array(),

        //currentBand: null,
        //currentPlaylist: null,
        activeItem: null,
        //activePlaylist: null,
        anchorItem: null,
        anchorItemSticky: false,
        lastAction: null,

        edit_song_id: null,
        songitemEditMode: false,

        playlist: null,
        songlist: new Map(),
        usedSongs: [],
        songlistFetched: false,
        playlistsFetched: false,

        tagFilters: new Map(),
        tagFilterCombine: "OR",
        tagFilterAdvanced: false,
        gateStates: new Map(),
        allTags: new Map(),

        collapsedSets: new Set(),
        /*socket_auth: {
            auth: {
                band: null,
                key: null,
            },
        },*/
    });

    setupEventListeners();
    setupSocketCallbacks();
    initDragAndDrop(state, handle_drag_and_drop);

    // Use HTTP-bootstrapped data if available (from /api/init.js <script> tag)
    if (window.__INIT__) {
        songlist_update(window.__INIT__.songlist);
        playlists_update(window.__INIT__.playlists);
        if (window.__INIT__.playlist) playlist_select(window.__INIT__.playlist);
    }

    window.addEventListener("DOMContentLoaded", function () {
        socket.emit("get_songlist", {});
        /* HOTFIX(synchronization): should emit "get_playlists" and "select_playlist",
         * but it has issues. Maybe try async requests */
    });

    function handle_drag_and_drop(msg) {
        if (state.selection.length != 0) {
            msg.moved_ids = state.selection;
        }
        state.socket.emit("move_item", msg);
        state.selection.length = 0;
    }

    /* Livelist */
    function livelist_update_song_items() {
        document.querySelectorAll('.livelist-item').forEach(item_e => {
            const song = state.songlist.get(parseInt(item_e.dataset.songId));
            if (song) {
                item_e.querySelector('.song-name').textContent = song.name;
                item_e.querySelector('.song-tags').textContent = song.tags.join(",");
            }
        });
    }

    function livelist_update_playing_item(itemId) {
        const old_ie = document.querySelectorAll('.livelist-item');
        const new_ie = document.querySelector(`.livelist-item[data-item-id="${itemId}"]`);
        const old_e = document.querySelectorAll('.livelist-item-play');
        const new_e = document.querySelector(`.livelist-item[data-item-id="${itemId}"] .livelist-item-play`);

        old_ie.forEach(item => {
            item.classList.remove('playing');
        });
        // Also clear any stale playing state from break items (should not happen)
        document.querySelectorAll('.livelist-break').forEach(item => {
            item.classList.remove('playing');
        });
        new_ie?.classList.add('playing');

        old_e.forEach(item => {
            item.classList.remove('btn-success');
            item.classList.add('btn-outline-success');
        });

        new_e?.classList.remove('btn-outline-success');
        new_e?.classList.add('btn-success');
    }

    function livelist_update(msg) {
        document.getElementById("livelist-name").textContent = msg.name;
        document.getElementById("livelist-date").textContent = msg.date;

        const list_e = document.getElementById('livelist-items')
        const prevAnchor = state.anchorItem;

        list_e.innerHTML = "";

        // Pre-scan: count breaks to assign set numbers and song counts per set
        const SET1_KEY = "__set1__";
        let tempSetNum = 1;
        let tempCount = 0;
        const breakSetMap = {};   // break item id -> set number
        const setSongCounts = {}; // set number -> song count

        msg.items.forEach(item => {
            if (item.meta && item.meta.is_break) {
                setSongCounts[tempSetNum] = tempCount;
                tempSetNum++;
                breakSetMap[item.id] = tempSetNum;
                tempCount = 0;
            } else {
                tempCount++;
            }
        });
        setSongCounts[tempSetNum] = tempCount;

        // Render virtual Set 1 header
        const set1tmpl = document.getElementById("livelist-break-template").content.cloneNode(true);
        const set1_e = set1tmpl.querySelector('.livelist-break');
        set1_e.dataset.setKey = SET1_KEY;
        set1_e.querySelector('.livelist-break-label').textContent = "Set 1";
        set1_e.querySelector('.livelist-break-songcount').textContent =
            setSongCounts[1] + (setSongCounts[1] === 1 ? " song" : " songs");

        // Collapse state for Set 1
        const set1Collapsed = state.collapsedSets.has(SET1_KEY);
        set1_e.querySelector('.livelist-break-collapse').classList.toggle('bi-chevron-down', !set1Collapsed);
        set1_e.querySelector('.livelist-break-collapse').classList.toggle('bi-chevron-right', set1Collapsed);

        // Drag handle for Set 1: visible in move mode but disabled (can't drag virtual header)
        // Move-to-anchor is not applicable to Set 1
        set1_e.querySelector('.drag-handle')?.classList.add('set1-grip-disabled');
        set1_e.querySelector('.livelist-break-delete')?.classList.add('set1-delete-disabled');
        set1_e.querySelector('.livelist-break-move-to-anchor')?.remove();

        // Show anchor on Set 1 if anchorItem points to this element (from previous render)
        if (state.anchorItem != null && state.anchorItem.dataset.setKey === SET1_KEY) {
            set1_e.querySelector('.livelist-item-anchor').classList.remove('d-none');
        }

        list_e.appendChild(set1_e);

        // Second pass: render items
        let setNumber = 1;
        let currentBreakId = SET1_KEY; // Set 1 is the current "break" until a real break appears
        let songIndex = 0;

        msg.items.forEach(
            item => {
                if (item.meta && item.meta.is_break) {
                    // Render break separator
                    setNumber = breakSetMap[item.id];
                    currentBreakId = item.id;

                    const tmpl = document.getElementById("livelist-break-template").content.cloneNode(true);
                    const break_e = tmpl.querySelector('.livelist-break');
                    break_e.dataset.itemId = item.id;
                    break_e.dataset.isBreak = "true";

                    const label = item.meta.label || ("Set " + setNumber);
                    break_e.querySelector('.livelist-break-label').textContent = label;
                    break_e.querySelector('.livelist-break-songcount').textContent =
                        setSongCounts[setNumber] + (setSongCounts[setNumber] === 1 ? " song" : " songs");

                    // Collapse state
                    const isCollapsed = state.collapsedSets.has(item.id);
                    const collapseBtn = break_e.querySelector('.livelist-break-collapse');
                    collapseBtn.classList.toggle('bi-chevron-down', !isCollapsed);
                    collapseBtn.classList.toggle('bi-chevron-right', isCollapsed);

                    // Delete button visibility in edit mode
                    break_e.querySelector('.livelist-break-delete').classList.toggle('d-none', !state.editMode);

                    // Restore anchor if this break was the anchor
                    if (prevAnchor != null && prevAnchor.dataset.isBreak && item.id == prevAnchor.dataset.itemId) {
                        break_e.querySelector('.livelist-item-anchor').classList.remove('d-none');
                        state.anchorItem = break_e;
                    }

                    list_e.appendChild(break_e);
                } else {
                    // Render regular song item
                    const tmpl = document.getElementById("livelist-item-template").content.cloneNode(true);
                    const item_e = tmpl.querySelector('.livelist-item');
                    const song = state.songlist.get(item.song_id);
                    item_e.dataset.itemId = item.id;
                    item_e.dataset.songId = item.song_id;
                    item_e.dataset.setNumber = setNumber;

                    if (song) {
                        item_e.querySelector('.song-name').textContent = song.name;
                        item_e.querySelector('.song-tags').textContent = song.tags.join(",");
                        item_e.querySelector('.song-user_id').textContent =
                            (song.user_id ? song.user_id + ' - ' : '') + (song.notes || '');
                    }
                    item_e.querySelector('.livelist-item-position').textContent = songIndex + 1;

                    // Hide if parent set is collapsed
                    if (currentBreakId && state.collapsedSets.has(currentBreakId)) {
                        item_e.classList.add('d-none');
                    }

                    list_e.appendChild(item_e);
                    songIndex++;

                    if (prevAnchor != null && item.id == prevAnchor.dataset.itemId) {
                        state.anchorItem = item_e;
                    }
                }
            }
        );

        let ids = msg.items.map(x => x.id);
        state.selection.forEach(
            item => {
                if (ids.indexOf(item) < 0) {
                    state.selection.splice(state.selection.indexOf(item), 1);
                }
            }
        );

        let ai = state.anchorItem;
        if (state.lastAction == "add_song") {
            if (!state.anchorItemSticky) {
                if (ai == null) {
                    ai = document.querySelectorAll('.livelist-item')[0];
                } else {
                    // Skip past break elements when advancing anchor
                    let next = ai.nextElementSibling;
                    while (next && !next.classList.contains('livelist-item')) {
                        next = next.nextElementSibling;
                    }
                    ai = next;
                }
            }
            state.lastAction = null;
        }
        livelist_item_set_anchor(ai);

        livelist_update_item_numbers();
        livelist_update_playing_item(msg.active_item_id);
        songlist_update_used_items(msg.items);
        update_mode();
    }

    function livelist_update_item_numbers() {
        document.querySelectorAll(".livelist-item").forEach(item => {
            const itemId = parseInt(item.dataset.itemId);
            const pos = state.selection.indexOf(itemId);
            const selectbox = item.querySelector(".livelist-item-selectbox");
            const position = item.querySelector(".livelist-item-position");

            if (selectbox) {
                selectbox.textContent = pos >= 0 ? String(pos + 1) : "";
                selectbox.classList.toggle('btn-outline-warning', pos == -1);
                selectbox.classList.toggle('btn-warning', pos != -1);
                selectbox.classList.toggle('d-none', !state.editMode || pos == -1);
            }

            if (position) {
                position.classList.toggle('d-none', state.editMode && pos != -1);
                position.classList.toggle('btn-primary', !state.editMode);
                position.classList.toggle('btn-outline-primary', state.editMode);
            }
        });
    }

    function livelist_item_set_anchor(pi, user_action = false) {
        if (state.anchorItem) {
            state.anchorItem.querySelector(".livelist-item-anchor")?.classList.add("d-none");
        }

        if (pi == state.anchorItem && user_action && pi != null) {
            // Set 1 anchor always uses non-sticky (below) behavior
            if (!pi.dataset.setKey) {
                state.anchorItemSticky = !state.anchorItemSticky;
            }
        } else if (pi != null && pi.dataset.setKey) {
            // Setting anchor on Set 1 — force non-sticky
            state.anchorItemSticky = false;
        }

        let ai_el;
        state.anchorItem = pi;
        if (state.anchorItem != null) {
            ai_el = pi.querySelector(".livelist-item-anchor");
            ai_el?.classList.remove("d-none");
        }

        // Update anchor direction indicators
        const dirDown = ai_el?.querySelector('.anchor-dir-down');
        const dirUp = ai_el?.querySelector('.anchor-dir-up');
        if (dirDown && dirUp) {
            dirDown.classList.toggle('d-none', state.anchorItemSticky);
            dirUp.classList.toggle('d-none', !state.anchorItemSticky);
        }

        // Sticky indicator styling
        if (ai_el != null) {
            ai_el.classList.toggle("btn-outline-primary", state.anchorItemSticky);
        }

        // Update move-to-anchor button visibility
        update_move_to_anchor_visibility();

        // Update navbar anchor info
        update_anchor_info();
    }

    function update_anchor_info() {
        const posEl = document.getElementById('anchor-info-pos');
        const nameEl = document.getElementById('anchor-info-name');
        const dirEl = document.getElementById('anchor-info-dir');
        const infoEl = document.getElementById('anchor-info');

        if (!posEl || !nameEl || !dirEl || !infoEl) return;

        if (state.anchorItem == null) {
            posEl.textContent = '';
            nameEl.textContent = '';
            dirEl.className = 'bi bi-arrow-down';
        } else if (state.anchorItem.classList.contains('livelist-break')) {
            posEl.textContent = '';
            const label = state.anchorItem.querySelector('.livelist-break-label');
            nameEl.textContent = label ? label.textContent : '';
            dirEl.className = state.anchorItemSticky ? 'bi bi-arrow-up' : 'bi bi-arrow-down';
        } else {
            const position = state.anchorItem.querySelector('.livelist-item-position');
            const name = state.anchorItem.querySelector('.song-name');
            posEl.textContent = position ? position.textContent : '';
            nameEl.textContent = name ? name.textContent : '';
            dirEl.className = state.anchorItemSticky ? 'bi bi-arrow-up' : 'bi bi-arrow-down';
        }
    }

    function scroll_to_active_or_anchor() {
        let target = null;
        if (state.activeItem != null) {
            target = document.querySelector(`.livelist-item[data-item-id="${state.activeItem}"]`);
        }
        if (!target && state.anchorItem != null) {
            target = state.anchorItem;
        }
        if (target) {
            target.scrollIntoView({block: 'center', behavior: 'instant'});
        }
    }

    function toggleSetCollapse(setKey) {
        const isCollapsed = state.collapsedSets.has(setKey);
        if (isCollapsed) {
            state.collapsedSets.delete(setKey);
        } else {
            state.collapsedSets.add(setKey);
        }

        // Find the break element — either by setKey (virtual Set 1) or itemId (real breaks)
        let breakEl;
        if (setKey === "__set1__") {
            breakEl = document.querySelector('.livelist-break[data-set-key="__set1__"]');
        } else {
            breakEl = document.querySelector(`.livelist-break[data-item-id="${setKey}"]`);
        }
        if (!breakEl) return;

        let el = breakEl.nextElementSibling;
        while (el && !el.classList.contains('livelist-break')) {
            if (el.classList.contains('livelist-item')) {
                el.classList.toggle('d-none', !isCollapsed); // if was collapsed, now show; if was shown, now hide
            }
            el = el.nextElementSibling;
        }

        // Update collapse button icon
        const collapseBtn = breakEl.querySelector('.livelist-break-collapse');
        collapseBtn.classList.toggle('bi-chevron-down', isCollapsed);
        collapseBtn.classList.toggle('bi-chevron-right', !isCollapsed);
    }

    function copySetToClipboard(setKey) {
        // Collect songs belonging to the set after this break
        let str = "";
        let breakEl;
        if (setKey === "__set1__") {
            breakEl = document.querySelector('.livelist-break[data-set-key="__set1__"]');
        } else {
            breakEl = document.querySelector(`.livelist-break[data-item-id="${setKey}"]`);
        }
        if (!breakEl) return;

        let el = breakEl.nextElementSibling;
        while (el && !el.classList.contains('livelist-break')) {
            if (el.classList.contains('livelist-item')) {
                const song = state.songlist.get(parseInt(el.dataset.songId));
                if (song) {
                    const pos = el.querySelector('.livelist-item-position');
                    str += (pos ? pos.textContent : '') + ". " + song.name + "\n";
                }
            }
            el = el.nextElementSibling;
        }
        navigator.clipboard.writeText(str);
    }

    /* Songlist */
    function songlist_update_used_item(item) {
        const idx = state.usedSongs.indexOf(parseInt(item.dataset.songId));
        item.classList.toggle("active", idx >= 0);
    }

    function songlist_update_used_items(items) {
        document.querySelectorAll(".songlist-item").forEach((item) => {
            item.classList.remove("active");
        });
        items.forEach(
            item => {
                if (!item.song_id) return; // skip break items
                const qry = `.songlist-item[data-song-id="${item.song_id}"]`;
                document.querySelector(qry)?.classList.add("active");
            }
        );
    }

    function parseTag(rawTag) {
        if (rawTag.startsWith('!')) {
            return { name: rawTag.slice(1), defaultOff: true, advancedOnly: false, raw: rawTag };
        }
        if (rawTag.startsWith('#')) {
            return { name: rawTag.slice(1), defaultOff: false, advancedOnly: true, raw: rawTag };
        }
        return { name: rawTag, defaultOff: false, advancedOnly: false, raw: rawTag };
    }

    function renderGates() {
        const container = document.getElementById('tag-filter-gates');
        container.innerHTML = '';

        for (const [tagName, tagInfo] of state.allTags) {
            if (!tagInfo.defaultOff) continue;

            const tmpl = document.getElementById('tag-filter-gate-template').content.cloneNode(true);
            const gate = tmpl.querySelector('.tag-filter-gate');
            gate.dataset.tag = tagName;
            gate.querySelector('.tag-filter-gate-name').textContent = tagName;

            const isOpen = state.gateStates.get(tagName) || false;
            applyGateState(gate, isOpen);

            container.appendChild(gate);
        }

        document.getElementById('tag-filter-gates-section')
            .classList.toggle('d-none', container.children.length === 0);
    }

    function applyGateState(gate, isOpen) {
        const indicator = gate.querySelector('.tag-filter-gate-indicator');
        gate.classList.toggle('btn-primary', isOpen);
        gate.classList.toggle('btn-outline-secondary', !isOpen);
        indicator.classList.toggle('bi-eye-slash-fill', isOpen);
        indicator.classList.toggle('bi-eye-slash', !isOpen);
    }

    function addFilterChip(tag, mode) {
        state.tagFilters.set(tag, mode);

        const tagInfo = state.allTags.get(tag);
        const tmpl = document.getElementById('tag-filter-chip-template').content.cloneNode(true);
        const chip = tmpl.querySelector('.tag-filter-chip');
        chip.dataset.tag = tag;
        if (tagInfo && tagInfo.advancedOnly) {
            const icon = document.createElement('i');
            icon.className = 'bi bi-eye-fill me-1 tag-chip-icon';
            chip.prepend(icon);
        }
        chip.querySelector('.tag-filter-chip-name').textContent = tag;
        applyChipMode(chip, mode);

        document.getElementById('tag-filter-chips').appendChild(chip);
        renderAvailableTags();
        filterSongs();
    }

    function applyChipMode(chip, mode) {
        const isIncluded = mode === 'include';
        chip.classList.toggle('btn-success', isIncluded);
        chip.classList.toggle('btn-danger', !isIncluded);
        chip.querySelector('.tag-filter-chip-toggle').innerHTML =
            isIncluded ? '<i class="bi bi-check-lg"></i>' : '<i class="bi bi-x-lg"></i>';
    }

    function renderAvailableTags() {
        const container = document.getElementById('tag-filter-available');
        container.innerHTML = '';

        for (const [tagName, tagInfo] of state.allTags) {
            if (tagInfo.defaultOff) continue;
            if (tagInfo.advancedOnly && !state.tagFilterAdvanced) continue;
            if (state.tagFilters.has(tagName)) continue;

            const tmpl = document.getElementById('tag-filter-available-template').content.cloneNode(true);
            const btn = tmpl.querySelector('.tag-filter-available');
            btn.dataset.tag = tagName;
            btn.textContent = tagName;
            if (tagInfo.advancedOnly) {
                const icon = document.createElement('i');
                icon.className = 'bi bi-eye me-1';
                btn.prepend(icon);
            }
            container.appendChild(btn);
        }
    }

    function songlist_update(msg) {
        document.getElementById('song-list').innerHTML = "";

        state.songlist = new Map();
        state.allTags = new Map();

        msg.items.forEach(item => {
            const parsedTags = item.tags.map(t => parseTag(t));
            const song = Object.assign({}, item, {
                rawTags: item.tags,
                tags: parsedTags.map(t => t.name),
            });
            state.songlist.set(item.id, song);

            parsedTags.forEach(pt => {
                if (!state.allTags.has(pt.name)) {
                    state.allTags.set(pt.name, { defaultOff: pt.defaultOff, advancedOnly: pt.advancedOnly });
                }
            });
        });

        // Store raw tag list for edit modal
        state.tags = msg.tags;

        msg.items.forEach(item => {
            const tmpl = document.getElementById("songlist-item-template").content.cloneNode(true);
            const pi = tmpl.querySelector('.songlist-item');

            pi.dataset.songId = item.id;
            pi.dataset.songName = item.name;
            pi.dataset.songBpm = item.bpm;
            songlist_update_used_item(pi);

            pi.querySelector('.songlist-item-name').textContent = item.name;
            pi.querySelector('.songlist-item-meta').textContent =
                (item.user_id ? item.user_id + ' \u00B7 ' : '') +
                (item.bpm ? 'BPM: ' + item.bpm + ' \u00B7 ' : '');

            item.tags.forEach(tag => {
                const parsed = parseTag(tag);
                const tag_tmpl = document.getElementById("songlist-tag-template").content.cloneNode(true);
                const tag_item = tag_tmpl.querySelector('.songlist-item-tag');
                tag_item.textContent = parsed.name;
                if (parsed.defaultOff) {
                    tag_item.classList.add('bi', 'bi-eye-slash');
                }
                if (parsed.advancedOnly) {
                    tag_item.classList.add('tag-advanced-only', 'bi', 'bi-eye');
                    if (!state.tagFilterAdvanced) {
                        tag_item.classList.add('d-none');
                    }
                }
                pi.querySelector('.songlist-item-tags').appendChild(tag_item);
            });

            document.getElementById('song-list').appendChild(pi);
        });

        renderGates();
        renderAvailableTags();
        edit_song_update_tags(state.songlist.get(state.edit_song_id));
        update_songlist_panel_edit();
        livelist_update_song_items();
        filterSongs();

        /* HOTFIX(synchronization) */
        if (state.songlistFetched == false) {
            state.songlistFetched = true;
            socket.emit("get_playlists", {});
        }
    }

    /* Playlist */
    function playlist_select(msg) {
        state.playlist = msg;
        state.currentPlaylist = msg.playlist_id;
        state.activeItem = msg.active_item_id;
        state.anchorItem = null;
        state.usedSongs = msg.items.filter(item => item.song_id).map(item => item.song_id);

        state.selection.length = 0;

        livelist_update(msg);

        /* Select last item as anchor */
        let li = document.querySelectorAll('.livelist-item');
        livelist_item_set_anchor(li.item(li.length - 1));

        // Update the UI to show the selected playlist
        const playlistButtons = document.querySelectorAll(".playlist-btn-select");
        playlistButtons.forEach((btn) => {
            btn.classList.remove("active");
        });

        const qry = `.playlist-btn-select[data-playlist-id="${msg.playlist_id}"]`;
        document.querySelector(qry)?.classList.add("active");

        scroll_to_active_or_anchor();
    }

    function playlist_update_active_item(item) {
        const pa = item.querySelector('.playlist-btn-activate');
        pa.classList.toggle("btn-success", item.dataset.playlistId == state.activePlaylist);
        pa.classList.toggle("btn-outline-success", item.dataset.playlistId != state.activePlaylist);
    }

    function playlist_update_active_items() {
        document.querySelectorAll('.playlist-btn-activate.btn-success').forEach(
            item => playlist_update_active_item(item.closest(".playlist-item"))
        );

        const item = document.querySelector(`.playlist-item[data-playlist-id="${state.activePlaylist}"]`)
        playlist_update_active_item(item);
    }

    function playlists_update(msg) {
        document.getElementById('playlist-items').innerHTML = "";
        msg.forEach(
            item => {
                const tmpl = document.getElementById("playlist-item-template").content.cloneNode(true);
                const pi = tmpl.querySelector('.playlist-item');
                pi.dataset.playlistId = item.id;
                pi.querySelector('.playlist-item-name').textContent = item.name;
                pi.querySelector('.playlist-item-date').textContent = item.date;
                const sc = item.song_count != null ? item.song_count : item.item_count;
                const sets = item.set_count != null ? item.set_count : 1;
                pi.querySelector('.playlist-item-songcount').textContent =
                    sets + ' set' + (sets !== 1 ? 's' : '') + ', ' + sc + ' song' + (sc !== 1 ? 's' : '');

                pi.classList.toggle("active", item.id == state.currentPlaylist);

                playlist_update_active_item(pi);

                document.getElementById('playlist-items').appendChild(pi);
            }
        );

        /* HOTFIX(synchronization) */
        if (state.playlistsFetched == false) {
            state.playlistsFetched = true;

            if (state.currentPlaylist != null) {
                socket.emit("select_playlist", { playlist_id: state.currentPlaylist });
            }
        }
    }

    function setupSocketCallbacks() {
        //socket.on("connect", () => {});
        socket.on("item_played",        msg => livelist_update_playing_item(msg.item_id));
        socket.on("playlists",          msg => playlists_update(msg));
        socket.on("playlist_select",    msg => playlist_select(msg));
        socket.on("playlist_created",   msg => playlist_select(msg));
        socket.on("songlist",           msg => songlist_update(msg));
        socket.on("playlist_updated",   msg => {
            if (state.currentPlaylist == msg.playlist_id) {
                livelist_update(msg);
            }
        });
        socket.on("playlist_activated", msg => {
            state.activePlaylist = msg.playlist_id;
            playlist_update_active_items();
            socket.emit("select_playlist", { playlist_id: state.activePlaylist});
        });
    }

    function setupEventListeners() {
        document.getElementById('mode-play')?.addEventListener('click', () => setViewMode('play'));
        document.getElementById('mode-move')?.addEventListener('click', () => setViewMode('move'));
        document.getElementById('mode-edit')?.addEventListener('click', () => setViewMode('edit'));

        document.querySelectorAll('.keypad-btn').forEach(btn => {
            btn.addEventListener('click', handleKeypadButton);
        });

        document.getElementById('songlist-toggle-keypad').addEventListener('click', () => {
            document.getElementById('keypad-container').classList.toggle('d-none');
        });
        document.getElementById('songlist-song-create').addEventListener('click', handle_songlist_create_song);
        document.getElementById('btn-add-break')?.addEventListener('click', addBreakToPlaylist);

        document.getElementById('song-filter').addEventListener('input', debounce(filterSongs, 200));
        document.getElementById('sort-alpha').addEventListener('click', () => sortSongs('alpha'));
        document.getElementById('sort-bpm').addEventListener('click', () => sortSongs('bpm'));
        document.getElementById('sort-id').addEventListener('click', () => sortSongs('id'));
        //document.getElementById('tag-filter').addEventListener('change', filterSongs);
        document.getElementById('tag-filter-btn').addEventListener('click', handle_tag_filter_btn);
        document.getElementById('create-playlist-btn').addEventListener('click', playlist_new);
        document.getElementById('save-playlist-changes').addEventListener('click', playlist_save);
        document.getElementById('save-song-changes').addEventListener('click', song_save);
        document.getElementById('edit-sort').addEventListener('click', editSort);
        document.getElementById('songlist-panel-pin').addEventListener('click', handle_songlist_panel_pin);
        document.getElementById('songlist-panel-edit').addEventListener('click', (e) => {
            state.songitemEditMode = !state.songitemEditMode;
            update_songlist_panel_edit();
        });

        document.getElementById('livelist-delete-selected').addEventListener('click', handle_livelist_delete_selected);
        document.getElementById('edit-song-tag-create').addEventListener('click', handle_editsong_tag_create);

        document.getElementById('tag-filter-and').addEventListener('click', () => {
            state.tagFilterCombine = 'AND';
            document.getElementById('tag-filter-and').classList.add('active');
            document.getElementById('tag-filter-or').classList.remove('active');
            filterSongs();
        });
        document.getElementById('tag-filter-or').addEventListener('click', () => {
            state.tagFilterCombine = 'OR';
            document.getElementById('tag-filter-or').classList.add('active');
            document.getElementById('tag-filter-and').classList.remove('active');
            filterSongs();
        });
        document.getElementById('tag-filter-advanced-toggle').addEventListener('click', () => {
            if (document.getElementById('tag-filter').classList.contains('d-none')) {
                toggleTagPanel(true);
            }

            state.tagFilterAdvanced = !state.tagFilterAdvanced;
            document.getElementById('tag-filter-advanced').classList.toggle('d-none', !state.tagFilterAdvanced);
            const btn = document.getElementById('tag-filter-advanced-toggle');
            btn.classList.toggle('btn-outline-primary', !state.tagFilterAdvanced);
            btn.classList.toggle('btn-primary', state.tagFilterAdvanced);
            renderAvailableTags();

            document.querySelectorAll('.tag-advanced-only').forEach(el => {
                el.classList.toggle('d-none', !state.tagFilterAdvanced);
            });
        });
        document.getElementById('edit-song-tag-toggle').addEventListener('click', (e) => {
            const input = document.getElementById('edit-song-tag');
            const btn = e.currentTarget;
            const iconEl = btn.querySelector('i');
            const prefixes = ['', '!', '#'];
            const icons = ['bi-dash', 'bi-eye-slash', 'bi-eye'];
            const currentPrefix = input.value.startsWith('!') ? '!' : input.value.startsWith('#') ? '#' : '';
            const currentIndex = prefixes.indexOf(currentPrefix);
            const nextIndex = (currentIndex + 1) % prefixes.length;
            const nextPrefix = prefixes[nextIndex];

            // Remove current prefix from input
            if (currentPrefix && input.value.startsWith(currentPrefix)) {
                input.value = input.value.slice(currentPrefix.length);
            }
            // Insert next prefix
            if (nextPrefix) {
                input.value = nextPrefix + input.value;
            }

            // Update icon
            icons.forEach(cls => iconEl.classList.remove(cls));
            iconEl.classList.add(icons[nextIndex]);
            btn.classList.toggle('btn-outline-secondary', nextIndex === 0);
            btn.classList.toggle('btn-primary', nextIndex !== 0);
            input.focus();
        });

        function toggleTagPanel(open) {
            const panel = document.getElementById('tag-filter');
            const btn = document.getElementById('tag-filter-btn');
            if (open === undefined) {
                open = panel.classList.contains('d-none');
            }
            panel.classList.toggle('d-none', !open);
            btn.classList.toggle('btn-outline-primary', !open);
            btn.classList.toggle('btn-primary', open);
            btn.classList.toggle('bi-tags', !open);
            btn.classList.toggle('bi-tags-fill', open);
        }

        function handle_tag_filter_btn(ev) {
            toggleTagPanel();
        }
        function handle_livelist_item_number(pi, itemId) {
            if (state.selection.includes(itemId)) {
                const index = state.selection.indexOf(itemId);
                state.selection.splice(index, 1);
                pi.classList.toggle("list-group-item-warning", false);
            } else {
                state.selection.push(itemId);
                pi.classList.toggle("list-group-item-warning", true);
            }

            // Don't auto-toggle editMode — mode is controlled by mode toggle
            livelist_update_item_numbers();
        }

        function handle_livelist_item_select(pi) {
            livelist_item_set_anchor(pi, true);
        }

        function handle_livelist_delete_selected(e) {
            state.socket.emit("delete_items", { playlist_id: state.currentPlaylist, item_ids: state.selection });
            state.selection.length = 0;
        }

        function handle_livelist_item_click(target, livelist_item, itemId) {
            if (target.classList.contains("livelist-item-play")) {
                on_livelist_item_play(itemId);
            } else if (target.classList.contains("livelist-item-delete")) {
                on_livelist_item_delete(itemId);
            } else if (target.classList.contains('livelist-item-move-to-anchor')) {
                handle_move_to_anchor(itemId);
            } else if (target.classList.contains('livelist-item-selectbox')) {
                handle_livelist_item_number(livelist_item, itemId);
            } else if (target.classList.contains('livelist-item-position')) {
                if (state.editMode) {
                    handle_livelist_item_number(livelist_item, itemId);
                }
            } else {
                handle_livelist_item_select(livelist_item);
            }
        }

        function handle_songlist_item_click(target, songlist_item, songId) {
            if (document.getElementById('songlist-panel-edit').classList.contains("btn-outline-primary")) {
                addSongToPlaylist(songId);
            } else {
                editSong(songId);
            }
        }

        function handle_playlist_item_click(target, playlist_item, playlistId) {
            if (target.classList.contains("playlist-btn-activate")) {
                activatePlaylist(playlistId);
            } else if (target.classList.contains("playlist-btn-delete")) {
                deletePlaylist(playlistId);
            } else if (target.classList.contains("playlist-btn-edit")) {
                editPlaylist(playlistId);
            } else if (target.closest(".playlist-btn-select")) {
                selectPlaylist(playlistId);
            } else {
                return false;
            }
            return true;
        }

        function handle_editsong_tag_create(ev) {
            const toggleBtn = document.getElementById('edit-song-tag-toggle');
            let tagName = document.getElementById('edit-song-tag').value.trim();
            if (!tagName) return;

            // Add tag to song data so save_song includes it
            if (state.edit_song_id != null) {
                const song = state.songlist.get(state.edit_song_id);
                if (song && !song.rawTags.includes(tagName)) {
                    song.rawTags.push(tagName);
                    song.tags.push(parseTag(tagName).name);
                }
            }

            state.socket.emit('batch', {
                requests: [
                    { cmd: 'create_tag', arg: { name: tagName } },
                    { cmd: 'save_song', arg: {
                        id: state.edit_song_id,
                        name: document.getElementById('edit-song-name').value,
                        bpm: document.getElementById('edit-song-bpm').value,
                        tags: state.songlist.get(state.edit_song_id).rawTags,
                    }},
                ]
            });
            document.getElementById('edit-song-tag').value = '';
            const toggleIcon = toggleBtn.querySelector('i');
            toggleIcon.className = 'bi bi-dash';
            toggleBtn.classList.replace('btn-primary', 'btn-outline-secondary');
        }

        function handle_songlist_create_song(ev) {
            const filterInput = document.getElementById("song-filter");
            state.socket.emit("create_song", {name: filterInput.value});
            filterInput.value = '';
            filterSongs();
        }

        // Playlist item actions
        document.addEventListener("click", (e) => {
            const target = e.target;

            const livelist_item = target.closest(".livelist-item");
            const livelist_break = target.closest(".livelist-break");
            const songlist_item = target.closest(".songlist-item");
            const playlist_item = target.closest(".playlist-item");
            const tag_filter_gate = target.closest(".tag-filter-gate");
            const tag_filter_chip = target.closest(".tag-filter-chip");
            const tag_filter_available = target.closest(".tag-filter-available");
            const songlist_item_tag = target.closest(".songlist-item-tag");

            if (livelist_item) {
                handle_livelist_item_click(target, livelist_item, parseInt(livelist_item.dataset.itemId));
            } else if (livelist_break) {
                const breakId = parseInt(livelist_break.dataset.itemId);
                const setKey = livelist_break.dataset.setKey;
                if (target.closest('.livelist-break-collapse')) {
                    toggleSetCollapse(setKey || breakId);
                } else if (target.closest('.livelist-break-delete')) {
                    state.socket.emit("delete_items", { playlist_id: state.currentPlaylist, item_ids: [breakId] });
                } else if (target.closest('.livelist-break-move-to-anchor')) {
                    if (breakId) {
                        handle_move_to_anchor(breakId);
                    }
                } else if (target.closest('.clipboard-copy-break-set')) {
                    copySetToClipboard(setKey || breakId);
                    e.stopPropagation();
                } else {
                    // Clicking a break header sets the anchor on this break
                    livelist_item_set_anchor(livelist_break, true);
                }
            } else if (songlist_item) {
                handle_songlist_item_click(target, songlist_item, parseInt(songlist_item.dataset.songId));
            } else if (playlist_item) {
                const ret = handle_playlist_item_click(target, playlist_item, parseInt(playlist_item.dataset.playlistId));
                if (ret) {
                    e.stopPropagation();
                }
            } else if (songlist_item_tag) {
                const song = state.songlist.get(state.edit_song_id);
                songlist_item_tag.classList.toggle("btn-outline-primary");
                songlist_item_tag.classList.toggle("btn-primary");
                const rawName = songlist_item_tag.dataset.name;
                if (songlist_item_tag.classList.contains("btn-outline-primary")) {
                    song.rawTags.splice(song.rawTags.indexOf(rawName), 1);
                    song.tags.splice(song.tags.indexOf(parseTag(rawName).name), 1);
                } else {
                    song.rawTags.push(rawName);
                    song.tags.push(parseTag(rawName).name);
                }
                song_save_silent();
            } else if (tag_filter_available) {
                addFilterChip(tag_filter_available.dataset.tag, 'include');
            } else if (tag_filter_gate) {
                const tag = tag_filter_gate.dataset.tag;
                const currentOpen = state.gateStates.get(tag) || false;
                state.gateStates.set(tag, !currentOpen);
                applyGateState(tag_filter_gate, !currentOpen);
                filterSongs();
            } else if (tag_filter_chip) {
                const tag = tag_filter_chip.dataset.tag;

                if (target.closest('.tag-filter-chip-remove')) {
                    state.tagFilters.delete(tag);
                    tag_filter_chip.remove();
                } else {
                    const current = state.tagFilters.get(tag);
                    const next = current === 'include' ? 'exclude' : 'include';
                    state.tagFilters.set(tag, next);
                    applyChipMode(tag_filter_chip, next);
                }
                renderAvailableTags();
                filterSongs();
            }
        });
    }

    function setViewMode(mode) {
        const prevMode = state.editMode ? 'edit' : (state.moveMode ? 'move' : 'play');
        if (mode === prevMode) return;

        state.moveMode = (mode === 'move');
        state.editMode = (mode === 'edit');

        // Clear selection when leaving edit mode
        if (mode !== 'edit') {
            state.selection.length = 0;
            document.querySelectorAll(".livelist-item.list-group-item-warning").forEach(
                item => item.classList.toggle("list-group-item-warning", false)
            );
        }
        livelist_update_item_numbers();
        update_mode();
    }

    function update_move_to_anchor_visibility() {
        const mode = state.editMode ? 'edit' : (state.moveMode ? 'move' : 'play');
        // Regular items
        document.querySelectorAll('.livelist-item-move-to-anchor').forEach(btn => {
            const item = btn.closest('.livelist-item');
            const isAnchor = item === state.anchorItem;
            btn.classList.toggle('d-none', mode !== 'move' || isAnchor);
        });
        // Break items
        document.querySelectorAll('.livelist-break-move-to-anchor').forEach(btn => {
            const breakEl = btn.closest('.livelist-break');
            const isAnchor = breakEl === state.anchorItem;
            btn.classList.toggle('d-none', mode !== 'move' || isAnchor);
        });
    }

    function update_mode() {
        const mode = state.editMode ? 'edit' : (state.moveMode ? 'move' : 'play');

        // Grip icons (right side): Move mode only
        document.querySelectorAll('.livelist-item-grip').forEach(el => {
            el.classList.toggle('d-none', mode !== 'move');
        });

        // Break grip handles: Move mode only (Set 1 shows as disabled via CSS)
        document.querySelectorAll('.livelist-break .drag-handle').forEach(el => {
            el.classList.toggle('d-none', mode !== 'move');
        });

        // Delete buttons: Edit mode only
        document.querySelectorAll('.livelist-item-delete').forEach(btn => {
            btn.classList.toggle('d-none', mode !== 'edit');
        });

        // Break delete buttons: Edit mode only
        document.querySelectorAll('.livelist-break-delete').forEach(btn => {
            btn.classList.toggle('d-none', mode !== 'edit');
        });

        // Select checkbox / position visibility is handled by livelist_update_item_numbers()

        // Play buttons: Play mode only
        document.querySelectorAll('.livelist-item-play').forEach(btn => {
            btn.classList.toggle('d-none', mode !== 'play');
        });

        // Break clipboard/copy buttons: Play mode only (replaces play button position)
        document.querySelectorAll('.clipboard-copy-break-set').forEach(btn => {
            btn.classList.toggle('d-none', mode !== 'play');
        });

        // Move-to-anchor: Move mode, non-anchor items
        update_move_to_anchor_visibility();

        // Right button group styling — btn-group only in move mode
        // (play: single button with rounded edges; edit: single delete with rounded edges)
        document.querySelectorAll('.livelist-item-btn-group-right').forEach(el => {
            el.classList.toggle('btn-group', mode === 'move');
        });

        // Break right button group styling
        document.querySelectorAll('.livelist-break-btn-group-right').forEach(el => {
            el.classList.toggle('btn-group', mode === 'move');
        });

        // Navbar mode toggle buttons
        const modePlay = document.getElementById('mode-play');
        const modeMove = document.getElementById('mode-move');
        const modeEdit = document.getElementById('mode-edit');

        [modePlay, modeMove, modeEdit].forEach(btn => {
            btn.classList.remove('btn-primary', 'btn-outline-primary');
        });

        if (mode === 'play') {
            modePlay.classList.add('btn-primary');
            modeMove.classList.add('btn-outline-primary');
            modeEdit.classList.add('btn-outline-primary');
        } else if (mode === 'move') {
            modePlay.classList.add('btn-outline-primary');
            modeMove.classList.add('btn-primary');
            modeEdit.classList.add('btn-outline-primary');
        } else {
            modePlay.classList.add('btn-outline-primary');
            modeMove.classList.add('btn-outline-primary');
            modeEdit.classList.add('btn-primary');
        }

        // Apply mode class to livelist for CSS targeting
        const livelistEl = document.getElementById('livelist');
        livelistEl?.classList.toggle('mode-play', mode === 'play');
        livelistEl?.classList.toggle('mode-move', mode === 'move');
        livelistEl?.classList.toggle('mode-edit', mode === 'edit');

        // Nav sections: main nav visible in Play + Move, edit nav in Edit
        document.getElementById('nav-main').classList.toggle('d-none', mode === 'edit');
        document.getElementById('nav-edit').classList.toggle('d-none', mode !== 'edit');
    }

    function handle_move_to_anchor(itemId) {
        const ai = state.anchorItem;
        if (!ai) {
            // Move to top (before first item)
            const firstItem = document.querySelectorAll('.livelist-item')[0];
            if (firstItem) {
                const msg = {
                    moved_ids: [itemId],
                    target_id: parseInt(firstItem.dataset.itemId),
                    before: true,
                    playlist_id: state.currentPlaylist,
                };
                handle_drag_and_drop(msg);
            }
            return;
        }

        let targetId;
        let isBreakAnchor = false;
        if (ai.dataset.setKey) {
            // Virtual Set 1 anchor — move before first song
            const firstItem = document.querySelectorAll('.livelist-item')[0];
            if (firstItem) {
                targetId = parseInt(firstItem.dataset.itemId);
            }
        } else if (ai.dataset.itemId && ai.classList.contains('livelist-break')) {
            // Real break anchor — always insert after the break (= start of set)
            targetId = parseInt(ai.dataset.itemId);
            isBreakAnchor = true;
        } else if (ai.dataset.itemId) {
            targetId = parseInt(ai.dataset.itemId);
        }

        if (targetId == null) return;

        // For break anchors, always insert after the break regardless of sticky state;
        // for regular items, sticky inserts before, non-sticky inserts after.
        const before = isBreakAnchor ? false : state.anchorItemSticky;

        const msg = {
            moved_ids: [itemId],
            target_id: targetId,
            before: before,
            playlist_id: state.currentPlaylist,
        };

        // Anchor advancement for non-sticky mode (same as add_song)
        if (!state.anchorItemSticky) {
            state.lastAction = "add_song";
        }

        handle_drag_and_drop(msg);
    }

    function on_livelist_item_play(pid) {
        state.socket.emit("play_item", { item_id: pid, playlist_id: state.currentPlaylist });
    }

    function selectPlaylist(playlist_id) {
        state.socket.emit("select_playlist", { playlist_id: playlist_id });
    }

    function activatePlaylist(playlist_id) {
        state.socket.emit("activate_playlist", { playlist_id: playlist_id });
        state.socket.emit("select_playlist", { playlist_id: playlist_id });
    }

    function deletePlaylist(id) {
        state.socket.emit("delete_playlist", { playlist_id: id });
    }

    function editPlaylist(id) {
        const qry = `.playlist-btn-select[data-playlist-id="${id}"]`;
        const pn = document.querySelector(qry).querySelector(".playlist-item-name");
        const pd = document.querySelector(qry).querySelector(".playlist-item-date");
        document.getElementById('edit-playlist-id').value = id;
        document.getElementById('edit-playlist-name').value = pn.innerHTML;
        document.getElementById('edit-playlist-date').value = pd.innerHTML;
    }

    function editSong(id) {
        state.edit_song_id = id;
        const song = state.songlist.get(id);
        document.getElementById('edit-song-id').value = song.id;
        document.getElementById('edit-song-name').value = song.name;
        document.getElementById('edit-song-bpm').value = song.bpm;
        edit_song_update_tags(song);
    }

    function edit_song_update_tags(song) {
        const tagedit = document.getElementById('edit-song-tags');
        /* INFO: song can be null */
        tagedit.textContent = "";
        state.tags.forEach(
            item => {
                const parsed = parseTag(item);
                const tag_tmpl = document.getElementById("edit-song-tag-template").content.cloneNode(true);
                const tag_item = tag_tmpl.querySelector('.songlist-item-tag');
                tag_item.textContent = parsed.name;
                tag_item.dataset.name = item;
                if (parsed.defaultOff) {
                    tag_item.classList.add('bi', 'bi-eye-slash');
                }
                if (parsed.advancedOnly) {
                    tag_item.classList.add('bi', 'bi-eye');
                }
                if (song != null && song.rawTags.indexOf(item) >= 0) {
                    tag_item.classList.toggle("btn-primary");
                    tag_item.classList.toggle("btn-outline-primary");
                }
                tagedit.appendChild(tag_item);
            }
        );
    }

    function song_save() {
        song_save_silent();
        bootstrap.Modal.getInstance(document.getElementById('edit-song-modal')).hide();
    }

    function song_save_silent() {
        const id = parseInt(document.getElementById('edit-song-id').value);
        const data = {
            id: id,
            name: document.getElementById('edit-song-name').value,
            bpm: document.getElementById('edit-song-bpm').value,
            tags: state.songlist.get(id).rawTags,
        }

        state.socket.emit("save_song", data);
    }

    function addSongToPlaylist(id) {
        const data = {
            playlist_id: state.currentPlaylist,
            song_id: id,
            before: false,
        };

        let ai = state.anchorItem;
        if (ai == null) {
            let elms = document.querySelectorAll('.livelist-item');
            ai = elms.length > 0 ? elms[0] : null;
            data.before = true;
        }

        if (ai != null && ai.dataset.itemId) {
            data.target_id = parseInt(ai.dataset.itemId);
            // Break anchors always insert after the break (= start of that set)
            // regardless of sticky state; regular items follow sticky semantics
            if (ai.classList.contains('livelist-break')) {
                data.before = false;
            } else {
                data.before = state.anchorItemSticky;
            }
        } else if (ai && ai.dataset.setKey) {
            // Anchor on virtual Set 1 with no real itemId — insert before first song
            let elms = document.querySelectorAll('.livelist-item');
            let first = elms.length > 0 ? elms[0] : null;
            if (first) {
                data.target_id = parseInt(first.dataset.itemId);
                data.before = true;
            }
        }
        state.lastAction = "add_song";
        state.socket.emit("add_song", data);

        document.getElementById('song-filter').value = '';
        filterSongs();

        if (document.getElementById('songlist-panel-pin').classList.contains("bi-pin")) {
            bootstrap.Offcanvas.getInstance(document.getElementById('songlist-panel')).hide();
        }
    }

    function addBreakToPlaylist() {
        const data = {
            playlist_id: state.currentPlaylist,
            before: false,
        };

        let ai = state.anchorItem;
        if (ai == null) {
            // No anchor — insert before the first real item
            const firstItem = document.querySelector('#livelist-items .livelist-item, #livelist-items .livelist-break[data-item-id]');
            if (firstItem && firstItem.dataset.itemId) {
                data.target_id = parseInt(firstItem.dataset.itemId);
                data.before = true;
            }
        } else if (ai.dataset.itemId) {
            data.target_id = parseInt(ai.dataset.itemId);
            if (ai.classList.contains('livelist-break')) {
                data.before = state.anchorItemSticky;
            }
        } else if (ai.dataset.setKey) {
            // Anchor on virtual Set 1 — insert before first song or break
            const firstItem = document.querySelector('#livelist-items .livelist-item, #livelist-items .livelist-break[data-item-id]');
            if (firstItem && firstItem.dataset.itemId) {
                data.target_id = parseInt(firstItem.dataset.itemId);
                data.before = true;
            }
        }

        state.socket.emit("add_break", data);
    }

    function on_livelist_item_delete(id) {
        state.socket.emit("delete_items", { playlist_id: state.currentPlaylist, item_ids: [id] });
    }

    /* Songlist - utils */
    function handleKeypadButton(event) {
        const key = event.target.getAttribute('data-key');
        const filterInput = document.getElementById('song-filter');

        if (!filterInput) return;

        if (key === 'backspace') {
            filterInput.value = filterInput.value.slice(0, -1);
        } else if (key === 'clear') {
            filterInput.value = '';
        } else {
            filterInput.value += key;
        }

        filterInput.dispatchEvent(new Event('input'));
    }

    function handle_songlist_panel_pin(e) {
        e.target.classList.toggle("bi-pin-fill");
        e.target.classList.toggle("bi-pin");
    }

    function update_songlist_panel_edit() {
        const mode = state.songitemEditMode;
        const edit = document.getElementById("songlist-panel-edit");
        edit.classList.toggle("btn-outline-primary", !mode);
        edit.classList.toggle("btn-primary", mode);
        document.querySelectorAll(".songlist-mode-edit").forEach(item => item.classList.toggle("d-none", !mode));
        document.querySelectorAll(".songlist-mode-add").forEach(item => item.classList.toggle("d-none", mode));
    }

    function songIsVisible(songId) {
        const song = state.songlist.get(songId);
        const songTags = song.tags;

        // Layer 1: Gate check - hide songs with closed default-off tags
        for (const [tagName, tagInfo] of state.allTags) {
            if (!tagInfo.defaultOff) continue;
            if (!songTags.includes(tagName)) continue;
            if (!state.gateStates.get(tagName)) return false;
        }

        // Layer 2: Exclude chips
        for (const [tag, mode] of state.tagFilters) {
            if (mode === 'exclude' && songTags.includes(tag)) return false;
        }

        // Layer 2: Include chips
        const includes = [];
        for (const [tag, mode] of state.tagFilters) {
            if (mode === 'include') includes.push(tag);
        }
        if (includes.length === 0) return true;

        if (state.tagFilterCombine === 'AND') {
            return includes.every(t => songTags.includes(t));
        } else {
            return includes.some(t => songTags.includes(t));
        }
    }

    function filterSongs() {
        const nummap = {
            '1': "^\n",
            '2': "2aábcč",
            '3': "3dďeéf",
            '4': "4ghií",
            '5': "5jkl",
            '6': "6mnňoó",
            '7': "7pqrřsš",
            '8': "8tťuúův",
            '9': "9wxyýzž",
            '0': "0 ",
        };
        const filterInput = document.getElementById('song-filter').value;

        let res = ""
        for (let i = 0; i < filterInput.length; i++) {
            res += "[" + (filterInput[i] in nummap ? nummap[filterInput[i]] : filterInput[i]) + "]";
        }

        const re = new RegExp(res, "i");
        const el = document.getElementsByClassName("songlist-item");

        Array.from(el).forEach(e => {
            const textMatch = re.test(e.dataset.songName);
            const tagMatch = songIsVisible(parseInt(e.dataset.songId));
            e.classList.toggle("d-none", !(textMatch && tagMatch));
        });
    }

    function sortSongs(sortBy) {
        const wrapper = document.getElementById("song-list");
        const items = Array.from(wrapper.querySelectorAll(".songlist-item"));
        items.sort(function (a, b) {
            if (sortBy == "alpha") {
                return a.dataset.songName > b.dataset.songName ? 1 : -1;
            } else if (sortBy == "bpm") {
                let va = parseInt(a.dataset.songBpm);
                let vb = parseInt(b.dataset.songBpm);
                if (isNaN(va))
                    return 1;
                if (isNaN(vb))
                    return -1;

                if (va == vb)
                    return 0;
                return va > vb ? 1 : -1;
            } else if (sortBy == "id") {
                let va = parseInt(a.dataset.songId);
                let vb = parseInt(b.dataset.songId);
                return va > vb ? 1 : -1;
            }
        });
        items.forEach(function (item) {
            wrapper.appendChild(item);
        });
    }

    /* Playlist - utils */
    function playlist_new() {
        const nameInput = document.getElementById('new-playlist-name');
        const dateInput = document.getElementById('new-playlist-date');

        if (!nameInput || !nameInput.value.trim()) {
            alert('Please enter a playlist name');
            return;
        }

        const playlistData = {
            band_id: state.currentBand,
            name: nameInput.value.trim(),
            date: dateInput.value || new Date().toISOString().split('T')[0],
        };

        state.socket.emit("create_playlist", playlistData);

        nameInput.value = '';
        dateInput.value = new Date().toISOString().split('T')[0];

        bootstrap.Offcanvas.getInstance(document.getElementById('playlist-panel')).hide();
    }

    function playlist_save() {
        const data = {
            playlist_id: parseInt(document.getElementById('edit-playlist-id').value),
            name: document.getElementById('edit-playlist-name').value,
            date: document.getElementById('edit-playlist-date').value,
        }
        state.socket.emit("save_playlist", data);
        bootstrap.Modal.getInstance(document.getElementById('edit-playlist-modal')).hide();
    }

    function editSort() {
        const data = {
            moved_ids: state.selection.slice(1),
            target_id: state.selection[0],
            before: false,
            playlist_id: state.currentPlaylist,
        };

        state.socket.emit("move_item", data);
        state.selection.length = 0;
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = window.setTimeout(later, wait);
        };
    }
}
