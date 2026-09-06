#!/usr/bin/env python3
"""Tablica stopni klubu Semedori — wydruk 660 x 950 mm na mala tablice magnetyczna.

Uruchomienie: python3 tablica/tablica_kyu_pdf.py   (zapisuje tablica/ranking_table-660x950mm.pdf
w wybranej palecie); z opcja --palety pisze ranking_table-660x950mm-palety.pdf — strona na
kazda palete z PALETY, z podpisami, do porownywania kolorow.

Siatka 5 kolumn kratek: kolorowy pasek z liczba sily klubowej z lewej
(sila = 50 - kyu: 1 dan = 50, 50 kyu = 0; samych nazw kyu/dan na tablicy
nie ma), obok biale pole 82 x 30 mm na etykiety magnetyczne 50 x 25 mm;
cala kratka ma 106 mm. Silniejszy po prawej, dan u gory. Skala do sily 40
idzie cwiartkami, nizej polowkami. Kazda kolumna sekcji scala sie w jeden
slupek: wspolny obrys, kreski dzielace segmenty progresji, pasek z lewej
niesie liczbe segmentu. Progiem jest kazda sila podzielna przez 5 od 25
w gore — stoi w lewym dolnym rogu sekcji i dostaje ciemny odcien barwy;
w skali poczatkujacych progow nie ma. Sekcje odroznia wylacznie kolor
i odstep — zadnych ramek wokol sekcji.

Struktura kolorow: sekcja ma wlasna barwe paskow, biale pola nosza jej
lekki odcien, a liczby calkowite (najnizsza komorka kolumny) dostaja mala
biala plakietke z liczba w barwie sekcji — negatyw barwnego paska. Progi
w pierwszej kolumnie (25-50) maja te sama plakietke, tylko z wieksza czcionka.

Naglowek to jeden pas: logo z nazwa i podtytulem po lewej, adres zg-go.pl
dosuniety do prawej, gorne krawedzie pisma wyrownane. Tabele wyrownania
wszystkich plansz stoja na samym dole, pod zasadami, rozlozone na szerokosc —
musza byc na tablicy, bo z nich odczytuje sie wyrownanie przy stoliku.
"""

import re
import sys
from colorsys import hls_to_rgb
from pathlib import Path

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfgen.pathobject import PDFPathObject

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import karta_pdf
import zasady_tablicy
from wyrownanie.tabela_html import PLANSZE, siatka

# paleta ze style.css — ta sama co strona i karta gracza
BG = HexColor("#f4e9cf")                # --bg: krem calej tablicy
INK = HexColor("#1a1a1a")               # --fg: krawedzie i logo
MUTED = HexColor("#666666")             # --muted: podpisy i notki
CIEMNY = HexColor("#444444")            # podtytul: ciemniejszy od --muted
ACCENT = HexColor("#9c2a2a")            # --accent: wyeksponowany adres zg-go.pl
RULE = HexColor("#d9c896")              # --rule: zloty
CARD = HexColor("#ffffff")              # --card: biale pola na etykiety
SILA = karta_pdf.KOLOROWA.sila          # kolor sily, ten sam co na karcie

FONT = "DejaVu"
FONT_BOLD = "DejaVu-Bold"
FONT_SERIF = "DejaVu-Serif"
FONT_SERIF_BOLD = "DejaVu-Serif-Bold"

PROMIEN = 3 * mm                        # zaokraglenie rogow slupkow
KRESKA = 0.5 * mm                       # grubosc krawedzi


def zarejestruj_czcionki() -> None:
    dejavu = Path("/usr/share/fonts/truetype/dejavu")
    assert dejavu.is_dir(), f"brak katalogu czcionek DejaVu: {dejavu}"
    pdfmetrics.registerFont(TTFont(FONT, str(dejavu / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(dejavu / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_SERIF, str(dejavu / "DejaVuSerif.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_SERIF_BOLD, str(dejavu / "DejaVuSerif-Bold.ttf")))


def wymiary_siatki(plansza: str) -> tuple[float, float]:
    """(szerokosc, wysokosc) jednej siatki wyrownania w jednostkach karty gracza."""
    pola = siatka(plansza)
    jency = len({j for j, _ in pola})
    ruchy = len({r for _, r in pola})
    return (jency * karta_pdf.KRATKA_W + karta_pdf.BRZEG_W,
            (ruchy + 2) * karta_pdf.WIERSZ_H)


def zaokraglony(c: Canvas, x: float, y: float, w: float, h: float, r: float) -> PDFPathObject:
    p = c.beginPath()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.arcTo(x + w - 2 * r, y, x + w, y + 2 * r, 270, 90)
    p.lineTo(x + w, y + h - r)
    p.arcTo(x + w - 2 * r, y + h - 2 * r, x + w, y + h, 0, 90)
    p.lineTo(x + r, y + h)
    p.arcTo(x, y + h - 2 * r, x + 2 * r, y + h, 90, 90)
    p.lineTo(x, y + r)
    p.arcTo(x, y, x + 2 * r, y + 2 * r, 180, 90)
    p.close()
    return p


def _cwiartki(okragle: list[float], przesuniecia: tuple[float, ...]) -> list[list[float]]:
    """Sekcja cwiartkowa: nad wierszem okraglych ida wiersze przesuniete o
    podane czesci kyu (od gory) — kazda kolumna to ciagly odcinek skali,
    a okragla liczba stoi na dole."""
    return [[k - p for k in okragle] for p in przesuniecia]


PELNA = (0.75, 0.5, 0.25, 0.0)          # cztery wiersze cwiartek
BEZ_CWIARTKI = (0.75, 0.5, 0.0)         # sekcja 40-44: bez wiersza ,25


# Sekcje wierszy wartosci (kyu; na paskach stoi sila = 50 - kyu): piatka stopni
# z progiem w lewym dolnym rogu (silniejszy po prawej, dan u gory);
# (wiersze, czy pola podwojne). Skala konczy sie na 54,75 sily.
GRUPY: list[tuple[list[list[float]], bool]] = [
    (_cwiartki([0.0, -1.0, -2.0, -3.0, -4.0], PELNA), False),
    (_cwiartki([5.0, 4.0, 3.0, 2.0, 1.0], PELNA), False),
    (_cwiartki([10.0, 9.0, 8.0, 7.0, 6.0], BEZ_CWIARTKI), False),
    ([[14.5, 13.5, 12.5, 11.5, 10.5], [15.0, 14.0, 13.0, 12.0, 11.0]], False),
    ([[20.0, 19.0, 18.0, 17.0, 16.0]], True),
    ([[25.0, 24.0, 23.0, 22.0, 21.0]], True),
    ([[30.0, 29.0, 28.0, 27.0, 26.0]], True),
    # Skala poczatkujacych: dwa osobne wiersze co 2, w dol az do zera.
    ([[40.0, 38.0, 36.0, 34.0, 32.0]], True),
    ([[50.0, 48.0, 46.0, 44.0, 42.0]], True),
]

PAS_LICZBY = 24 * mm                    # kolorowy pasek z liczba, z lewej kratki
POLE_BIALE = 83 * mm                    # samo biale pole na etykiety
POLE_SZER = PAS_LICZBY + POLE_BIALE     # cala kratka
POLE_WYS = 32 * mm                      # wymog: dokladnie 32
POLE_WYS_2 = 63 * mm                    # dwa pola minus wspolna kreska; miesci dwie etykiety
LICZBA_FS = 20
TINT_POLA = 0.12                        # domieszka barwy sekcji w bialych polach
ODSTEP_POZIOM = 5 * mm

# Wydruk: 660 mm szerokosci (weziej niz tablica, marginesy boczne przyciete)
# na 950 mm wysokosci; wolna wysokosc idzie w marginesy — dwie trzecie na
# dol, jedna trzecia na gore, wiec dol dostaje wyrazny oddech.
PAGE_W = 660 * mm
PAGE_H = 950 * mm
MARGINES = 9 * mm                       # baza; reszte doklada margines_gorny()
ODSTEP_GRUP = 7 * mm
SEKCJA = 8 * mm
NAGLOWEK_H = 50 * mm                    # jeden pas: logo, nazwa, podtytul, adres
LOGO = 38 * mm
TYTUL_FS = 50
TYTUL_ROZSTRZELENIE = 5                 # odstep miedzy literami "Semedori" (pt)
PODTYTUL_FS = 18
ADRES_FS = 37
# Ciemne zloto adresu (hsl 33/48%/36%): ciemniejsza wersja cieplego poczatku
# gradientu tablicy, spokojnie gra z kremowym tlem.
ZLOTO_ADRESU = HexColor("#886030")
# Dolny pas to jeden rzad kafli: trzy kolumny zasad i trzy tabele wyrownania
# obok siebie — najwyzszy kafel (tabela 19x19) wyznacza jego wysokosc.
DOLNY_PAS_H = 61 * mm
ZASADY_KOL_W = 108 * mm
ODSTEP_KOLUMN_ZASAD = 10 * mm
ODSTEP_ZASADY_TABELE = 14 * mm
KAFEL_W = 52 * mm                       # przelicznik sil na stopnie pod zasadami
KAFEL_H = 18 * mm
KAFEL_PAS = 20 * mm
KAFEL_GAP = 8 * mm
KAFEL_FS = 13

# Punkty zaczepienia skali do oficjalnych stopni; numer wskazuje sekcje,
# ktorej barwa maluje kafelek.
PRZELICZNIK: list[tuple[str, str, int]] = [
    ("20", "≈ 30 kyu", 6),
    ("30", "≈ 20 kyu", 4),
    ("40", "≈ 10 kyu", 2),
    ("50", "≈ 1 dan", 0),
]
ZASADY_TYTUL_FS = 12
ZASADY_FS = 10.5
ZASADY_LINIA_H = 4.9 * mm
WYR_SKALA = 2.05                        # tabele wyrownania; cyfry ~4,1 mm
TABELA_GAP = 13 * mm
# Tla tabel wyrownania: trzy stonowane barwy spoza palety sekcji — roznice
# sily to inne znaczenie niz sily, wiec nie wolno im wygladac jak sekcje;
# przygaszone nasycenie trzyma je w tle. Kolejnosc jak PLANSZE (19, 13, 9).
TABELE_BARWY = (HexColor("#c8ab72"), HexColor("#a8b077"), HexColor("#93aec0"))
PODPIS_FS = 12                          # podpis wariantu na dole strony

KOLUMNY = 5
SIATKA_W = KOLUMNY * POLE_SZER + (KOLUMNY - 1) * ODSTEP_POZIOM
MARGINES_BOK = (PAGE_W - SIATKA_W) / 2

assert POLE_BIALE > 50 * mm + 4 * mm, "etykieta 50 mm nie wchodzi w pole"
assert POLE_WYS > 25 * mm + 4 * mm, "etykieta 25 mm nie wchodzi w pole na wysokosc"
assert MARGINES_BOK > 0, f"siatka szersza niz tablica: {SIATKA_W / mm:.0f} mm"


def liczba_skali(kyu: float) -> str:
    """Na paskach stoi sila klubowa (50 - kyu) zaokraglona w dol do polowki:
    cwiartka dzieli etykiete z polowka pod soba, wiec komorki ida parami
    ("50" i "50" nizej, "50,5" i "50,5" wyzej) — dwa sloty na te sama liczbe."""
    sila = int((50 - kyu) * 2) / 2
    return f"{sila:g}".replace(".", ",")


def prog(kyu: float) -> bool:
    """Progiem jest kazda sila podzielna przez 5 — jej liczba idzie wieksza czcionka."""
    return (50 - kyu) % 5 == 0


def mieszaj(a: Color, b: Color, t: float) -> Color:
    return Color(a.red + (b.red - a.red) * t,
                 a.green + (b.green - a.green) * t,
                 a.blue + (b.blue - a.blue) * t)


def jasny(kolor: Color) -> bool:
    """Czy na tym tle czytelny jest ciemny tekst."""
    return 0.299 * kolor.red + 0.587 * kolor.green + 0.114 * kolor.blue > 0.55


# --- palety -----------------------------------------------------------------
# Struktura kolorow jest jedna: sekcja ma wlasna barwe — jasne tlo obwiedni,
# paski segmentow w barwie, prog (sila podzielna przez 5) jej ciemniejszym
# odcieniem z biala liczba. Kazda paleta to siedem barw sekcji, od gory
# (dany) do skali poczatkujacych; kazda paleta to strona PDF.


def hsl(h: float, s: float, l: float) -> Color:
    """Barwa z kola: h w stopniach, s/l w [0, 1]."""
    return Color(*hls_to_rgb((h % 360) / 360, l, s))


def przejscie(h_od: float, h_do: float, s: float, l: float, n: int = 7) -> list[Color]:
    """n barw plynnie od h_od do h_do, stala saturacja i jasnosc.

    Luki maja rozpietosc co najmniej 180 stopni na siedem sekcji, wiec sasiednie
    sekcje sa pokrewne, ale wyraznie rozne odcieniem (kroki 30-40 stopni).
    Zakres trzyma sie z dala od czerwieni i rozu (odcinek 45-300 stopni) —
    te wolno uzyc tylko w gornym pasie danow.
    """
    return [hsl(h_od + (h_do - h_od) * i / (n - 1), s, l) for i in range(n)]


# Pas danow (50+) moze byc mocniejszy niz reszta, ale wyraznie slabszy niz
# pelna czerwien: stonowane wino albo ciemniejszy koniec wlasnego luku.
WINO = hsl(350, 0.38, 0.60)

# Luki dla sekcji 45-15 (szesc barw) w zakresie 45-300 stopni; rozpietosc
# 190-240 stopni, czyli kroki 38-48 — sasiedzi pokrewni, ale wyraznie rozni.
LUK_A = (60, 285)                       # zolc -> zielen -> turkus -> fiolet
LUK_C = (45, 255)                       # zloto -> zielen -> granat
LUK_E = (90, 300)                       # zielen -> blekit -> sliwka


def _paleta(top: Color, h_od: float, h_do: float, s_: float, l_: float) -> list[Color]:
    return [top] + przejscie(h_od, h_do, s_, l_, len(GRUPY) - 1)


def _top_ciemny(h: float, s_: float, l_: float) -> Color:
    """Top jako ciemniejsza, mocniejsza wersja pierwszej barwy luku."""
    return mieszaj(hsl(h, s_, l_), INK, 0.35)


def _top_przedluzony(h_od: float, h_do: float) -> Color:
    """Top kontynuuje luk o jeden krok poza poczatek — cieplejszy i glebszy."""
    return hsl(h_od - (h_do - h_od) / 5, 0.48, 0.60)


# Palety do porownywania (--palety); top danow akcentuje delikatnie —
# w natezeniu zblizonym do reszty luku, nie mocniej.
# Rowne kroki w stopniach kola nie sa rowne dla oka: zielenie i niebieskosci
# zlewaja sie w jedno, a pomarancz z zolcia skacza. Odcienie sa wiec dobrane
# recznie — szersze przeskoki w zieleniach i miedzy turkusem a fioletem,
# ciasniejsze na cieplym poczatku; koniec dochodzi do granicy fioletu (300),
# bo dalej zaczyna sie roz, ktorego na skali nie chcemy.
ODCIENIE = (30, 58, 92, 135, 172, 202, 234, 267, 300)

PALETY: list[tuple[str, list[Color]]] = [
    ("luk ciagly, kroki wyrownane optycznie",
     [hsl(h, 0.44, 0.70) for h in ODCIENIE]),
    ("luk A odwrocony, top wino", _paleta(hsl(350, 0.40, 0.68), LUK_A[1], LUK_A[0], 0.44, 0.70)),
    ("luk A gleboki, top wino", _paleta(hsl(350, 0.44, 0.60), *LUK_A, 0.50, 0.62)),
]

WYBRANA = PALETY[0]                     # paleta wydruku: luk A, top przedluzony


def rysuj_slupek(c: Canvas, x: float, y: float,
                 segmenty: list[tuple[str, Color, Color, Color | None, float, bool]],
                 wys_segmentu: float) -> None:
    """Slupek sekcji: segmenty (liczba, barwa, kolor liczby, plakietka, stopien
    pisma, czy prog) od gory, wspolny obrys i kreski dzielace.

    Pasek segmentu idzie pelna barwa, biale pole jej lekkim odcieniem; liczby
    calkowite dostaja biala plakietke. Progi (piatki) wyroznia biale halo
    wokol plakietki.
    """
    wys = len(segmenty) * wys_segmentu
    c.saveState()
    c.clipPath(zaokraglony(c, x, y, POLE_SZER, wys, PROMIEN), stroke=0, fill=0)
    for nr, (_, barwa, _, _, _, _) in enumerate(segmenty):
        dol = y + wys - (nr + 1) * wys_segmentu
        c.setFillColor(mieszaj(CARD, barwa, TINT_POLA))
        c.rect(x + PAS_LICZBY, dol, POLE_SZER - PAS_LICZBY, wys_segmentu, stroke=0, fill=1)
        c.setFillColor(barwa)
        c.rect(x, dol, PAS_LICZBY, wys_segmentu, stroke=0, fill=1)
    c.restoreState()
    # Obrysy i kreski w ciemnej wersji barwy sekcji — tej samej, ktora pisze
    # polowki; slupek trzyma sie jednej rodziny koloru.
    c.setStrokeColor(mieszaj(segmenty[0][1], INK, 0.55))
    c.setLineWidth(KRESKA)
    c.line(x + PAS_LICZBY, y, x + PAS_LICZBY, y + wys)
    for nr in range(1, len(segmenty)):
        c.line(x, y + wys - nr * wys_segmentu, x + POLE_SZER, y + wys - nr * wys_segmentu)
    c.drawPath(zaokraglony(c, x, y, POLE_SZER, wys, PROMIEN), stroke=1, fill=0)
    for nr, (liczba, barwa, kolor_liczby, plakietka, fs, prog_) in enumerate(segmenty):
        srodek_x = x + PAS_LICZBY / 2
        srodek_y = y + wys - nr * wys_segmentu - wys_segmentu / 2
        if plakietka is not None:
            szer = c.stringWidth(liczba, FONT_BOLD, fs) + 5 * mm
            wys_p = 0.72 * fs + 5 * mm
            lewa_p, dol_p = srodek_x - szer / 2, srodek_y - wys_p / 2
            c.setFillColor(plakietka)
            c.roundRect(lewa_p, dol_p, szer, wys_p, 2 * mm, stroke=0, fill=1)
            if prog_:                           # biale halo wokol plakietki progu
                c.setStrokeColor(CARD)
                c.setLineWidth(2 * KRESKA)
                c.roundRect(lewa_p - 1 * mm, dol_p - 1 * mm, szer + 2 * mm,
                            wys_p + 2 * mm, 3 * mm, stroke=1, fill=0)
        c.setFillColor(kolor_liczby)
        c.setFont(FONT_BOLD, fs)
        c.drawCentredString(srodek_x, srodek_y - 0.36 * fs, liczba)


def rysuj_naglowek_kyu(c: Canvas, gora_y: float) -> None:
    """Jeden pas: napis Semedori (rozstrzelony) wycentrowany nad srodkowa
    kolumna siatki, logo wysuniete na lewo od niego; adres wycentrowany nad
    ostatnia kolumna, na linii podtytulu."""
    gora = gora_y - 2 * mm
    baza = gora - 30 * mm               # wspolna linia pisma nazwy i adresu
    srodek = PAGE_W / 2                 # srodek srodkowej kolumny siatki
    tytul = "Semedori"
    tytul_w = (pdfmetrics.stringWidth(tytul, FONT_SERIF_BOLD, TYTUL_FS)
               + (len(tytul) - 1) * TYTUL_ROZSTRZELENIE)
    tx = srodek - tytul_w / 2
    karta_pdf.rysuj_logo(c, karta_pdf.SEMEDORI.logo, tx - 8 * mm - LOGO,
                         gora - 6 * mm - LOGO, LOGO, INK)
    c.setFillColor(INK)
    tekst = c.beginText(tx, baza)
    tekst.setFont(FONT_SERIF_BOLD, TYTUL_FS)
    tekst.setCharSpace(TYTUL_ROZSTRZELENIE)
    tekst.textOut(tytul)
    tekst.setCharSpace(0)               # rozstrzelenie zostaje w stanie PDF — wyzeruj
    c.drawText(tekst)
    c.setFillColor(CIEMNY)
    c.setFont(FONT_SERIF, PODTYTUL_FS)
    c.drawCentredString(srodek, baza - 10 * mm, "Gramy w Go w Zielonej Górze")
    c.setFillColor(ZLOTO_ADRESU)
    c.setFont(FONT_SERIF_BOLD, ADRES_FS)
    srodek_ostatniej = (MARGINES_BOK + (KOLUMNY - 1) * (POLE_SZER + ODSTEP_POZIOM)
                        + POLE_SZER / 2)
    c.drawCentredString(srodek_ostatniej, baza - 10 * mm, "zg-go.pl")


def _polam(zasada: str, szerokosc: float) -> list[list[str]]:
    """Zasada polamana na linie slow miesczace sie w szerokosci."""
    spacja = pdfmetrics.stringWidth(" ", FONT, ZASADY_FS)
    linie, linia, szer = [], [], 0.0
    for slowo in zasada.split():
        w = pdfmetrics.stringWidth(slowo, FONT, ZASADY_FS)
        if linia and szer + spacja + w > szerokosc:
            linie.append(linia)
            linia, szer = [], 0.0
        linia.append(slowo)
        szer += w + (spacja if len(linia) > 1 else 0)
    linie.append(linia)
    return linie


def rysuj_kolumne_zasad(c: Canvas, x: float, gora_y: float, tytul: str) -> None:
    """Jedna kolumna zasad dolnego pasa: naglowek, linia i wyjustowane punkty.

    Kazda linia poza ostatnia w punkcie jest justowana do prawej krawedzi
    kolumny (luz rozchodzi sie po spacjach); zdania sa tak dobrane, zeby
    punkt konczyl sie w dwoch liniach — pilnuje tego assert.
    """
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, ZASADY_TYTUL_FS)
    c.drawString(x, gora_y, zasady_tablicy.NAGLOWKI[tytul])
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8 * mm)
    c.line(x, gora_y - 2 * mm, x + ZASADY_KOL_W, gora_y - 2 * mm)
    y = gora_y - 7.5 * mm
    spacja = pdfmetrics.stringWidth(" ", FONT, ZASADY_FS)
    szerokosc = ZASADY_KOL_W - 4 * mm
    for zasada in zasady_tablicy.w_kolumnie(tytul):
        c.setFillColor(MUTED)
        c.setFont(FONT_BOLD, ZASADY_FS)
        c.drawString(x, y, "•")
        c.setFillColor(INK)
        c.setFont(FONT, ZASADY_FS)
        linie = _polam(zasada, szerokosc)
        assert len(linie) <= 2, f"zasada lamie sie na {len(linie)} linie: {zasada[:40]}..."
        for nr, linia in enumerate(linie):
            slow_w = [pdfmetrics.stringWidth(slowo, FONT, ZASADY_FS) for slowo in linia]
            ostatnia = nr == len(linie) - 1
            odstep = (spacja if ostatnia or len(linia) < 2
                      else (szerokosc - sum(slow_w)) / (len(linia) - 1))
            lx = x + 4 * mm
            for slowo, w in zip(linia, slow_w):
                c.drawString(lx, y, slowo)
                lx += w + odstep
            y -= ZASADY_LINIA_H
        y -= 1.2 * mm
    assert y >= gora_y - DOLNY_PAS_H, f"kolumna zasad '{tytul}' nie miesci sie w pasie"


def rysuj_przelicznik(c: Canvas, lewa: float, prawa: float, dol_y: float,
                      kolory: list[Color]) -> None:
    """Rzad mini-kafelkow "sila ≈ stopien" w barwach swoich sekcji,
    wysrodkowany miedzy lewa a prawa."""
    razem = len(PRZELICZNIK) * KAFEL_W + (len(PRZELICZNIK) - 1) * KAFEL_GAP
    x = lewa + (prawa - lewa - razem) / 2
    for sila, stopien, nr_sekcji in PRZELICZNIK:
        barwa = kolory[nr_sekcji]
        c.setFillColor(CARD)
        c.drawPath(zaokraglony(c, x, dol_y, KAFEL_W, KAFEL_H, 2 * mm), stroke=0, fill=1)
        c.saveState()
        c.clipPath(zaokraglony(c, x, dol_y, KAFEL_W, KAFEL_H, 2 * mm), stroke=0, fill=0)
        c.setFillColor(barwa)
        c.rect(x, dol_y, KAFEL_PAS, KAFEL_H, stroke=0, fill=1)
        c.restoreState()
        c.setStrokeColor(mieszaj(barwa, INK, 0.55))
        c.setLineWidth(KRESKA)
        c.line(x + KAFEL_PAS, dol_y, x + KAFEL_PAS, dol_y + KAFEL_H)
        c.drawPath(zaokraglony(c, x, dol_y, KAFEL_W, KAFEL_H, 2 * mm), stroke=1, fill=0)
        # sila na bialej plakietce o proporcjach plakietek z glownej siatki:
        # ciasno wokol liczby, duzo barwy paska dookola
        szer_p = c.stringWidth(sila, FONT_BOLD, KAFEL_FS) + 4 * mm
        wys_p = 0.72 * KAFEL_FS + 2.5 * mm
        c.setFillColor(CARD)
        c.roundRect(x + KAFEL_PAS / 2 - szer_p / 2, dol_y + KAFEL_H / 2 - wys_p / 2,
                    szer_p, wys_p, 1.5 * mm, stroke=0, fill=1)
        c.setFillColor(barwa)
        c.setFont(FONT_BOLD, KAFEL_FS)
        c.drawCentredString(x + KAFEL_PAS / 2, dol_y + KAFEL_H / 2 - 0.36 * KAFEL_FS, sila)
        c.setFillColor(INK)
        c.setFont(FONT, 12)
        c.drawCentredString(x + KAFEL_PAS + (KAFEL_W - KAFEL_PAS) / 2,
                            dol_y + KAFEL_H / 2 - 0.36 * 12, stopien)
        x += KAFEL_W + KAFEL_GAP


def rysuj_tabele_stopni(c: Canvas, x: float, gora: float, plansza: str,
                        barwa: Color) -> None:
    """Tabela wyrownania w jezyku tablicy: pelna barwa na brzegach z ruchami
    i jencami (jak paski sekcji), wnetrze z roznicami w tincie barwy, liczby
    ciemna wersja barwy. Rysowana w jednostkach karty — wola sie pod skala."""
    pola = siatka(plansza)
    jency = sorted({j for j, _ in pola})
    ruchy = sorted({r for _, r in pola})
    KRATKA_W, BRZEG_W, WIERSZ_H = karta_pdf.KRATKA_W, karta_pdf.BRZEG_W, karta_pdf.WIERSZ_H
    szer = len(jency) * KRATKA_W + BRZEG_W
    wys = (len(ruchy) + 2) * WIERSZ_H
    ciemna = mieszaj(barwa, INK, 0.55)

    c.setFillColor(mieszaj(CARD, barwa, 0.22))
    c.rect(x, gora - wys, szer, wys, stroke=0, fill=1)
    c.setFillColor(barwa)                       # brzeg z ruchami i wiersz jencow
    c.rect(x + szer - BRZEG_W, gora - wys + WIERSZ_H, BRZEG_W, wys - WIERSZ_H,
           stroke=0, fill=1)
    c.rect(x, gora - wys, szer, WIERSZ_H, stroke=0, fill=1)

    c.setFillColor(ciemna)                      # plakietka nazwy planszy
    PLAKIETKA_FS = 5.6
    plakietka_w = c.stringWidth(plansza, FONT_BOLD, PLAKIETKA_FS) + 3 * mm
    c.roundRect(x + (len(jency) * KRATKA_W - plakietka_w) / 2, gora - WIERSZ_H + 0.35 * mm,
                plakietka_w, WIERSZ_H - 0.7 * mm, 0.45 * mm, stroke=0, fill=1)
    c.setFillColor(CARD)
    c.setFont(FONT_BOLD, PLAKIETKA_FS)
    c.drawCentredString(x + len(jency) * KRATKA_W / 2, gora - WIERSZ_H + 0.9 * mm, plansza)
    c.setFillColor(ciemna)
    c.setFont(FONT, 4.4)
    c.drawCentredString(x + szer - BRZEG_W / 2, gora - WIERSZ_H + 1.0 * mm, "↓ ruchy")

    for numer, r in enumerate(ruchy):
        y = gora - (numer + 2) * WIERSZ_H + 1.0 * mm
        c.setFont(FONT, 5.4)
        for kolumna, j in enumerate(jency):
            c.drawCentredString(x + (kolumna + 0.5) * KRATKA_W, y,
                                karta_pdf._kratka_sily(pola[(j, r)], ",5"))
        c.setFont(FONT_BOLD, 5.4)
        c.drawCentredString(x + szer - BRZEG_W / 2, y, str(r))
    dol = gora - (len(ruchy) + 2) * WIERSZ_H + 1.0 * mm
    for kolumna, j in enumerate(jency):
        c.setFont(FONT_BOLD, 5.4)
        c.drawCentredString(x + (kolumna + 0.5) * KRATKA_W, dol, str(j))
    c.setFont(FONT, 4.4)
    c.drawCentredString(x + szer - BRZEG_W / 2, dol, "← jeńcy")

    c.setStrokeColor(ciemna)
    c.setLineWidth(0.3)
    for numer in range(len(ruchy) + 2):
        ly = gora - (numer + 1) * WIERSZ_H
        c.line(x, ly, x + szer, ly)
    for kolumna in range(1, len(jency) + 1):
        c.line(x + kolumna * KRATKA_W, gora - WIERSZ_H, x + kolumna * KRATKA_W, gora - wys)
    c.setLineWidth(0.7)
    c.rect(x, gora - wys, szer, wys, stroke=1, fill=0)


def rysuj_dol(c: Canvas, gora_y: float, kolory: list[Color]) -> None:
    """Dolny pas jednym rzedem kafli: kolumny zasad, potem tabele wyrownania;
    pod zasadami rzad kafelkow przelicznika sil na oficjalne stopnie.

    Kafle maja bardzo rozne szerokosci, wiec ida od lewej w naturalnych
    rozmiarach, a caly luz zbiera sie w odstepach po rowno — pas wykorzystuje
    pelna szerokosc siatki i wysokosc najwyzszego kafla (tabeli 19x19).
    """
    wymiary = [tuple(w * WYR_SKALA for w in wymiary_siatki(p)) for p in PLANSZE]
    # Przerwy waza sie osobno: kolumny zasad i granice zasady/tabele maja
    # oddech na sztywno, a reszta luzu rozchodzi sie miedzy tabele.
    luz_tabel = (SIATKA_W - len(zasady_tablicy.KOLUMNY) * ZASADY_KOL_W
                 - ODSTEP_KOLUMN_ZASAD - ODSTEP_ZASADY_TABELE
                 - sum(szer for szer, _ in wymiary)) / (len(wymiary) - 1)
    assert luz_tabel >= 5 * mm, f"tabele bez przerw: {luz_tabel / mm:.1f} mm"
    x = MARGINES_BOK
    for tytul in zasady_tablicy.KOLUMNY:
        rysuj_kolumne_zasad(c, x, gora_y - 1 * mm, tytul)
        x += ZASADY_KOL_W + ODSTEP_KOLUMN_ZASAD
    x += ODSTEP_ZASADY_TABELE - ODSTEP_KOLUMN_ZASAD
    rysuj_przelicznik(c, MARGINES_BOK, x - ODSTEP_ZASADY_TABELE,
                      gora_y - DOLNY_PAS_H - 2 * mm, kolory)
    for ((szer, wys), plansza), barwa in zip(zip(wymiary, PLANSZE), TABELE_BARWY):
        c.saveState()
        c.translate(x, gora_y)
        c.scale(WYR_SKALA, WYR_SKALA)
        rysuj_tabele_stopni(c, 0, 0, plansza, barwa)
        c.restoreState()
        x += szer + luz_tabel


def sekcje_tablicy() -> list[tuple[list[list[float]], float]]:
    """Sekcje jako (wiersze kyu od gory, wysokosc segmentu slupka)."""
    return [(grupa, POLE_WYS_2 if podwojne else POLE_WYS) for grupa, podwojne in GRUPY]


def margines_gorny() -> float:
    """Margines gorny: baza plus jedna trzecia wolnej wysokosci strony.

    Strona ma sztywny wymiar, a wszystkie elementy sztywne wysokosci — wolna
    reszta idzie w biel: trzecia na gore, a dwie trzecie zostaja na dole samo
    przez sie, bo tresc plynie od gory.
    """
    sekcje = sekcje_tablicy()
    pola = sum(len(grupa) * wys for grupa, wys in sekcje)
    assert max(wys * WYR_SKALA for _, wys in map(wymiary_siatki, PLANSZE)) <= DOLNY_PAS_H, \
        "tabela wyrownania wyzsza niz dolny pas"
    siatka_h = pola + (len(sekcje) - 1) * ODSTEP_GRUP
    reszta = (PAGE_H - 2 * MARGINES
              - (NAGLOWEK_H + SEKCJA + siatka_h + SEKCJA + DOLNY_PAS_H))
    assert reszta >= 0, f"tresc wyzsza niz strona o {-reszta / mm:.0f} mm"
    return MARGINES + reszta / 3


def rysuj_strone(c: Canvas, page_h: float, podpis: str | None,
                 kolory: list[Color]) -> None:
    sekcje = sekcje_tablicy()
    assert len(kolory) == len(sekcje), "paleta musi miec barwe dla kazdej sekcji"
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, page_h, stroke=0, fill=1)
    rysuj_naglowek_kyu(c, page_h - margines_gorny())

    y = page_h - margines_gorny() - NAGLOWEK_H - SEKCJA
    for nr, (grupa, wys_segmentu) in enumerate(sekcje):
        barwa = kolory[nr]
        y -= (ODSTEP_GRUP if nr > 0 else 0) + len(grupa) * wys_segmentu
        for kolumna in range(KOLUMNY):
            segmenty = []
            for wiersz in grupa:
                kyu = wiersz[kolumna]
                # Wszystkie liczby w ciemnej wersji barwy sekcji — na
                # plakietkach (calkowite, progi z halo) i wprost na pasku
                # (polowki i powtorki par).
                ciemna = mieszaj(barwa, INK, 0.55)
                if kyu == int(kyu):
                    segmenty.append((liczba_skali(kyu), barwa, ciemna, CARD,
                                     LICZBA_FS, prog(kyu)))
                else:
                    segmenty.append((liczba_skali(kyu), barwa, ciemna, None,
                                     LICZBA_FS, False))
            x = MARGINES_BOK + kolumna * (POLE_SZER + ODSTEP_POZIOM)
            rysuj_slupek(c, x, y, segmenty, wys_segmentu)

    rysuj_dol(c, y - SEKCJA, kolory)
    if podpis is not None:
        c.setFillColor(MUTED)
        c.setFont(FONT, PODPIS_FS)
        c.drawString(MARGINES_BOK, 4 * mm, podpis)


def generuj(sciezka: Path, palety: list[tuple[str, list[Color]]], podpisy: bool) -> None:
    margines_gorny()                    # asserty ukladu pionowego przed rysowaniem
    page_h = PAGE_H
    zarejestruj_czcionki()
    c = Canvas(str(sciezka), pagesize=(PAGE_W, page_h))
    c.setTitle("Tablica stopni — Semedori")
    for nr, (nazwa, kolory) in enumerate(palety, start=1):
        rysuj_strone(c, page_h, f"paleta {nr}: {nazwa}" if podpisy else None, kolory)
        c.showPage()
    c.save()
    print(f"{sciezka.relative_to(REPO)}: {PAGE_W / mm:.0f} x {page_h / mm:.0f} mm, "
          f"stron: {len(palety)}")


if __name__ == "__main__":
    assert sys.argv[1:] in ([], ["--palety"]), "jedyna opcja to --palety"
    if sys.argv[1:] == ["--palety"]:
        generuj(REPO / "tablica" / "ranking_table-660x950mm-palety.pdf", PALETY, podpisy=True)
    else:
        generuj(REPO / "tablica" / "ranking_table-660x950mm.pdf", [WYBRANA], podpisy=False)
