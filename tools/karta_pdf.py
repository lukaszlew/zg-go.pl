#!/usr/bin/env python3
"""Karta gracza klubu Semedori (pionowe A4) — biblioteka + generator karta.pdf.

Uruchomienie:  python3 tools/karta_pdf.py   (zapisuje puste karty w korzeniu repo:
karta.pdf w kolorach strony i karta-cb.pdf czarno-biala, na drukarke laserowa i ksero)
Jako biblioteka: generuj_karte(sciezka, [KartaDane(...), ...], paleta) — karta na
strone, z wypelnionym naglowkiem i wierszami gier (np. karty przykladowe).
Wymaga: reportlab, czcionki DejaVu (pakiet fonts-dejavu).
"""

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from wyrownanie.tabela_html import PLANSZE, siatka
from zasady import KOLUMNY, ZASADY, w_kolumnie

PAGE_W, PAGE_H = A4                     # 210 x 297 mm, pion
MARGIN = 10 * mm                        # margines zewnetrzny strony

CZERN = HexColor("#000000")
BIEL = HexColor("#ffffff")              # papier; takze napis na plakietce nazwy planszy


@dataclass(frozen=True)
class Paleta:
    """Wszystkie kolory karty w jednym miejscu; kazda draw_* dostaje ja jawnie.

    Dwie instancje nizej: KOLOROWA (barwy strony) i CZARNO_BIALA. Tla w wersji
    czarno-bialej sa po prostu biale — rysuja sie pod wszystkim innym, wiec biel
    na bialym papierze znaczy "bez tla", a kod nie potrzebuje osobnej galezi.
    """
    tusz: Color          # tekst, krawedzie, wpisy
    przygaszony: Color   # etykiety rubryk, punktory sciagi, stopka
    siatka: Color        # wewnetrzne linie siatki (jasniejsze od krawedzi)
    tytul: Color         # "Karta gracza"
    linia: Color         # kreski pod tytulem i tytulami sciagi, rozdzielacze brzegow siatek
    tlo_naglowka: Color  # naglowek tabeli gier
    tlo_wyniku: Color    # rubryka "wynik" na calej wysokosci tabeli
    tlo_brzegu: Color    # brzegi siatek wyrownania (ruchy, jency)
    rog: Color           # podpis rogu siatki ("↓ ruchy", "← jency")
    sila: Color          # wszystko, co niesie sile


KOLOROWA = Paleta(
    tusz=HexColor("#1a1a1a"),
    przygaszony=HexColor("#555555"),
    siatka=HexColor("#9a9a9a"),
    tytul=HexColor("#6b6b6b"),          # --muted ze style.css (kolor tytulow strony)
    linia=HexColor("#d9c896"),          # --rule ze style.css
    tlo_naglowka=HexColor("#d9c896"),   # --rule ze style.css
    # tlo rubryki "wynik": ten sam zloty co naglowek, rozcienczony do 45% na bialym.
    # Na drukarce czarno-bialej zostaje z tego okolo 10% szarosci — rubryka dalej
    # odstaje, a wpis olowkiem jest czytelny.
    tlo_wyniku=HexColor("#f0e6cd"),
    # Brzegi siatek wyrownania: na stronie to --rule zmieszane w 45% z tlem, wiec i tu
    # ta sama, jasniejsza wersja — pelna sila przygniatala liczby.
    tlo_brzegu=HexColor("#eee6d0"),
    # Podpis rogu ("↓ ruchy", "← jency"): na stronie --fg z opacity 0.7 na tle brzegu,
    # czyli dokladnie ten kolor. Drobniej i bledziej niz liczby, bo to podpis.
    rog=HexColor("#585449"),
    sila=HexColor("#2e7d32"),           # --kolor-sily ze style.css
)

# Bez jednej szarosci: na ksero i drukarce laserowej kazdy polton wychodzi
# inaczej, a czysta czern i biel zawsze tak samo. Co w kolorze rozni sie barwa
# (sila, podpisy, cienkie linie), tu rozni sie juz tylko grubosc kreski i
# pogrubienie pisma.
CZARNO_BIALA = Paleta(
    tusz=CZERN, przygaszony=CZERN, siatka=CZERN, tytul=CZERN, linia=CZERN,
    tlo_naglowka=BIEL, tlo_wyniku=BIEL, tlo_brzegu=BIEL, rog=CZERN, sila=CZERN,
)
assert {kolor.hexval() for kolor in vars(CZARNO_BIALA).values()} <= {CZERN.hexval(), BIEL.hexval()}, \
    "paleta czarno-biala nie ma prawa znac innych kolorow niz czern i biel"

FONT = "DejaVu"
FONT_BOLD = "DejaVu-Bold"
FONT_SERIF = "DejaVu-Serif"
FONT_HAND = "Caveat"                    # "odreczne" wpisy na kartach przykladowych
HAND_FS = 14                            # rozmiar wpisow w wierszach
HAND_FS_FIELDS = 16                     # rozmiar wpisow w rubrykach naglowka

WERSJA = "22.08.2026k"                   # stopka karty; podbij przy zmianie zasad/ukladu

# Obcy klub: jedyne, co jest w karcie lokalne, to nazwa w naglowku (draw_title)
# i adres w stopce oraz w kodzie QR (draw_sciaga). Gdy zglosi sie pierwszy klub,
# wyciagnac te trzy napisy do parametru wiersza polecen zamiast kopiowac plik.
ROWS = 20                               # trzy siatki wyrownania i 11 zasad w sciadze kosztuja reszte strony
# 7,7 mm zamiast 8: jedenasta zasada wypchnela stopke poza strone, a wiersz nizszy
# o 0,3 mm dalej z zapasem miesci odreczny wpis (Caveat 14 pt to okolo 4,9 mm).
ROW_H = 7.7 * mm
HEAD_H = 13 * mm
NICK_MAX = 40 * mm                      # nick nie zabiera calej reszty szerokosci
HEAD_FS = 6.0                           # naglowki kolumn (wersaliki)
SUB_FS = 5.2                            # naglowki podkolumn (wersaliki)

# INWARIANT: nazwy rubryk/kolumn (FIELDS, COLUMNS) musza byc zgodne z terminologia
# przykladu i zasad na ranking.html — sprawdzaj przy kazdej edycji. Karta moze
# nazwe skrocic, gdy grupa daje kontekst ("roznica" pod "przeciwnik"), ale nie
# moze jej zmienic.
# (Tresc sciagi nie wymaga juz czujnosci: idzie z zasady.py, pilnuje jej test_zasady.py.)
#
# (naglowek grupy, [(podkolumna, szerokosc)]) — pojedyncza podkolumna "" = kolumna
# bez podzialu; szerokosc 0.0 = reszta szerokosci karty (nick przeciwnika)
COLUMNS: list[tuple[str, list[tuple[str, float]]]] = [
    ("data", [("", 9 * mm)]),
    ("moja\nsiła", [("", 11 * mm)]),
    # "różnica" bez dopowiedzenia: stoi w grupie "przeciwnik", tuż obok jego siły,
    # więc nie ma czego mylić, a kolumna schodzi o jedno słowo węziej
    ("przeciwnik", [("nick", 0.0), ("siła", 8 * mm), ("różnica", 11 * mm)]),
    # "dla Czarnego" raz, w naglowku grupy — podkolumny zostaja krotkie
    ("wyrównanie dla Czarnego", [("startowe\nruchy", 17 * mm), ("dodatkowi\njeńcy", 19 * mm)]),
    # K u kalibrowanego, P u jego przeciwnika, w zwyklej grze myslnik; ostatnia
    # rubryka wypelniana przed pierwszym ruchem, wiec zamyka srodkowa sekcje karty
    ("typ gry", [("", 15 * mm)]),
    ("wynik", [("", 12 * mm)]),
    ("zmiana\nsiły", [("", 12 * mm)]),
    ("nowa\nsiła", [("", 12 * mm)]),
]

# przed tymi grupami biegnie gruba kreska — sekcje jak w przykladzie na stronie:
# przed gra | przeciwnik, roznica i wyrownanie | po grze
THICK_BEFORE = {"przeciwnik", "wynik"}

# Nadruk planszy w naglowku karty: kazda w swojej kratce, zakresla sie jedna.
# Trzy kratki zamiast jednego napisu, bo kolko wokol nazwy w ciagu bylo mylace —
# przy "13×13 · 19×19" nie bylo widac, gdzie konczy sie jedna nazwa, a zaczyna druga.
PLANSZE_KARTY: tuple[str, ...] = ("9×9", "13×13", "19×19")
PLANSZA_FS = 9                          # nadruk wyraznie wiekszy od etykiet rubryk
KRATKA_PLANSZY_H = 5.4 * mm
KRATKA_PLANSZY_GAP = 2.0 * mm           # tyle, zeby kolko nie dotykalo sasiadki
KRATKA_PLANSZY_MARGINES = 1.5 * mm

@dataclass(frozen=True)
class Wiersz:
    """Jedna gra na karcie; wartosci jako napisy, dokladnie jak wpisalby je gracz."""
    data: str
    moja_sila: str
    przeciwnik_nick: str
    sila_przeciwnika: str
    roznica: str
    ruchy: str              # startowe ruchy Czarnego (1 = gra rowna)
    jency: str              # dodatkowi jency dla Czarnego (liczba ujemna = dla Bialego)
    typ_gry: str            # K, P albo myslnik
    wynik: str
    zmiana: str
    nowa_sila: str


@dataclass(frozen=True)
class KartaDane:
    """Wypelnienie naglowka karty + wiersze gier; cala karta dotyczy jednej planszy."""
    nick: str
    plansza: str            # "9×9" | "13×13" | "19×19" — zakreslana w naglowku
    wiersze: list[Wiersz]


# Tytul kolumny sciagi dostaje kolor sily, gdy o niej mowi. Wersaliki, bo tak sie
# je rysuje; formy odmienione, bo nazwy kolumn sa po polsku.
SILA_W_NAZWIE = {"SIŁA", "SIŁY"}

# Sciaga czyta sie kolorem: zielone niesie sile, pogrubione to pozostale liczby
# (progi i wpisy w punktach). Slowo "sila" znaczy sile w kazdej kolumnie, ale
# liczba juz nie — "20 punktow" to punkty, a "+1" to sila — wiec liczby zielenieja
# tylko w tych kolumnach, w ktorych mowa o zmianie sily.
SCIAGA_FS = 6
SILA_SLOWA = {"siła", "siły", "siłę", "sile", "siłą"}
SILA_KOLUMNY = {"zmiana siły", "typ gry"}

# indeksy podkolumn (w kolejnosci COLUMNS) niosace sile — one, ich naglowki i
# wpisy w nich ida kolorem sily
SILA_W_RUBRYCE = {1, 3, 4, 9, 10}   # moja sila, sila przeciwnika, roznica, zmiana, nowa

# sciaga na dole karty: (tytul kolumny, [zasada, ...]); kolumny w rytmie
# wypelniania karty (wyrownanie -> wynik -> zmiana sily); siatki rysuje draw_siatki
# stoi w srodkowej kolumnie "wynik", bo ta ma najmniej zasad i najwiecej luzu.
# Tresc pochodzi w calosci z zasady.py — sciaga to dokladnie zasady ze strony,
# nic wiecej i nic mniej.
SCIAGA: list[tuple[str, list[str]]] = [
    (kolumna, w_kolumnie(kolumna)) for kolumna in KOLUMNY
]



def register_fonts() -> None:
    dejavu = Path("/usr/share/fonts/truetype/dejavu")
    assert dejavu.is_dir(), f"brak katalogu czcionek DejaVu: {dejavu}"
    pdfmetrics.registerFont(TTFont(FONT, str(dejavu / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(dejavu / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_SERIF, str(dejavu / "DejaVuSerif.ttf")))
    hand = Path(__file__).resolve().parent / "fonts" / "Caveat-Bold.ttf"
    assert hand.is_file(), f"brak fontu odrecznego: {hand}"
    pdfmetrics.registerFont(TTFont(FONT_HAND, str(hand)))


def draw_title(c: Canvas, p: Paleta, x0: float, top: float, card_w: float) -> float:
    """Tytul karty jak naglowek strony zg-go.pl; zwraca y pod nim."""
    y = top - 6 * mm
    c.setFillColor(p.tytul)
    c.setFont(FONT_SERIF, 14)
    c.drawString(x0, y, "Karta gracza")
    c.setFont(FONT, 7)
    c.drawRightString(x0 + card_w, y, "Ranking Semedori · zg-go.pl")
    c.setStrokeColor(p.linia)
    c.setLineWidth(0.8)
    c.line(x0, y - 3 * mm, x0 + card_w, y - 3 * mm)
    return y - 6 * mm


FIELD_H = 11 * mm

# (etykieta rubryki, szerokosc) — nick dostaje reszte szerokosci karty
POLE_PLANSZY = "ROZMIAR PLANSZY (ZAKREŚL JEDEN)"

FIELDS: list[tuple[str, float]] = [
    ("NICK", 0.0),
    (POLE_PLANSZY, 50 * mm),
]


def plansza_kratki(x: float, w: float) -> list[tuple[float, float]]:
    """(lewa krawedz, szerokosc) kolejnych kratek plansz w rubryce naglowka."""
    ile = len(PLANSZE_KARTY)
    kratka_w = (w - 2 * KRATKA_PLANSZY_MARGINES - (ile - 1) * KRATKA_PLANSZY_GAP) / ile
    return [(x + KRATKA_PLANSZY_MARGINES + i * (kratka_w + KRATKA_PLANSZY_GAP), kratka_w)
            for i in range(ile)]


def draw_fields(c: Canvas, p: Paleta, x0: float, top: float, card_w: float,
                dane: KartaDane | None) -> float:
    """Rubryki Nick / plansza jako obramowany pasek; zwraca y pod nim."""
    fixed = sum(w for _, w in FIELDS)
    nick_w = card_w - fixed
    assert nick_w > 30 * mm, f"za malo miejsca na rubryke nicku: {nick_w / mm:.1f} mm"
    widths = [w if w > 0 else nick_w for _, w in FIELDS]
    values = ["", ""] if dane is None else [dane.nick, ""]

    bottom = top - FIELD_H
    c.setStrokeColor(p.tusz)
    c.setLineWidth(0.6)
    c.rect(x0, bottom, card_w, FIELD_H, stroke=1, fill=0)
    x = x0
    for (label, _), w, value in zip(FIELDS, widths, values):
        c.line(x, top, x, bottom)
        c.setFillColor(p.przygaszony)
        c.setFont(FONT, 5.5)
        c.drawString(x + 1.5 * mm, top - 3 * mm, label)
        if label == POLE_PLANSZY:
            y_kratek = bottom + 1.2 * mm
            c.setFont(FONT_BOLD, PLANSZA_FS)
            for (kx, kw), plansza in zip(plansza_kratki(x, w), PLANSZE_KARTY):
                assert pdfmetrics.stringWidth(plansza, FONT_BOLD, PLANSZA_FS) <= kw - 1.5 * mm, \
                    f"nazwa planszy {plansza} za szeroka na kratke {kw / mm:.1f} mm"
                c.setStrokeColor(p.siatka)
                c.setLineWidth(0.6)
                c.rect(kx, y_kratek, kw, KRATKA_PLANSZY_H, stroke=1, fill=0)
                c.setFillColor(p.tusz)
                c.drawCentredString(kx + kw / 2, y_kratek + 1.6 * mm, plansza)
            if dane is not None:
                draw_plansza_kolko(c, p, x, w, y_kratek, dane.plansza)
        else:
            c.setFillColor(p.tusz)
            c.setFont(FONT_HAND, HAND_FS_FIELDS)
            c.drawString(x + 2 * mm, bottom + 2.5 * mm, value)
        x += w
    return bottom - 3 * mm


def group_widths(card_w: float) -> list[list[float]]:
    """Szerokosci podkolumn; 0.0 (nick) dostaje reszte karty do NICK_MAX,
    nadwyzka rozchodzi sie po rowno na pozostale kolumny (luz naglowkow)."""
    fixed = sum(w for _, subs in COLUMNS for _, w in subs)
    nick_w = min(card_w - fixed, NICK_MAX)
    assert nick_w > 20 * mm, f"za malo miejsca na nick przeciwnika: {nick_w / mm:.1f} mm"
    n_rest = sum(len(subs) for _, subs in COLUMNS) - 1
    extra = (card_w - fixed - nick_w) / n_rest
    assert extra >= 0, f"ujemny luz kolumn: {extra / mm:.2f} mm"
    return [[w + extra if w > 0 else nick_w for _, w in subs] for _, subs in COLUMNS]


def draw_header_text(c: Canvas, p: Paleta, cx: float, y: float, text: str, fs: float,
                     max_w: float, sila: bool) -> None:
    """Jedna linia naglowka, wersalikami; `sila` decyduje o kolorze.

    Kolor bierze sie z tego, ktora rubryka niesie sile (SILA_W_RUBRYCE), a nie z
    tego, czy slowo "sila" pada w nazwie: naglowek dwuwierszowy inaczej wyszedlby
    dwukolorowy, a "roznica" zostalaby czarna nad zielonymi liczbami.
    """
    text = text.upper()
    text_w = pdfmetrics.stringWidth(text, FONT_BOLD, fs)
    assert text_w <= max_w - 1 * mm, f"naglowek '{text}' za szeroki na kolumne {max_w / mm:.1f} mm"
    c.setFillColor(p.sila if sila else p.tusz)
    c.setFont(FONT_BOLD, fs)
    c.drawCentredString(cx, y, text)


def draw_header_labels(c: Canvas, p: Paleta, x0: float, top: float,
                       widths: list[list[float]]) -> None:
    line_h = 3.5 * mm
    x = x0
    leaf = 0
    for (label, subs), sub_ws in zip(COLUMNS, widths):
        group_w = sum(sub_ws)
        lines = label.split("\n")
        if len(subs) == 1:
            y = top - (HEAD_H - (len(lines) - 1) * line_h) / 2 - 0.8 * mm
            for line in lines:
                draw_header_text(c, p, x + group_w / 2, y, line, HEAD_FS, group_w,
                                 leaf in SILA_W_RUBRYCE)
                y -= line_h
            leaf += 1
        else:
            assert "\n" not in label, "naglowek grupy z podkolumnami musi byc jednoliniowy"
            # Naglowek grupy zbiera rubryki rozne co do tresci, wiec zostaje czarny;
            # kolor niosa podkolumny, kazda za siebie.
            draw_header_text(c, p, x + group_w / 2, top - HEAD_H / 4 - 0.8 * mm, label, HEAD_FS,
                             group_w, False)
            sx = x
            sub_line_h = 2.9 * mm
            for (sub_label, _), sub_w in zip(subs, sub_ws):
                sub_lines = sub_label.split("\n")
                y = top - HEAD_H / 2 - (HEAD_H / 2 - (len(sub_lines) - 1) * sub_line_h) / 2 - 0.8 * mm
                for line in sub_lines:
                    draw_header_text(c, p, sx + sub_w / 2, y, line, SUB_FS, sub_w,
                                     leaf in SILA_W_RUBRYCE)
                    y -= sub_line_h
                sx += sub_w
                leaf += 1
        x += group_w


def draw_grid(c: Canvas, p: Paleta, x0: float, top: float, card_w: float,
              widths: list[list[float]], n_rows: float) -> None:
    """Siatka tabeli; ulamkowe n_rows -> ostatni wiersz uciety, bez dolnej krawedzi.

    Tuszem sa tylko krawedzie: obrys, spod naglowka i grube granice sekcji;
    wewnetrzne linie wierszy i podkolumn ida kolorem siatki i ciensza kreska.
    """
    bottom = top - HEAD_H - n_rows * ROW_H
    last = int(n_rows) + 1
    for row in range(last + 1):
        y = top - min(row, 1) * HEAD_H - max(row - 1, 0) * ROW_H
        edge = row <= 1 or (row == last and n_rows == int(n_rows))
        c.setStrokeColor(p.tusz if edge else p.siatka)
        c.setLineWidth(0.6 if edge else 0.4)
        c.line(x0, y, x0 + card_w, y)
    x = x0
    for i, ((label, _), sub_ws) in enumerate(zip(COLUMNS, widths)):
        if label in THICK_BEFORE:                     # granica sekcji karty
            c.setStrokeColor(p.tusz)
            c.setLineWidth(1.8)
        elif i == 0:                                  # lewa krawedz tabeli
            c.setStrokeColor(p.tusz)
            c.setLineWidth(0.6)
        else:
            c.setStrokeColor(p.siatka)
            c.setLineWidth(0.5)
        c.line(x, top, x, bottom)                     # granica grupy: pelna wysokosc
        c.setStrokeColor(p.siatka)
        c.setLineWidth(0.4)
        sx = x
        for sub_w in sub_ws[:-1]:
            sx += sub_w
            c.line(sx, top - HEAD_H / 2, sx, bottom)  # granica podkolumny: od polowy naglowka
        if len(sub_ws) > 1:                           # kreska miedzy etykieta grupy a podkolumnami
            c.line(x, top - HEAD_H / 2, x + sum(sub_ws), top - HEAD_H / 2)
        x += sum(sub_ws)
    c.setStrokeColor(p.tusz)
    c.setLineWidth(0.6)
    c.line(x0 + card_w, top, x0 + card_w, bottom)     # prawa krawedz tabeli


def leaf_geometry(x0: float, widths: list[list[float]]) -> list[tuple[float, float]]:
    """(x, szerokosc) kazdej podkolumny, w kolejnosci od lewej."""
    out: list[tuple[float, float]] = []
    x = x0
    for sub_ws in widths:
        for w in sub_ws:
            out.append((x, w))
            x += w
    return out


def row_baseline(top: float, row: int) -> float:
    return top - HEAD_H - row * ROW_H - ROW_H / 2 - 1


def draw_plansza_kolko(c: Canvas, p: Paleta, x: float, w: float, y: float, plansza: str) -> None:
    """Zakresla kratke wybranej planszy — tak, jak zrobilby to gracz olowkiem."""
    assert plansza in PLANSZE_KARTY, f"nieznana plansza: {plansza}"
    kx, kw = plansza_kratki(x, w)[PLANSZE_KARTY.index(plansza)]
    cx, cy = kx + kw / 2, y + KRATKA_PLANSZY_H / 2
    rx, ry = kw / 2 + 0.6 * mm, KRATKA_PLANSZY_H / 2 + 0.9 * mm
    c.setStrokeColor(p.tusz)
    c.setLineWidth(1.5)
    c.ellipse(cx - rx, cy - ry, cx + rx, cy + ry, stroke=1, fill=0)


def draw_wiersze(c: Canvas, p: Paleta, x0: float, top: float, widths: list[list[float]],
                 wiersze: list[Wiersz]) -> None:
    """Wypelnione wiersze gier (karty przykladowe)."""
    leaves = leaf_geometry(x0, widths)
    assert len(leaves) == 11, len(leaves)
    for row, w in enumerate(wiersze):
        y = row_baseline(top, row)
        values = [w.data, w.moja_sila, w.przeciwnik_nick, w.sila_przeciwnika, w.roznica,
                  w.ruchy, w.jency, w.typ_gry, w.wynik, w.zmiana, w.nowa_sila]
        for li, ((lx, lw), value) in enumerate(zip(leaves, values)):
            if not value:
                continue
            c.setFillColor(p.sila if li in SILA_W_RUBRYCE else p.tusz)
            c.setFont(FONT_HAND, HAND_FS)
            c.drawCentredString(lx + lw / 2, y, value)


def draw_table(c: Canvas, p: Paleta, x0: float, top: float, card_w: float,
               wiersze: list[Wiersz], n_rows: float) -> float:
    """Tabela gier (naglowek dwupoziomowy + wiersze); zwraca y pod tabela.

    Ulamkowe n_rows (np. 1.5) rysuje wycinek: ostatni, niepelny wiersz zostaje
    pusty (bez nadruku planszy) i bez dolnej krawedzi — tabela "biegnie dalej".
    """
    assert len(wiersze) <= int(n_rows), f"za duzo wierszy: {len(wiersze)} > {int(n_rows)}"
    widths = group_widths(card_w)
    bottom = top - HEAD_H - n_rows * ROW_H

    c.setFillColor(p.tlo_naglowka)
    c.rect(x0, top - HEAD_H, card_w, HEAD_H, stroke=0, fill=1)

    # Rubryka "wynik" dostaje wlasne tlo na calej wysokosci tabeli: to jedyna
    # liczba wpisywana z pamieci zaraz po grze i ona rozstrzyga o zmianie sily,
    # wiec ma sie rzucac w oczy takze przy porownywaniu dwoch kart.
    x = x0
    for (label, _), sub_ws in zip(COLUMNS, widths):
        szerokosc = sum(sub_ws)
        if label == "wynik":
            c.setFillColor(p.tlo_wyniku)
            c.rect(x, bottom, szerokosc, top - HEAD_H - bottom, stroke=0, fill=1)
        x += szerokosc

    draw_header_labels(c, p, x0, top, widths)

    draw_wiersze(c, p, x0, top, widths, wiersze)
    draw_grid(c, p, x0, top, card_w, widths, n_rows)
    return bottom - 4 * mm


def draw_qr(c: Canvas, x: float, y: float, size: float, url: str) -> None:
    """Kod QR o boku size, lewym dolnym rogiem w (x, y)."""
    qr = QrCodeWidget(url, barLevel="M")
    x0, y0, x1, y1 = qr.getBounds()
    d = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    d.add(qr)
    renderPDF.draw(d, c, x, y)




KRATKA_W, BRZEG_W, WIERSZ_H = 6.0 * mm, 8.4 * mm, 2.8 * mm
SIATKA_GAP = 6 * mm


def _kratka_sily(roznica: float) -> str:
    """Polowka jednym znakiem, tak jak w tabeli na stronie."""
    calosc = int(roznica)
    if roznica == calosc:
        return str(calosc)
    return f"{calosc}½" if calosc else "½"


def _rysuj_kratke(c: Canvas, srodek: float, y: float, roznica: float) -> None:
    """Roznica w kratce: cyfry zawsze koncza sie w tym samym miejscu.

    Gdyby napis byl po prostu wysrodkowany, "3" i "3½" mialyby cyfre w innym
    miejscu i kolumna bylaby poszarpana. Dlatego calosc dosuwa sie do prawej,
    a polowka zwisa za nia — tak samo jak w plikach z tabelami.
    """
    polowka_w = c.stringWidth("½", FONT, 5.4)
    kres = srodek + polowka_w / 2
    calosc = int(roznica)
    c.drawRightString(kres, y, str(calosc) if calosc or roznica == calosc else "")
    if roznica != calosc:
        c.drawString(kres, y, "½")


def draw_siatka(c: Canvas, p: Paleta, x: float, top: float, plansza: str) -> float:
    """Jedna siatka wyrownania; zwraca jej szerokosc.

    Liczby ida wprost z wyrownanie/zg.py — to samo zrodlo, co tabele na stronie,
    wiec karta nie ma jak sie z nia rozjechac.
    """
    pola = siatka(plansza)
    jency = sorted({j for j, _ in pola})
    ruchy = sorted({r for _, r in pola})
    szer = len(jency) * KRATKA_W + BRZEG_W
    wys = (len(ruchy) + 2) * WIERSZ_H

    # Brzeg z ruchami szarzeje tak samo jak dolny wiersz z jencami — obu czyta sie
    # tak samo i oba maja odstawac od siatki. Tlo siega az pod gorna krawedz, bo
    # rog "↓ ruchy" nalezy do tej kolumny, a nie do wiersza z nazwa planszy.
    c.setFillColor(p.tlo_brzegu)
    c.rect(x + szer - BRZEG_W, top - wys + WIERSZ_H, BRZEG_W, wys - WIERSZ_H, stroke=0, fill=1)

    # Nazwa planszy jako plakietka: ciemne tlo obejmuje sam napis, a nie cala
    # szerokosc siatki. Belka na cala szerokosc przygniatala liczby pod soba.
    # Wysokosc pisma dobrana tak, zeby wersaliki miescily sie w plakietce —
    # przy wiekszej roznicy napis wychodzil ponad jej gorna krawedz.
    PLAKIETKA_FS = 5.6
    c.setFont(FONT_BOLD, PLAKIETKA_FS)
    plakietka_w = c.stringWidth(plansza, FONT_BOLD, PLAKIETKA_FS) + 3.0 * mm
    c.setFillColor(p.tusz)
    c.roundRect(
        x + (len(jency) * KRATKA_W - plakietka_w) / 2, top - WIERSZ_H + 0.35 * mm,
        plakietka_w, WIERSZ_H - 0.7 * mm, 0.45 * mm, stroke=0, fill=1,
    )
    c.setFillColor(BIEL)
    c.drawCentredString(x + len(jency) * KRATKA_W / 2, top - WIERSZ_H + 0.9 * mm, plansza)
    c.setFillColor(p.rog)
    c.setFont(FONT, 4.4)
    c.drawCentredString(x + szer - BRZEG_W / 2, top - WIERSZ_H + 1.0 * mm, "↓ ruchy")

    for numer, r in enumerate(ruchy):
        y = top - (numer + 2) * WIERSZ_H + 1.0 * mm
        for kolumna, j in enumerate(jency):
            c.setFillColor(p.sila)
            c.setFont(FONT, 5.4)
            _rysuj_kratke(c, x + (kolumna + 0.5) * KRATKA_W, y, pola[(j, r)])
        c.setFillColor(p.tusz)
        c.setFont(FONT_BOLD, 5.4)
        c.drawCentredString(x + szer - BRZEG_W / 2, y, str(r))

    dol = top - (len(ruchy) + 2) * WIERSZ_H + 1.0 * mm
    c.setFillColor(p.tlo_brzegu)
    # Caly wiersz, razem z rogiem: rog nalezy do brzegu, ktory nazywa.
    c.rect(x, dol - 1.0 * mm, szer, WIERSZ_H, stroke=0, fill=1)
    for kolumna, j in enumerate(jency):
        c.setFillColor(p.tusz)
        c.setFont(FONT_BOLD, 5.4)
        c.drawCentredString(x + (kolumna + 0.5) * KRATKA_W, dol, str(j))
    c.setFillColor(p.rog)
    c.setFont(FONT, 4.4)
    c.drawCentredString(x + szer - BRZEG_W / 2, dol, "← jeńcy")

    c.setStrokeColor(p.siatka)
    c.setLineWidth(0.4)
    # Od zera, bo pierwsza kreska oddziela czapke od pierwszego wiersza liczb —
    # bez niej nazwa planszy zlewa sie z siatka.
    for numer in range(len(ruchy) + 2):
        ly = top - (numer + 1) * WIERSZ_H
        c.line(x, ly, x + szer, ly)
    for kolumna in range(1, len(jency) + 1):
        c.line(x + kolumna * KRATKA_W, top - WIERSZ_H, x + kolumna * KRATKA_W, top - wys)
    # Brzegi oddziela kreska w kolorze --rule, ledwie grubsza od siatki — tak samo
    # jak na stronie: ma dzielic, a nie przecinac tabele na pol.
    # Kreska pionowa idzie od samej gory, bo odcina takze rog "↓ ruchy" — ten
    # nalezy do kolumny ruchow. Konczy sie nad wierszem jencow: dolny rog nalezy
    # do niego i ta sama kreska odcielaby go od jego wlasnych liczb.
    c.setStrokeColor(p.linia)
    c.setLineWidth(0.9)
    c.line(x + szer - BRZEG_W, top, x + szer - BRZEG_W, top - wys + WIERSZ_H)
    c.line(x, top - wys + WIERSZ_H, x + szer, top - wys + WIERSZ_H)
    c.setStrokeColor(p.tusz)
    c.setLineWidth(0.7)
    c.rect(x, top - wys, szer, wys, stroke=1, fill=0)
    return szer


def draw_siatki(c: Canvas, p: Paleta, x0: float, top: float, card_w: float) -> float:
    """Trzy siatki w rzedzie; zwraca y dolnej krawedzi."""
    x, najnizej = x0, top
    for plansza in PLANSZE:
        szer = draw_siatka(c, p, x, top, plansza)
        x += szer + SIATKA_GAP
        najnizej = min(najnizej, top - (len(sorted({r for _, r in siatka(plansza)})) + 2) * WIERSZ_H)
    assert x - SIATKA_GAP <= x0 + card_w, f"siatki nie miesza sie w szerokosc karty: {(x - SIATKA_GAP - x0) / mm:.1f} mm"
    return najnizej


OGON = ".,;:—()„”"


def _kawalki(slowo: str, kolumna: str, p: Paleta) -> list[tuple[str, str, Color]]:
    """Slowo rozbite na (tekst, czcionka, kolor).

    Interpunkcja odpada na koniec zwykla i czarna: zielony srednik po "+1" albo
    pogrubiony po "0" czytaja sie jak czesc liczby, a nia nie sa.
    """
    rdzen = slowo.rstrip(OGON)
    ogon = slowo[len(rdzen):]
    goly = rdzen.lstrip(OGON)
    if goly.lower() in SILA_SLOWA:
        styl = (FONT, p.sila)
    elif kolumna in SILA_KOLUMNY and ("½" in goly or goly == "0"
                                      or re.fullmatch(r"[+−±]\d+", goly)):
        styl = (FONT, p.sila)
    elif any(z.isdigit() for z in goly):
        styl = (FONT_BOLD, p.tusz)
    else:
        styl = (FONT, p.tusz)
    kawalki = [(rdzen, *styl)] if rdzen else []
    return kawalki + ([(ogon, FONT, p.tusz)] if ogon else [])


def _lamanie(zasada: str, kolumna: str, szerokosc: float,
             p: Paleta) -> list[list[tuple[str, str, Color]]]:
    """Zasada polamana na linie slow (slowo, czcionka, kolor).

    Wlasne lamanie zamiast simpleSplit, bo slowa roznia sie czcionka: pogrubiona
    liczba jest szersza niz ta sama liczba zwykla i linia by sie przelewala.
    """
    spacja = pdfmetrics.stringWidth(" ", FONT, SCIAGA_FS)
    linie: list[list[tuple[str, str, Color]]] = []
    biezaca: list[tuple[str, str, Color]] = []
    szer = 0.0
    for slowo in zasada.split():
        kawalki = _kawalki(slowo, kolumna, p)
        w = sum(pdfmetrics.stringWidth(t, f, SCIAGA_FS) for t, f, _ in kawalki)
        if biezaca and szer + spacja + w > szerokosc:
            linie.append(biezaca)
            biezaca, szer = [], 0.0
        elif biezaca:
            biezaca.append((" ", FONT, p.tusz))
            szer += spacja
        biezaca.extend(kawalki)
        szer += w
    if biezaca:
        linie.append(biezaca)
    return linie


def draw_sciaga(c: Canvas, p: Paleta, x0: float, top: float, card_w: float) -> float:
    """Trzykolumnowa sciaga z mini-naglowkami i punktami; zwraca y pod nia."""
    gap = 6 * mm
    col_w = (card_w - (len(SCIAGA) - 1) * gap) / len(SCIAGA)
    y0 = top - 4 * mm
    line_h = 2.7 * mm
    bottoms: list[float] = []
    for i, (title, items) in enumerate(SCIAGA):
        x = x0 + i * (col_w + gap)
        t = title.upper()
        c.setFont(FONT_BOLD, 6)
        c.setFillColor(p.sila if SILA_W_NAZWIE & set(t.split()) else p.tusz)
        c.drawString(x, y0, t)
        c.setStrokeColor(p.linia)
        c.setLineWidth(0.8)
        c.line(x, y0 - 1.6 * mm, x + col_w, y0 - 1.6 * mm)
        y = y0 - 5 * mm
        for zasada in items:
            c.setFont(FONT_BOLD, SCIAGA_FS)
            c.setFillColor(p.przygaszony)
            c.drawString(x, y, "•")
            for linia in _lamanie(zasada, title, col_w - 4.2 * mm, p):
                lx = x + 4.2 * mm
                for tekst, font, kolor in linia:
                    c.setFont(font, SCIAGA_FS)
                    c.setFillColor(kolor)
                    c.drawString(lx, y, tekst)
                    lx += pdfmetrics.stringWidth(tekst, font, SCIAGA_FS)
                y -= line_h
            y -= 0.7 * mm
        bottoms.append(y)
    # Siatki wszystkich trzech plansz ida pod sciaga, na calej szerokosci: karta
    # sluzy trzem planszom, wiec kazda musi miec swoja — jedna wystarczylaby
    # tylko wtedy, gdyby wyrownanie bylo wszedzie takie samo, a nie jest.
    # 4 mm, a nie 1,5: napis rosnie w gore od linii pisma, wiec przy ciasniejszym
    # odstepie wchodzil w ramke najnizszej siatki.
    y = draw_siatki(c, p, x0, min(bottoms) - 2.5 * mm, card_w) - 4 * mm
    qr_size = 14 * mm
    draw_qr(c, x0 + card_w - qr_size, y, qr_size, "https://zg-go.pl/ranking.html")
    c.setFont(FONT, 6)
    c.setFillColor(p.przygaszony)
    c.drawString(x0, y, "Pełne zasady: zg-go.pl/ranking.html")
    c.drawRightString(x0 + card_w - qr_size - 2 * mm, y, f"wersja karty {WERSJA}")
    return y


def draw_card(c: Canvas, p: Paleta, x0: float, card_w: float, dane: KartaDane | None) -> None:
    top = PAGE_H - MARGIN
    y = draw_title(c, p, x0, top, card_w)
    y = draw_fields(c, p, x0, y, card_w, dane)
    y = draw_table(c, p, x0, y, card_w, [] if dane is None else dane.wiersze, ROWS)
    y = draw_sciaga(c, p, x0, y, card_w)
    assert y > 5 * mm, f"karta nie miesci sie na stronie: y={y / mm:.1f} mm"


CUT_MARGIN = 2 * mm


def generuj_wycinek(out: Path, karty: list[KartaDane], n_rows: float, p: Paleta) -> None:
    """Zapisuje PDF-wycinek karty (naglowek + n_rows wierszy) do osadzenia na stronie.

    Jedna karta na strone; strona ma dokladnie rozmiar wycinka.
    """
    assert karty, "co najmniej jedna karta"
    register_fonts()
    card_w = PAGE_W - 2 * MARGIN
    page_w = card_w + 2 * CUT_MARGIN
    page_h = 2 * CUT_MARGIN + FIELD_H + 3 * mm + HEAD_H + n_rows * ROW_H
    c = Canvas(str(out), pagesize=(page_w, page_h))
    c.setTitle("Karta gracza (przykład) — Klub Go Semedori")
    for dane in karty:
        y = draw_fields(c, p, CUT_MARGIN, page_h - CUT_MARGIN, card_w, dane)
        draw_table(c, p, CUT_MARGIN, y, card_w, dane.wiersze, n_rows)
        c.showPage()
    c.save()
    print(f"OK: {out} ({out.stat().st_size} B)")


def generuj_karte(out: Path, karty: list[KartaDane | None], p: Paleta) -> None:
    """Zapisuje PDF: jedna karta na strone; None = pusta karta do druku."""
    assert karty, "co najmniej jedna karta"
    register_fonts()
    c = Canvas(str(out), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Karta gracza — Klub Go Semedori")
    for dane in karty:
        draw_card(c, p, MARGIN, PAGE_W - 2 * MARGIN, dane)
        c.showPage()
    c.save()
    print(f"OK: {out} ({out.stat().st_size} B)")


KORZEN = Path(__file__).resolve().parent.parent
ZAMEK = KORZEN / "karta.lock"


def odcisk() -> str:
    """Odcisk danych, ktore decyduja o tresci wydrukowanej karty.

    Sa tu zasady i uklad rubryk — czyli wszystko, czego zmiana unieważnia karty
    lezace w klubie. Wymiary czysto kosmetyczne (wysokosc wiersza, marginesy)
    swiadomie zostaja poza odciskiem: nie chcemy podbijac wersji karty dlatego,
    ze ktos przesunal kreske o pol milimetra.
    """
    dane = {
        "zasady": [[k, z] for k, z in ZASADY],
        "kolumny": list(KOLUMNY),
        "columns": [[g, [[s, round(w, 3)] for s, w in subs]] for g, subs in COLUMNS],
        "fields": [[etykieta, round(w, 3)] for etykieta, w in FIELDS],
        # Siatki wyrownania: same liczby, bo to one moga sie rozjechac z zasada.
        "siatki": {p: {f"{j}/{r}": d for (j, r), d in sorted(siatka(p).items())} for p in PLANSZE},
        "plansza": list(PLANSZE_KARTY),
    }
    kanoniczne = json.dumps(dane, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(kanoniczne.encode()).hexdigest()


def czytaj_zamek() -> dict[str, str]:
    """Zawartosc karta.lock jako slownik; pusty, gdy pliku jeszcze nie ma."""
    if not ZAMEK.is_file():
        return {}
    return dict(
        linia.split("=", 1)
        for linia in ZAMEK.read_text().splitlines()
        if linia and not linia.startswith("#")
    )


def zapisz_zamek() -> None:
    """Zapisuje odcisk i wersje karty; pilnuje, by zmiana tresci podbila WERSJA.

    Bez tego karta.pdf w repo moze byc o dwie zmiany zasad z tylu i nikt tego
    nie zauwazy — plik jest binarny, wiec diff nic nie mowi.
    """
    poprzedni = czytaj_zamek()
    biezacy = odcisk()
    assert not (poprzedni and poprzedni["odcisk"] != biezacy and poprzedni["wersja"] == WERSJA), (
        f"zasady albo uklad karty sie zmienily, a WERSJA dalej brzmi {WERSJA} — "
        "podbij ja w tools/karta_pdf.py, zeby dalo sie odroznic wydruki"
    )
    ZAMEK.write_text(
        "# Odcisk danych, z ktorych powstaje karta.pdf — pilnuje go tools/test_zasady.py.\n"
        "# Zmiana zasad albo ukladu bez ponownego `make` konczy sie czerwonym testem.\n"
        f"wersja={WERSJA}\n"
        f"odcisk={biezacy}\n"
    )


def main() -> None:
    generuj_karte(KORZEN / "karta.pdf", [None], KOLOROWA)
    generuj_karte(KORZEN / "karta-cb.pdf", [None], CZARNO_BIALA)
    zapisz_zamek()


if __name__ == "__main__":
    main()
