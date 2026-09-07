#!/usr/bin/env python3
"""Tablica siły klubu Semedori — wydruk 660 x 950 mm na mala tablice magnetyczna.

Uruchomienie: python3 tablica/tablica_kyu_pdf.py   (zapisuje tablica/ranking_table-660x950mm.pdf
w wybranej palecie); z opcja --palety pisze ranking_table-660x950mm-palety.pdf — strona na
kazda palete z PALETY, z podpisami, do porownywania kolorow.

Siatka 5 kolumn kratek: kolorowy pasek z liczba sily klubowej z lewej
(sila = 50 - kyu: 1 dan = 50, 50 kyu = 0; samych nazw kyu/dan na tablicy
nie ma), obok biale pole 82 x 30 mm na etykiety magnetyczne 50 x 25 mm;
cala kratka ma 106 mm. Silniejszy po prawej, dan u gory. Skala do sily 40
idzie cwiartkami, nizej polowkami. Kazda kolumna sekcji scala sie w jeden
slupek osobnych kafli rozdzielonych waska szczelina; pasek z lewej
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

import hashlib
import json
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


# Oddech wokol tresci w komorkach tabel wyrownania (jednostki karty gracza).
PAD_KOMORKI = 1.0 * mm
PAD_BRZEGU = 1.2 * mm


def metryki_tabeli(plansza: str) -> tuple[float, float, float, float]:
    """(kratka_w, brzeg_w, szerokosc, wysokosc) jednej siatki wyrownania
    w jednostkach karty gracza. Szerokosc komorki liczy sie z najszerszej
    wartosci tej tabeli plus oddech — kazda tabela jest tak waska, jak
    pozwala jej tresc; dolne ograniczenie pilnuje, zeby plakietka nazwy
    planszy nie wystawala poza kolumny wartosci."""
    pola = siatka(plansza)
    jency = sorted({j for j, _ in pola})
    ruchy = sorted({r for _, r in pola})
    naj = max(pdfmetrics.stringWidth(karta_pdf._kratka_sily(w, ",5"), FONT, 5.4)
              for w in pola.values())
    naj = max(naj, max(pdfmetrics.stringWidth(str(j), FONT_BOLD, 5.4) for j in jency))
    plakietka_w = pdfmetrics.stringWidth(plansza, FONT_BOLD, 5.6) + 3 * mm
    kratka_w = max(naj + PAD_KOMORKI, (plakietka_w + 1 * mm) / len(jency))
    brzeg_w = max(pdfmetrics.stringWidth(podpis, FONT, 4.4)
                  for podpis in ("↓ ruchy", "← jeńcy")) + PAD_BRZEGU
    return (kratka_w, brzeg_w,
            len(jency) * kratka_w + brzeg_w,
            (len(ruchy) + 2) * karta_pdf.WIERSZ_H)


def wymiary_siatki(plansza: str) -> tuple[float, float]:
    """(szerokosc, wysokosc) jednej siatki wyrownania w jednostkach karty gracza."""
    return metryki_tabeli(plansza)[2:]


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
BEZ_CWIARTKI = (0.75, 0.5, 0.0)         # sekcje 40-44 i 45-49: bez wiersza ,25


# Sekcje wierszy wartosci (kyu; na paskach stoi sila = 50 - kyu): piatka stopni
# z progiem w lewym dolnym rogu (silniejszy po prawej, dan u gory);
# (wiersze, czy pola podwojne). Skala konczy sie na 54,75 sily.
GRUPY: list[tuple[list[list[float]], bool]] = [
    (_cwiartki([0.0, -1.0, -2.0, -3.0, -4.0], PELNA), False),
    (_cwiartki([5.0, 4.0, 3.0, 2.0, 1.0], BEZ_CWIARTKI), False),
    (_cwiartki([10.0, 9.0, 8.0, 7.0, 6.0], BEZ_CWIARTKI), False),
    ([[14.5, 13.5, 12.5, 11.5, 10.5], [15.0, 14.0, 13.0, 12.0, 11.0]], False),
    ([[19.5, 18.5, 17.5, 16.5, 15.5], [20.0, 19.0, 18.0, 17.0, 16.0]], False),
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
ODSTEP_PARY = 3 * mm                    # zwarta przerwa miedzy sklejonymi sekcjami
# Sekcje sklejone z poprzednia: caly gorny pas skali (dany i wysokie sily,
# 30-54) idzie zwarta kolumna, a nizej pary o wspolnej barwie —
# 20-24 z 25-29 i pas 0-8 z pasem 10-18.
SKLEJONE_Z_POPRZEDNIA = (1, 2, 3, 4, 6, 8)
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
# Dolny pas to jeden rzad kafli na pelnej szerokosci strony (wyjezdza na
# marginesy siatki slupkow): trzy kolumny zasad i trzy tabele wyrownania
# obok siebie — najwyzsza z kolumn wyznacza jego wysokosc.
DOLNY_MARGINES = 14 * mm             # minimalny; reszta luzu tez idzie w marginesy
DOLNY_PAS_H = 66 * mm
ODSTEP_KOLUMN_ZASAD = 10 * mm
ODSTEP_ZASADY_TABELE = 14 * mm
KAFEL_W = 34 * mm                       # przelicznik sil na stopnie pod tabela 9x9
KAFEL_H = 11 * mm
KAFEL_PAS = 12 * mm
KAFEL_GAP = 6 * mm
KAFEL_FS = 11

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
# Pary sekcji dziela odcien: 25-29 z 20-24 i oba pasy poczatkujacych —
# na tablicy tworza wspolne, zwarte bloki skali.
ODCIENIE = (30, 58, 92, 135, 172, 218, 218, 284, 284)

PALETY: list[tuple[str, list[Color]]] = [
    ("luk ciagly, kroki wyrownane optycznie",
     [hsl(h, 0.44, 0.70) for h in ODCIENIE]),
    ("luk A odwrocony, top wino", _paleta(hsl(350, 0.40, 0.68), LUK_A[1], LUK_A[0], 0.44, 0.70)),
    ("luk A gleboki, top wino", _paleta(hsl(350, 0.44, 0.60), *LUK_A, 0.50, 0.62)),
]

WYBRANA = PALETY[0]                     # paleta wydruku: luk A, top przedluzony


SZCZELINA = 1 * mm                      # przerwa miedzy osobnymi kaflami slupka


def wysokosc_slupka(segmentow: int, wys_segmentu: float) -> float:
    """Wysokosc slupka: osobne kafle plus szczeliny miedzy nimi."""
    return segmentow * wys_segmentu + (segmentow - 1) * SZCZELINA


def odstep_przed(nr: int) -> float:
    """Przerwa nad sekcja nr: zwykla albo zwarta dla sekcji sklejonych."""
    return ODSTEP_PARY if nr in SKLEJONE_Z_POPRZEDNIA else ODSTEP_GRUP


def rysuj_strzalke(c: Canvas, x: float, dol: float, wys_seg: float,
                   kierunek: str, kolor: Color) -> None:
    """Strzalka na krawedzi bialego pola kafla, w barwie pola docelowego.

    Wszystkie strzalki maja ten sam plaski grot prostopadly do krawedzi
    i te sama kreske. Sasiad na tym samym pietrze skali dostaje prosta
    strzalke ("gora"/"dol"/"prawo"/"lewo"). Skoki rysuja zygzak o zrodle
    na srodku pola: krotki was od srodka, bieg wzdluz krawedzi w strone
    celu, krotki odcinek ku krawedzi i grot. Kierunki: "prawo-dol"
    i "lewo-gora" na wejscie w slupek wielosegmentowy, "gora-lewo"
    i "dol-prawo" na styk sekcji."""
    GRUB, KROTKI = 1.0 * mm, 1.5 * mm
    RUN_PION, RUN_POZIOM = 10 * mm, 30 * mm   # bieg wzdluz boku / wzdluz gory-dolu
    HEAD_W, HEAD_G = 3.6 * mm, 1.6 * mm   # wspolny grot: szeroki i plaski
    WCIECIE, NAKLADKA = 0.9 * mm, 0.2 * mm
    cx = x + PAS_LICZBY + (POLE_SZER - PAS_LICZBY) / 2
    cy = dol + wys_seg / 2
    yg, yd = dol + wys_seg - WCIECIE, dol + WCIECIE
    xp, xl = x + POLE_SZER - WCIECIE, x + PAS_LICZBY + WCIECIE
    y_gora, y_dol = yg - HEAD_G - KROTKI, yd + HEAD_G + KROTKI   # biegi przy krawedziach
    x_prawo, x_lewo = xp - HEAD_G - KROTKI, xl + HEAD_G + KROTKI
    trasy: dict[str, tuple[list[tuple[float, float]], tuple[float, float], tuple[int, int]]] = {
        # Proste siegaja tak samo gleboko jak zygzaki, tylko bez zygzaka.
        "gora": ([(cx, y_gora - KROTKI), (cx, yg - HEAD_G + NAKLADKA)],
                 (cx, yg), (0, 1)),
        "dol": ([(cx, y_dol + KROTKI), (cx, yd + HEAD_G - NAKLADKA)],
                (cx, yd), (0, -1)),
        "prawo": ([(x_prawo - KROTKI, cy), (xp - HEAD_G + NAKLADKA, cy)],
                  (xp, cy), (1, 0)),
        "lewo": ([(x_lewo + KROTKI, cy), (xl + HEAD_G - NAKLADKA, cy)],
                 (xl, cy), (-1, 0)),
        "gora-lewo": ([(cx, y_gora - KROTKI), (cx, y_gora), (cx - RUN_POZIOM, y_gora),
                       (cx - RUN_POZIOM, yg - HEAD_G + NAKLADKA)], (cx - RUN_POZIOM, yg), (0, 1)),
        "dol-prawo": ([(cx, y_dol + KROTKI), (cx, y_dol), (cx + RUN_POZIOM, y_dol),
                       (cx + RUN_POZIOM, yd + HEAD_G - NAKLADKA)], (cx + RUN_POZIOM, yd), (0, -1)),
        "prawo-dol": ([(x_prawo - KROTKI, cy), (x_prawo, cy), (x_prawo, cy - RUN_PION),
                       (xp - HEAD_G + NAKLADKA, cy - RUN_PION)], (xp, cy - RUN_PION), (1, 0)),
        "lewo-gora": ([(x_lewo + KROTKI, cy), (x_lewo, cy), (x_lewo, cy + RUN_PION),
                       (xl + HEAD_G - NAKLADKA, cy + RUN_PION)], (xl, cy + RUN_PION), (-1, 0)),
    }
    punkty, (tx, ty), (dx, dy) = trasy[kierunek]
    c.saveState()
    c.setStrokeColor(kolor)
    c.setLineWidth(GRUB)
    c.setLineCap(1)
    c.setLineJoin(1)
    p = c.beginPath()
    p.moveTo(*punkty[0])
    for punkt in punkty[1:]:
        p.lineTo(*punkt)
    c.drawPath(p, stroke=1, fill=0)
    bx, by = tx - dx * HEAD_G, ty - dy * HEAD_G   # srodek podstawy grotu
    g = c.beginPath()
    g.moveTo(tx, ty)
    g.lineTo(bx - dy * HEAD_W / 2, by + dx * HEAD_W / 2)
    g.lineTo(bx + dy * HEAD_W / 2, by - dx * HEAD_W / 2)
    g.close()
    c.setFillColor(kolor)
    c.drawPath(g, stroke=0, fill=1)
    c.restoreState()


def rysuj_slupek(c: Canvas, x: float, y: float,
                 segmenty: list[tuple[str, Color, Color, Color | None, float, bool]],
                 wys_segmentu: float) -> None:
    """Slupek sekcji: segmenty (liczba, barwa, kolor liczby, plakietka, stopien
    pisma, czy prog) od gory — kazdy jako osobny kafel z wlasnym obrysem,
    rozdzielone minimalna szczelina.

    Pasek kafla idzie pelna barwa, biale pole jej lekkim odcieniem; progi
    (piatki) dostaja biala plakietke z halo.
    """
    for nr, (liczba, barwa, kolor_liczby, plakietka, fs, prog_) in enumerate(segmenty):
        dol = y + (len(segmenty) - 1 - nr) * (wys_segmentu + SZCZELINA)
        c.saveState()
        c.clipPath(zaokraglony(c, x, dol, POLE_SZER, wys_segmentu, PROMIEN), stroke=0, fill=0)
        c.setFillColor(mieszaj(CARD, barwa, TINT_POLA))
        c.rect(x + PAS_LICZBY, dol, POLE_SZER - PAS_LICZBY, wys_segmentu, stroke=0, fill=1)
        c.setFillColor(barwa)
        c.rect(x, dol, PAS_LICZBY, wys_segmentu, stroke=0, fill=1)
        c.restoreState()
        # Obrys i kreska paska w ciemnej wersji barwy sekcji — tej samej,
        # ktora pisze liczby; kafel trzyma sie jednej rodziny koloru.
        c.setStrokeColor(mieszaj(barwa, INK, 0.55))
        c.setLineWidth(KRESKA)
        c.line(x + PAS_LICZBY, dol, x + PAS_LICZBY, dol + wys_segmentu)
        c.drawPath(zaokraglony(c, x, dol, POLE_SZER, wys_segmentu, PROMIEN), stroke=1, fill=0)
        srodek_x = x + PAS_LICZBY / 2
        srodek_y = dol + wys_segmentu / 2
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


def szerokosc_kolumny(tytul: str) -> float:
    """Najwezsza szerokosc kolumny, przy ktorej kazda zasada miesci sie
    w swojej zadeklarowanej liczbie linii, a naglowek w jednej."""
    kol_w = pdfmetrics.stringWidth(zasady_tablicy.NAGLOWKI[tytul], FONT_BOLD, ZASADY_TYTUL_FS)
    for zasada, limit in zasady_tablicy.zasady_kolumny(tytul):
        dol = max(pdfmetrics.stringWidth(slowo, FONT, ZASADY_FS) for slowo in zasada.split())
        gora = pdfmetrics.stringWidth(zasada, FONT, ZASADY_FS) + 10 * mm
        while gora - dol > 0.1 * mm:
            srodek = (dol + gora) / 2
            if len(_polam(zasada, srodek)) <= limit:
                gora = srodek
            else:
                dol = srodek
        kol_w = max(kol_w, gora + 4 * mm)   # wciecie punktu przed tekstem
    return kol_w + 0.5 * mm                 # zapas na blad wyszukiwania


def rysuj_kolumne_zasad(c: Canvas, x: float, gora_y: float, tytul: str,
                        kol_w: float) -> None:
    """Jedna kolumna zasad dolnego pasa: naglowek, linia i wyjustowane punkty.

    Kazda linia poza ostatnia w punkcie jest justowana do prawej krawedzi
    kolumny (luz rozchodzi sie po spacjach); zdanie ma sie zmiescic w liczbie
    linii zadeklarowanej w zasady_tablicy — pilnuje tego assert.
    """
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, ZASADY_TYTUL_FS)
    c.drawString(x, gora_y, zasady_tablicy.NAGLOWKI[tytul])
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8 * mm)
    c.line(x, gora_y - 2 * mm, x + kol_w, gora_y - 2 * mm)
    y = gora_y - 7.5 * mm
    spacja = pdfmetrics.stringWidth(" ", FONT, ZASADY_FS)
    szerokosc = kol_w - 4 * mm
    for zasada, limit in zasady_tablicy.zasady_kolumny(tytul):
        c.setFillColor(MUTED)
        c.setFont(FONT_BOLD, ZASADY_FS)
        c.drawString(x, y, "•")
        c.setFillColor(INK)
        c.setFont(FONT, ZASADY_FS)
        linie = _polam(zasada, szerokosc)
        assert len(linie) <= limit, \
            f"zasada lamie sie na {len(linie)} linie (limit {limit}): {zasada[:40]}..."
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


def rysuj_przelicznik(c: Canvas, prawa: float, dol_y: float,
                      kolory: list[Color]) -> None:
    """Rzad mini-kafelkow "sila ≈ stopien" w barwach swoich sekcji,
    dosuniety do prawej krawedzi — konczy sie pod tabela 9x9."""
    razem = len(PRZELICZNIK) * KAFEL_W + (len(PRZELICZNIK) - 1) * KAFEL_GAP
    x = prawa - razem
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
        # Krój jak w tabelach wyrownania obok — DejaVu bez pogrubienia.
        szer_p = c.stringWidth(sila, FONT, KAFEL_FS) + 4 * mm
        wys_p = 0.72 * KAFEL_FS + 2.5 * mm
        c.setFillColor(CARD)
        c.roundRect(x + KAFEL_PAS / 2 - szer_p / 2, dol_y + KAFEL_H / 2 - wys_p / 2,
                    szer_p, wys_p, 1.5 * mm, stroke=0, fill=1)
        c.setFillColor(barwa)
        c.setFont(FONT, KAFEL_FS)
        c.drawCentredString(x + KAFEL_PAS / 2, dol_y + KAFEL_H / 2 - 0.36 * KAFEL_FS, sila)
        c.drawCentredString(x + KAFEL_PAS + (KAFEL_W - KAFEL_PAS) / 2,
                            dol_y + KAFEL_H / 2 - 0.36 * KAFEL_FS, stopien)
        x += KAFEL_W + KAFEL_GAP


def rysuj_tabele_stopni(c: Canvas, x: float, gora: float, plansza: str,
                        barwa: Color) -> None:
    """Tabela wyrownania w jezyku tablicy: pelna barwa na brzegach z ruchami
    i jencami (jak paski sekcji), wnetrze z roznicami w tincie barwy, liczby
    ciemna wersja barwy. Rysowana w jednostkach karty — wola sie pod skala."""
    pola = siatka(plansza)
    jency = sorted({j for j, _ in pola})
    ruchy = sorted({r for _, r in pola})
    KRATKA_W, BRZEG_W, szer, wys = metryki_tabeli(plansza)
    WIERSZ_H = karta_pdf.WIERSZ_H
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
    # Wszystkie przerwy pasa sa stale, a caly wolny luz rozchodzi sie po rowno
    # na oba marginesy — tresc pasa stoi zwarta na srodku strony.
    LUZ_TABEL = 8 * mm
    kolumny_w = {tytul: szerokosc_kolumny(tytul) for tytul in zasady_tablicy.KOLUMNY}
    tresc_w = (sum(kolumny_w.values()) + (len(kolumny_w) - 1) * ODSTEP_KOLUMN_ZASAD
               + ODSTEP_ZASADY_TABELE + sum(szer for szer, _ in wymiary)
               + (len(wymiary) - 1) * LUZ_TABEL)
    margines_pasa = (PAGE_W - tresc_w) / 2
    assert margines_pasa >= DOLNY_MARGINES, \
        f"pas szerszy niz strona: margines {margines_pasa / mm:.1f} mm"
    x = margines_pasa
    for tytul in zasady_tablicy.KOLUMNY:
        rysuj_kolumne_zasad(c, x, gora_y - 1 * mm, tytul, kolumny_w[tytul])
        x += kolumny_w[tytul] + ODSTEP_KOLUMN_ZASAD
    x += ODSTEP_ZASADY_TABELE - ODSTEP_KOLUMN_ZASAD
    szer9, wys9 = wymiary[-1]
    razem_kafli = len(PRZELICZNIK) * KAFEL_W + (len(PRZELICZNIK) - 1) * KAFEL_GAP
    assert razem_kafli <= szer9, f"kafelki szersze niz tabela 9x9: {razem_kafli / mm:.0f} mm"
    kafle_dol = gora_y - wys9 - 5 * mm - KAFEL_H
    assert kafle_dol >= gora_y - DOLNY_PAS_H, "kafelki wychodza pod dolny pas"
    rysuj_przelicznik(c, PAGE_W - margines_pasa, kafle_dol, kolory)
    for ((szer, wys), plansza), barwa in zip(zip(wymiary, PLANSZE), TABELE_BARWY):
        c.saveState()
        c.translate(x, gora_y)
        c.scale(WYR_SKALA, WYR_SKALA)
        rysuj_tabele_stopni(c, 0, 0, plansza, barwa)
        c.restoreState()
        x += szer + LUZ_TABEL


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
    pola = sum(wysokosc_slupka(len(grupa), wys) for grupa, wys in sekcje)
    odstepy = sum(odstep_przed(nr) for nr in range(1, len(sekcje)))
    assert max(wys * WYR_SKALA for _, wys in map(wymiary_siatki, PLANSZE)) <= DOLNY_PAS_H, \
        "tabela wyrownania wyzsza niz dolny pas"
    siatka_h = pola + odstepy
    reszta = (PAGE_H - 2 * MARGINES
              - (NAGLOWEK_H + SEKCJA + siatka_h + SEKCJA + DOLNY_PAS_H))
    assert reszta >= 0, f"tresc wyzsza niz strona o {-reszta / mm:.0f} mm"
    return 0.54 * (MARGINES + reszta / 3)


def granice_sekcji() -> list[tuple[float, float]]:
    """(gora, dol) kazdego slupka sekcji w ukladzie strony (y od dolu).

    Jedyne zrodlo pionowej geometrii siatki — korzysta z niego rysowanie
    strony i kadry wycinkow SVG (tablica/wycinki_svg.py)."""
    y = PAGE_H - margines_gorny() - NAGLOWEK_H - SEKCJA
    granice = []
    for nr, (grupa, wys) in enumerate(sekcje_tablicy()):
        y -= (odstep_przed(nr) if nr > 0 else 0) + wysokosc_slupka(len(grupa), wys)
        granice.append((y + wysokosc_slupka(len(grupa), wys), y))
    return granice


def rysuj_strone(c: Canvas, page_h: float, podpis: str | None,
                 kolory: list[Color]) -> None:
    sekcje = sekcje_tablicy()
    assert len(kolory) == len(sekcje), "paleta musi miec barwe dla kazdej sekcji"
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, page_h, stroke=0, fill=1)
    rysuj_naglowek_kyu(c, page_h - margines_gorny())

    granice = granice_sekcji()
    for nr, (grupa, wys_segmentu) in enumerate(sekcje):
        barwa = kolory[nr]
        y = granice[nr][1]
        for kolumna in range(KOLUMNY):
            segmenty = []
            for wiersz in grupa:
                kyu = wiersz[kolumna]
                # Wszystkie liczby w ciemnej wersji barwy sekcji, wprost na
                # pasku; biala plakietke (z halo) dostaja wylacznie progi.
                ciemna = mieszaj(barwa, INK, 0.55)
                segmenty.append((liczba_skali(kyu), barwa, ciemna,
                                 CARD if prog(kyu) else None, LICZBA_FS, prog(kyu)))
            x = MARGINES_BOK + kolumna * (POLE_SZER + ODSTEP_POZIOM)
            rysuj_slupek(c, x, y, segmenty, wys_segmentu)
            # Strzalki sasiadow: skala biegnie w gore kolumny, ze szczytu
            # w prawo na dol sasiedniego slupka, a ze szczytu ostatniej kolumny
            # do sekcji wyzej — spadek lustrzanie. Skrajne pola bez strzalki.
            for idx in range(len(grupa)):
                dol_seg = y + (len(grupa) - 1 - idx) * (wys_segmentu + SZCZELINA)
                if idx > 0:
                    awans = ("gora", barwa)
                elif kolumna < KOLUMNY - 1:
                    # W sekcji jednorzedowej sasiednia kolumna to to samo
                    # pietro skali (wysokie pole tylko miesci wiecej
                    # magnesow) — strzalka prosta; w wielorzedowej wchodzi
                    # sie na dol sasiedniego slupka — zygzak.
                    awans = ("prawo-dol" if len(grupa) > 1 else "prawo", barwa)
                elif nr > 0:
                    awans = ("gora-lewo", kolory[nr - 1])
                else:
                    awans = None
                if idx < len(grupa) - 1:
                    spadek = ("dol", barwa)
                elif kolumna > 0:
                    spadek = ("lewo-gora" if len(grupa) > 1 else "lewo", barwa)
                elif nr < len(sekcje) - 1:
                    spadek = ("dol-prawo", kolory[nr + 1])
                else:
                    spadek = None
                for strzalka in (awans, spadek):
                    if strzalka is not None:
                        rysuj_strzalke(c, x, dol_seg, wys_segmentu, *strzalka)

    rysuj_dol(c, granice[-1][1] - SEKCJA, kolory)
    if podpis is not None:
        c.setFillColor(MUTED)
        c.setFont(FONT, PODPIS_FS)
        c.drawString(MARGINES_BOK, 4 * mm, podpis)


WERSJA = "07.09.2026o"                  # dopiska wydruku; podbij przy zmianie zasad/ukladu
ZAMEK = Path(__file__).resolve().parent / "tablica.lock"


def odcisk() -> str:
    """Odcisk danych, ktore decyduja o tresci wydrukowanej tablicy.

    Sa tu zasady, kolumny pasa, skala slupkow, przelicznik stopni i siatki
    wyrownania — wszystko, czego zmiana uniewaznia wiszacy wydruk. Wymiary
    czysto kosmetyczne swiadomie zostaja poza odciskiem."""
    dane = {
        "zasady": [[k, z, linie] for k, z, linie in zasady_tablicy.ZASADY],
        "kolumny": list(zasady_tablicy.KOLUMNY),
        "naglowki": dict(zasady_tablicy.NAGLOWKI),
        "grupy": [[wiersze, podwojne] for wiersze, podwojne in GRUPY],
        "przelicznik": [list(k) for k in PRZELICZNIK],
        "siatki": {p: {f"{j}/{r}": d for (j, r), d in sorted(siatka(p).items())} for p in PLANSZE},
    }
    kanoniczne = json.dumps(dane, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(kanoniczne.encode()).hexdigest()


def czytaj_zamek() -> dict[str, str]:
    """Zawartosc tablica.lock jako slownik; pusty, gdy pliku jeszcze nie ma."""
    if not ZAMEK.is_file():
        return {}
    return dict(
        linia.split("=", 1)
        for linia in ZAMEK.read_text().splitlines()
        if linia and not linia.startswith("#")
    )


def zapisz_zamek() -> None:
    """Zapisuje odcisk i wersje tablicy; pilnuje, by zmiana tresci podbila WERSJA.

    Bez tego wydruk w repo moze byc o dwie zmiany zasad z tylu i nikt tego
    nie zauwazy — plik jest binarny, wiec diff nic nie mowi."""
    poprzedni = czytaj_zamek()
    biezacy = odcisk()
    assert not (poprzedni and poprzedni["odcisk"] != biezacy and poprzedni["wersja"] == WERSJA), (
        f"zasady albo uklad tablicy sie zmienily, a WERSJA dalej brzmi {WERSJA} — "
        "podbij ja w tablica/tablica_kyu_pdf.py, zeby dalo sie odroznic wydruki"
    )
    ZAMEK.write_text(
        "# Odcisk danych, z ktorych powstaje ranking_table-660x950mm.pdf — pilnuje go\n"
        "# tools/test_tablica.py. Zmiana zasad albo ukladu bez `make` to czerwony test.\n"
        f"wersja={WERSJA}\n"
        f"odcisk={biezacy}\n"
    )


def generuj(sciezka: Path, palety: list[tuple[str, list[Color]]], podpisy: bool) -> None:
    zarejestruj_czcionki()              # metryki tabel mierza pismo, wiec czcionki ida pierwsze
    margines_gorny()                    # asserty ukladu pionowego przed rysowaniem
    page_h = PAGE_H
    c = Canvas(str(sciezka), pagesize=(PAGE_W, page_h))
    c.setTitle("Tablica siły — Semedori")
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
        zapisz_zamek()
