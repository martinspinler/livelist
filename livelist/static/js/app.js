"use strict";

const selCls = "list-group-item-warning";
const nbsp = "&nbsp;";

function pliClassSelected(item) {
    return item.id == state.currentItem ? "active" : "";
}

function pliClassActive(item) {
    return item.id == state.activeItem ? "btn-success" : "btn-outline-success";
}

function plClassSelected(item) {
    return item.id == state.currentPlaylist ? "active" : "";
}

function plClassActive(item) {
    return item.id == state.activePlaylist ? "btn-success" : "btn-outline-success";
}

function siClassUsed(item) {
    const used = state.usedSongs.indexOf(item.id) >= 0;
    return used ? "active" : "";
}

function updatePlaylist(msg) {
    document.getElementById("playlist-items").outerHTML = "";
    mapToTemplate("#playlistItems", msg);

    document.getElementById("playlistHeader").outerHTML = "";
    mapToTemplate("#playlistHeaderTemplate", msg);

    highlightPlayingItem(msg.active_item_id);

    document.querySelectorAll(".song-item").forEach((item) => {
        item.classList.remove("active");
    });
    msg.items.forEach(
        item => {
            const qry = `.song-item[data-song-id="${item.song_id}"]`;
            document.querySelector(qry)?.classList.add("active");
        }
    );
}

function playlist_select(msg) {
    state.playlist = msg;
    state.currentPlaylist = msg.playlist_id;
    state.activeItem = msg.active_item_id;
    state.currentItem = null;
    state.usedSongs = msg.items.map(item => item.song_id);

    updatePlaylist(msg);

    // Update the UI to show the selected playlist
    const playlistButtons = document.querySelectorAll(
        ".playlist-select-btn",
    );
    playlistButtons.forEach((btn) => {
        btn.classList.remove("active");
    });

    const qry = `.playlist-select-btn[data-playlist-id="${msg.playlist_id}"]`;
    document.querySelector(qry)?.classList.add("active");
}

function initApplication(s) {
    const socket = state.io(window.Location.host, {
        auth: {
            band: state.currentBand,
            token: 123,
        },
    });
    state.socket = socket;

    //socket.on("connect", () => {});
    socket.on("item_played", (msg) => highlightPlayingItem(msg.item_id));
    socket.on("playlist_select", (msg) => { playlist_select(msg)});
    socket.on("playlists", (msg) => {
        document.getElementById("playlist-list").outerHTML = "";
        mapToTemplate("#playlists", msg);
    });

    socket.on("playlist_activated", (msg) => {
        //state.currentPlaylist = msg.playlist_id;
        //socket.emit("select_playlist", { playlist_id: state.currentPlaylist });
        document.querySelectorAll(".playlist-select-btn").forEach((btn) => {
            btn.classList.remove("active");
        });
        const qry = `.playlist-select-btn[data-playlist-id="${msg.playlist_id}"]`;
        document.querySelector(qry).classList.add("active");
    });

    socket.on("playlist_updated", (msg) => {
        if (state.currentPlaylist == msg.playlist_id) {
            updatePlaylist(msg);
        }
    });

    socket.on("playlist_created", (msg) => {
       playlist_select(msg);
    });

    setupEventListeners();
    initDragAndDrop(state);

    window.addEventListener("DOMContentLoaded", function () {
        socket.emit("get_playlists", {});
        socket.emit("select_playlist", { playlist_id: state.currentPlaylist });
    });
}

function setupEventListeners() {
    document.getElementById('toggle-edit')?.addEventListener('click', toggleEditMode);

    document.querySelectorAll('.keypad-btn').forEach(btn => {
        btn.addEventListener('click', handleKeypadButton);
    });

    document.getElementById('toggle-keypad')?.addEventListener('click', () => {
        document.getElementById('keypad-container')?.classList.toggle('d-none');
    });

    document.getElementById('song-filter').addEventListener('input', debounce(filterSongs, 200));
    document.getElementById('sort-alpha').addEventListener('click', () => sortSongs('alpha'));
    document.getElementById('sort-bpm').addEventListener('click', () => sortSongs('bpm'));
    document.getElementById('sort-id').addEventListener('click', () => sortSongs('id'));
    document.getElementById('tag-filter').addEventListener('change', filterSongs);
    document.getElementById('create-playlist-btn').addEventListener('click', createNewPlaylist);
    document.getElementById('save-playlist-changes').addEventListener('click', savePlaylist);
    document.getElementById('edit-sort').addEventListener('click', editSort);

    // Playlist item actions
    document.addEventListener("click", (event) => {
        const target = event.target;
        let p;

        if (target.classList.contains("playlist-item-play")) {
            const itemId = target.getAttribute("data-item-id");
            if (itemId) onPlayItem(parseInt(itemId));
        } else if (target.classList.contains("delete-item-button")) {
            const itemId = target.getAttribute("data-item-id");
            if (itemId) deleteItem(parseInt(itemId));
        } else if (target.classList.contains("edit-item-button")) {
            const itemId = target.getAttribute("data-item-id");
            if (itemId) editItem(parseInt(itemId));
        } else if (target.classList.contains("song-item")) {
            const songId = target.getAttribute("data-song-id");
            if (songId) addSongToPlaylist(parseInt(songId));
            //} else if (target.classList.contains('playlist-select-btn')) {
        } else if (target.classList.contains("activate-playlist-btn")) {
            const playlistId = target.closest(".playlist-select-btn").getAttribute("data-playlist-id");
            if (playlistId) activatePlaylist(parseInt(playlistId));
            event.stopPropagation();
        } else if (target.classList.contains("delete-playlist-btn")) {
            const playlistId = target.closest(".playlist-select-btn").getAttribute("data-playlist-id");
            if (playlistId) deletePlaylist(parseInt(playlistId));
            event.stopPropagation();
        } else if (target.classList.contains("edit-playlist-btn")) {
            const playlistId = target.closest(".playlist-select-btn").getAttribute("data-playlist-id");
            if (playlistId) editPlaylist(parseInt(playlistId));
            event.stopPropagation();
        } else if ((p = target.closest(".playlist-select-btn"))) {
            const playlistId = p.closest(".playlist-select-btn").getAttribute("data-playlist-id");
            if (playlistId) selectPlaylist(parseInt(playlistId));
            event.stopPropagation();
        } else if (target.classList.contains('item-position')) {
            target.parentElement.classList.toggle("list-group-item-warning");
        } else {
            const pi = target.closest(".playlist-item");
            if (pi) {
                if (state.editMode == false) {
                    //state.selectionMode = "single";
                    //state.selectionMode = state.editMode ? "multi" : "single";
                    //pi.classList.toggle("active");
                    if (state.currentItem == pi) {
                        pi.classList.remove("active");
                        state.currentItem = null;
                    } else {
                        if (state.currentItem) {
                            state.currentItem.classList.remove("active");
                        }
                        state.currentItem = pi;
                        //state.currentItem = parseInt(pi.dataset.itemId);
                        pi.classList.add("active");
                    }
                    if (state.currentItem) {
                        document.getElementById("song-insert-after").removeAttribute("disabled")
                        document.getElementById("song-insert-before").removeAttribute("disabled")
                    } else {
                        document.getElementById("song-insert-after").setAttribute("disabled", "disabled")
                        document.getElementById("song-insert-before").setAttribute("disabled", "disabled")
                    }
                    //state.selection.push(parseInt(pi.dataset.itemId));
                } else if (false && state.selectionMode === "single") {
                    if (state.selection.includes(parseInt(pi.dataset.itemId))) {
                        state.selection.length = 0;
                        state.selectionMode = "none";
                        pi.classList.toggle(selCls);
                    } else {
                        document.querySelectorAll(".playlist-item." + "list-group-item-primary").forEach(
                            (item) => item.classList.remove(selCls)
                        );

                        state.selection.length = 0;
                        pi.classList.toggle(selCls);
                        state.selection.push(parseInt(pi.dataset.itemId));
                    }
                } else if (state.selectionMode === "multi") {
                    if (state.selection.includes(parseInt(pi.dataset.itemId))) {
                        const index = state.selection.indexOf(parseInt(pi.dataset.itemId));
                        state.selection.splice(index, 1);

                        pi.querySelectorAll(".item-selectbox").forEach(
                            subitem => {
                                subitem.textContent = "";
                                subitem.classList.toggle("bi-square");
                                subitem.classList.toggle("bi-check-square");
                                //subitem.classList.toggle("sort-numeric-down");
                            }
                        );
                    } else {
                        state.selection.push(parseInt(pi.dataset.itemId));
                    }

                    pi.classList.toggle(selCls);
                    document.querySelectorAll('.playlist-item.' + selCls).forEach(
                        item => item.querySelectorAll(".item-selectbox").forEach(
                            subitem => subitem.innerHTML = nbsp + String(state.selection.indexOf(parseInt(item.dataset.itemId)) + 1)
                        )
                    );
                }
            }
        }
    });
}

function toggleEditMode() {
    state.editMode = !state.editMode;

    // Show/hide edit buttons
    const editButtons = document.querySelectorAll('.edit-item-button, .delete-item-button, .item-selectbox');

    editButtons.forEach(btn => {
        if (state.editMode) {
            btn.classList.remove('d-none');
        } else {
            btn.classList.add('d-none');
        }
    });

    // Update button text
    const toggleEditBtn = document.getElementById('toggle-edit');
    if (toggleEditBtn) {
        toggleEditBtn.textContent = state.editMode ? 'Done' : 'Edit';
        toggleEditBtn.classList.toggle('btn-outline-primary', !state.editMode);
        toggleEditBtn.classList.toggle('btn-outline-success', state.editMode);
    }
}

function onPlayItem(pid) {
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
    const qry = `.playlist-select-btn[data-playlist-id="${id}"]`;
    const pn = document.querySelector(qry).querySelector(".list-playlist-name");
    const pd = document.querySelector(qry).querySelector(".list-playlist-date");
    document.getElementById('edit-playlist-id').value = id;
    document.getElementById('edit-playlist-name').value = pn.innerHTML;
    document.getElementById('edit-playlist-date').value = pd.innerHTML;
}

function addSongToPlaylist(id) {
    const data = { playlist_id: state.currentPlaylist, song_id: id };
    if (state.currentItem && !document.getElementById('song-insert-end').checked) {
        data.target_id = parseInt(state.currentItem.dataset.itemId);
        data.before = document.getElementById('song-insert-before').checked;
    }
    state.socket.emit("add_song", data);
}

function deleteItem(id) {
    state.socket.emit("delete_item", { playlist_id: state.currentPlaylist, item_id: id });
}

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

function filterSongs() {
    const nummap = { '1': "^\n", '2': "2aábcč", '3': "3dďeéf", '4': "4ghií", '5': "5jkl", '6': "6mnňoó", '7': "7pqrřsš", '8': "8tťuúův", '9': "9wxyýzž", '0': "0 " }
    const filterInput = document.getElementById('song-filter').value;

    let res = ""
    for (let i = 0; i < filterInput.length; i++) {
        res += "[" + (filterInput[i] in nummap ? nummap[filterInput[i]] : filterInput[i]) + "]";
    }

    const re = new RegExp(res, "i");
    const el = document.getElementsByClassName("song-item");
    Array.from(el).forEach(
        (e) => {
            if (re.test(e.dataset.songName)) {
                e.classList.remove("d-none");
            } else {
                e.classList.add("d-none");
            }
        }
    );
}

function sortSongs(sortBy) {
    const wrapper = document.querySelector("#song-list");
    const items = Array.from(wrapper.querySelectorAll(".song-item"));
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

function createNewPlaylist() {
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

    const offcanvas = bootstrap.Offcanvas.getInstance(document.getElementById('playlist-panel'));
    offcanvas?.hide();
}

function savePlaylist() {
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
    /* TODO: CLEAR SELECTION! to enable next selection */
    state.socket.emit("move_item", data);
}

function highlightPlayingItem(itemId) {
    const playingItems = document.querySelectorAll('.playlist-item.playing');
    playingItems.forEach(item => item.classList.remove('playing'));

    const activeItem = document.querySelector(`.playlist-item[data-item-id="${itemId}"]`);
    activeItem?.classList.add('playing');
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
