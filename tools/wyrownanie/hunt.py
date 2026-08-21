#!/usr/bin/env python3
"""Tabele wyrownania Tima Hunta dla malych planszy.

Propozycja z grupy dyskusyjnej rec.games.go, siegajaca do roznicy 15 stopni —
najkrotsza z czterech tabel w repo i jedyna calkiem regularna od pierwszego
wiersza: kamien wart 10 punktow, stopien wart 2 na 9x9 i 4 na 13x13.

Tabela 13x13 daje dokladnie to samo wyrownanie co tabela BGA, tylko zapisane
oszczedniej: Hunt woli mniej kamieni i ujemne komi tam, gdzie BGA dokłada kamien
i podnosi komi ponad 6. Punkt w punkt to jedno i to samo, wiersz po wierszu.

Komi jest calkowite, wiec remis jest mozliwy.
"""

from .tabela import Arytmetyka, Tabela, UWAGA_KOMI, sprawdz

NAZWA = "hunt"

# TODO: potwierdzic adres — tabele przyszly jako tekst, a nie ze strony.
_STRONA = "https://senseis.xmp.net/?HandicapForSmallerBoardSizes"

ZRODLA: dict[str, str] = {"9x9": _STRONA, "13x13": _STRONA}

UWAGA = UWAGA_KOMI + " Komi jest całkowite, więc remis jest możliwy."

TABELA_9X9: Tabela = [
    (0, 1, 6),
    (1, 1, 4),
    (2, 1, 2),
    (3, 1, 0),
    (4, 1, -2),
    (5, 1, -4),
    (6, 2, 4),
    (7, 2, 2),
    (8, 2, 0),
    (9, 2, -2),
    (10, 2, -4),
    (11, 3, 4),
    (12, 3, 2),
    (13, 3, 0),
    (14, 3, -2),
    (15, 3, -4),
]

TABELA_13X13: Tabela = [
    (0, 1, 6),
    (1, 1, 2),
    (2, 1, -2),
    (3, 2, 4),
    (4, 2, 0),
    (5, 2, -4),
    (6, 3, 2),
    (7, 3, -2),
    (8, 4, 4),
    (9, 4, 0),
    (10, 4, -4),
    (11, 5, 2),
    (12, 5, -2),
    (13, 6, 4),
    (14, 6, 0),
    (15, 6, -4),
]

TABELE: dict[str, Tabela] = {"9x9": TABELA_9X9, "13x13": TABELA_13X13}

ARYTMETYKA: dict[str, Arytmetyka] = {
    "9x9": Arytmetyka(wartosc_kamienia=10, krok=2),
    "13x13": Arytmetyka(wartosc_kamienia=10, krok=4),
}

sprawdz(TABELE)
