#!/usr/bin/env python3
"""Tablica stopni na mala tablice magnetyczna (67 x 93,5 cm) — szkic.

Uruchomienie: python3 tablica/tablica_kyu_pdf.py   (zapisuje tablica/tablica-kyu.pdf)

Siatka 5 kolumn kratek: kolorowy pasek z liczba sily klubowej z lewej
(sila = 50 - kyu: 1 dan = 50, 50 kyu = 0; samych nazw kyu/dan na tablicy
nie ma), obok biale pole 82 x 32 mm na etykiety magnetyczne 50 x 25 mm;
cala kratka ma 106 mm.
Silniejszy po prawej, dan u gory. Skala do sily 40 idzie cwiartkami, nizej
polowkami. Kazda kolumna sekcji scala sie w jeden slupek: wspolny obrys,
w srodku kreski dzielace segmenty progresji (np. 50 / 49,75 / 49,5 / 49,25),
a pasek z lewej niesie liczbe kazdego segmentu. Zielone sa okragle piatki
sily (55-20) w prawych rogach sekcji. Sekcje rozdziela wyrazny odstep.

Naglowek: logo z nazwa i adresem zg-go.pl/ranking po lewej, tabele wyrownania
wszystkich plansz (z karty gracza) po prawej — musza byc, bo z nich odczytuje
sie wyrownanie przy stoliku.
"""

from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from tablica_pdf import (ACCENT, BG, CARD, FONT_BOLD, FONT_SERIF_BOLD, INK, KRESKA,
                         PROMIEN, REPO, RULE, SILA, wymiary_siatki, zaokraglony,
                         zarejestruj_czcionki)

import karta_pdf                        # sciezke do tools/ dodaje tablica_pdf
from wyrownanie.tabela_html import PLANSZE

def _cwiartki(gorny_wiersz: list[float]) -> list[list[float]]:
    """Sekcja cwiartkowa: pod wierszem okraglych ida +0,25, +0,5 i +0,75 —
    kazda kolumna to ciagly odcinek skali, a okragla liczba stoi na gorze."""
    return [[k + p for k in gorny_wiersz] for p in (0.0, 0.25, 0.5, 0.75)]


# Sekcje wierszy wartosci: piatka stopni konczaca sie okragla liczba w prawym
# gornym rogu (silniejszy po prawej, dan u gory); (wiersze, czy pola podwojne).
GRUPY: list[tuple[list[list[float]], bool]] = [
    (_cwiartki([-1.0, -2.0, -3.0, -4.0, -5.0]), False),
    (_cwiartki([4.0, 3.0, 2.0, 1.0, 0.0]), False),
    (_cwiartki([9.0, 8.0, 7.0, 6.0, 5.0]), False),
    ([[14.0, 13.0, 12.0, 11.0, 10.0], [14.5, 13.5, 12.5, 11.5, 10.5]], True),
    ([[19.0, 18.0, 17.0, 16.0, 15.0], [19.5, 18.5, 17.5, 16.5, 15.5]], True),
    ([[24.0, 23.0, 22.0, 21.0, 20.0]], True),
    # Ostatni wiersz to osobna sekcja: skala poczatkujacych o wiekszych skokach.
    ([[40.0, 34.0, 30.0, 27.0, 25.0]], True),
]

PAS_LICZBY = 24 * mm                    # kolorowy pasek z liczba, z lewej kratki
POLE_BIALE = 82 * mm                    # samo biale pole na etykiety
POLE_SZER = PAS_LICZBY + POLE_BIALE     # cala kratka
POLE_WYS = 32 * mm
POLE_WYS_2 = 2 * POLE_WYS - 5 * mm      # pole podwojne: 57 mm, z linia dzielaca
LICZBA_FS = 20
ODSTEP_GRUP = 8 * mm
ODSTEP_POZIOM = 12 * mm

PAGE_W = 670 * mm                       # szerokosc malej tablicy, na styk
MARGINES = 15 * mm
SEKCJA = 10 * mm
NAGLOWEK_H = 80 * mm                    # logo+nazwa+adres | tabele wyrownania
LOGO = 30 * mm
TYTUL_FS = 40
ADRES_FS = 18
WYR_SKALA = 2.0                         # tabele wyrownania; cyfry ~4 mm
TABELA_GAP = 9 * mm
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


def zielona(kyu: float) -> bool:
    """Wyroznione okragle piatki sily: 55, 50, 45, 40, 35, 30, 25 i 20."""
    return kyu in (-5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0)


def rysuj_slupek(c: Canvas, x: float, y: float, wartosci: list[float],
                 wys_segmentu: float) -> None:
    """Slupek sekcji: segmenty progresji jeden nad drugim we wspolnym obrysie.

    wartosci ida od gory do dolu; kazdy segment ma na pasku z lewej swoja
    liczbe (zielony segment i biala liczba przy okraglych piatkach, poza tym
    zloty pasek i zielona liczba), a segmenty rozdzielaja kreski przez cala
    szerokosc slupka.
    """
    wys = len(wartosci) * wys_segmentu
    c.setFillColor(CARD)
    c.drawPath(zaokraglony(c, x, y, POLE_SZER, wys, PROMIEN), stroke=0, fill=1)
    c.saveState()
    c.clipPath(zaokraglony(c, x, y, POLE_SZER, wys, PROMIEN), stroke=0, fill=0)
    for nr, kyu in enumerate(wartosci):
        c.setFillColor(SILA if zielona(kyu) else RULE)
        c.rect(x, y + wys - (nr + 1) * wys_segmentu, PAS_LICZBY, wys_segmentu,
               stroke=0, fill=1)
    c.restoreState()
    c.setStrokeColor(INK)
    c.setLineWidth(KRESKA)
    c.line(x + PAS_LICZBY, y, x + PAS_LICZBY, y + wys)
    for nr in range(1, len(wartosci)):
        c.line(x, y + wys - nr * wys_segmentu, x + POLE_SZER, y + wys - nr * wys_segmentu)
    c.drawPath(zaokraglony(c, x, y, POLE_SZER, wys, PROMIEN), stroke=1, fill=0)
    c.setFont(FONT_BOLD, LICZBA_FS)
    for nr, kyu in enumerate(wartosci):
        # Liczby ida kolorem sily — bialo tylko na zielonych segmentach.
        c.setFillColor(CARD if zielona(kyu) else SILA)
        srodek = y + wys - nr * wys_segmentu - wys_segmentu / 2
        c.drawCentredString(x + PAS_LICZBY / 2, srodek - 0.36 * LICZBA_FS, liczba_skali(kyu))


def rysuj_naglowek_kyu(c: Canvas, gora_y: float) -> None:
    """Logo, nazwa i adres po lewej; trzy tabele wyrownania w rzedzie po prawej."""
    srodek = gora_y - NAGLOWEK_H / 2
    x = MARGINES_BOK
    karta_pdf.rysuj_logo(c, karta_pdf.SEMEDORI.logo, x, srodek - LOGO / 2 + 4 * mm, LOGO, INK)
    c.setFillColor(INK)
    c.setFont(FONT_SERIF_BOLD, TYTUL_FS)
    c.drawString(x + LOGO + 6 * mm, srodek - 0.36 * TYTUL_FS + 4 * mm, "Semedori")
    c.setFillColor(ACCENT)
    c.setFont(FONT_SERIF_BOLD, ADRES_FS)
    c.drawString(x + LOGO + 6 * mm, srodek - LOGO / 2 - 2 * mm, "zg-go.pl/ranking")

    wymiary = [tuple(w * WYR_SKALA for w in wymiary_siatki(p)) for p in PLANSZE]
    tabele_w = sum(w for w, _ in wymiary) + (len(wymiary) - 1) * TABELA_GAP
    tab_x = PAGE_W - MARGINES_BOK - tabele_w
    for (szer, wys), plansza in zip(wymiary, PLANSZE):
        c.saveState()
        c.translate(tab_x, srodek + wys / 2)
        c.scale(WYR_SKALA, WYR_SKALA)
        karta_pdf.draw_siatka(c, karta_pdf.KOLOROWA, 0, 0, plansza)
        c.restoreState()
        tab_x += szer + TABELA_GAP


def sekcje_tablicy() -> list[tuple[list[list[float]], float]]:
    """Sekcje jako (wiersze kyu od gory, wysokosc segmentu slupka)."""
    return [(grupa, POLE_WYS_2 if podwojne else POLE_WYS) for grupa, podwojne in GRUPY]


def generuj(sciezka: Path) -> None:
    sekcje = sekcje_tablicy()
    siatka_h = (sum(len(grupa) * wys for grupa, wys in sekcje)
                + (len(sekcje) - 1) * ODSTEP_GRUP)
    page_h = MARGINES + NAGLOWEK_H + SEKCJA + siatka_h + MARGINES
    assert page_h <= MAKS_H, f"tablica stopni za wysoka: {page_h / mm:.0f} mm"

    zarejestruj_czcionki()
    c = Canvas(str(sciezka), pagesize=(PAGE_W, page_h))
    c.setTitle("Tablica stopni — Semedori")
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, page_h, stroke=0, fill=1)
    rysuj_naglowek_kyu(c, page_h - MARGINES)

    y = page_h - MARGINES - NAGLOWEK_H - SEKCJA
    for nr, (grupa, wys_segmentu) in enumerate(sekcje):
        y -= (ODSTEP_GRUP if nr > 0 else 0) + len(grupa) * wys_segmentu
        for kolumna in range(KOLUMNY):
            x = MARGINES_BOK + kolumna * (POLE_SZER + ODSTEP_POZIOM)
            rysuj_slupek(c, x, y, [wiersz[kolumna] for wiersz in grupa], wys_segmentu)
    c.showPage()
    c.save()
    print(f"{sciezka.relative_to(REPO)}: {PAGE_W / mm:.0f} x {page_h / mm:.0f} mm")


if __name__ == "__main__":
    generuj(REPO / "tablica" / "tablica-kyu.pdf")
