#!/usr/bin/env python3
"""Tablica stopni na mala tablice magnetyczna (67 x 93,5 cm).

Uruchomienie: python3 tablica/tablica_kyu_pdf.py   (zapisuje tablica/tablica-kyu.pdf
w wybranej palecie); z opcja --palety pisze tablica-kyu-palety.pdf — strona na
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
from reportlab.pdfgen.canvas import Canvas

from tablica_pdf import (ACCENT, BG, CARD, CIEMNY, FONT, FONT_BOLD, FONT_SERIF,
                         FONT_SERIF_BOLD, INK, KRESKA, MUTED, PROMIEN, REPO, RULE,
                         SILA, wymiary_siatki, zaokraglony, zarejestruj_czcionki)

import karta_pdf                        # sciezke do tools/ dodaje tablica_pdf
import zasady_tablicy
from wyrownanie.tabela_html import PLANSZE


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
    ([[14.5, 13.5, 12.5, 11.5, 10.5], [15.0, 14.0, 13.0, 12.0, 11.0]], True),
    ([[19.5, 18.5, 17.5, 16.5, 15.5], [20.0, 19.0, 18.0, 17.0, 16.0]], True),
    ([[25.0, 24.0, 23.0, 22.0, 21.0]], True),
    # Ostatni wiersz to osobna sekcja: skala poczatkujacych o wiekszych skokach.
    ([[35.0, 32.0, 30.0, 28.0, 26.0]], True),
]

PAS_LICZBY = 24 * mm                    # kolorowy pasek z liczba, z lewej kratki
POLE_BIALE = 83 * mm                    # samo biale pole na etykiety
POLE_SZER = PAS_LICZBY + POLE_BIALE     # cala kratka
POLE_WYS = 32 * mm                      # wymog: dokladnie 32
POLE_WYS_2 = 63 * mm                    # dwa pola minus wspolna kreska; miesci dwie etykiety
LICZBA_FS = 20
LICZBA_PROG_FS = 30                     # progi: ta sama plakietka, wieksza czcionka
TINT_POLA = 0.12                        # domieszka barwy sekcji w bialych polach
# Obrysy, kreski i czcionka wewnatrz komorek ida szaroscia, nie czernia —
# czern zostaje w naglowku, zasadach i tabelach wyrownania.
SZAROSC_KOMOREK = HexColor("#4f4f4f")
ODSTEP_POZIOM = 5 * mm

# Wydruk ma zawsze dokladnie rozmiar malej tablicy minus 2 mm z kazdego
# wymiaru; wolna wysokosc idzie w marginesy — dwie trzecie na dol, jedna
# trzecia na gore.
PAGE_W = 668 * mm
PAGE_H = 933 * mm
MARGINES = 10 * mm                      # baza; reszte dokladaja marginesy()
ODSTEP_GRUP = 8 * mm
SEKCJA = 8 * mm
NAGLOWEK_H = 50 * mm                    # jeden pas: logo, nazwa, podtytul, adres
LOGO = 38 * mm
TYTUL_FS = 50
TYTUL_ROZSTRZELENIE = 5                 # odstep miedzy literami "Semedori" (pt)
PODTYTUL_FS = 18
ADRES_FS = 37
# Dolny pas to jeden rzad kafli: trzy kolumny zasad i trzy tabele wyrownania
# obok siebie — najwyzszy kafel (tabela 19x19) wyznacza jego wysokosc.
DOLNY_PAS_H = 61 * mm
ZASADY_KOL_W = 112 * mm
KAFEL_W = 52 * mm                       # przelicznik sil na stopnie pod zasadami
KAFEL_H = 18 * mm
KAFEL_PAS = 20 * mm
KAFEL_GAP = 8 * mm
KAFEL_FS = 13

# Punkty zaczepienia skali do oficjalnych stopni; numer wskazuje sekcje,
# ktorej barwa maluje kafelek.
PRZELICZNIK: list[tuple[str, str, int]] = [
    ("50", "≈ 1 dan", 0),
    ("40", "≈ 10 kyu", 2),
    ("30", "≈ 20 kyu", 4),
    ("20", "≈ 30 kyu", 6),
]
ZASADY_TYTUL_FS = 12
ZASADY_FS = 10.5
ZASADY_LINIA_H = 4.9 * mm
WYR_SKALA = 2.15                        # tabele wyrownania; cyfry ~4,3 mm
TABELA_GAP = 13 * mm
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
    """Progiem jest sila podzielna przez 5, od 25 w gore — skala poczatkujacych
    (15 i 20 w ostatnim wierszu) progow nie ma."""
    sila = 50 - kyu
    return sila % 5 == 0 and sila >= 25


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
    return [top] + przejscie(h_od, h_do, s_, l_, 6)


def _top_ciemny(h: float, s_: float, l_: float) -> Color:
    """Top jako ciemniejsza, mocniejsza wersja pierwszej barwy luku."""
    return mieszaj(hsl(h, s_, l_), INK, 0.35)


def _top_przedluzony(h_od: float, h_do: float) -> Color:
    """Top kontynuuje luk o jeden krok poza poczatek — cieplejszy i glebszy."""
    return hsl(h_od - (h_do - h_od) / 5, 0.48, 0.60)


# Palety do porownywania (--palety); top danow akcentuje delikatnie —
# w natezeniu zblizonym do reszty luku, nie mocniej.
PALETY: list[tuple[str, list[Color]]] = [
    ("luk A, top przedluzony", _paleta(hsl(15, 0.44, 0.70), *LUK_A, 0.44, 0.70)),
    ("luk A odwrocony, top wino", _paleta(hsl(350, 0.40, 0.68), LUK_A[1], LUK_A[0], 0.44, 0.70)),
    ("luk A gleboki, top wino", _paleta(hsl(350, 0.44, 0.60), *LUK_A, 0.50, 0.62)),
]

WYBRANA = PALETY[0]                     # paleta wydruku: luk A, top przedluzony


def rysuj_slupek(c: Canvas, x: float, y: float,
                 segmenty: list[tuple[str, Color, Color, Color | None, float]],
                 wys_segmentu: float) -> None:
    """Slupek sekcji: segmenty (liczba, barwa, kolor liczby, plakietka, stopien
    pisma) od gory, wspolny obrys i kreski dzielace przez cala szerokosc.

    Pasek segmentu idzie pelna barwa, biale pole jej lekkim odcieniem; liczby
    calkowite dostaja plakietke w negatywie (kolor w czwartym polu segmentu).
    """
    wys = len(segmenty) * wys_segmentu
    c.saveState()
    c.clipPath(zaokraglony(c, x, y, POLE_SZER, wys, PROMIEN), stroke=0, fill=0)
    for nr, (_, barwa, _, _, _) in enumerate(segmenty):
        dol = y + wys - (nr + 1) * wys_segmentu
        c.setFillColor(mieszaj(CARD, barwa, TINT_POLA))
        c.rect(x + PAS_LICZBY, dol, POLE_SZER - PAS_LICZBY, wys_segmentu, stroke=0, fill=1)
        c.setFillColor(barwa)
        c.rect(x, dol, PAS_LICZBY, wys_segmentu, stroke=0, fill=1)
    c.restoreState()
    c.setStrokeColor(SZAROSC_KOMOREK)
    c.setLineWidth(KRESKA)
    c.line(x + PAS_LICZBY, y, x + PAS_LICZBY, y + wys)
    for nr in range(1, len(segmenty)):
        c.line(x, y + wys - nr * wys_segmentu, x + POLE_SZER, y + wys - nr * wys_segmentu)
    c.drawPath(zaokraglony(c, x, y, POLE_SZER, wys, PROMIEN), stroke=1, fill=0)
    for nr, (liczba, _, kolor_liczby, plakietka, fs) in enumerate(segmenty):
        srodek_x = x + PAS_LICZBY / 2
        srodek_y = y + wys - nr * wys_segmentu - wys_segmentu / 2
        if plakietka is not None:
            szer = c.stringWidth(liczba, FONT_BOLD, fs) + 5 * mm
            wys_p = 0.72 * fs + 5 * mm
            c.setFillColor(plakietka)
            c.roundRect(srodek_x - szer / 2, srodek_y - wys_p / 2, szer, wys_p,
                        2 * mm, stroke=0, fill=1)
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
    c.setFillColor(ACCENT)
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
        c.setStrokeColor(SZAROSC_KOMOREK)
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


def rysuj_dol(c: Canvas, gora_y: float, kolory: list[Color]) -> None:
    """Dolny pas jednym rzedem kafli: kolumny zasad, potem tabele wyrownania;
    pod zasadami rzad kafelkow przelicznika sil na oficjalne stopnie.

    Kafle maja bardzo rozne szerokosci, wiec ida od lewej w naturalnych
    rozmiarach, a caly luz zbiera sie w odstepach po rowno — pas wykorzystuje
    pelna szerokosc siatki i wysokosc najwyzszego kafla (tabeli 19x19).
    """
    wymiary = [tuple(w * WYR_SKALA for w in wymiary_siatki(p)) for p in PLANSZE]
    kafli_w = (len(zasady_tablicy.KOLUMNY) * ZASADY_KOL_W
               + sum(szer for szer, _ in wymiary))
    przerw = len(zasady_tablicy.KOLUMNY) + len(wymiary) - 1
    luz = (SIATKA_W - kafli_w) / przerw
    assert luz >= 4 * mm, f"dolny pas nie zostawia przerw: {luz / mm:.1f} mm"
    x = MARGINES_BOK
    for tytul in zasady_tablicy.KOLUMNY:
        rysuj_kolumne_zasad(c, x, gora_y - 1 * mm, tytul)
        x += ZASADY_KOL_W + luz
    rysuj_przelicznik(c, MARGINES_BOK, x - luz, gora_y - DOLNY_PAS_H - 2 * mm, kolory)
    for (szer, wys), plansza in zip(wymiary, PLANSZE):
        c.saveState()
        c.translate(x, gora_y)
        c.scale(WYR_SKALA, WYR_SKALA)
        karta_pdf.draw_siatka(c, karta_pdf.KOLOROWA, 0, 0, plansza, ",5")
        c.restoreState()
        x += szer + luz


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
                if prog(kyu):
                    segmenty.append((liczba_skali(kyu), barwa, barwa, CARD, LICZBA_PROG_FS))
                elif kyu == int(kyu):
                    # kazda calkowita dostaje biala plakietke; 15 — jak progi,
                    # bo zamyka skale od dolu
                    fs = LICZBA_PROG_FS if kyu == 35.0 else LICZBA_FS
                    segmenty.append((liczba_skali(kyu), barwa, barwa, CARD, fs))
                else:
                    liczba = SZAROSC_KOMOREK if jasny(barwa) else CARD
                    segmenty.append((liczba_skali(kyu), barwa, liczba, None, LICZBA_FS))
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
        generuj(REPO / "tablica" / "tablica-kyu-palety.pdf", PALETY, podpisy=True)
    else:
        generuj(REPO / "tablica" / "tablica-kyu.pdf", [WYBRANA], podpisy=False)
