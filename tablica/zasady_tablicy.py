#!/usr/bin/env python3
"""Zrodlo prawdy dla zasad rankingu prowadzonego na tablicy stopni.

Kazda zasada to jedno zdanie plus metadana: na ile linii wolno mu sie zlamac
na wydruku. Z limitow linii generator (tablica_kyu_pdf.py) sam liczy najwezsza
szerokosc kazdej kolumny pasa — zdania mowia, ile miejsca potrzebuja, zamiast
dopasowywac sie do sztywnej szerokosci.

Zasady mowia wylacznie o tym, co widac przy tablicy: o liczbach na paskach,
o polach i o magnesach. Co jest za drobne na zasade, nie trafia na tablice.

Z tego pliku powstaje pas zasad na dole wydruku oraz sciaga na stronie
ranking — testy w tools/test_tablica.py pilnuja, ze strona i wydruk mowia
tymi samymi zdaniami.
"""

KOLUMNY: tuple[str, ...] = ("gra", "magnes", "gosc")

# Naglowki kolumn w formie do druku (dopisek przy magnesie malymi literami).
NAGLOWKI: dict[str, str] = {
    "gra": "GRA",
    "magnes": "MAGNES (własny, zaraz po grze)",
    "gosc": "GOŚĆ",
}

# (kolumna, zdanie, najwyzsza dozwolona liczba linii na wydruku)
ZASADY: list[tuple[str, str, int]] = [
    ("gra", "Różnica siły to liczba silniejszego minus liczba słabszego; silniejszy gra Białymi.", 2),
    ("gra", "Tabela wyznacza liczbę ruchów startowych Czarnego i jeńców, których dostaje przed grą od Białego.", 2),
    ("gra", "Jeżeli różnicy nie ma w tabeli, losujemy kolory nigiri i zaczyna Czarny.", 2),
    ("gra", "Biały dostaje wtedy od razu 6 jeńców i wygrywa remisy (tak jakby 6,5).", 2),
    ("magnes", "Wygrana to pole wyżej (lub w prawo), przegrana — pole niżej, remis — bez zmiany.", 2),
    ("magnes", "Wyraźny wynik to poddanie albo 15 punktów na 9×9, 30 na 13×13, 60 na 19×19.", 2),
    ("magnes", "Wyraźna wygrana to dwa pola w górę, wyraźna przegrana — dwa pola w dół.", 2),
    ("magnes", "Pierwsza przegrana w tygodniu nie zsuwa magnesu.", 1),
    ("magnes", "Przy różnicy siły 10+, silniejszy nie przesuwa magnesu.", 1),
    ("gosc", "Gość wiesza magnes na zerze.", 1),
    ("gosc", "Po 2-3 przegranych gość zostaje klubowiczem.", 1),
    ("gosc", "Po grze gościa z klubowiczem magnes przesuwa tylko gość.", 2),
    ("gosc", "Silny klubowicz może przewiesić każdy magnes na pole prawdziwej siły gracza — to szybka korekta.", 2),
]

assert [k for k, _, _ in ZASADY] == sorted(
    (k for k, _, _ in ZASADY), key=KOLUMNY.index
), "zasady musza byc pogrupowane w kolejnosci KOLUMNY — tak ida kolumny pasa"
assert len({z for _, z, _ in ZASADY}) == len(ZASADY), "zdania zasad musza byc unikalne"
assert {k for k, _, _ in ZASADY} == set(KOLUMNY), "kazda kolumna musi miec przynajmniej jedna zasade"
assert all(linie in (1, 2) for _, _, linie in ZASADY), "zasada zajmuje jedna albo dwie linie"


def zasady_kolumny(kolumna: str) -> list[tuple[str, int]]:
    """(zdanie, limit linii) jednej kolumny pasa, w kolejnosci listy."""
    assert kolumna in KOLUMNY, f"nieznana kolumna: {kolumna}"
    return [(z, linie) for k, z, linie in ZASADY if k == kolumna]
