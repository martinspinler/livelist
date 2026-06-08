"""Czech (cs) translations for Livelist."""

TRANSLATIONS: dict[str, str] = {
    # ---- Navigační lišta ----
    "nav_add_song":       "Přidat píseň",
    "nav_playlists":      "Playlisty",
    "nav_live":           "Živě",
    "nav_help":           "Nápověda",

    # ---- Přepínač režimu ----
    "mode_play":          "Hraní",
    "mode_move":          "Přesun",
    "mode_edit":          "Úpravy",

    # ---- Akce v režimu úprav ----
    "action_delete_selected": "Smazat vybrané",
    "action_update_order":    "Aktualizovat pořadí",

    # ---- Panel knihovny písní ----
    "song_library_title":     "Knihovna písní",
    "song_library_search_ph": "Začni psát nebo použij keypad...",
    "sort_alpha":             "A-Z",
    "sort_bpm":               "BPM",
    "sort_id":                "ID",
    "tag_filter_btn":         "Štítky",
    "hidden_songs":           "Skryté písně",
    "filter_and":             "AND",
    "filter_or":              "OR",
    "add_break":              "Přidat set",

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
    "title_move_to_anchor": "Přesunout ke kotvě",
    "title_delete":         "Smazat",
    "title_delete_break":   "Smazat set",
    "title_collapse_set":   "Sbalit set",
    "title_copy_set":       "Kopírovat položky v setu",

    # ---- Systém ukotvení ----
    "anchor_label":         "Kotva",

    # ---- Popisy sad / přerušení ----
    "set_label":            "Set {n}",

    # ---- Okno nápovědy ----
    "help_title":                         "Nápověda",

    "help_livelist_title":                "Livelist (Hlavní zobrazení)",
    "help_livelist_desc":                 "Centrální oblast zobrazuje aktuální playlist jako uspořádaný číslovaný seznam písní. Zobrazení pracuje ve třech režimech, přepínatelných skupinou tlačítek Přehrávání / Přesun / Úpravy v navigační liště.",

    "help_play_mode":                     "Režim hraní (výchozí) — Klepnutí na tlačítko přehrání u libovolné položky ji označí jako akutálně přehrávanou; událost se odešle všem připojeným klientům.",
    "help_move_mode":                     'Režim přesunu — U každé položky se zobrazí úchyt pro přetažení a tlačítko "přesunout ke kotvě" na pravé straně. Písně lze přeskládat přetažením na konkrétní pozici nebo pomocí tlačítka k pozici kotvy.',
    "help_edit_mode":                     "Režim úprav — Slouží pro výběr více položek a následně pro hromadné smazání nebo přehlednější změnu pořadí.",

    "help_set_breaks_title":              "Sety / přestávky",
    "help_set_breaks_desc":               'Pro lepší přehled může být playlist organizován do více setů (např. pro indikaci přestávky), přičemž každý playlist obsahuje alespoň jeden set.',
    "help_add_break":                     'Přidat set — Klepněte na tlačítko "Přidat set" v panelu Knihovna písní pro vložení oddělovače za aktuální pozici kotvy.',
    "help_set_header":                    'Nadpis setu — Každý set zobrazuje: popisek (např. "Set 1"), počet písní, tlačítko kopírování části playlistu do schránky a přepínač pro sbalení/skrytí položek setu pro lepší přehled.',
    "help_collapse":                      "Sbalení — Klepněte na šipku v napisu setu pro sbalení/rozbalení písní v daném setu.",
    "help_anchor_in_set":                 "Kotva — Kotva u nadpisu setu funguje úplně stejně jako pro jednotlivé položky playlistu. Klepněte na hlavičku setu pro nastavení kotvy na danou pozici.",
    "help_reorder_delete_breaks":         "Přeskládání / smazání — V režimu přesunu mají přestávky úchyty pro přetažení; v režimu úprav zobrazují tlačítka smazání. První set nelze smazat.",
    "help_nav_skip_breaks":               "Navigace — Funcke Přehrát další / předchozí automaticky přeskakuje přestávky; ty samozřejmě nelze přehrávat.",

    "help_anchor_title":                  "Systém ukotvení",
    "help_anchor_desc":                   'Kotva určuje, kam se vkládají nové písně a kam se přesouvají položky při použití "přesunout ke kotvě". Má dva stavy, přepínatelné kliknutím na položku:',
    "help_anchor_nonsticky":              "Pohyblivé (⚓↓) — Položky se vkládají/přesouvají za kotvu, poté se kotva posune na novou/přesunutou položku. Umožňuje postupně přidávat položky ZA.",
    "help_anchor_sticky":                 "Stálé (⚓↑) — Položky se vkládají/přesouvají před kotvu a ta zůstává na stejné položce. Umožňuje postupně přidávat položky PŘED.",

    "help_song_library_title":            "Knihovna písní",
    "help_song_library_desc":             "Prohledávatelný a filtrovatelný katalog všech písní v knihovně kapely.",
    "help_search":                        "Hledání — Textový vstup s filtrováním během psaní plus volitelná klávesnice ve stylu T9 pro rychlé vyhledávání.",
    "help_sorting":                       "Řazení — Seřaďte abecedně (A–Z), podle BPM nebo podle ID.",
    "help_tag_filter":                    'Filtrování štítků — Přidejte/odstraňte štítky; přepínejte každý štítek mezi režimem "zahrnout" / "vyloučit". Rozšířené nastavení zobrazuje skryté štítky a přepínač logiky AND/OR.',
    "help_add_to_playlist":               "Přidat do playlistu — Klepněte na píseň pro její přidání do aktuálního playlistu.",
    "help_pin_panel":                     "Připnout panel — Připněte boční panel, aby se nezavřel po přidání písně a umožnil tak přidání více skladeb najednou.",
    "help_library_edit_mode":             "Režim úprav — Přepněte knihovnu do režimu úprav pro vytváření nových písní, úpravu stávajících nebo správu štítků.",

    "help_playlist_manager_title":        "Správa playlistů",
    "help_playlist_manager_desc":         "Spravujte všechny playlisty kapely.",
    "help_playlist_create":               "Vytvořit — Dialog s názvem a datem pro vytvoření nového playlistu.",
    "help_playlist_select":               "Vybrat — Klepněte na playlist pro jeho načtení do hlavního zobrazení pouze pro sebe.",
    "help_playlist_activate":             "Aktivovat — Nastavte playlist jako aktivní playlist kapely (ikona vysílání) i pro všechny ostatní.",
    "help_playlist_edit":                 "Upravit — Přejmenujte playlist nebo změňte datum.",
    "help_playlist_delete":               "Smazat — Odstraňte playlist.",

    # ---- Úvodní stránka ----
    "index_title":          "Livelist",
    "index_subtitle":       "Spolupracujte na playlistu pro koncert vaší kapely živě",
    "index_features":       "Webová aplikace, která kapelám pomáhá organizovat knihovnu písní a spravovat playlisty během živých vystoupení. Všichni členové kapely se mohou připojit současně, podílet se na přípravě playlistu a okamžitě vidět změny od ostatních.",
    "index_select_band":    "Vybrat kapelu",
    "index_choose_band":    "Vyberte již uloženou kapelu pro zobrazení a správu playlistů.",
    "index_bad_access":     "Adresa kapely nebo klíč nefunguje.",
    "index_address":        "Adresa",
    "index_enter_key_for":  "Zadejte klíč pro {addr}:",
    "index_or_access":      "Nebo přejděte na existující pomocí adresy a klíče:",
    "index_go":             "Přejít",
    "index_log_out":        "Odhlásit se z {addr}",

    # ---- Sekce funkcí na úvodní stránce ----
    "feature_realtime_title":   "Spolupráce v reálném čase",
    "feature_realtime_desc":    "Všechny změny playlistu jsou hned zobrazeny všem připojeným členům kapely.",
    "feature_modes_title":      "Tři pracovní režimy",
    "feature_modes_desc":       "Režim hraní pro vystoupení, režim přesunu pro přeskládání a režim úprav pro hromadnou správu.",
    "feature_anchor_title":     "Chytrý systém ukotvení",
    "feature_anchor_desc":      "Flexibilní kotva pro rychlé přeuspořádání s možností přidat/přesunout za/před kotvu.",
    "feature_library_title":    "Prohledávatelná knihovna písní",
    "feature_library_desc":     "Filtrujte podle názvu, BPM nebo štítků s podporou T9 klávesnice a pokročilou AND/OR logikou štítků.",
    "feature_sets_title":       "Možnost více setů",
    "feature_sets_desc":        "Organizujte playlist do přehledných setů s možností kopírováním názvů písní schránky.",
    "feature_live_title":       "Obrazovka Živě",
    "feature_live_desc":        "Zobrazení PDF s notami nebo akordy podobně jako v iReal aplikaci.",
}
