from lona.html import NumberInput, TextInput, A, Span, HTML, H1, Div, Node, Widget, Tr, Td, Ul, Li, Hr, Ol, Nav, Img, Small
from lona_bootstrap_5 import (
    BootstrapDiv,
    SecondaryButton,
    SuccessButton,
    PrimaryButton,
    DangerButton,
    Button,
    Modal,
)

from offcanvas import Offcanvas

class PlaylistItemWidget(Li):
    def __init__(self, handler, song, pli):
        super().__init__(Div(_class="btn rounded-pill bg-primary playlistitemnr"),
        SuccessButton(_class="bi bi-play-fill", handle_click=handler.on_play),
        SuccessButton(_class="bi bi-sort-numeric-down sort_number", handle_click=handler.on_sort),
        Div(song.name, _class="flex-grow-1"),
        DangerButton (_class="bi bi-trash btn-edit d-xxl-block", handle_click=handler.on_delete),
        _class="list-group-item gap-3 d-flex")

        self.playlistItem = pli
        self.sort_btn = self.nodes[2]

        if hasattr(song, 'visual'):
            if song.visual == 'yellow':
                self.class_list.append('list-group-item-danger')

    def sort_set(self, active, index = 0):
        s = self.sort_btn
        if active:
            s.set_text(index + 1)
            s.class_list.remove("bi-self-numeric-down")
            s.class_list.remove("btn-success")
            s.class_list.append("btn-primary" if index else "btn-warning")
            # + "bi-arrow-bar-down"
        else:
            s.class_list.append("bi-sort-numeric-down")
            s.class_list.append("btn-success")
            s.class_list.remove("btn-primary")
            #s.class_list.remove("bi-arrow-bar-down")
            s.class_list.remove("btn-warning")
            s.set_text("")


class SonglistItem(Div):
    def __init__(self, panel, song, h, h2):
        Div.__init__(self)
        #self.class_list.append("d-grid")
        #self.class_list.append("d-md-block d-grid")
        self.class_list.append("clearfix")
        self.class_list.append("d-flexlock")
        self.class_list.append("d-md-block")
        self._panel = panel

        name = song.name if len(song.name) <= 30 else song.name[:30] + "..."
        self.btn = SecondaryButton(
                Span(name, _class="d-grid flex-grow-1"),
                handle_click=h,
                _class="flex-grow-1",
                )

        self.song = self.btn.song = song

        self.btn_edit = SecondaryButton(
                #Span(name, _class="d-grid flex-grow-1"),
                handle_click=h2,
                _class="bi bi-pencil float-end",
                )
        self.btn_edit.song = song
        self.bpm = Span(f"{song.bpm}", _class="bi bi-music-note float-end")

        self.nodes = [
                self.btn,
                Span(str(song.played), _class="badge bg-primary rounded-pill float-end"),
                #*[Span(f"{song.bpm}", _class="bi bi-music-note float-end")]*(song.bpm!=None),
                self.btn_edit,
                self.bpm,
            ]
        if not song.bpm:
            self.bpm.hide()

    #def edit(self, e):
    #    self._panel.hide()
    #    self._panel.editSongDialog


class InstrumentSelector(Div):
    def __init__(self):
        Div.__init__(self, _class="dropdown")
        self.nodes = HTML("""<button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenu2" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Instrument</button>
  <div class="dropdown-menu" aria-labelledby="dropdownMenu2">
  </div>""")
        self.menu = self.query_selector('div.dropdown-menu')

def PaginationWidget():
    return HTML("""<ul class="pagination">
    <li class="page-item">
      <a class="page-link disabled" href="#" aria-label="Previous">
        <span aria-hidden="true">&laquo;</span>
      </a>
    </li>
    <li class="page-item"><a class="page-link disabled" href="#">1</a></li>
    <li class="page-item"><a class="page-link disabled" href="#">2</a></li>
    <li class="page-item"><a class="page-link disabled" href="#">3</a></li>
    <li class="page-item">
      <a class="page-link disabled" href="#" aria-label="Next">
        <span aria-hidden="true">&raquo;</span>
      </a>
    </li>
  </ul>""")

class Keypad(Widget):
    nummap = {'1': "^\n", '2': "2aábcč", '3': "3dďeéf", '4': "4ghií", '5': "5jkl", '6': "6mnňoó", '7': "7pqrřsš", '8': "8tťuúův", '9': "9wxyýzž", '0': "0 "}
    keypad_btns = ['1', '2 ABC', '3 DEF', '4 GHI ', '5 JKL', '6 MNO', '7 PQRS', '8 TUV', '9 WXYZ', 'BS', '0', 'Clr']
    def __init__(self):
        btns = [PrimaryButton(t, handle_click=self.on_keypad, _class="btn-lg") for i, t in enumerate(Keypad.keypad_btns)]
        self.nodes = Div([Tr([Td(Div(btns[y*3+x], _class="d-grid p-1"), _class="gap-2") for x in range(3)], _class="gap-2") for y in range(4)])
        self.listeners = []

    def on_keypad(self, ev):
        key = ev.node.get_text()[0]
        [l(key) for l in self.listeners]

class EditSongDialog(Modal):
    def __init__(self, db):
        super().__init__()

        d = Div(_id="editSongDialog")
        d.modal = self
        #self.attributes['id'] = "editSongDialog"
        #self.attributes['id'] = "editSongDialog"

        self._db = db

        self.name = TextInput(placeholder='Name')
        self.tempo = NumberInput(placeholder='Tempo')

        self.set_title("Song edit")
        self.set_body(
            d,
            self.name,
            self.tempo,
        )
        self.set_buttons(
                PrimaryButton("OK", handle_click=lambda x: self.save()),
                SecondaryButton("Cancel", handle_click=lambda x: self.hide()),
        )

    def loadSong(self, song):
        self._song = song

        #s = self._db.songs[self._song]
        s = self._song

        self.name.value = s.name
        if s.bpm: self.tempo.value = s.bpm

        self.show()

    def save(self):
        s = self._song
        s.name = self.name.value
        s.bpm = int(self.tempo.value) if self.tempo.value else None 

        self._db.saveSonglist()
        self.hide()

class EditPlaylistDialog(Modal):
    def __init__(self, db):
        super().__init__()

        d = Div(_id="editPlaylistDialog")
        d.modal = self

        self._db = db

        self.name = TextInput(placeholder='Name')
        self.date = HTML("""<input
            type="datetime-local"
            name="partydate"
            value="2017-06-01T08:30" />""")

        self.set_title("Playlist edit")
        self.set_body(
            d,
            self.name,
            self.date,
        )
        self.set_buttons(
                PrimaryButton("OK", handle_click=lambda x: self.save()),
                SecondaryButton("Cancel", handle_click=lambda x: self.hide()),
        )

    def load(self, playlist):
        self._playlist = playlist

        #s = self._song

        #self.name.value = s.name
        #if s.bpm: self.tempo.value = s.bpm

        self.show()

    def save(self):
        #s = self._song
        #s.name = self.name.value
        #s.bpm = int(self.tempo.value) if self.tempo.value else None 

        #self._db.saveSonglist()
        self.hide()
