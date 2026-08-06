#!/usr/bin/env python3
"""Zrodlo prawdy dla zasad gry klubowej.

Kazda zasada to jedno zdanie. Te same zdania, co do slowa, stoja w trzech
miejscach:
- ranking.html, sekcja "Zasady" (lista, w tej kolejnosci),
- ranking.html, rozdzialy Wyrownanie / Wynik / Zmiana PS (jako <strong> nad
  akapitem ze szczegolami),
- sciaga na dole karty gracza (SCIAGA w karta_pdf.py, budowana stad).

Zasada: na karcie sa dokladnie te zdania — nic wiecej i nic mniej. Co jest za
drobne na zasade, idzie do szczegolow pod nia na stronie i na karte nie trafia.
Zgodnosci pilnuje tools/test_zasady.py (pre-commit hook w tools/githooks).

Zasady sa o grze klubowej i tylko o niej. Kalibracja nowego gracza to robota
prowadzacego, nie dwojki przy stoliku — stoi wylacznie w rozdziale "Kalibracja
nowego gracza" na stronie i na karte nie trafia.

Numeracja jest ciagla przez cala liste i wynika z kolejnosci — nie zapisujemy
jej, tylko liczymy, zeby nie dalo sie jej rozjechac.

Podzial na kolumny odpowiada kolejnosci wypelniania wiersza karty:
wyrownanie -> wynik -> zmiana PS. Rozdzialy strony ida tak samo.
"""

KOLUMNY: tuple[str, ...] = ("wyrównanie", "wynik", "zmiana PS")

ZASADY: list[tuple[str, str]] = [
    ("wyrównanie", "Policzcie różnicę PS: PS silniejszego minus PS słabszego."),
    ("wyrównanie", "Różnica PS 0–5 to gra równa: kolory przez nigiri, Czarny daje Białemu 6 jeńców i wygraną przy równym wyniku — razem komi 6,5."),
    ("wyrównanie", "Różnica PS 6 i więcej to gra z wyrównaniem: silniejszy gra Białymi, a Czarny bierze z tabeli pierwsze ruchy i dodatkowych jeńców — liczonych na koniec jak zbite w grze."),
    ("wyrównanie", "W kolumnie kalibracja nowy gracz odlicza swój mnożnik — ×4, ×3, ×2 w trzech pierwszych grach — jego przeciwnik wpisuje K, a w każdej innej grze oboje stawiają myślnik."),
    ("wynik", "Wynik wpisujecie w punktach ze znakiem: plus u zwycięzcy, minus u przegranego, remis jako zero; po poddaniu +R i −R."),
    ("wynik", "Ta sama gra stoi na dwóch kartach: różnica PS jednakowa, wynik z przeciwnymi znakami."),
    ("zmiana PS", "Zwycięzca +1 PS, przegrany −1 PS, remis 0."),
    ("zmiana PS", "Wygrana o 13 punktów lub więcej albo przez poddanie mnoży zmianę PS obu graczy ×2."),
    ("zmiana PS", "Seria, czyli trzecia wygrana z rzędu na danej planszy i każda kolejna, mnoży zmianę PS zwycięzcy ×2."),
    ("zmiana PS", "Gra kalibracyjna działa jak zwykła, tylko stoi poza serią: nowy gracz mnoży swoją zmianę PS jeszcze przez mnożnik z kolumny kalibracja, a przeciwnik przy K dostaje dokładnie ±1 PS."),
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
