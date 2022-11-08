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

from lona import Route

from database import PlaylistItem
from views import ClientMiddleware, Client, proxy_path
import views

host, port = ('0.0.0.0', 8012)

app = LonaApp(__file__)

class BootstrapThemeHTML(HTML):
    STATIC_FILES = [StyleSheet(
        name='bootstrap-darkly',
        path='static/bootstrap-darkly.min.css',
    )]

app.add_template('lona/frontend.js', """
    lona_context.add_disconnect_hook(function(lona_context, event) {
        document.querySelector('#lona').innerHTML = `Server disconnected <br> Trying to reconnect...`;
        setTimeout(function() {lona_context.reconnect();}, 2000);
    });
""")

#db = Database()
app.routes = [
    Route(proxy_path + '/', views.PlaylistView),
    Route(proxy_path + '/play/<playlistId:.*>', views.PlayView),
    Route(proxy_path + '/sheets/<song>', views.SheetView, interactive=False),
    Route(proxy_path + '/client/', views.Client),
]
# INFO: Doesn't work
#app.settings.INITITAL_SERVER_STATE = {"proxy_path": proxy_path}
app.settings.STATIC_URL_PREFIX = proxy_path + '/static/'
app.settings.MIDDLEWARES = [
        ClientMiddleware,
]
app.add_static_file('lona/style.css', """
.playlistitemnr {pointer-events: none; width:3rem;}
""")
app.run(host=host, port=port, log_level='warn')
