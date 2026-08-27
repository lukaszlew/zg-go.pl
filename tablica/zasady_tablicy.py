#!/usr/bin/env python3
"""Zrodlo prawdy dla zasad rankingu na tablicy magnetycznej.

Kazda zasada to jedno zdanie. Zasady mowia wylacznie o tym, co widac przy
tablicy: o liczbach na paskach, o kratkach i o magnesach — bez kart, zapisow
i procedur. Co jest za drobne na zasade, nie trafia na tablice wcale.

Pas z tymi zdaniami drukuje sie na dole tablicy (tablica_kyu_pdf.py);
docelowo z tego samego zrodla powstanie tresc strony ranking.
"""

KOLUMNY: tuple[str, ...] = ("wyrównanie", "po grze", "wyjątki")

ZASADY: list[tuple[str, str]] = [
    ("wyrównanie", "Różnica siły to liczba silniejszego minus liczba słabszego; silniejszy gra Białymi."),
    ("wyrównanie", "Startowe ruchy Czarnego i dodatkowych jeńców, liczonych na koniec jak zbite w grze, odczytajcie z tabeli swojej planszy."),
    ("wyrównanie", "Jeżeli różnica siły jest mniejsza niż pierwsza kratka tabeli, gra jest równa: kolory rozstrzyga nigiri, a Biały dostaje 6,5 jeńca — połówka wyklucza remis."),
    ("po grze", "Zwycięzca przesuwa swój magnes o kratkę w górę, przegrany o kratkę w dół."),
    ("po grze", "Wygrana o 20 punktów lub więcej albo przez poddanie przesuwa zwycięzcę o dwie kratki; przegrany schodzi o jedną jak zawsze."),
    ("wyjątki", "Pierwsza przegrana w danym tygodniu nie zsuwa magnesa; każda następna kosztuje kratkę jak zawsze."),
    ("wyjątki", "Przy różnicy siły 10 lub większej silniejszy stoi w miejscu — rusza się tylko słabszy."),
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
