#!/usr/bin/env python3
"""Zrodlo prawdy dla zasad rankingu na tablicy magnetycznej.

Kazda zasada to jedno zdanie. Zasady mowia wylacznie o tym, co widac przy
tablicy: o liczbach na paskach, o kratkach i o magnesach — bez kart, zapisow
i procedur. Co jest za drobne na zasade, nie trafia na tablice wcale.

Pas z tymi zdaniami drukuje sie na dole tablicy (tablica_kyu_pdf.py);
docelowo z tego samego zrodla powstanie tresc strony ranking.
"""

KOLUMNY: tuple[str, ...] = ("gra", "magnes")

# Naglowki kolumn w formie do druku (dopisek przy magnesie malymi literami).
NAGLOWKI: dict[str, str] = {
    "gra": "GRA",
    "magnes": "MAGNES (własny, zaraz po grze)",
}

ZASADY: list[tuple[str, str]] = [
    ("gra", "Różnica siły to liczba silniejszego minus liczba słabszego; silniejszy gra Białymi."),
    ("gra", "Tabela wyznacza liczbę ruchów startowych Czarnego i jeńców, których dostaje przed grą od Białego."),
    ("gra", "Jeżeli różnicy nie ma w tabeli, losujemy kolory nigiri; Biały dostaje 6,5 jeńca i wygrywa remisy."),
    ("magnes", "Wygrana to pole wyżej (lub w prawo), wygrana o 20+ punktów albo poddaniem — o dwa pola wyżej."),
    ("magnes", "Przegrana to pole niżej. Pierwsza przegrana w tygodniu lub remis — bez zmiany pola."),
    ("magnes", "Gra szkoleniowa (przy różnicy siły 10 i większej) — silniejszy nigdy nie zmienia pola."),
]

assert [k for k, _ in ZASADY] == sorted(
    (k for k, _ in ZASADY), key=KOLUMNY.index
), "zasady musza byc pogrupowane w kolejnosci KOLUMNY — tak ida kolumny pasa"
assert len({z for _, z in ZASADY}) == len(ZASADY), "zdania zasad musza byc unikalne"
assert {k for k, _ in ZASADY} == set(KOLUMNY), "kazda kolumna musi miec przynajmniej jedna zasade"


def w_kolumnie(kolumna: str) -> list[str]:
    """Zdania jednej kolumny pasa, w kolejnosci listy."""
    assert kolumna in KOLUMNY, f"nieznana kolumna: {kolumna}"
    return [z for k, z in ZASADY if k == kolumna]
