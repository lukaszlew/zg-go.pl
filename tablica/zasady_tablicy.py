#!/usr/bin/env python3
"""Zrodlo prawdy dla zasad rankingu prowadzonego na tablicy siły.

Kazda zasada to jedno zdanie plus metadana: na ile linii wolno mu sie zlamac
na wydruku. Z limitow linii generator (tablica_kyu_pdf.py) sam liczy najwezsza
szerokosc kazdej kolumny pasa — zdania mowia, ile miejsca potrzebuja, zamiast
dopasowywac sie do sztywnej szerokosci. Kolumna NOWY GRACZ ma luzniejsze
limity, zeby byla wezsza — caly pas trzyma sie wtedy dalej od marginesow.

Zasady mowia wylacznie o tym, co widac przy tablicy: o liczbach w tle pol,
o magnesach i o paskach pola — WYGRANA i SERIA przy lewej krawedzi, ktore
magnes odslania, odsuwajac sie od krawedzi po kazdej wygranej, oraz
PRZEGRANA po prawej, widoczny tylko przy magnesie dosunietym do krawedzi. Tablica nie ma
innej pamieci: kto stoi na SERII, ten wygral co najmniej dwie gry z rzedu,
i widac to przed gra. Co jest za drobne na zasade, nie trafia na tablice.

Z tego pliku powstaje pas zasad na dole wydruku oraz sciaga na stronie
ranking — testy w tools/test_tablica.py pilnuja, ze strona i wydruk mowia
tymi samymi zdaniami.
"""

KOLUMNY: tuple[str, ...] = ("gra", "magnes", "nowy")

# Naglowki kolumn w formie do druku (dopisek przy magnesie malymi literami).
NAGLOWKI: dict[str, str] = {
    "gra": "GRA",
    "magnes": "MAGNES (własny, zaraz po grze)",
    "nowy": "NOWY GRACZ",
}

# Napisy paskow w polu, w kolejnosci od lewej krawedzi: pierwsza wygrana odslania
# pierwszy, druga — drugi; na drugim magnes zostaje po kazdej nastepnej.
PASKI: tuple[str, str] = ("WYGRANA", "SERIA")
# Pasek po prawej stronie strefy etykiety: widac go tylko, gdy magnes stoi
# przy lewej krawedzi — czyli po przegranej. Za nim pusty pasek dla symetrii.
PASEK_PRZEGRANEJ = "PRZEGRANA"

# (kolumna, zdanie, najwyzsza dozwolona liczba linii na wydruku)
ZASADY: list[tuple[str, str, int]] = [
    ("gra", "Gracz to magnes ze swoim nickiem i rozmiarem planszy, a liczba pod nim to jego siła — miara tego, jak dobrze aktualnie gra.", 3),
    ("gra", "Różnica siły to liczba silniejszego minus liczba słabszego; silniejszy gra Białymi.", 2),
    ("gra", "Tabela wyznacza liczbę ruchów startowych Czarnego i jeńców, których dostaje przed grą od Białego.", 2),
    ("gra", "Jeśli różnica jest mniejsza niż najmniejsza w tabeli, losujemy kolory nigiri i zaczyna Czarny; Biały dostaje od razu 6 jeńców i wygrywa remisy (tak jakby 6,5).", 3),
    ("magnes", "Wygrana to strzałka w górę (lub w prawo), przegrana — w dół (lub w lewo), remis — bez zmiany.", 2),
    ("magnes", "Poddanie albo różnica od 15 punktów na 9×9, 30 na 13×13, 60 na 19×19 to wynik wyraźny: dwie strzałki, i u wygranego, i u przegranego.", 3),
    ("magnes", "Po każdej wygranej magnes idzie też o pasek w prawo, dalej od lewej krawędzi — najpierw WYGRANA, potem SERIA; przegrana dosuwa go w lewo do krawędzi.", 3),
    ("magnes", "Pierwsza przegrana w tygodniu i każda przegrana z graczem na SERII (jego trzecia wygrana z rzędu) nie zsuwają magnesu w dół — tylko dosuwają go do lewej krawędzi.", 3),
    ("nowy", "Kto nigdy nie grał w Go, wiesza magnes na zerze, od razu na SERII.", 3),
    ("nowy", "Kto już grał i wie, z kim na tablicy gra mniej więcej równo, wiesza magnes 6 strzałek niżej od tego gracza — też na SERII.", 4),
]

assert [k for k, _, _ in ZASADY] == sorted(
    (k for k, _, _ in ZASADY), key=KOLUMNY.index
), "zasady musza byc pogrupowane w kolejnosci KOLUMNY — tak ida kolumny pasa"
assert len({z for _, z, _ in ZASADY}) == len(ZASADY), "zdania zasad musza byc unikalne"
assert {k for k, _, _ in ZASADY} == set(KOLUMNY), "kazda kolumna musi miec przynajmniej jedna zasade"
assert all(linie in (1, 2, 3, 4) for _, _, linie in ZASADY), "zasada zajmuje od jednej do czterech linii"
assert all(any(pasek.casefold() in z.casefold() for _, z, _ in ZASADY)
           for pasek in PASKI + (PASEK_PRZEGRANEJ,)), \
    "kazdy napis paska musi padac w zasadach — inaczej tablica pokazuje cos, czego nie tlumaczy"


def zasady_kolumny(kolumna: str) -> list[tuple[str, int]]:
    """(zdanie, limit linii) jednej kolumny pasa, w kolejnosci listy."""
    assert kolumna in KOLUMNY, f"nieznana kolumna: {kolumna}"
    return [(z, linie) for k, z, linie in ZASADY if k == kolumna]
