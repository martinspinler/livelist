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
from datetime import date

from pathlib import Path

import lona
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

from lona.static_files import StyleSheet, Script, SORT_ORDER

class PlaylistItem():
    def __repr__(self):
        return str(self.songId)

class Song():
    @classmethod
    def from_yaml(cls, loader, node):
        s = cls()
        attrs = ['id', 'name', 'file', 'store', 'notes', 'bpm', 'instruments', 'visual']
        [setattr(s, x, node[x]) for x in attrs if x in node]
        [setattr(s, x, None) for x in attrs if x not in node]

        # Temporary conversion
        #if 'Tempo' in node: s.bpm = node['Tempo']
        #if 'Notes' in node: s.notes = node['Notes']
        s.played = 0
        return s

    @classmethod
    def to_yaml(cls, dumper, data):
        node = data.__dict__.copy()
        exclude = ['played', 'filename']
        for i in data.__dict__:
            if node[i] == None or i in exclude:
                del node[i]
        return node

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Song):
            return {x: getattr(obj, x) for x in ['name', 'file', 'filename', 'store', 'notes', 'bpm', 'played']}
        if isinstance(obj, PlaylistItem):
            return {x: getattr(obj, x) for x in ['id', 'playlistId', 'songId']}
        return json.JSONEncoder.default(self, obj)

class Database():
    def __init__(self):
        self.pli_counter = 1

        self.config = yaml.load(open('config.yaml', 'r').read(), yaml.Loader)

        songs = yaml.load(open('songs.yaml', 'r').read(), yaml.Loader)
        self.songs = {int(s['id']):Song.from_yaml(None, s) for s in songs}

        for song in self.songs.values():
            store = (self.config['stores'][song.store]) if song.store != None else (self.config['stores'][self.config['defaultStore']])
            song.filename = self.config['prefixes'][store['prefix']] + store['path'] + song.file + store['suffix'] if song.file != None else None

            if 'format' in store:
                song.prefix = self.config['prefixes'][store['prefix']]
                song._format = store['format']
                #song._format = song.format + store['path'] + song.file + store['suffix'] if song.file != None else None

        self.playlist = yaml.load(open('playlist.yaml', 'r').read(), yaml.Loader)

        for p in self.playlist.values():
            if not hasattr(p, 'currentItemId'):
                p['currentItemId'] = None

        for p in self.playlist.values():
            for i in range(len(p['items'])):
                pli = p['items'][i]
                self.songs[pli.songId].played += 1
                p['items'][i].id = self.pli_counter
                #self.songs[i.songId].played += 1
                self.pli_counter += 1

        self.save()

    def save(self):
        with open('playlist.yaml', 'w') as yaml_file:
            yaml.dump(self.playlist, yaml_file, default_flow_style=False)

    def newPlaylist(self, band, name):
        index = len(self.playlist) + 1
        assert index not in self.playlist
        p = self.playlist[index] = {}

        p['id'] = index
        p['band'] = band
        p['currentItemId'] = None
        p['date'] = str(date.today().strftime("%Y-%m-%d"))
        p['items'] = []
        p['note'] = name

        self.save()
        return index

    def newPlaylistItem(self, pl, song):
        item = PlaylistItem()
        item.id = self.pli_counter
        item.playlistId = pl
        item.songId = song.id
        item.played = False
        #item.pos = len(self.playlist[pl]['items'])
        self.pli_counter += 1

        #self.playlist[pl]['items'][item.id] = item
        self.playlist[pl]['items'].append(item)

        self.save()

        return item

    def deletePlaylistItem(self, pli):
        i = self.playlist[pli.playlistId]['items'].index(pli)
        del self.playlist[pli.playlistId]['items'][i]
        #del self.playlist[pli.playlistId]['items'][pli.id]

        self.save()

    def playlistItemMove(self, item, new_index, relative=False):
        pl = self.playlist[item.playlistId]['items']
        index = pl.index(item) # item.pos
        if relative:
            if index + new_index not in range(0, len(pl) + 1):
                return False
            pl.pop(index)
            pl.insert(index + (-1 if new_index < 0 else 1), item)
        else:
            i = pl.pop(index)
            pl.insert(new_index, item)

        self.save()
        return True

    def get_currentPlaylistItem(self, playlistId):
        playlist = self.playlist[playlistId]
        pl = playlist['items']
        ci = playlist['currentItemId']
        if ci == None:
            return None
        pli = [x for x in pl if x.id == ci]
        # Can be deleted
        if pli:
            return pli[0]
        return None

    def set_currentPlaylistItem(self, playlistId, item):
        playlist = self.playlist[playlistId]
        pl = playlist['items']
        playlist['currentItemId'] = item.id

    def get_playlistItemNeighbour(self, playlistId, pli, offset):
        playlist = self.playlist[playlistId]
        if pli == None:
            #i = len(playlist['items']) if offset < 0 else -offset
            i = -1 if offset < 0 else -offset
        else:
            i = playlist['items'].index(pli)
        if i + offset not in range(len(playlist['items'])):
            return None
        else:
            return playlist['items'][i + offset]

    #def get_currentPlaylistItem(self, playlistId):
    #    playlist  = db.playlist[playlistId]
    #    ci = pli['currentItemId']
