#!/usr/bin/env python3
"""Zrodlo prawdy dla zasad gry klubowej.

Kazda zasada to jedno zdanie. Te same zdania, co do slowa, stoja w trzech
miejscach:
- ranking.html, sekcja "Zasady" (lista, w tej kolejnosci),
- ranking.html, rozdzialy Wyrownanie / Wynik / Zmiana St (jako <strong> nad
  akapitem ze szczegolami),
- sciaga na dole karty gracza (SCIAGA w karta_pdf.py, budowana stad).

Zasada: na karcie sa dokladnie te zdania — nic wiecej i nic mniej. Co jest za
drobne na zasade, idzie do szczegolow pod nia na stronie i na karte nie trafia.
Zgodnosci pilnuje tools/test_zasady.py (pre-commit hook w tools/githooks).

Sila gracza stoi w stopniach (St), po polowce — pol stopnia to typowa zmiana po grze.
Stopien znaczy tyle samo na kazdej planszy, ale w punktach wychodzi rozne: 2 na
9x9, 5 na 13x13, 13 na 19x19. Dlatego wyrownanie czyta sie z tabeli swojej
planszy (tools/wyrownanie/), a nie z jednej dla wszystkich.

Kalibracja ma wlasna kolumne, a nie doklejone zasady w cudzych: dotyczy trzech
pierwszych gier nowego gracza i nikogo poza nim, wiec reszta stolika moze ja
przeczytac raz i wiecej do niej nie wracac.

Podzial na kolumny odpowiada kolejnosci wypelniania wiersza karty:
wyrownanie -> wynik -> zmiana St. Rozdzialy strony ida tak samo.
"""

KOLUMNY: tuple[str, ...] = ("wyrównanie", "wynik", "zmiana St", "kalibracja")

ZASADY: list[tuple[str, str]] = [
    ("wyrównanie", "Różnica St to St silniejszego minus St słabszego; silniejszy gra Białymi."),
    ("wyrównanie", "Ruchy Czarnego i dodatkowych jeńców, liczonych na koniec jak zbite w grze, odczytajcie z tabeli swojej planszy i przepiszcie na obie karty."),
    ("wyrównanie", "Jeżeli różnica St jest mniejsza niż w tabeli, gra jest równa: zapisujecie 1 ruch i −6,5 jeńca, czyli Biały dostaje 6 jeńców i wygrywa remisy, a kolory rozstrzyga nigiri."),
    ("wynik", "Wynik wpisujecie w punktach ze znakiem: + u zwycięzcy, − u przegranego, remis jako 0; po poddaniu +R i −R."),
    ("wynik", "Ta sama gra stoi na dwóch kartach: różnica St jednakowa, wynik z przeciwnymi znakami."),
    ("zmiana St", "Zwycięzca +½ St, przegrany −½ St, remis 0 — w grze równej remisu nie ma, bo wyklucza go połówka komi."),
    ("zmiana St", "Wygrana o 20 punktów lub więcej albo przez poddanie daje zwycięzcy +1 St; przegrany traci ½ St jak zawsze."),
    ("zmiana St", "Szybką korektę St przyznaje najsilniejszy gracz w klubie: skorygowaną wartość zapisujecie z wykrzyknikiem w rubryce moje St następnej gry."),
    ("kalibracja", "W kolumnie kalibracja nowy gracz wpisuje K przez swoje trzy pierwsze gry, jego przeciwnik P, a w każdej innej grze oboje stawiają myślnik."),
    ("kalibracja", "W grze kalibracyjnej nowy gracz dostaje ±1 St, a po wyraźnej wygranej lub przegranej ±2 St; przeciwnik przy P nie zmienia swoich St."),
]

assert [k for k, _ in ZASADY] == sorted(
    (k for k, _ in ZASADY), key=KOLUMNY.index
), "zasady musza byc pogrupowane w kolejnosci KOLUMNY — numeracja rosnie od lewej kolumny"
assert len({z for _, z in ZASADY}) == len(ZASADY), "zdania zasad musza byc unikalne"
assert {k for k, _ in ZASADY} == set(KOLUMNY), "kazda kolumna musi miec przynajmniej jedna zasade"


def w_kolumnie(kolumna: str) -> list[str]:
    """Zdania jednej kolumny sciagi, w kolejnosci listy.

    Zasady nie maja numerow — trzyma je kolejnosc i kolumna, w ktorej stoja.
    Numer musialby sie zgadzac na stronie, na karcie i w testach naraz, a
    odsylamy do zasad nazwa rubryki, nie liczba.
    """
    assert kolumna in KOLUMNY, f"nieznana kolumna: {kolumna}"
    return [z for k, z in ZASADY if k == kolumna]
