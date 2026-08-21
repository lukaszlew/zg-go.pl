#!/usr/bin/env python3
"""Wspolny format tabel wyrownania — jeden uklad pliku JSON dla wszystkich zrodel.

Zrodlo tabel (BGA, LSG, Ishikura, Hunt) trzyma u siebie same liczby; sklada je i
zapisuje generuj.py. Dzieki temu pliki JSON roznia sie wylacznie
trescia, nigdy ukladem, i strona czyta je jednym kodem.

Wiersz to (roznica sily, kamienie wyrownania, komi dla Bialego). Komi ujemne
oznacza, ze to Bialy daje komi Czarnemu — ponad kamienie wyrownania.

JSON sklada sie tu recznie, bo json.dumps nie umie dosunac liczb do kolumny, a
plik ma sie czytac jak tabela w PDF-ie: cyfry stoja jedna pod druga, minus zwisa
w lewo, a koncowka ".5" w prawo. Same napisy i tak ida przez json.dumps, zeby
ucieczki byly jego robota, nie nasza.
"""

import json
from pathlib import Path
from typing import NamedTuple

KATALOG_PAKIETU = Path(__file__).resolve().parent

KOLUMNY: tuple[str, ...] = ("roznica", "kamienie", "komi")

# Znak komi znaczy w kazdej tabeli to samo, wiec zdanie o nim ma jedna kopie;
# kazde zrodlo dopisuje do niego tylko to, co u niego wlasne.
UWAGA_KOMI = "Komi ujemne oznacza, że komi daje Biały Czarnemu — ponad kamienie wyrównania."

Tabela = list[tuple[int, int, float]]


def plik_json(nazwa: str) -> Path:
    """Sciezka pliku JSON dla zrodla o tej nazwie — obok modulu, z ktorego powstal."""
    return KATALOG_PAKIETU / f"wyrownanie-{nazwa}.json"


class Arytmetyka(NamedTuple):
    """Opis regularnej tabeli: o ile rosnie wyrownanie i ile wart jest kamien.

    Deklaruja go tylko te tabele, ktore naprawde sa ciagiem arytmetycznym — test
    przelicza je wtedy co do punktu. Tabela nieregularna po prostu tego nie
    deklaruje, a jej dziwactwa opisuje wlasny test.
    """
    wartosc_kamienia: float
    krok: float             # o ile rosnie wyrownanie na jednostke roznicy
    od: int = 0             # od ktorej roznicy sily ciag jest regularny


def przewaga(tabela: Tabela, wartosc_kamienia: float) -> list[float]:
    """Wyrownanie w punktach dla kazdego wiersza: darmowe ruchy minus komi.

    Pierwszy kamien to nie darmowy ruch, tylko prawo pierwszego ruchu, ktore ma
    kazdy Czarny — stad max(kamienie - 1, 0). Jeden rachunek obsluguje dzieki temu
    tabele zapisujace gre rowna jako 1 kamien i te zapisujace ja jako 0.

    Sens ma tylko tam, gdzie kamien jest wart stale tyle samo — a to nie jest
    prawda w kazdej tabeli, wiec wartosc podaje sie jawnie zamiast trzymac ja
    przy danych.
    """
    return [max(kamienie - 1, 0) * wartosc_kamienia - komi for _, kamienie, komi in tabela]


def sprawdz(tabele: dict[str, Tabela]) -> None:
    """Asserty wspolne wszystkim tabelom — wolane przy imporcie modulu z danymi."""
    assert tabele, "zrodlo musi miec przynajmniej jedna tabele"
    for plansza, tabela in tabele.items():
        assert [r for r, _, _ in tabela] == list(range(len(tabela))), \
            f"tabela {plansza} musi pokrywac roznice sily od 0 bez dziur"
        assert all(len(w) == len(KOLUMNY) for w in tabela), \
            f"wiersz tabeli {plansza} musi miec kolumny {KOLUMNY}"
        kamienie = [k for _, k, _ in tabela]
        assert all(k >= 0 for k in kamienie), f"tabela {plansza}: kamieni nie moze byc ujemnie"
        assert kamienie == sorted(kamienie), \
            f"tabela {plansza}: kamieni nie ubywa, gdy roznica sily rosnie"


# --- zapis do JSON -----------------------------------------------------------


def rozbij(liczba: float) -> tuple[str, str]:
    """(calosc ze znakiem, ulamek z kropka albo pusto) — do wyrownania kolumny.

    Cyfry maja stac w jednej kolumnie, wiec calosc dosuwa sie do prawej, a ulamek
    do lewej: minus zwisa poza kolumne w lewo, ".5" w prawo, i zadne z nich nie
    rusza cyfr.
    """
    assert abs(liczba) < 1000, f"format 'g' przeszedlby na wykladnik: {liczba}"
    calosc, _, ulamek = f"{liczba:g}".partition(".")
    return calosc, f".{ulamek}" if ulamek else ""


def _wiersze(tabela: Tabela, wciecie: str) -> list[str]:
    """Wiersze tabeli jako tekst: kolumna pod kolumna, blok kamieni pod blokiem."""
    pola = [[rozbij(x) for x in wiersz] for wiersz in tabela]
    szerokosci = [
        (max(len(c) for c, _ in kolumna), max(len(u) for _, u in kolumna))
        for kolumna in zip(*pola)
    ]

    wiersze: list[str] = []
    for numer, (wiersz, komorki) in enumerate(zip(tabela, pola)):
        # Pusta linia miedzy blokami kamieni — tak samo, jak tabele lamia sie w zrodlach.
        wiersze.extend([""] if numer and wiersz[1] != tabela[numer - 1][1] else [])
        tresc = ", ".join(
            f"{calosc:>{szer_c}}{ulamek:<{szer_u}}"
            for (calosc, ulamek), (szer_c, szer_u) in zip(komorki, szerokosci)
        )
        wiersze.append(f"{wciecie}[{tresc}]" + ("," if numer < len(tabela) - 1 else ""))
    return wiersze


def _napis(tekst: str) -> str:
    return json.dumps(tekst, ensure_ascii=False)


def jako_json(zrodla: dict[str, str], uwaga: str, tabele: dict[str, Tabela]) -> str:
    """Cala tresc pliku JSON — z koncowa nowa linia, gotowa do zapisu."""
    assert zrodla.keys() == tabele.keys(), "kazda tabela musi miec swoj adres zrodlowy"
    wiersze_zrodel = ",\n".join(f"    {_napis(p)}: {_napis(a)}" for p, a in zrodla.items())
    wiersze_tabel = ",\n".join(
        f"    {_napis(plansza)}: [\n" + "\n".join(_wiersze(tabela, " " * 6)) + "\n    ]"
        for plansza, tabela in tabele.items()
    )
    return (
        "{\n"
        f'  "zrodlo": {{\n{wiersze_zrodel}\n  }},\n'
        f'  "uwaga": {_napis(uwaga)},\n'
        f'  "kolumny": [{", ".join(_napis(k) for k in KOLUMNY)}],\n'
        f'  "tabele": {{\n{wiersze_tabel}\n  }}\n'
        "}\n"
    )
