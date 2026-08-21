#!/usr/bin/env python3
"""Tabele wyrownania turniejow LSG (lsg.go.art.pl) dla malych planszy.

Komi jest wszedzie polowkowe, wiec remis nie wychodzi. Czarny stawia kamienie
wyrownania tam, gdzie chce — to nie jest ustalony uklad gwiazd.

9x9 jest regularne: kamien wart 12 punktow, stopien wart 2.

13x13 jest regularne do roznicy 15 — kamien wart na przemian 13 i 12 punktow
(srednio 12,5), stopien wart 5 — a potem sie lamie:

    15   6   -5.5
    16   6  -23.5     <- komi spada o 18, nie o 5, przy tej samej liczbie kamieni
    17   6  -28.5     <- i od tego miejsca znowu po 5

Wiersze 16-21 pasowalyby do ciagu co do polowki punktu, gdyby w kolumnie kamieni
stalo 5, a nie 6. Innymi slowy: od roznicy 16 w gore tabela LSG daje Czarnemu
mniej wiecej jeden kamien wiecej, niz wynika z jej wlasnej arytmetyki. Przepisane
jest to, co stoi w PDF-ie — bo wedlug tego gra sie na turnieju — a uskok pilnuje
osobny test w test_wyrownanie.py, zeby nikt go po cichu nie "naprawil".
"""

from .tabela import Arytmetyka, Tabela, UWAGA_KOMI, sprawdz

NAZWA = "lsg"

ZRODLA: dict[str, str] = {
    "9x9": "https://lsg.go.art.pl/public/handi/handi-9.pdf",
    "13x13": "https://lsg.go.art.pl/public/handi/handi-13.pdf",
}

UWAGA = (
    UWAGA_KOMI
    + " Komi jest połówkowe, więc remis nie wychodzi."
    + " Czarny stawia kamienie wyrównania tam, gdzie chce."
)

TABELA_9X9: Tabela = [
    (0, 0, 6.5),
    (1, 0, 4.5),
    (2, 0, 2.5),
    (3, 0, 0.5),
    (4, 0, -1.5),
    (5, 0, -3.5),
    (6, 0, -5.5),
    (7, 2, 4.5),
    (8, 2, 2.5),
    (9, 2, 0.5),
    (10, 2, -1.5),
    (11, 2, -3.5),
    (12, 2, -5.5),
    (13, 3, 4.5),
    (14, 3, 2.5),
    (15, 3, 0.5),
    (16, 3, -1.5),
    (17, 3, -3.5),
    (18, 3, -5.5),
    (19, 4, 4.5),
    (20, 4, 2.5),
    (21, 4, 0.5),
]

TABELA_13X13: Tabela = [
    (0, 0, 6.5),
    (1, 0, 1.5),
    (2, 0, -3.5),
    (3, 2, 4.5),
    (4, 2, -0.5),
    (5, 2, -5.5),
    (6, 3, 1.5),
    (7, 3, -3.5),
    (8, 4, 4.5),
    (9, 4, -0.5),
    (10, 4, -5.5),
    (11, 5, 1.5),
    (12, 5, -3.5),
    (13, 6, 4.5),
    (14, 6, -0.5),
    (15, 6, -5.5),
    (16, 6, -23.5),
    (17, 6, -28.5),
    (18, 6, -33.5),
    (19, 6, -38.5),
    (20, 6, -43.5),
    (21, 6, -48.5),
]

TABELE: dict[str, Tabela] = {"9x9": TABELA_9X9, "13x13": TABELA_13X13}

# 13x13 nie deklaruje arytmetyki, bo lamie sie na roznicy 16 — patrz docstring.
ARYTMETYKA: dict[str, Arytmetyka] = {
    "9x9": Arytmetyka(wartosc_kamienia=12, krok=2),
}

# Roznica stopni, na ktorej tabela 13x13 przestaje isc swoim krokiem, i o ile
# naprawde skacze. Stoi tu, a nie w tescie, bo to fakt o danych.
USKOK_13X13: tuple[int, float] = (16, 18.0)

sprawdz(TABELE)
