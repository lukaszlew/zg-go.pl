#!/usr/bin/env python3
"""Zrodlo prawdy dla zasad gry klubowej.

Kazda zasada to jedno zdanie. Te same zdania, co do slowa, stoja w trzech
miejscach:
- ranking.html, blok "Wszystkie zasady" (lista, w tej kolejnosci),
- ranking.html, rozdzialy Wyrownanie / Wynik / Zmiana PS (jako <strong> nad
  akapitem ze szczegolami),
- sciaga na dole karty gracza (SCIAGA w karta_pdf.py, budowana stad).

Zasada: na karcie sa dokladnie te zdania — nic wiecej i nic mniej. Co jest za
drobne na zasade, idzie do szczegolow pod nia na stronie i na karte nie trafia.
Zgodnosci pilnuje tools/test_zasady.py (pre-commit hook w tools/githooks).

Numeracja jest ciagla przez cala liste i wynika z kolejnosci — nie zapisujemy
jej, tylko liczymy, zeby nie dalo sie jej rozjechac.

Podzial na kolumny odpowiada kolejnosci wypelniania wiersza karty:
wyrownanie -> wynik -> zmiana PS. Rozdzialy strony ida tak samo.
"""

KOLUMNY: tuple[str, ...] = ("wyrównanie", "wynik", "zmiana PS")

ZASADY: list[tuple[str, str]] = [
    ("wyrównanie", "Policzcie różnicę PS: PS silniejszego minus PS słabszego."),
    ("wyrównanie", "Różnica 0–5 to gra równa: kolory przez nigiri, Czarny daje Białemu 6 jeńców."),
    ("wyrównanie", "Od różnicy 6 silniejszy gra Białymi, a Czarny bierze z tabeli ruchy i jeńców."),
    ("wynik", "Przy liczeniu doliczcie jeńców — każdy z nich to punkt."),
    ("wynik", "Wynik wpisujecie w punktach ze znakiem: plus u zwycięzcy, minus u przegranego."),
    ("wynik", "Po poddaniu wpisujecie +R i −R zamiast liczby."),
    ("wynik", "Równy wynik w grze równej wygrywa Biały — remis zdarza się tylko przy wyrównaniu."),
    ("wynik", "Ta sama gra stoi na dwóch kartach: różnica jednakowa, wynik z przeciwnymi znakami."),
    ("zmiana PS", "Zwycięzca +1 PS, przegrany −1 PS; remis nie zmienia nic."),
    ("zmiana PS", "Wygrana o 13 punktów lub więcej albo przez poddanie: ±2 PS."),
    ("zmiana PS", "Trzecia wygrana z rzędu na danej planszy i każda kolejna podwaja zmianę zwycięzcy."),
    ("zmiana PS", "Gra kalibrująca nowego gracza nie zmienia PS przeciwnika — wpisuje zero."),
]

assert [k for k, _ in ZASADY] == sorted(
    (k for k, _ in ZASADY), key=KOLUMNY.index
), "zasady musza byc pogrupowane w kolejnosci KOLUMNY — numeracja rosnie od lewej kolumny"
assert len({z for _, z in ZASADY}) == len(ZASADY), "zdania zasad musza byc unikalne"
assert {k for k, _ in ZASADY} == set(KOLUMNY), "kazda kolumna musi miec przynajmniej jedna zasade"


def ponumerowane() -> list[tuple[int, str, str]]:
    """(numer od 1, kolumna, zdanie) dla wszystkich zasad, w kolejnosci listy."""
    return [(n, k, z) for n, (k, z) in enumerate(ZASADY, 1)]


def w_kolumnie(kolumna: str) -> list[tuple[int, str]]:
    """(numer, zdanie) dla jednej kolumny sciagi."""
    assert kolumna in KOLUMNY, f"nieznana kolumna: {kolumna}"
    return [(n, z) for n, k, z in ponumerowane() if k == kolumna]
