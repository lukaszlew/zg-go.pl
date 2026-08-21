#!/usr/bin/env python3
"""Sklada pliki wyrownanie-*.json z tabel czterech zrodel.

Uruchomienie (albo `make wyrownanie`):
    PYTHONPATH=tools python3 -m wyrownanie.generuj

Regeneracja jest reczna, a swiezosci pilnuje test_wyrownanie.py: sklada tresc
jeszcze raz i porownuje ja z plikiem na dysku. Zmiana liczby w module bez
przegenerowania nie przejdzie wiec przez pre-commit.

Lista zrodel stoi tutaj jawnie, a nie w automatycznym szukaniu plikow — nowe
zrodlo dopisuje sie w jednym miejscu i widac, co wchodzi do zestawu.
"""

from . import bga
from . import hunt
from . import ishikura
from . import lsg
from . import tabela_html
from . import zg
from .tabela import jako_json, plik_json
from .zestawienie import plik_zestawienia, zestawienie

ZRODLA_DANYCH = (zg, bga, lsg, ishikura, hunt)

assert len({modul.NAZWA for modul in ZRODLA_DANYCH}) == len(ZRODLA_DANYCH), \
    "nazwy zrodel musza byc rozne — inaczej jedno nadpisze plik drugiego"

# Nie kazde zrodlo mowi o kazdej planszy: tabela Semedori obejmuje tez 19x19,
# ktorej nie ma zadna z przepisanych. Kolejnosc idzie za pierwszym wystapieniem,
# wiec o ukladzie kolumn decyduje kolejnosc modulow wyzej.
PLANSZE: tuple[str, ...] = tuple(
    dict.fromkeys(plansza for modul in ZRODLA_DANYCH for plansza in modul.TABELE)
)


def zrodla_planszy(plansza: str) -> tuple:
    """Te zrodla, ktore maja tabele dla tej planszy — w kolejnosci ZRODLA_DANYCH."""
    zrodla = tuple(modul for modul in ZRODLA_DANYCH if plansza in modul.TABELE)
    assert zrodla, f"plansza {plansza} bez ani jednego zrodla"
    return zrodla


def tresc(modul) -> str:
    """Cala tresc pliku JSON dla jednego zrodla."""
    return jako_json(modul.ZRODLA, modul.UWAGA, modul.TABELE)


def tresc_zestawienia(plansza: str) -> str:
    """Cala tresc pliku zestawienia dla jednej planszy."""
    return zestawienie(plansza, zrodla_planszy(plansza))


def main() -> None:
    pliki = [(plik_json(m.NAZWA), tresc(m)) for m in ZRODLA_DANYCH]
    pliki += [(plik_zestawienia(p), tresc_zestawienia(p)) for p in PLANSZE]
    pliki += [(tabela_html.PLIK, tabela_html.jako_html())]
    for plik, zawartosc in pliki:
        plik.write_text(zawartosc, encoding="utf-8")
        print(f"zapisane: {plik.name}")


if __name__ == "__main__":
    main()
