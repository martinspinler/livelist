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
    def __init__(self, song, h):
        Div.__init__(self)
        #self.class_list.append("d-grid")
        #self.class_list.append("d-md-block d-grid")
        self.class_list.append("clearfix")
        self.class_list.append("d-flexlock")
        self.class_list.append("d-md-block")

        name = song.name if len(song.name) <= 30 else song.name[:30] + "..."
        self.btn = SecondaryButton(
                Span(name, _class="d-grid flex-grow-1"),
                handle_click=h,
                _class="flex-grow-1",
                )
        self.song = self.btn.song = song
        self.nodes = [
                self.btn,
                Span(str(song.played), _class="badge bg-primary rounded-pill float-end"),
            ] + ([Span(f"{song.bpm}", _class="bi bi-music-note float-end")] if song.bpm else [])


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

