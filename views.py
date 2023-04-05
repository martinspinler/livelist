#!/usr/bin/python3
import argparse
import os
import sys
import json
import yaml
import re
import contextlib
import random
import sqlite3
import subprocess
from pathlib import Path

import lona
import lona.html
import lona.middlewares.sessions
import lona_bootstrap_5
from lona import LonaView, LonaApp
from lona.html import NumberInput, TextInput, A, Span, HTML, H1, Div, Node, Widget, Tr, Td, Ul, Li, Hr, Ol, Nav, Img, Small
from lona_bootstrap_5 import (
    BootstrapDiv,
    SecondaryButton,
    SuccessButton,
    PrimaryButton,
    DangerButton,
    Button,
)
from offcanvas import Offcanvas

from database import *
from widgets import *

proxy_path = '/playlist'

img_cache_path = 'cache/'

db = Database()

class CommonUser():
    pass

class User():
    pass

class MyLonaView(LonaView):
    def trigger_view_event(self, name, data, urls=['/band/', '/client/', '/play/']):
        for url in urls:
            vc = self.server.get_view_class(url=proxy_path + url)
            if vc:
                self.server.fire_view_event(name, data, view_classes=vc)


class PlaylistPanel(Offcanvas):
    def __init__(self, band, on_song, _id):
        self.band = band
        self._on_song = on_song
        Offcanvas.__init__(self, _id)

        self.div_play_list = Div(_class="list-group gap-1")
        for i, p in db.playlist.items():
            if 'deleted' in p: continue
            if p['band'] != self.band: continue
            bt = self._add(i, p)

        self.name_edit = TextInput(placeholder='Name')
        self.hdr = Div(
            self.name_edit,
            PrimaryButton(_class="bi bi-pencil", handle_click=self.on_rename),
            PrimaryButton(_class="bi bi-plus", handle_click=self.on_add),
            PrimaryButton(_class="bi bi-trash", handle_click=self.on_delete),
            PrimaryButton(_class="bi bi-broadcast", handle_click=self.on_broadcast),
        )

        self.set_title("Playlists")
        self.set_body(Div(self.hdr, self.div_play_list))

    def _add(self, i, p):
        bt = PrimaryButton(p['date'] + " " + p['note'], handle_click=self.on_item)
        bt.playlistId = i
        self.div_play_list.nodes.append(Div(bt, _class="list-group-item"))
        return bt

    def on_item(self, ev):
        self.currentItem = ev.node
        self.name_edit.value = ev.node.get_text()
        self._on_song(ev)

    def on_rename(self, ev):
        self.currentItem.nodes[0].set_text(self.name_edit.value)
        db.playlist[self.currentItem.playlistId].note = self.name_edit.value

    def on_add(self, ev):
        index = db.newPlaylist(self.band, self.name_edit.value)
        self._add(index, db.playlist[index])

    def on_copy(self, ev):
        index = db.newPlaylist(self.band, self.name_edit.value)
        self._add(index, db.playlist[index])

    def on_delete(self, ev):
        db.playlist[self.currentItem.playlistId]['deleted'] = True
        self.div_play_list.nodes.remove(self.currentItem.parent)
        db.save()

    def on_broadcast(self, ev):
        db.setActivePlaylist(self.currentBand, self.currentItem.playlistId)


class SonglistPanel(Offcanvas):
    def __init__(self, band, on_song, _id):
        Offcanvas.__init__(self, _id)
        self.currentBand = band
        self.on_song_cb = on_song
        self.use_keypad_filter = True
        self.kp = Keypad()
        self.kp.listeners.append(self.keypad_btns)

        self.div_song_list = Div(_class="list-group gap-1")
        #n = [SonglistItem(db.songs[s], on_song) for s in db.songs]
        #self.div_song_list.nodes = n
        self.on_sort(None)

        self.sort_alp = PrimaryButton(_class="bi bi-sort-alpha-down", handle_click=self.on_sort)
        self.sort_bpm = PrimaryButton(_class="bi bi-sort-numeric-down", handle_click=self.on_sort)

        self.input_filter = TextInput(placeholder='Name', handle_change=self.on_kbf)

        self.kpfs = Small()
        self.set_title("Song list")
        self.set_body(self.kp, self.input_filter, Hr(), Div(self.sort_alp, self.sort_bpm, self.kpfs, _class="d-flex gap-2"), Hr(), self.div_song_list)

        self.kpf = ""
        self.keypad_btns("C")

    def on_kbf(self, ev):
        if ev.data == "":
            self.kpf = ""
            self.use_keypad_filter = True
            self._update_filter(self.kpf)
        else:
            self.kpf = ''.join(filter(lambda x: str.isalnum(x) or x in '\'" ', ev.data))
            self.use_keypad_filter = False
            self._update_filter(self.kpf)

    def on_sort(self, ev):
        n = [SonglistItem(db.songs[s], self.on_song_cb) for s in db.songs if db.songs[s].band == self.currentBand]
        if ev and ev.node == self.sort_bpm:
            n = sorted(n, key=lambda x: x.song.bpm if type(x.song.bpm) == int else 1000)
        self.div_song_list.nodes = n

    def keypad_btns(self, key):
        if not self.use_keypad_filter:
            self.use_keypad_filter = True
            self.kpf = ""

        if key == 'B':
            self.kpf = self.kpf[:-1]
        elif key == 'C':
            self.kpf = ""
        else:
            self.kpf += key
        kf = "".join(["[" + Keypad.nummap[num] + "]" for num in self.kpf])

        self._update_filter(kf)
        kb = {x[0]:x for x in Keypad.keypad_btns}
        self.kpfs.set_text("|".join([kb[num] for num in self.kpf]).replace(" ",""))

    def _update_filter(self, filter_string):
        for n in self.div_song_list.nodes:
            if re.search(filter_string, n.song.name, re.I) != None:
                n.show()
                #n.class_list.append("d-grid")
                n.class_list.append("d-md-block")
            else:
                n.hide()
                #n.class_list.remove("d-grid")
                n.class_list.remove("d-md-block")


class PlaylistView(MyLonaView):
    def on_play(self, ev):
        item = ev.node.parent.playlistItem
        db.set_currentPlaylistItem(self.currentPlaylist, item)
        self.trigger_view_event('play', {'playlistItem': item})

    def on_sort(self, ev):
        item = ev.node.parent
        if item not in self.sort_items:
            item.sort_set(True, len(self.sort_items))
            self.sort_items.append(item)
        else:
            # Update state: remove moving flags
            for ind, i in enumerate(self.sort_items):
                i.sort_set(False)

            # First item is anchor -> cancel action, don't move in this case
            firstItem = self.sort_items.pop(0).playlistItem
            if item.playlistItem != firstItem:
                # TODO: Move handling to Database
                playlist = db.playlist[item.playlistItem.playlistId]['items']
                for i in self.sort_items:
                    playlist.remove(i.playlistItem)

                base_index = playlist.index(firstItem)
                for i in reversed(self.sort_items):
                    playlist.insert(base_index + 1, i.playlistItem)

                db.save()

                self.trigger_view_event('update', {'playlistId': item.playlistItem.playlistId})
            self.sort_items.clear()

    def on_delete(self, ev):
        item = ev.node.parent.playlistItem
        db.deletePlaylistItem(item)
        self.trigger_view_event('delete', {'playlistItem': item})

    def song_delete(self, pli):
        node = [x for x in self.playlist.nodes if x.playlistItem == pli]
        same = [x for x in self.playlist.nodes if x.playlistItem.songId == pli.songId]
        if node: self.playlist.nodes.remove(node[0])
        songNode = [s for s in self.songlist.div_song_list.nodes if s.song.id == pli.songId]
        if songNode and len(same) == 1: songNode[0].btn.class_list.remove("btn-dark")

    def setCurrentPlaylist(self, pid):
        pl = [x for x in self.playlistPanel.div_play_list if x.nodes[0].playlistId == self.currentPlaylist]
        for p in pl: p.class_list.remove("active")

        self.currentPlaylist = pid

        self.btn_play.set_href(f'{proxy_path}/play/{self.currentPlaylist}')

        pl = [x for x in self.playlistPanel.div_play_list if x.nodes[0].playlistId == self.currentPlaylist]
        for item in pl: item.class_list.append("active")
        self.populate_playlist()

    def on_songlist(self, ev):
        song = ev.node.song
        pli = db.newPlaylistItem(self.currentPlaylist, song)
        self.songlist.keypad_btns('C')
        self.trigger_view_event('add', {'playlistItem': pli})

    def play_item(self, item):
        if self.playing:
            self.playing.class_list.remove("active")
            #self.playing.class_list.append("list-group-item-secondary")
        self.playing = [x for x in self.playlist.nodes if x.playlistItem == item][0]
        self.playing.class_list.append("active")

    def add_playlist_item(self, pli):
        song = db.songs[pli.songId]

        songNode = [s for s in self.songlist.div_song_list.nodes if s.song.id == song.id]
        if songNode:
            songNode[0].btn.class_list.append("btn-dark")

        li = PlaylistItemWidget(self, song, pli)
        #self.playlist.nodes.insert(pli.pos, li) # CHECK
        self.playlist.nodes.append(li)

        li.nodes[0].set_text(str(self.playlist.nodes.index(li) + 1))

    def populate_playlist(self):
        self.playlist.nodes.clear()
        songNode = [s.btn.class_list.remove("btn-dark") for s in self.songlist.div_song_list.nodes]

        for pli in db.playlist[self.currentPlaylist]['items']:
            self.add_playlist_item(pli)
        pli = db.get_currentPlaylistItem(self.currentPlaylist)
        if pli:
            self.play_item(pli)

    def hide_edit(self, x):
        items = self.playlist.query_selector_all('button.bi-recycle,button.bi-trash,button.bi-arrow-up,button.bi-arrow-down')
        [f.show() for f in items] if self._e_hidden else [f.hide() for f in items]
        self._e_hidden = not self._e_hidden

    def handle_request(self, request):
        self.currentBand = None
        if 'bandName' in request.match_info:# and request.match_info['playlistId']:
            currentBand = request.match_info['bandName']
            cb = [i for i in db.config['bands'] if db.config['bands'][i]['addr'] == currentBand]
            if cb:
                self.currentBand = int(cb[0]);

        if not self.currentBand:
            self.show("Kapela nebyla nalezena")
            return

        self.set_title("Playlist")

        # Login
        access = db.config['bands'][self.currentBand]['access']
        if isinstance(request.user, lona.middlewares.sessions.AnonymousUser):
            self.set_title("Anonymous Playlist")
            request.user.can_edit = False
            request.user.can_show = False
            #print(request.cookies)
        elif isinstance(request.user, CommonUser):
            #request.user.can_edit = False
            #request.user.can_show = False
            pass
        elif isinstance(request.user, User):
            pass
        



        #if access['edit']

        self._e_hidden = False
        self.playing = None
        self.currentPlaylist = None
        self.sort_items = []

        self.playlist = Ul(_class="list-group gap-2", _id="playlist")
        self.songlist = sl = SonglistPanel(self.currentBand, self.on_songlist, "songlistpanel")
        self.playlistPanel = pp = PlaylistPanel(self.currentBand, lambda ev: self.setCurrentPlaylist(ev.node.playlistId), "playlistpanel")

        self.btn_play = A("Live", _class="btn btn-primary bi bi-file-play", attributes={'href': f'{proxy_path}/play/{self.currentPlaylist}', 'target': "_blank"})

        self.setCurrentPlaylist(int(db.config['bands'][self.currentBand]['lastPlaylist']))# = int(cb[0]);
        self.populate_playlist()
        self.hide_edit(None)

        nav = Nav(
            Button("Add song", _class="btn btn-primary bi bi-plus", attributes={'data-bs-toggle': "offcanvas", 'data-bs-target': "#songlistpanel"}),
            Button("Playlists", _class="btn btn-primary bi bi-list-ul", attributes={'data-bs-toggle': "offcanvas", 'data-bs-target': "#playlistpanel"}),
            self.btn_play,
            Button("Edit", _class="btn btn-primary bi bi-pencil-fill", handle_click=self.hide_edit),
            _class="navbar navbar-expand-lg gap-2"
        )

        html = HTML(
            """<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">""",
            nav,
            self.songlist,
            self.playlistPanel,
            self.playlist,
        )

        self.show(html)

    def on_view_event(self, e):
        if e.name == 'add' and e.data['playlistItem'].playlistId == self.currentPlaylist:
            self.add_playlist_item(e.data['playlistItem'])
        if e.name == 'delete' and e.data['playlistItem'].playlistId == self.currentPlaylist:
            self.song_delete(e.data['playlistItem'])
        if e.name == 'play' and e.data['playlistItem'].playlistId == self.currentPlaylist:
            self.play_item(e.data['playlistItem'])
        if e.name == 'update' and e.data['playlistId'] == self.currentPlaylist:
            self.populate_playlist()

    def on_cleanup(self):
        pass


class PlayView(MyLonaView):
    def on_forward(self, ev):
        self.on_to(+1)
    def on_backward(self, ev):
        self.on_to(-1)
    def on_to(self, offset):
        pli = db.get_currentPlaylistItem(self.activePlaylist)
        item = db.get_playlistItemNeighbour(self.activePlaylist, pli, offset)
        if item != None:
            db.set_currentPlaylistItem(self.activePlaylist, item)
            self.trigger_view_event('play', {'playlistItem': item})

    def handle_request(self, request):
        self.activePlaylist = None
        if 'playlistId' in request.match_info and request.match_info['playlistId']:
            self.activePlaylist = int(request.match_info['playlistId'])

        if self.activePlaylist == None:
            return HTML("No current playlist")

        self.currentSong = Div()

        self.img = Div()
        self.instr_select = InstrumentSelector()

        self.forward = SuccessButton(_class="bi bi-skip-forward-fill push-right", handle_click=self.on_forward)
        self.backward = SuccessButton(_class="bi bi-skip-backward-fill", handle_click=self.on_backward)
        self.pagination = PaginationWidget() 
        nav = Nav(
            self.backward,
            A("Playlist", _class="btn btn-primary bi bi-list-ul", attributes={'href': f'{proxy_path}/', 'target': "_blank"}),
            self.forward,
            self.instr_select,
#            self.pagination,
            Div("Current Playlist: " + db.playlist[self.activePlaylist]['date'] + " | song: ", self.currentSong),
            _class="navbar navbar-expand-lg gap-2"
        )
        pli = db.get_currentPlaylistItem(self.activePlaylist)
        if pli != None:
            #pli = [x for x in db.playlist[self.activePlaylist]['items'] if x.id == pli][0]
            self.loadSong(pli)

        self.update_btns()

        return HTML(nav, self.img)

    def update_btns(self):
        if self.activePlaylist == None:
            return
        ci = db.get_currentPlaylistItem(self.activePlaylist)
        bw, fw = [db.get_playlistItemNeighbour(self.activePlaylist, ci, o) for o in [-1, 1]]
        self.backward.set_text(db.songs[bw.songId].name if bw else "")
        self.backward.class_list.remove("disabled") if bw else self.backward.class_list.append("disabled")
        self.forward.set_text (db.songs[fw.songId].name if fw else "")
        self.forward.class_list.remove("disabled") if fw else self.forward.class_list.append("disabled")
        return

        if ci != None:
            pl = playlist['items']
            pli = [x for x in pl if x.id == ci][0]
            i = pl.index(pli)
            self.backward.set_text(db.songs[pl[i-1].songId].name if i > 0 else "")
            self.backward.class_list.remove("disabled") if i > 0 else self.backward.class_list.append("disabled")
            self.forward.set_text (db.songs[pl[i+1].songId].name if i < len(pl) - 1 else "")
            self.forward.class_list.remove("disabled") if i < len(pl) -1 else self.forward.class_list.append("disabled")

    def on_view_event(self, e):
        if e.name == 'play' and e.data['playlistItem'].playlistId == self.activePlaylist:
            playlistItem = e.data['playlistItem']
            self.loadSong(playlistItem)
            self.update_btns()
        if e.name == 'update' and e.data['playlistId'] == self.activePlaylist:
            self.update_btns()

    def loadSong(self, playlistItem):
        if not hasattr(self, 'currentInstrument'):
            self.currentInstrument = 'Piano'
        self.currentPlaylistItem = playlistItem

        self._currentSong = db.songs[playlistItem.songId]
        song = self._currentSong
        self.currentSong.set_text(song.name)
        self.img.nodes = []

        if song.instruments:
            for i in song.instruments:
                self.instr_select.menu.nodes.append(lona.html.Button(i, _class="dropdown-item", handle_click=self.on_changeInstrument))
        else:
            self.instr_select.menu.nodes.clear()

        self.loadSongInstrument(self.currentInstrument)

    def loadSongInstrument(self, playlistItem):
        song = self._currentSong
        instrument = self.currentInstrument
        filename = song._format.format(prefix=song.prefix, file=song.file, instrument=instrument) if hasattr(song, '_format') else song.filename
        if filename == None or not os.path.isfile(filename):
            self.img.nodes = [Div("No sheet")]
            return

        pages = subprocess.check_output(f'pdfinfo "{filename}" |grep -a Pages:', shell = True).decode()
        pages = int(pages.split(":")[1].strip())
        self.img.nodes = [Img(attributes={'src': proxy_path + "/sheets/" + str(song.id) + f"-{instrument}--{i+1}.jpg"}) for i in range(pages)]

    def on_changeInstrument(self, ev):
        self.currentInstrument = ev.node.get_text()
        self.loadSongInstrument(self.currentPlaylistItem)

class MainView(MyLonaView):
    def handle_request(self, request):
        html = HTML(f"Patrne jsi chtel navstivit <a href='{proxy_path}/band/perfecttime'>Perfect Time</a>")
        self.show(html)

 
class SheetView(MyLonaView):
    def handle_request(self, request):
        p = re.compile(r'(\w+)-(\w*)-(\w*)-(\w*).(\w+)')
        songId, instrument, mod, page, suffix = p.match(request.match_info['song']).groups()
        songId, page = int(songId), int(page)

        song = db.songs[songId]

        fn = song._format.format(prefix=song.prefix, file=song.file, instrument=instrument) if hasattr(song, '_format') else song.filename
        if not fn:
            return None

        ofn = f'{img_cache_path}{songId}-{instrument}-{mod}-{page}'

        if not Path(f"{ofn}-{page}.jpg").is_file():
            cmd = f'pdftoppm -jpeg -singlefile -f {page} -l {page} "{fn}" {ofn}'
            pages = subprocess.check_output(cmd, shell=True)

        return {
            'content_type': 'image/jpeg',
            'body': open(f'{ofn}.jpg', 'rb').read(),
        }

class Client(MyLonaView):
    def on_view_event(self, e):
        if e.name == 'add' and e.data['playlistItem'].playlistId == self.activePlaylist:
            data = JSONEncoder().encode(e.data['playlistItem'])
            self.send_str(f"client:{e.name}:{data}")
        elif e.name == 'delete' and e.data['playlistItem'].playlistId == self.activePlaylist:
            data = JSONEncoder().encode(e.data['playlistItem'])
            self.send_str(f"client:{e.name}:{data}")
        elif e.name == 'play' and e.data['playlistItem'].playlistId == self.activePlaylist:
            data = JSONEncoder().encode(e.data['playlistItem'])
            self.send_str(f"client:{e.name}:{data}")
        elif e.name == "update" and e.data['playlistId'] == self.activePlaylist:
            playlistId = e.data['playlistId']
            data = JSONEncoder().encode({x:y for x,y in db.playlist[playlistId].items()})
            self.send_str(f"client:{e.name}:" + data)

    def handle_request(self, request):
        self.activePlaylist = None

class ClientMiddleware:
    def handle_request(self, data):
        if isinstance(data.view, Client):
            data.connection.view = data.view
            data.view.connection = data.connection
        return data

    def handle_websocket_message(self, data):
        server = data.server
        connection = data.connection
        message = data.message
        if message.startswith("client:"):
            _, cmd, d = message.split(":", 2)
            view = connection.view
            if cmd == "get-songlist":
                js = JSONEncoder().encode({x:y for x,y in db.songs.items()})
                connection.send_str("client:songlist:" + js)
            elif cmd == "get-playlist":
                msg = json.JSONDecoder().decode(d)
                view.activePlaylist = msg['playlistId']
                js = JSONEncoder().encode({x:y for x,y in db.playlist[view.activePlaylist].items()})
                connection.send_str("client:playlist:" + js)
            elif cmd == "add":
                msg = json.JSONDecoder().decode(d)
                pli = db.newPlaylistItem(msg['playlistId'], db.songs[msg['songId']])
                trigger_view_event(server, 'add', {'playlistItem': pli})
            elif cmd == "delete":
                msg = json.JSONDecoder().decode(d)
                pli = [x for x in db.playlist[msg['playlistId']]['items'] if x.id == msg['id']][0]
                trigger_view_event(server, 'delete', {'playlistItem': pli})
            elif cmd == "move":
                msg = json.JSONDecoder().decode(d)
                pli = [x for x in db.playlist[msg['playlistId']]['items'] if x.id == msg['id']][0]
                if db.playlistItemMove(pli, msg['pos'], True):
                    trigger_view_event(server, 'update', msg)
            elif cmd == "play":
                msg = json.JSONDecoder().decode(d)
                offset = msg['off']
                playlistId = msg['playlistId']
                pli = db.get_currentPlaylistItem(playlistId)
                pli = db.get_playlistItemNeighbour(playlistId, pli, offset)
                if pli != None:
                    db.set_currentPlaylistItem(playlistId, pli)
                    trigger_view_event(server, 'play', {'playlistItem': pli})
        return data

def trigger_view_event(server, name, data, urls= ['/band/', '/client/', '/play/']):
    for url in urls:
        vc = server.get_view_class(url=proxy_path + url)
        if vc:
            server.fire_view_event(name, data, view_classes=vc)
