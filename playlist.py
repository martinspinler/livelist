#!/usr/bin/python3
import argparse
import os
import sys

import lona
from lona import LonaApp
from lona.html import HTML

from offcanvas import Offcanvas

from lona import Route
from lona.static_files import StyleSheet, Script, SORT_ORDER

import views
from views import proxy_path

host, port = ('0.0.0.0', 8012)
#host, port = ('0.0.0.0', 80)

app = LonaApp(__file__)

#class BootstrapThemeHTML(HTML):
#    STATIC_FILES = [StyleSheet(
#        name='bootstrap-darkly',
#        path='static/bootstrap-darkly.min.css',
#    )]

app.add_template('lona/frontend.js', """
    lona_context.add_disconnect_hook(function(lona_context, event) {
        document.querySelector('#lona').innerHTML = `Server disconnected <br> Trying to reconnect...`;
        setTimeout(function() {lona_context.reconnect();}, 2000);
    });
""")

#db = Database()
app.routes = [
    Route(proxy_path + '/band/<bandName:.*>', views.PlaylistView),
    Route(proxy_path + '/', views.PlaylistView),
    Route(proxy_path + '/play/<playlistId:.*>', views.PlayView),
    Route(proxy_path + '/sheets/<song>', views.SheetView, interactive=False),
    Route(proxy_path + '/client/', views.Client),
    Route(proxy_path + '/home/', views.MainView),
]
# INFO: Doesn't work
#app.settings.INITITAL_SERVER_STATE = {"proxy_path": proxy_path}
app.settings.CLIENT_PING_INTERVAL = 600
app.settings.CLIENT_VIEW_START_TIMEOUT = 1
app.settings.STATIC_URL_PREFIX = proxy_path + '/static/'
app.settings.MIDDLEWARES = [
        views.ClientMiddleware,
]
app.STATIC_FILES = [StyleSheet(
        name='bootstrap-darkly',
        path='static/bootstrap-darkly.min.css',
    )]

app.add_static_file('lona/style.css', """
.playlistitemnr {pointer-events: none; width:3rem;}
""")
app.run(host=host, port=port, log_level='warn')
