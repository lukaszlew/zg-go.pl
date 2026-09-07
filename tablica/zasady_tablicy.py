#!/usr/bin/env python3
"""Zrodlo prawdy dla zasad rankingu prowadzonego na tablicy siły.

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
    ("gra", "Gracz to magnes ze swoim nickiem i rozmiarem planszy, a liczba przy nim to jego siła — miara tego, jak dobrze aktualnie gra.", 3),
    ("gra", "Różnica siły to liczba silniejszego minus liczba słabszego; silniejszy gra Białymi.", 2),
    ("gra", "Tabela wyznacza liczbę ruchów startowych Czarnego i jeńców, których dostaje przed grą od Białego.", 2),
    ("gra", "Jeśli różnica jest mniejsza niż najmniejsza w tabeli, losujemy kolory nigiri i zaczyna Czarny; Biały dostaje od razu 6 jeńców i wygrywa remisy (tak jakby 6,5).", 3),
    ("magnes", "Wygrana to strzałka w górę (lub w prawo), przegrana — strzałka w dół (lub w lewo), remis — bez zmiany.", 2),
    ("magnes", "Wyraźny wynik to poddanie albo dużo punktów: 15 na 9×9, 30 na 13×13, 60 na 19×19.", 2),
    ("magnes", "Wyraźna wygrana/przegrana to 2 strzałki w górę/dół.", 1),
    ("magnes", "Pierwsza przegrana w tygodniu nie zsuwa magnesu.", 1),
    ("magnes", "Gra szkoleniowa — od 4 ruchów startowych na 9×9, 6 na 13×13, 8 na 19×19 — silniejszy nie przesuwa w niej magnesu.", 2),
    ("gosc", "Gość wiesza magnes na zerze.", 1),
    ("gosc", "Gość znający swoje kyu/dan może powiesić magnes z przelicznika — 5 strzałek niżej.", 2),
    ("gosc", "Po grze gościa z klubowiczem magnes przesuwa tylko gość.", 2),
    ("gosc", "Po 2-3 przegranych gość zostaje klubowiczem.", 1),
    ("gosc", "Silny klubowicz może wspólnie z właścicielem przewiesić magnes na pole jego prawdziwej siły — to szybka korekta.", 3),
]

assert [k for k, _, _ in ZASADY] == sorted(
    (k for k, _, _ in ZASADY), key=KOLUMNY.index
), "zasady musza byc pogrupowane w kolejnosci KOLUMNY — tak ida kolumny pasa"
assert len({z for _, z, _ in ZASADY}) == len(ZASADY), "zdania zasad musza byc unikalne"
assert {k for k, _, _ in ZASADY} == set(KOLUMNY), "kazda kolumna musi miec przynajmniej jedna zasade"
assert all(linie in (1, 2, 3) for _, _, linie in ZASADY), "zasada zajmuje od jednej do trzech linii"


def zasady_kolumny(kolumna: str) -> list[tuple[str, int]]:
    """(zdanie, limit linii) jednej kolumny pasa, w kolejnosci listy."""
    assert kolumna in KOLUMNY, f"nieznana kolumna: {kolumna}"
    return [(z, linie) for k, z, linie in ZASADY if k == kolumna]
