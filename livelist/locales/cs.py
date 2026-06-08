"""Czech (cs) translations for Livelist."""

TRANSLATIONS: dict[str, str] = {
    # ---- Navigační lišta ----
    "nav_add_song":       "Přidat píseň",
    "nav_playlists":      "Playlisty",
    "nav_live":           "Živě",
    "nav_help":           "Nápověda",

    # ---- Přepínač režimu ----
    "mode_play":          "Hrát",
    "mode_move":          "Přesun",
    "mode_edit":          "Upravit",

    # ---- Akce v režimu úprav ----
    "action_delete_selected": "Smazat vybrané",
    "action_update_order":    "Aktualizovat pořadí",

    # ---- Panel knihovny písní ----
    "song_library_title":     "Knihovna písní",
    "song_library_search_ph": "Hledej nebo použij klávesnici...",
    "sort_alpha":             "A-Z",
    "sort_bpm":               "BPM",
    "sort_id":                "ID",
    "tag_filter_btn":         "Štítky",
    "hidden_songs":           "Skryté písně",
    "filter_and":             "AND",
    "filter_or":              "OR",
    "add_break":              "Přidat přerušení",

    # ---- Panel playlistů ----
    "playlist_panel_title":   "Playlisty",
    "playlist_name_ph":       "Název playlistu",
    "playlist_create":        "Vytvořit",

    # ---- Modální okno úpravy playlistu ----
    "modal_edit_playlist_title": "Upravit playlist",
    "label_name":               "Název",
    "label_date":               "Datum",
    "btn_cancel":               "Zrušit",
    "btn_save_changes":         "Uložit změny",

    # ---- Modální okno úpravy písně ----
    "modal_edit_song_title": "Upravit píseň",
    "label_bpm":            "BPM",
    "label_tags":           "Štítky",

    # ---- Tooltipy / názvy prvků seznamu ----
    "title_play":           "Přehrát",
    "title_move_to_anchor": "Přesunout k ukotvení",
    "title_delete":         "Smazat",
    "title_delete_break":   "Smazat přerušení",
    "title_collapse_set":   "Sbalit sadu",
    "title_copy_set":       "Kopírovat sadu",

    # ---- Systém ukotvení ----
    "anchor_label":         "Ukotvení",

    # ---- Popisy sad / přerušení ----
    "set_label":            "Sada {n}",

    # ---- Modální okno nápovědy ----
    "help_title":                         "Nápověda",

    "help_livelist_title":                "Livelist (Hlavní zobrazení)",
    "help_livelist_desc":                 "Centrální oblast zobrazuje aktuální playlist jako uspořádaný číslovaný seznam písní. Zobrazení pracuje ve třech režimech, přepínatelných skupinou tlačítek Hrát / Přesun / Upravit v navigační liště.",

    "help_play_mode":                     "Režim hraní (výchozí) — Režim pro vystoupení. Klepněte na tlačítko přehrání u libovolné položky pro označení jako aktivní píseň; událost se odešle všem připojeným klientům. Ukotvení je viditelné pro přidávání písní na určitou pozici.",
    "help_move_mode":                     'Režim přesunu — Režim pro přeskládání. Každá položka zobrazuje úchyt pro přetažení a tlačítko "přesunout k ukotvení" na pravé straně. Písně lze přeskládat přetažením nebo přesunem na pozici ukotvení.',
    "help_edit_mode":                     "Režim úprav — Režim správy. Čísla pozic se stávají klikatelnými cíly výběru. Vyberte více položek pro hromadné smazání nebo aktualizaci pořadí.",

    "help_set_breaks_title":              "Přerušení mezi sadami",
    "help_set_breaks_desc":               'Položky přerušení/pauzy rozdělují playlist do sad. Každý playlist začíná hlavičkou "Sada 1", další přerušení lze vložit pro vytvoření dalších sad (Sada 2, Sada 3 atd.).',
    "help_add_break":                     'Přidat přerušení — Klepněte na tlačítko "Přidat přerušení" v panelu Knihovna písní pro vložení oddělovače sad za aktuální pozici ukotvení.',
    "help_set_header":                    'Hlavička sady — Každá sada zobrazuje: popisek (např. "Sada 1"), počet písní, tlačítko kopírování do schránky a přepínání sbalení.',
    "help_collapse":                      "Sbalení — Klepněte na šipku v hlavičce sady pro sbalení/rozbalení písní v dané sadě.",
    "help_anchor_in_set":                 "Ukotvení — Klepněte na hlavičku sady nebo její ikonu ukotvení pro nastavení ukotvení na danou pozici.",
    "help_reorder_delete_breaks":         "Přeskládání/smazání — V režimu přesunu mají přerušení úchyty pro přetažení; v režimu úprav zobrazují tlačítka smazání. Sadu 1 nelze smazat.",
    "help_nav_skip_breaks":               "Navigace — Předchozí/následující přehrávání automaticky přeskakuje položky přerušení; přerušení nelze přehrát.",

    "help_anchor_title":                  "Systém ukotvení",
    "help_anchor_desc":                   'Ukotvení určuje, kam se vkládají nové písně a kam se přesouvají položky při použití "přesunout k ukotvení". Má dva stavy, přepínatelné kliknutím na položku ukotvení:',
    "help_anchor_nonsticky":              "Nelepkavé (⚓↓) — Položky se vkládají/přesouvají za ukotvení, poté se ukotvení posune za novou položku. Umožňuje sekvenční postup.",
    "help_anchor_sticky":                 "Lepkavé (⚓↑) — Položky se vkládají/přesouvají před ukotvení a ukotvení zůstává na místě. Umožňuje hromadění položek na pevné pozici.",

    "help_song_library_title":            "Knihovna písní",
    "help_song_library_desc":             "Prohledávatelný a filtrovatelný katalog všech písní v knihovně kapely.",
    "help_search":                        "Hledání — Textový vstup s filtrováním během psaní plus volitelná klávesnice ve stylu T9 pro rychlé vyhledávání.",
    "help_sorting":                       "Řazení — Seřaďte abecedně (A–Z), podle BPM nebo podle ID.",
    "help_tag_filter":                    "Filtrování štítků — Přidejte/odstraňte štítky; přepínejte každý štítek mezi režimem zahrnutí/vyloučení. Rozšířené nastavení zobrazuje ovládací prvky bran a přepínač logiky AND/OR.",
    "help_add_to_playlist":               "Přidat do playlistu — Klepněte na píseň pro její přidání do aktuálního playlistu.",
    "help_pin_panel":                     "Připnout panel — Připněte boční panel otevřený místo automatického zavírání.",
    "help_library_edit_mode":             "Režim úprav — Přepněte knihovnu do režimu úprav pro vytváření nových písní, úpravu stávajících nebo správu štítků s konvencemi prefixů.",

    "help_playlist_manager_title":        "Správa playlistů",
    "help_playlist_manager_desc":         "Spravujte všechny playlisty kapely.",
    "help_playlist_create":               "Vytvořit — Formulář s názvem a datem pro vytvoření nového playlistu.",
    "help_playlist_select":               "Vybrat — Klepněte na playlist pro jeho načtení do hlavního zobrazení.",
    "help_playlist_activate":             "Aktivovat — Nastavte playlist jako aktivní playlist kapely (ikona vysílání).",
    "help_playlist_edit":                 "Upravit — Přejmenujte playlist nebo změňte datum prostřednictvím modálního okna.",
    "help_playlist_delete":               "Smazat — Odstraňte playlist.",

    # ---- Úvodní stránka ----
    "index_title":          "Livelist",
    "index_subtitle":       "Spolupráce na playlistech pro živé kapely",
    "index_features":       "Webová aplikace v reálném čase, která kapelám pomáhá organizovat knihovnu písní a spravovat setlisty během živých vystoupení. Více členů kapely se může připojit současně a okamžitě vidět změny playlistu.",
    "index_select_band":    "Vybrat kapelu",
    "index_choose_band":    "Vyberte kapelu pro zobrazení a správu playlistů.",
    "index_bad_access":     "Adresa kapely nebo klíč nefunguje.",
    "index_address":        "Adresa",
    "index_enter_key_for":  "Zadejte klíč pro {addr}:",
    "index_or_access":      "Nebo přejděte pomocí adresy a klíče:",
    "index_go":             "Přejít",
    "index_log_out":        "Odhlásit se z {addr}",

    # ---- Sekce funkcí na úvodní stránce ----
    "feature_realtime_title":   "Spolupráce v reálném čase",
    "feature_realtime_desc":    "Všechny změny playlistu jsou okamžitě synchronizovány všem připojeným členům kapely přes WebSocket.",
    "feature_modes_title":      "Tři pracovní režimy",
    "feature_modes_desc":       "Režim hraní pro vystoupení, režim přesunu pro přeskládání a režim úprav pro hromadnou správu.",
    "feature_anchor_title":     "Chytré ukotvení",
    "feature_anchor_desc":      "Flexibilní bod vložení podporující jak sekvenční, tak fixní pracovní postup.",
    "feature_library_title":    "Prohledávatelná knihovna písní",
    "feature_library_desc":     "Filtrujte podle názvu, BPM nebo štítků s podporou T9 klávesnice a pokročilou AND/OR logikou štítků.",
    "feature_sets_title":       "Přerušení mezi sadami",
    "feature_sets_desc":        "Organizujte playlist do sad se sbalitelnými hlavičkami a kopírováním sady do schránky.",
    "feature_live_title":       "Obrazovka Živě",
    "feature_live_desc":        "Čisté zobrazení pouze pro čtení optimalizované pro projekci nebo sdílenou obrazovku, ukazující aktuální píseň v reálném čase.",
}
