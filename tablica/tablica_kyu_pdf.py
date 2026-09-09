#!/usr/bin/env python3
"""Tablica siły klubu Semedori — wydruk 660 x 950 mm na mala tablice magnetyczna.

Uruchomienie: python3 tablica/tablica_kyu_pdf.py   (zapisuje tablica/ranking_table-660x950mm.pdf
w wybranej palecie); z opcja --palety pisze ranking_table-660x950mm-palety.pdf — strona na
kazda palete z PALETY, z podpisami, do porownywania kolorow.

Siatka 5 kolumn pol na etykiety magnetyczne 80 x 30 mm; pole ma 111 x 32 mm,
a sila klubowa (sila = 50 - kyu: 1 dan = 50, 50 kyu = 0; samych nazw kyu/dan
na tablicy nie ma) stoi duza, blada czcionka na srodku pola, w tle — wiszaca
etykieta ja zakrywa, czyta sie ja z pustego pola albo po podniesieniu
magnesu. Silniejszy po prawej, dan u gory. Skala do sily 40 idzie
cwiartkami, nizej polowkami. Kazda kolumna sekcji scala sie w jeden slupek
osobnych kafli rozdzielonych waska szczelina. Progiem jest kazda sila
podzielna przez 5 od 25 w gore — stoi w lewym dolnym rogu sekcji i dostaje
ramke; w skali poczatkujacych progow nie ma. Sekcje odroznia
wylacznie kolor i odstep — zadnych ramek wokol sekcji.

Pole jest symetryczne: przy lewej krawedzi dwa pionowe paski serii (napisy
z zasady_tablicy.PASKI), przy prawej ich lustro — PRZEGRANA i pusty. Magnes
dosuniety do lewej krawedzi zakrywa oba lewe paski i odslania PRZEGRANA, po
wygranej odsuwa sie o szerokosc paska i odslania kolejny napis z lewej —
trzy pozycje magnesu to cala pamiec tablicy o wygranych z rzedu. W polu
centralnym miedzy paskami stoja obie strzalki i liczba. Pole podwojne to dwa
sloty rozdzielone jasna kreska, kazdy z wlasnymi paskami; liczba jest jedna.

Struktura kolorow: sekcja ma wlasna barwe; pole nosi jej lekki odcien,
paski SERIA / PRZEGRANA mocniejszy (napis negatywem), liczba w tle
nasycona i ciemniejsza, prog w ramce w tej barwie.

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

ETYKIETA_W, ETYKIETA_H = 80 * mm, 30 * mm   # etykieta magnetyczna gracza
# Paski serii przy lewej krawedzi pola: magnes przy krawedzi zakrywa oba,
# kazda wygrana odsuwa go o PASEK_W. Pierwszy pasek ma tlo pola, drugi (SERIA)
# tlo w barwie sekcji — odsloniety, widac go z drugiego konca sali.
PASEK_W = 14 * mm
PASEK_FS = 10
# Pole jest symetryczne: WYGRANA, SERIA, pole centralne, PRZEGRANA, pusty.
# Strefa etykiety zaczyna sie przy lewej krawedzi i na SERII konczy sie
# dokladnie na prawej.
PASKI_W = len(zasady_tablicy.PASKI) * PASEK_W   # oba paski serii razem
CENTRUM_W = ETYKIETA_W - PASKI_W        # pole centralne: strzalki i liczba
POLE_SZER = 2 * PASKI_W + CENTRUM_W
POLE_WYS = 32 * mm                      # wymog: dokladnie 32
POLE_WYS_2 = 63 * mm                    # dwa pola minus wspolna kreska; miesci dwie etykiety
# Paski po prawej stronie strefy etykiety: PRZEGRANA i pusty — lustro lewych.
PASKI_PRAWE = (zasady_tablicy.PASEK_PRZEGRANEJ, "")
# Liczba sily w tle pola: wyblakla, na srodku pola centralnego miedzy
# strefami strzalek, tak duza, jak pozwala najszersza liczba skali
# (rozmiar_liczby); prog w ramce.
LICZBA_FS_MAX = 64
LUZ_LICZBY = 2 * mm                     # oddech liczby od strzalek
STRZALKA_W = 10 * mm                    # strefa strzalki przy kazdym brzegu pola centralnego
# Strzalki stoja przyklejone do liczby: ODSTEP_STRZALKI od krawedzi najszerszej
# liczby skali do srodka strzalki, w kazdym polu tak samo.
ODSTEP_STRZALKI = 5.5 * mm
TINT_POLA = 0.12                        # domieszka barwy sekcji w polach
TINT_PASKA = 0.85                       # tlo paskow SERIA / PRZEGRANA (napis negatywem)
LICZBA_S, LICZBA_L = 0.55, 0.48         # liczby: odcien sekcji, ale nasycony i ciemniejszy od pasteli
RAMKA_PROGU = 3 * mm                    # oddech ramki wokol liczby progu
# Tla paskow od krawedzi do srodka (prawe lustrzanie): skrajny jak pole
# z napisem w odcieniu TINT_PASKA, wewnetrzny (SERIA / PRZEGRANA) negatywem.
TINT_PASKOW = (TINT_POLA, TINT_PASKA)
KRESKA_SLOTU = 0.2                      # domieszka ciemnej barwy w kresce miedzy slotami — pod liczba
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
DOLNY_PAS_H = 68 * mm
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

assert POLE_WYS_2 / 2 > ETYKIETA_H + 1 * mm, "etykieta nie wchodzi w slot pola podwojnego"
assert POLE_WYS > ETYKIETA_H + 1 * mm, "etykieta nie wchodzi w pole na wysokosc"
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


def nasycona(kolor: Color, s: float, l: float) -> Color:
    """Ten sam odcien kola barw, inne nasycenie i jasnosc."""
    from colorsys import rgb_to_hls
    h, _, _ = rgb_to_hls(kolor.red, kolor.green, kolor.blue)
    return Color(*hls_to_rgb(h, l, s))


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


def sciezka_zaokraglona(c: Canvas, punkty: list[tuple[float, float]], r: float) -> PDFPathObject:
    """Lamana przez punkty z kazdym zalamaniem zaokraglonym lukiem o promieniu r
    (cwiartka okregu jako krzywa Beziera). Odcinki musza byc osiowe, a kazdy
    przy zalamaniu miec co najmniej r, zeby luki sie nie nakladaly."""
    K = 0.5523                            # krzywa Beziera najblizsza cwiartce okregu
    p = c.beginPath()
    p.moveTo(*punkty[0])
    for (ax, ay), (bx, by), (cx_, cy_) in zip(punkty, punkty[1:], punkty[2:]):
        assert (ax == bx) != (ay == by) and (bx == cx_) != (by == cy_), "odcinki musza byc osiowe"
        assert abs(bx - ax) + abs(by - ay) >= r and abs(cx_ - bx) + abs(cy_ - by) >= r, \
            "odcinek za krotki na zaokraglenie"
        ux, uy = (bx - ax) / (abs(bx - ax) + abs(by - ay)), (by - ay) / (abs(bx - ax) + abs(by - ay))
        vx, vy = (cx_ - bx) / (abs(cx_ - bx) + abs(cy_ - by)), (cy_ - by) / (abs(cx_ - bx) + abs(cy_ - by))
        p1 = (bx - ux * r, by - uy * r)
        p2 = (bx + vx * r, by + vy * r)
        p.lineTo(*p1)
        p.curveTo(p1[0] + ux * r * K, p1[1] + uy * r * K, p2[0] - vx * r * K, p2[1] - vy * r * K, *p2)
    p.lineTo(*punkty[-1])
    return p


def rysuj_strzalke(c: Canvas, x: float, dol: float, wys_seg: float,
                   kierunek: str, kolor: Color) -> None:
    """Strzalka pola kafla, w wyblaklej barwie pola docelowego.

    Miejsce jest zawsze to samo: wygrana po prawej stronie liczby, przegrana
    po lewej (srodki_strzalek), kazda strzalka wysrodkowana na swoim punkcie
    w polowie wysokosci pola. O celu mowi ksztalt: prosta w gore/dol albo
    w prawo/lewo (dlugosci SEG) dla sasiada na tym samym pietrze skali; hak —
    polowka SEG bez grotu, zalamanie, SEG, zalamanie, odcinek z grotem
    (co najmniej SEG, a zawsze tyle, zeby miedzy spodem grotu a odcinkiem
    rownoleglym do niego zostala PRZERWA_GROTU kreski) — o zalamaniach zaokraglonych
    promieniem PROMIEN_HAKA dla skoku: "prawo-dol" i "lewo-gora" na wejscie
    w slupek wielosegmentowy, "gora-lewo" i "dol-prawo" na styk sekcji.
    Wszystkie maja ten sam plaski grot i te sama kreske."""
    # Haki sa o polowe mniejsze od bazowych wymiarow, proste o dziesiata czesc;
    # grot i kreska sa jedne dla wszystkich.
    SKALA = 0.5 if "-" in kierunek else 0.9
    GRUB = 1.4 * mm
    SEG, PROMIEN_HAKA = 6 * mm * SKALA, 2 * mm * SKALA
    A = SEG / 2                           # polowka: odcinek startowy haka (bez grotu)
    HEAD_W, HEAD_G = 5.4 * mm, 2.52 * mm  # wspolny grot: szeroki i plaski
    PRZERWA_GROTU = 1.8 * mm              # kreska miedzy spodem grotu a odcinkiem rownoleglym do niego
    KONCOWY = max(SEG, HEAD_G + PRZERWA_GROTU)   # ostatni odcinek haka, z grotem
    KONIEC = HEAD_G / 2                   # kreska konczy sie w polowie grotu — grot ja zakrywa
    BLADOSC = 0.6                         # domieszka barwy celu na bieli — strzalka nie krzyczy
    kolor = mieszaj(CARD, kolor, BLADOSC)
    xs, xw = srodki_strzalek(x)           # srodek strzalki przegranej / wygranej
    cy = dol + wys_seg / 2
    yg, yd = cy + A, cy - A               # zasieg prostych: SEG wokol srodka
    hg, hd = cy + (A + KONCOWY) / 2, cy - (A + KONCOWY) / 2   # zasieg hakow pionowych
    hp, hl = xw - (KONCOWY + A) / 2, xs + (KONCOWY + A) / 2   # poczatki hakow poziomych
    trasy: dict[str, tuple[list[tuple[float, float]], tuple[float, float], tuple[int, int]]] = {
        "gora": ([(xw, yd), (xw, yg - KONIEC)], (xw, yg), (0, 1)),
        "dol": ([(xs, yg), (xs, yd + KONIEC)], (xs, yd), (0, -1)),
        "prawo": ([(xw - A, cy), (xw + A - KONIEC, cy)], (xw + A, cy), (1, 0)),
        "lewo": ([(xs + A, cy), (xs - A + KONIEC, cy)], (xs - A, cy), (-1, 0)),
        "gora-lewo": ([(xw + A, hd), (xw + A, hd + A), (xw - A, hd + A), (xw - A, hg - KONIEC)],
                      (xw - A, hg), (0, 1)),
        "dol-prawo": ([(xs - A, hg), (xs - A, hg - A), (xs + A, hg - A), (xs + A, hd + KONIEC)],
                      (xs + A, hd), (0, -1)),
        "prawo-dol": ([(hp, yg), (hp + A, yg), (hp + A, yd), (hp + A + KONCOWY - KONIEC, yd)],
                      (hp + A + KONCOWY, yd), (1, 0)),
        "lewo-gora": ([(hl, yd), (hl - A, yd), (hl - A, yg), (hl - A - KONCOWY + KONIEC, yg)],
                      (hl - A - KONCOWY, yg), (-1, 0)),
    }
    punkty, (tx, ty), (dx, dy) = trasy[kierunek]
    c.saveState()
    c.setStrokeColor(kolor)
    c.setLineWidth(GRUB)
    c.setLineCap(1)
    c.setLineJoin(1)
    c.drawPath(sciezka_zaokraglona(c, punkty, PROMIEN_HAKA), stroke=1, fill=0)
    bx, by = tx - dx * HEAD_G, ty - dy * HEAD_G   # srodek podstawy grotu
    g = c.beginPath()
    g.moveTo(tx, ty)
    g.lineTo(bx - dy * HEAD_W / 2, by + dx * HEAD_W / 2)
    g.lineTo(bx + dy * HEAD_W / 2, by - dx * HEAD_W / 2)
    g.close()
    c.setFillColor(kolor)
    c.drawPath(g, stroke=0, fill=1)
    c.restoreState()


def rysuj_paski(c: Canvas, x: float, dol: float, wys: float, barwa: Color) -> None:
    """Paski pola: w kazdym slocie pionowe napisy — WYGRANA i SERIA przy lewej
    krawedzi, PRZEGRANA i pusty lustrzanie przy prawej — rozdzielone cienkimi
    kreskami w miejscach, gdzie staje krawedz magnesu. Skrajne paski maja tlo
    pola i napis w odcieniu liczb, wewnetrzne (SERIA, PRZEGRANA) — negatyw.
    W polu podwojnym kazdy slot ma wlasne paski."""
    assert wys in (POLE_WYS, POLE_WYS_2), f"nieznana wysokosc pola: {wys / mm:.1f} mm"
    ciemna = mieszaj(barwa, INK, 0.55)
    sloty = 2 if wys == POLE_WYS_2 else 1
    slot_h = wys / sloty
    lewe = [(x + nr * PASEK_W, napis, tint)
            for nr, (napis, tint) in enumerate(zip(zasady_tablicy.PASKI, TINT_PASKOW))]
    prawe = [(x + ETYKIETA_W + nr * PASEK_W, napis, tint)
             for nr, (napis, tint) in enumerate(zip(PASKI_PRAWE, reversed(TINT_PASKOW)))]
    negatyw = {TINT_POLA: TINT_PASKA, TINT_PASKA: TINT_POLA}   # napis odwrotnie do tla
    c.setLineWidth(KRESKA / 2)
    c.setStrokeColor(mieszaj(CARD, ciemna, KRESKA_SLOTU))
    for slot in range(sloty):
        y0 = dol + slot * slot_h
        for px, napis, tint in lewe + prawe:
            c.setFillColor(mieszaj(CARD, barwa, tint))
            c.rect(px, y0, PASEK_W, slot_h, stroke=0, fill=1)
            c.line(px, y0, px, y0 + slot_h)
            c.line(px + PASEK_W, y0, px + PASEK_W, y0 + slot_h)
            c.saveState()
            c.translate(px + PASEK_W / 2, y0 + slot_h / 2)
            c.rotate(90)
            c.setFillColor(mieszaj(CARD, barwa, negatyw[tint]))
            c.setFont(FONT_BOLD, PASEK_FS)
            c.drawCentredString(0, -0.36 * PASEK_FS, napis)
            c.restoreState()


def rozmiar_liczby() -> float:
    """Najwiekszy stopien pisma (do LICZBA_FS_MAX), przy ktorym najszersza
    liczba skali miesci sie w polu centralnym miedzy strefami strzalek,
    z luzem po obu stronach."""
    miejsce = CENTRUM_W - 2 * STRZALKA_W - 2 * LUZ_LICZBY
    return min(LICZBA_FS_MAX, LICZBA_FS_MAX * miejsce / najszersza_liczba(LICZBA_FS_MAX))


def najszersza_liczba(fs: float) -> float:
    """Szerokosc najszerszej liczby skali w stopniu pisma fs."""
    return max(pdfmetrics.stringWidth(liczba_skali(kyu), FONT_BOLD, fs)
               for grupa, _ in GRUPY for wiersz in grupa for kyu in wiersz)


def srodki_strzalek(x: float) -> tuple[float, float]:
    """(x strzalki przegranej, x strzalki wygranej) pola o lewej krawedzi x:
    ODSTEP_STRZALKI od krawedzi najszerszej liczby skali, symetrycznie."""
    brzeg = (POLE_SZER - najszersza_liczba(rozmiar_liczby())) / 2
    return x + brzeg - ODSTEP_STRZALKI, x + POLE_SZER - brzeg + ODSTEP_STRZALKI


def rysuj_kreske_slotow(c: Canvas, x: float, dol: float, wys: float, barwa: Color) -> None:
    """Jasna kreska dzielaca pole podwojne na dwa sloty, na cala szerokosc pola —
    rysowana przed liczba i strzalkami, wiec biegnie pod nimi."""
    assert wys in (POLE_WYS, POLE_WYS_2), f"nieznana wysokosc pola: {wys / mm:.1f} mm"
    c.setLineWidth(KRESKA / 2)
    c.setStrokeColor(mieszaj(CARD, mieszaj(barwa, INK, 0.55), KRESKA_SLOTU))
    for slot in range(1, 2 if wys == POLE_WYS_2 else 1):
        c.line(x, dol + slot * wys / 2, x + POLE_SZER, dol + slot * wys / 2)


def rysuj_liczba(c: Canvas, x: float, dol: float, wys: float, liczba: str,
                 barwa: Color, prog_: bool) -> None:
    """Liczba sily w tle: na srodku pola, w odcieniu sekcji nasyconym
    i ciemniejszym — jedna na pole, w podwojnym kreska slotow biegnie przez nia.
    Prog dostaje zaokraglona ramke w tej samej barwie."""
    fs = rozmiar_liczby()
    kolor = nasycona(barwa, LICZBA_S, LICZBA_L)
    cx = x + POLE_SZER / 2
    cy = dol + wys / 2
    szer, wys_l = c.stringWidth(liczba, FONT_BOLD, fs), 0.72 * fs
    c.setFont(FONT_BOLD, fs)
    c.setFillColor(kolor)
    c.drawCentredString(cx, cy - wys_l / 2, liczba)
    if prog_:
        c.setStrokeColor(kolor)
        c.setLineWidth(4 * KRESKA)
        c.roundRect(cx - szer / 2 - RAMKA_PROGU, cy - wys_l / 2 - RAMKA_PROGU,
                    szer + 2 * RAMKA_PROGU, wys_l + 2 * RAMKA_PROGU, 2 * mm, stroke=1, fill=0)


def rysuj_slupek(c: Canvas, x: float, y: float,
                 segmenty: list[tuple[str, Color, bool]],
                 wys_segmentu: float) -> None:
    """Slupek sekcji: segmenty (liczba, barwa, czy prog) od gory — kazdy jako
    osobny kafel z wlasnym obrysem, rozdzielone minimalna szczelina.

    Pole idzie lekkim odcieniem barwy, na nim kreska slotow (w podwojnym),
    liczba sily (prog w ramce), na to paski.
    """
    for nr, (liczba, barwa, prog_) in enumerate(segmenty):
        dol = y + (len(segmenty) - 1 - nr) * (wys_segmentu + SZCZELINA)
        c.saveState()
        c.clipPath(zaokraglony(c, x, dol, POLE_SZER, wys_segmentu, PROMIEN), stroke=0, fill=0)
        c.setFillColor(mieszaj(CARD, barwa, TINT_POLA))
        c.rect(x, dol, POLE_SZER, wys_segmentu, stroke=0, fill=1)
        rysuj_kreske_slotow(c, x, dol, wys_segmentu, barwa)
        rysuj_liczba(c, x, dol, wys_segmentu, liczba, barwa, prog_)
        rysuj_paski(c, x, dol, wys_segmentu, barwa)
        c.restoreState()
        # Obrys w ciemnej wersji barwy sekcji — kafel trzyma sie jednej
        # rodziny koloru.
        c.setStrokeColor(mieszaj(barwa, INK, 0.55))
        c.setLineWidth(KRESKA)
        c.drawPath(zaokraglony(c, x, dol, POLE_SZER, wys_segmentu, PROMIEN), stroke=1, fill=0)


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
        # Sila na bialej plakietce, ciasno wokol liczby, duzo barwy paska
        # dookola; liczba i stopien w barwie liczb z pol, zeby kafelek czytalo
        # sie tak samo jak tablice. Krój jak w tabelach wyrownania obok.
        szer_p = c.stringWidth(sila, FONT, KAFEL_FS) + 4 * mm
        wys_p = 0.72 * KAFEL_FS + 2.5 * mm
        c.setFillColor(CARD)
        c.roundRect(x + KAFEL_PAS / 2 - szer_p / 2, dol_y + KAFEL_H / 2 - wys_p / 2,
                    szer_p, wys_p, 1.5 * mm, stroke=0, fill=1)
        c.setFillColor(nasycona(barwa, LICZBA_S, LICZBA_L))   # jak liczby na polach
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
            segmenty = [(liczba_skali(wiersz[kolumna]), barwa, prog(wiersz[kolumna]))
                        for wiersz in grupa]
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


WERSJA = "08.09.2026"                  # dopiska wydruku; podbij przy zmianie zasad/ukladu
ZAMEK = Path(__file__).resolve().parent / "tablica.lock"


def odcisk() -> str:
    """Odcisk danych, ktore decyduja o tresci wydrukowanej tablicy.

    Sa tu zasady, kolumny pasa, paski serii, skala slupkow, przelicznik stopni
    i siatki wyrownania — wszystko, czego zmiana uniewaznia wiszacy wydruk. Wymiary
    czysto kosmetyczne swiadomie zostaja poza odciskiem."""
    dane = {
        "zasady": [[k, z, linie] for k, z, linie in zasady_tablicy.ZASADY],
        "kolumny": list(zasady_tablicy.KOLUMNY),
        "naglowki": dict(zasady_tablicy.NAGLOWKI),
        "paski": list(zasady_tablicy.PASKI) + [zasady_tablicy.PASEK_PRZEGRANEJ],
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
