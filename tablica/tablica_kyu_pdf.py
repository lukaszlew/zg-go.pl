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

Struktura kolorow: sekcja ma wlasna barwe paskow, a prog — zamiast calego
paska — dostaje mala plakietke wokol liczby, w ciemniejszym odcieniu barwy
swojej sekcji, z biala liczba. Liczby calkowite sekcji cwiartkowych
(najnizsza komorka kolumny: 41-44, 46-49, 51-54) dostaja taka sama plakietke
w negatywie pola (ciemna, z liczba w barwie paska) — kolor zostaje przy
progach w pierwszej kolumnie.

Naglowek: logo z nazwa i adresem zg-go.pl/ranking po lewej, tabele wyrownania
wszystkich plansz (z karty gracza) po prawej — musza byc, bo z nich odczytuje
sie wyrownanie przy stoliku.
"""

import sys
from colorsys import hls_to_rgb
from pathlib import Path

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from tablica_pdf import (ACCENT, BG, CARD, CIEMNY, FONT, FONT_BOLD, FONT_SERIF,
                         FONT_SERIF_BOLD, INK, KODY_QR, KRESKA, MUTED, PROMIEN, REPO,
                         RULE, SILA, wymiary_siatki, zaokraglony,
                         zarejestruj_czcionki)

import karta_pdf                        # sciezke do tools/ dodaje tablica_pdf
import zasady_tablicy
from wyrownanie.tabela_html import PLANSZE


def _cwiartki(okragle: list[float]) -> list[list[float]]:
    """Sekcja cwiartkowa: nad wierszem okraglych ida -0,25, -0,5 i -0,75 kyu —
    kazda kolumna to ciagly odcinek skali, a okragla liczba stoi na dole."""
    return [[k - p for k in okragle] for p in (0.75, 0.5, 0.25, 0.0)]


# Sekcje wierszy wartosci (kyu; na paskach stoi sila = 50 - kyu): piatka stopni
# z progiem w lewym dolnym rogu (silniejszy po prawej, dan u gory);
# (wiersze, czy pola podwojne). Skala konczy sie na 54,75 sily.
GRUPY: list[tuple[list[list[float]], bool]] = [
    (_cwiartki([0.0, -1.0, -2.0, -3.0, -4.0]), False),
    (_cwiartki([5.0, 4.0, 3.0, 2.0, 1.0]), False),
    (_cwiartki([10.0, 9.0, 8.0, 7.0, 6.0]), False),
    ([[14.5, 13.5, 12.5, 11.5, 10.5], [15.0, 14.0, 13.0, 12.0, 11.0]], True),
    ([[19.5, 18.5, 17.5, 16.5, 15.5], [20.0, 19.0, 18.0, 17.0, 16.0]], True),
    ([[25.0, 24.0, 23.0, 22.0, 21.0]], True),
    # Ostatni wiersz to osobna sekcja: skala poczatkujacych o wiekszych skokach.
    ([[35.0, 32.0, 30.0, 28.0, 26.0]], True),
]

PAS_LICZBY = 24 * mm                    # kolorowy pasek z liczba, z lewej kratki
POLE_BIALE = 82 * mm                    # samo biale pole na etykiety
POLE_SZER = PAS_LICZBY + POLE_BIALE     # cala kratka
POLE_WYS = 30 * mm
POLE_WYS_2 = 2 * POLE_WYS - 5 * mm      # pole podwojne — miesci dwie etykiety
LICZBA_FS = 20
ODSTEP_GRUP = 7 * mm                    # sekcje rozdziela sam odstep (i kolor)
ODSTEP_POZIOM = 5 * mm

PAGE_W = 670 * mm                       # szerokosc malej tablicy, na styk
MARGINES = 15 * mm
SEKCJA = 10 * mm
NAGLOWEK_H = 106 * mm                   # pas nazwy nad pasem tabel i kodu QR
LOGO = 30 * mm
TYTUL_FS = 50
PODTYTUL_FS = 18
ADRES_FS = 22
QR = 28 * mm
QR_PODPIS_FS = 7
PAS_NAZWY_H = 44 * mm                   # logo + Semedori + podtytul + adres
PAS_ZASAD_H = 40 * mm                   # zasady rankingu na dole tablicy
ZASADY_TYTUL_FS = 11
ZASADY_FS = 9
ZASADY_LINIA_H = 4.4 * mm
ZASADY_GAP = 10 * mm                    # odstep miedzy kolumnami zasad
WYR_SKALA = 2.15                        # tabele wyrownania; cyfry ~4,3 mm
TABELA_GAP = 13 * mm
PODPIS_FS = 12                          # podpis wariantu na dole strony
MAKS_H = 930 * mm

KOLUMNY = 5
SIATKA_W = KOLUMNY * POLE_SZER + (KOLUMNY - 1) * ODSTEP_POZIOM
MARGINES_BOK = (PAGE_W - SIATKA_W) / 2

assert POLE_BIALE > 50 * mm + 4 * mm, "etykieta 50 mm nie wchodzi w pole"
assert POLE_WYS > 25 * mm + 4 * mm, "etykieta 25 mm nie wchodzi w pole na wysokosc"
assert MARGINES_BOK > 0, f"siatka szersza niz tablica: {SIATKA_W / mm:.0f} mm"


def liczba_skali(kyu: float) -> str:
    """Na paskach stoi sila klubowa: 50 - kyu (1 dan = 50, 50 kyu = 0)."""
    return f"{50 - kyu:g}".replace(".", ",").replace("-", "−")


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
                 segmenty: list[tuple[str, Color, Color, Color | None]],
                 wys_segmentu: float) -> None:
    """Slupek sekcji: segmenty (liczba, kolor paska, kolor liczby, plakietka)
    od gory, wspolny obrys i kreski dzielace przez cala szerokosc.

    Prog nie barwi calego paska: dostaje mala plakietke wokol liczby
    (kolor w czwartym polu segmentu) z biala liczba.
    """
    wys = len(segmenty) * wys_segmentu
    c.setFillColor(CARD)
    c.drawPath(zaokraglony(c, x, y, POLE_SZER, wys, PROMIEN), stroke=0, fill=1)
    c.saveState()
    c.clipPath(zaokraglony(c, x, y, POLE_SZER, wys, PROMIEN), stroke=0, fill=0)
    for nr, (_, kolor, _, _) in enumerate(segmenty):
        c.setFillColor(kolor)
        c.rect(x, y + wys - (nr + 1) * wys_segmentu, PAS_LICZBY, wys_segmentu,
               stroke=0, fill=1)
    c.restoreState()
    c.setStrokeColor(INK)
    c.setLineWidth(KRESKA)
    c.line(x + PAS_LICZBY, y, x + PAS_LICZBY, y + wys)
    for nr in range(1, len(segmenty)):
        c.line(x, y + wys - nr * wys_segmentu, x + POLE_SZER, y + wys - nr * wys_segmentu)
    c.drawPath(zaokraglony(c, x, y, POLE_SZER, wys, PROMIEN), stroke=1, fill=0)
    c.setFont(FONT_BOLD, LICZBA_FS)
    for nr, (liczba, _, kolor_liczby, plakietka) in enumerate(segmenty):
        srodek_x = x + PAS_LICZBY / 2
        srodek_y = y + wys - nr * wys_segmentu - wys_segmentu / 2
        if plakietka is not None:
            szer = c.stringWidth(liczba, FONT_BOLD, LICZBA_FS) + 6 * mm
            wys_p = 0.72 * LICZBA_FS + 5.5 * mm
            c.setFillColor(plakietka)
            c.roundRect(srodek_x - szer / 2, srodek_y - wys_p / 2, szer, wys_p,
                        2 * mm, stroke=0, fill=1)
        c.setFillColor(kolor_liczby)
        c.drawCentredString(srodek_x, srodek_y - 0.36 * LICZBA_FS, liczba)


def rysuj_naglowek_kyu(c: Canvas, gora_y: float) -> None:
    """Dwa pasy: u gory logo, nazwa, podtytul i adres; pod nimi trzy tabele
    wyrownania w rzedzie, a przy prawym marginesie kod QR do zasad."""
    x = MARGINES_BOK
    gora = gora_y - 2 * mm
    karta_pdf.rysuj_logo(c, karta_pdf.SEMEDORI.logo, x, gora - LOGO - 4 * mm, LOGO, INK)
    tx = x + LOGO + 7 * mm
    c.setFillColor(INK)
    c.setFont(FONT_SERIF_BOLD, TYTUL_FS)
    c.drawString(tx, gora - 15 * mm, "Semedori")
    c.setFillColor(CIEMNY)
    c.setFont(FONT_SERIF, PODTYTUL_FS)
    c.drawString(tx, gora - 25 * mm, "Gramy w Go w Zielonej Górze")
    c.setFillColor(ACCENT)
    c.setFont(FONT_SERIF_BOLD, ADRES_FS)
    c.drawString(tx, gora - 35 * mm, "zg-go.pl/ranking")

    gora_tabel = gora - PAS_NAZWY_H
    wymiary = [tuple(w * WYR_SKALA for w in wymiary_siatki(p)) for p in PLANSZE]
    tab_x = x
    for (szer, wys), plansza in zip(wymiary, PLANSZE):
        c.saveState()
        c.translate(tab_x, gora_tabel)
        c.scale(WYR_SKALA, WYR_SKALA)
        karta_pdf.draw_siatka(c, karta_pdf.KOLOROWA, 0, 0, plansza)
        c.restoreState()
        tab_x += szer + TABELA_GAP

    url, podpis = KODY_QR[0]            # jeden kod: zasady rankingu na zg-go.pl
    qx = PAGE_W - MARGINES_BOK - QR
    assert qx > tab_x, "kod QR nachodzi na tabele wyrownania"
    karta_pdf.draw_qr(c, qx, gora_tabel - QR, QR, url)
    c.setFillColor(MUTED)
    c.setFont(FONT, QR_PODPIS_FS)
    c.drawCentredString(qx + QR / 2, gora_tabel - QR - 4 * mm, podpis)


def rysuj_zasady(c: Canvas, gora_y: float) -> None:
    """Pas zasad rankingu na dole tablicy: kolumna na kolumne zasad."""
    kolumn = len(zasady_tablicy.KOLUMNY)
    col_w = (SIATKA_W - (kolumn - 1) * ZASADY_GAP) / kolumn
    for nr, tytul in enumerate(zasady_tablicy.KOLUMNY):
        x = MARGINES_BOK + nr * (col_w + ZASADY_GAP)
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, ZASADY_TYTUL_FS)
        c.drawString(x, gora_y, tytul.upper())
        c.setStrokeColor(RULE)
        c.setLineWidth(0.8 * mm)
        c.line(x, gora_y - 2.2 * mm, x + col_w, gora_y - 2.2 * mm)
        y = gora_y - 8 * mm
        for zasada in zasady_tablicy.w_kolumnie(tytul):
            c.setFillColor(MUTED)
            c.setFont(FONT_BOLD, ZASADY_FS)
            c.drawString(x, y, "•")
            c.setFillColor(INK)
            linia, szer = [], 0.0
            from reportlab.pdfbase import pdfmetrics
            spacja = pdfmetrics.stringWidth(" ", FONT, ZASADY_FS)
            for slowo in zasada.split():
                w = pdfmetrics.stringWidth(slowo, FONT, ZASADY_FS)
                if linia and szer + spacja + w > col_w - 5 * mm:
                    c.setFont(FONT, ZASADY_FS)
                    c.drawString(x + 5 * mm, y, " ".join(linia))
                    y -= ZASADY_LINIA_H
                    linia, szer = [], 0.0
                linia.append(slowo)
                szer += w + (spacja if len(linia) > 1 else 0)
            c.setFont(FONT, ZASADY_FS)
            c.drawString(x + 5 * mm, y, " ".join(linia))
            y -= ZASADY_LINIA_H + 1.2 * mm
        assert y >= gora_y - PAS_ZASAD_H, f"kolumna zasad '{tytul}' nie miesci sie w pasie"


def sekcje_tablicy() -> list[tuple[list[list[float]], float]]:
    """Sekcje jako (wiersze kyu od gory, wysokosc segmentu slupka)."""
    return [(grupa, POLE_WYS_2 if podwojne else POLE_WYS) for grupa, podwojne in GRUPY]


def rysuj_strone(c: Canvas, page_h: float, podpis: str | None,
                 kolory: list[Color]) -> None:
    sekcje = sekcje_tablicy()
    assert len(kolory) == len(sekcje), "paleta musi miec barwe dla kazdej sekcji"
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, page_h, stroke=0, fill=1)
    rysuj_naglowek_kyu(c, page_h - MARGINES)

    y = page_h - MARGINES - NAGLOWEK_H - SEKCJA
    for nr, (grupa, wys_segmentu) in enumerate(sekcje):
        barwa = kolory[nr]
        kolor_plakietki = mieszaj(barwa, INK, 0.55)
        y -= (ODSTEP_GRUP if nr > 0 else 0) + len(grupa) * wys_segmentu
        cwiartkowa = len(grupa) == 4
        for kolumna in range(KOLUMNY):
            segmenty = []
            for wiersz in grupa:
                kyu = wiersz[kolumna]
                if prog(kyu):
                    segmenty.append((liczba_skali(kyu), barwa, CARD, kolor_plakietki))
                elif cwiartkowa and kyu == int(kyu):
                    # calkowite poza progiem: ta sama plakietka w negatywie pola
                    segmenty.append((liczba_skali(kyu), barwa, barwa, INK))
                else:
                    liczba = INK if jasny(barwa) else CARD
                    segmenty.append((liczba_skali(kyu), barwa, liczba, None))
            x = MARGINES_BOK + kolumna * (POLE_SZER + ODSTEP_POZIOM)
            rysuj_slupek(c, x, y, segmenty, wys_segmentu)

    rysuj_zasady(c, y - SEKCJA - 5 * mm)
    if podpis is not None:
        c.setFillColor(MUTED)
        c.setFont(FONT, PODPIS_FS)
        c.drawString(MARGINES_BOK, 4 * mm, podpis)


def generuj(sciezka: Path, palety: list[tuple[str, list[Color]]], podpisy: bool) -> None:
    sekcje = sekcje_tablicy()
    siatka_h = (sum(len(grupa) * wys for grupa, wys in sekcje)
                + (len(sekcje) - 1) * ODSTEP_GRUP)
    page_h = (MARGINES + NAGLOWEK_H + SEKCJA + siatka_h + SEKCJA + PAS_ZASAD_H
              + MARGINES)
    assert page_h <= MAKS_H, f"tablica stopni za wysoka: {page_h / mm:.0f} mm"

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
