#!/usr/bin/env python3
"""Tablica rankingowa na mala tablice magnetyczna klubu (67 x 93,5 cm).

Uruchomienie: python3 tablica/tablica_mala_pdf.py   (zapisuje tablica/tablica-mala.pdf)

Uklad i rysowanie sa wspolne z tablica_pdf.py; ten plik tylko dobiera wymiary:
wydruk przylepia sie na stale na mala tablice, wiec szerokosc idzie na styk
(670 mm), a wysokosc zostaje ponizej granicy 930 mm — nie trzeba jej wypelniac.
Etykiety magnetyczne z nazwiskami maja 50 x 25 mm; kratka 60 x 80 mm daje
etykiecie 5 mm luzu z boku, a jej puste pole 60 mm miesci dwie z 10 mm luzu.
"""

from pathlib import Path

from reportlab.lib.units import mm

from tablica_pdf import REPO, Uklad, generuj

MALA = Uklad(
    maks_w=670 * mm,                    # szerokosc malej tablicy, na styk
    maks_h=930 * mm,                    # wysokosc tablicy minus luz na zawieszki
    page_w=670 * mm,
    magnes_w=50 * mm, magnes_h=25 * mm,
    kratka_szer=60 * mm,
    pole=60 * mm,
    pasek=20 * mm,
    odstep=6 * mm,
    margines=16 * mm,
    naglowek_h=100 * mm,
    sekcja=12 * mm,
    wyr_skala=1.7,                      # cyfry okolo 3,5 mm — do czytania z bliska
    qr=30 * mm,
    notka_h=16 * mm,
    numer_fs=44,                        # cyfry ~11 mm na pasku 20 mm
    tytul_fs=80,
    podtytul_fs=27,
    adres_fs=24,
    ranking_fs=37,
    nazwa_wciecie=14 * mm,
    notka_fs=14,
    qr_podpis_fs=9,
    qr_gap=10 * mm,
    qr_podpis_odstep=4.5 * mm,
    adres_odstep=15 * mm,
    logo=54 * mm,
    tabela_gap=9 * mm,
)


if __name__ == "__main__":
    generuj(REPO / "tablica" / "tablica-mala.pdf", MALA)
