#!/usr/bin/env python3
"""Tabele wyrownania Ishikury Noboru (9p) dla malych planszy.

Stara rekomendacja japonska: artykul o komi i wyrownaniu na 9x9 i 13x13 w
miesieczniku Igo Kurabu, okolo 1985, oparty na wynikach wielu partii zawodowiec
kontra zawodowiec na tych planszach.

Obie tabele sa regularne od roznicy 1 w gore — 9x9 idzie po 3 punkty na stopien
przy kamieniu wartym 12, 13x13 po 5 przy kamieniu wartym 15. Wyjatkiem jest tylko
gra rowna: komi 5,5 zamiast 6 skraca pierwszy krok do 2,5 (odpowiednio 5,5) i
odbiera remis. Kazde inne komi jest calkowite, wiec przy roznicy 1 i wiekszej
remis jest mozliwy.

Wyrownanie zaczyna sie tu od jednego kamienia, czyli gra rowna to "1 kamien",
a nie "0 kamieni" — inaczej niz w LSG, tak samo jak u Hunta.
"""

from .tabela import Arytmetyka, Tabela, UWAGA_KOMI, sprawdz

NAZWA = "ishikura"

# TODO: potwierdzic adres — tabele przyszly jako tekst, a nie ze strony.
_STRONA = "https://senseis.xmp.net/?HandicapForSmallerBoardSizes"

ZRODLA: dict[str, str] = {"9x9": _STRONA, "13x13": _STRONA}

UWAGA = (
    UWAGA_KOMI
    + " Gra równa ma komi 5,5 i nie kończy się remisem;"
    + " przy różnicy 1 i większej komi jest całkowite, więc remis jest możliwy."
)

TABELA_9X9: Tabela = [
    (0, 1, 5.5),
    (1, 1, 3),
    (2, 1, 0),
    (3, 1, -3),
    (4, 1, -6),
    (5, 2, 3),
    (6, 2, 0),
    (7, 2, -3),
    (8, 2, -6),
    (9, 3, 3),
    (10, 3, 0),
    (11, 3, -3),
    (12, 3, -6),
    (13, 4, 3),
    (14, 4, 0),
    (15, 4, -3),
    (16, 4, -6),
    (17, 5, 3),
    (18, 5, 0),
    (19, 5, -3),
    (20, 5, -6),
    (21, 6, 3),
    (22, 6, 0),
    (23, 6, -3),
    (24, 6, -6),
    (25, 7, 3),
    (26, 7, 0),
    (27, 7, -3),
    (28, 7, -6),
    (29, 8, 3),
    (30, 8, 0),
]

TABELA_13X13: Tabela = [
    (0, 1, 5.5),
    (1, 1, 0),
    (2, 1, -5),
    (3, 2, 5),
    (4, 2, 0),
    (5, 2, -5),
    (6, 3, 5),
    (7, 3, 0),
    (8, 3, -5),
    (9, 4, 5),
    (10, 4, 0),
    (11, 4, -5),
    (12, 5, 5),
    (13, 5, 0),
    (14, 5, -5),
    (15, 6, 5),
    (16, 6, 0),
    (17, 6, -5),
    (18, 7, 5),
    (19, 7, 0),
    (20, 7, -5),
    (21, 8, 5),
    (22, 8, 0),
    (23, 8, -5),
    (24, 9, 5),
    (25, 9, 0),
    (26, 9, -5),
    (27, 10, 5),
    (28, 10, 0),
    (29, 10, -5),
    (30, 11, 5),
]

TABELE: dict[str, Tabela] = {"9x9": TABELA_9X9, "13x13": TABELA_13X13}

ARYTMETYKA: dict[str, Arytmetyka] = {
    "9x9": Arytmetyka(wartosc_kamienia=12, krok=3, od=1),
    "13x13": Arytmetyka(wartosc_kamienia=15, krok=5, od=1),
}

sprawdz(TABELE)
