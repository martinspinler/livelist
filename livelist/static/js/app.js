"use strict";

/*
TODO: retain songlist filter after songlist update
TODO: handle playlist name/date update in nav/header
TODO: update song name in all clients after one changes
TODO: after delete last, turn off livelist edit mode
*/

function initApplication() {
    const socket = state.io(window.Location.host, state.socket_auth);

    Object.assign(state, {
        editMode: false,
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
    function livelist_update_playing_item(itemId) {
        const old_ie = document.querySelectorAll('.livelist-item');
        const new_ie = document.querySelector(`.livelist-item[data-item-id="${itemId}"]`);
        const old_e = document.querySelectorAll('.livelist-item-play');
        const new_e = document.querySelector(`.livelist-item[data-item-id="${itemId}"] .livelist-item-play`);

        old_ie.forEach(item => {
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
        msg.items.forEach(
            item => {
                /* TODO: 'Break' item should create <div class="card-header">*/
                const tmpl = document.getElementById("livelist-item-template").content.cloneNode(true);
                const item_e = tmpl.querySelector('.livelist-item');
                item_e.dataset.itemId = item.id;
                item_e.dataset.songId = item.song_id;
                item_e.querySelector('.song-name').textContent = item.song.name;
                item_e.querySelector('.song-tags').textContent = item.song.tags.join(",");
                item_e.querySelector('.song-user_id').textContent =
                    (item.song.user_id ? item.song.user_id + ' - ' : '') + (item.song.notes || '');
                item_e.querySelector('.livelist-item-position').textContent = item.position + 1;

                list_e.appendChild(item_e);

                if (prevAnchor != null && item.id == prevAnchor.dataset.itemId) {
                    state.anchorItem = item_e;
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
                    ai = ai.nextSibling;
                }
            }
            state.lastAction = null;
        }
        livelist_item_set_anchor(ai);

        livelist_update_item_numbers();
        livelist_update_playing_item(msg.active_item_id);
        songlist_update_used_items(msg.items);
        update_edit_mode();
    }

    function livelist_update_item_numbers() {
        document.querySelectorAll(".livelist-item").forEach(
            item => item.querySelectorAll(".livelist-item-selectbox").forEach(subitem => {
                const pos = state.selection.indexOf(parseInt(item.dataset.itemId));
                    subitem.innerHTML = pos >= 0 ? ("&nbsp;" + String(pos + 1)) : "";
                    subitem.classList.toggle("btn-outline-warning", pos == -1);
                    subitem.classList.toggle("btn-warning", pos != -1);
                }
            )
        );
    }

    function livelist_item_set_anchor(pi, user_action=false) {
        if (state.anchorItem) {
            state.anchorItem.querySelector(".livelist-item-anchor").classList.add("d-none");
        }
        if (pi == state.anchorItem && user_action) {
            state.anchorItemSticky = !state.anchorItemSticky;
        }

        let ai_el;
        state.anchorItem = pi;
        if (state.anchorItem == null) {
            ai_el = document.getElementById("livelist-header-anchor");
            ai_el.classList.remove("d-none");
        } else {
            document.getElementById("livelist-header-anchor").classList.add("d-none");
            ai_el = pi.querySelector(".livelist-item-anchor");
            ai_el.classList.remove("d-none");
        }
        if (ai_el != null) {
            ai_el.classList.toggle("btn-outline-primary", state.anchorItemSticky);
        }
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
                const qry = `.songlist-item[data-song-id="${item.song_id}"]`;
                document.querySelector(qry)?.classList.add("active");
            }
        );
    }

    function songlist_update(msg) {
        document.getElementById('song-list').innerHTML = "";
        //document.getElementById('tag-filter-active').textContent = "";
        const tag_filter = document.getElementById('tag-filter-list');
        const all_tags = [];

        function add_tag(tag) {
            if (all_tags.indexOf(tag) == -1) {
                all_tags.push(tag);

                const tmpl = document.getElementById("tagfilter-template").content.cloneNode(true);
                const ti = tmpl.querySelector('.tag-filter-item');
                ti.textContent = tag;
                if (tag == "NOT") {
                    ti.dataset.tagType = "NOT";
                } else {
                    ti.dataset.tagType = "";
                }
                tag_filter.appendChild(ti);
            }
        }

        state.songlist = new Map(msg.items.map(s => Array(s.id, s)));
        state.tags = msg.tags;

        tag_filter.innerHTML = "";

        ["NOT"].forEach(item => add_tag(item));

        msg.items.forEach(
            item => {
                const tmpl = document.getElementById("songlist-item-template").content.cloneNode(true);
                const pi = tmpl.querySelector('.songlist-item');

                pi.dataset.songId = item.id;
                pi.dataset.songName = item.name;
                pi.dataset.songBpm = item.bpm;
                songlist_update_used_item(pi);

                pi.querySelector('.songlist-item-name').textContent = item.name;
                pi.querySelector('.songlist-item-meta').textContent =
                    (item.user_id ? item.user_id + ' · ' : '') +
                    (item.bpm ? 'BPM: ' + item.bpm + ' · ' : '');

                item.tags.forEach(
                    tag => {
                        const tag_tmpl = document.getElementById("tagfilter-template").content.cloneNode(true);
                        const tag_item = tag_tmpl.querySelector('.tag-filter-item');
                        tag_item.textContent = tag;
                        pi.querySelector('.songlist-item-tags').appendChild(tag_item);
                        add_tag(tag);
                    }
                );

                document.getElementById('song-list').appendChild(pi);
            }
        );

        edit_song_update_tags(state.songlist.get(state.edit_song_id));
        update_songlist_panel_edit();

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
        state.usedSongs = msg.items.map(item => item.song_id);

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
                pi.querySelector('.playlist-item-songcount').textContent = item.item_count;

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
        document.getElementById('toggle-edit')?.addEventListener('click', toggleEditMode);

        document.querySelectorAll('.keypad-btn').forEach(btn => {
            btn.addEventListener('click', handleKeypadButton);
        });

        document.getElementById('songlist-toggle-keypad').addEventListener('click', () => {
            document.getElementById('keypad-container').classList.toggle('d-none');
        });
        document.getElementById('songlist-song-create').addEventListener('click', handle_songlist_create_song);

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

        function handle_tag_filter_btn(ev) {
            document.getElementById('tag-filter').classList.toggle('d-none');
            document.getElementById('tag-filter-btn').classList.toggle('bi-tags');
            document.getElementById('tag-filter-btn').classList.toggle('bi-tags-fill');
        }
        function handle_livelist_item_number(pi, itemId) {
            if (state.selection.includes(itemId)) {
                const index = state.selection.indexOf(itemId);
                state.selection.splice(index, 1);

                pi.querySelector(".livelist-item-selectbox").textContent = "";

                pi.classList.toggle("list-group-item-warning", false);
            } else {
                state.selection.push(itemId);
                pi.classList.toggle("list-group-item-warning", true);
            }

            state.editMode = state.selection.length != 0;
            update_edit_mode();

            //document.querySelectorAll(".livelist-item.list-group-item-warning").forEach(
            livelist_update_item_numbers();
        }

        function handle_livelist_item_select(pi) {
            if (true || state.editMode == false) {
                livelist_item_set_anchor(pi, true);
            }
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
            } else if (target.classList.contains('livelist-item-selectbox')) {
                handle_livelist_item_number(livelist_item, itemId);
            } else if (target.classList.contains('livelist-item-position')) {
                handle_livelist_item_number(livelist_item, itemId);
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
            const tagName = document.getElementById("edit-song-tag").value;
            state.socket.emit("create_tag", {name: tagName});
        }

        function handle_songlist_create_song(ev) {
            const name = document.getElementById("song-filter").value;
            state.socket.emit("create_song", {name: name});
        }

        // Playlist item actions
        document.addEventListener("click", (e) => {
            const target = e.target;

            const livelist_item = target.closest(".livelist-item");
            const songlist_item = target.closest(".songlist-item");
            const playlist_item = target.closest(".playlist-item");
            const tag_filter_item = target.closest(".tag-filter-item");
            const songlist_item_tag = target.closest(".songlist-item-tag");

            if (livelist_item) {
                handle_livelist_item_click(target, livelist_item, parseInt(livelist_item.dataset.itemId));
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
                if (songlist_item_tag.classList.contains("btn-outline-primary")) {
                    song.tags.splice(song.tags.indexOf(songlist_item_tag.dataset.name), 1);
                } else {
                    song.tags.push(songlist_item_tag.dataset.name);
                }
                song_save();
            } else if (tag_filter_item) {
                if (tag_filter_item.textContent == "NOT") {
                    tag_filter_item.classList.toggle("btn-outline-primary");
                    tag_filter_item.classList.toggle("btn-primary");
                } else {
                    const tag_filter_list = tag_filter_item.closest('#tag-filter-list');
                    const tag_not = tag_filter_list.querySelector('button[data-tag-type="NOT"]');
                    if (tag_filter_item.classList.contains("btn-outline-primary")) {
                        if (tag_not.classList.contains("btn-primary")) {
                            tag_filter_item.classList.toggle("btn-outline-primary");
                            tag_filter_item.classList.toggle("btn-danger");

                        } else {
                            tag_filter_item.classList.toggle("btn-outline-primary");
                            tag_filter_item.classList.toggle("btn-success");
                        }
                    } else {
                        tag_filter_item.classList.toggle("btn-outline-primary");
                        tag_filter_item.classList.toggle("btn-success", false);
                        tag_filter_item.classList.toggle("btn-danger", false);
                    }
                    tag_not.classList.toggle("btn-primary", false);
                    tag_not.classList.toggle("btn-outline-primary", true);

                    /*
                    const tag_filter_active = document.getElementById('tag-filter-active');
                    const tag_filter_list = tag_filter_item.closest('#tag-filter-list');
                    if (tag_filter_list != null) {
                        const ti = tag_filter_item.cloneNode(true);
                        if (tag_filter_list.querySelector('button[data-tag-type="NOT"]').classList.contains("btn-outline-primary")) {
                    //tag_filter_item.classList.toggle("btn-outline-primary");
                            ti.classList.add("text-decoration-line-through");
                        }
                        tag_filter_active.appendChild(ti);
                    } else {
                        tag_filter_active.removeChild(tag_filter_item);
                    }*/

                    filterSongs();
                }
            } else if (target.classList.contains("clipboard-copy-set")) {
                let str = "";
                state.playlist.items.forEach(
                    item => {
                        str += String(item.position + 1) + ". " + item.song.name + "\n";
                    }
                )
                navigator.clipboard.writeText(str);
                e.stopPropagation();
            } else if (target.closest("#livelist-header")) {
                livelist_item_set_anchor(null, true);
            }
        });
    }

    function toggleEditMode() {
        state.editMode = !state.editMode;
        state.selection.length = 0;
        livelist_update_item_numbers();

        if (!state.editMode) {
            document.querySelectorAll(".livelist-item.list-group-item-warning").forEach(
                item => {
                    item.classList.toggle("list-group-item-warning", false);
                }
            );
        }
        update_edit_mode();
    }

    function update_edit_mode() {
        const editButtons = document.querySelectorAll('.livelist-item-delete, .livelist-item-selectbox');

        editButtons.forEach(btn => {
            btn.classList.toggle('d-none', !state.editMode);
        });

        document.querySelectorAll('.livelist-item-positions').forEach(btn => {
            btn.classList.toggle('btn-group', state.editMode);
        });
        document.querySelectorAll('.livelist-item-btn-group-right').forEach(btn => {
            btn.classList.toggle('btn-group', state.editMode);
        });

        // Update button text
        const toggleEditBtn = document.getElementById('toggle-edit');
        toggleEditBtn.textContent = state.editMode ? 'Done' : 'Edit';
        toggleEditBtn.classList.toggle('btn-outline-primary', !state.editMode);
        toggleEditBtn.classList.toggle('btn-outline-success', state.editMode);
        document.getElementById('nav-main').classList.toggle("d-none", state.editMode);
        document.getElementById('nav-edit').classList.toggle("d-none", !state.editMode);
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
                const tag_tmpl = document.getElementById("songlist-tag-template").content.cloneNode(true);
                const tag_item = tag_tmpl.querySelector('.songlist-item-tag');
                tag_item.textContent = item;
                tag_item.dataset.name = item;
                if (song != null && song.tags.indexOf(item) >= 0) {
                    tag_item.classList.toggle("btn-primary");
                    tag_item.classList.toggle("btn-outline-primary");
                }
                tagedit.appendChild(tag_item);
            }
        );
    }

    function song_save() {
        const id = parseInt(document.getElementById('edit-song-id').value);
        const data = {
            id: id,
            name: document.getElementById('edit-song-name').value,
            bpm: document.getElementById('edit-song-bpm').value,
            tags: state.songlist.get(id).tags,
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

        if (ai != null) {
            data.target_id = parseInt(ai.dataset.itemId);
        }
        state.lastAction = "add_song";
        state.socket.emit("add_song", data);

        if (document.getElementById('songlist-panel-pin').classList.contains("bi-pin")) {
            bootstrap.Offcanvas.getInstance(document.getElementById('songlist-panel')).hide();
        }
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

        function songInActiveTags(id) {
            const tfa = document.getElementById('tag-filter-list');
            const songTags = state.songlist.get(id).tags;
            var empty = true;
            var inlist = false;
            tfa.querySelectorAll(".btn-danger").forEach(
                item => {
                    //empty = false;
                    if (songTags.indexOf(item.textContent) >= 0) {
                        inlist = true;
                    }
                }
            );
            if (inlist)
                return false;

            empty = true;
            tfa.querySelectorAll(".btn-success").forEach(
                item => {
                    empty = false;
                    if (songTags.indexOf(item.textContent) >= 0) {
                        inlist = true;
                    }
                }
            );
            if (inlist)
                return true;
            return empty;
        }
        Array.from(el).forEach(
            (e) => {
                if (re.test(e.dataset.songName) && songInActiveTags(parseInt(e.dataset.songId))) {
                    e.classList.remove("d-none");
                } else {
                    e.classList.add("d-none");
                }
            }
        );
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
    }

    function editSort() {
        const data = {
            moved_ids: state.selection.slice(1, 4),
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
