#!/usr/bin/env python3
"""Zrodlo prawdy dla zasad gry klubowej.

Kazda zasada to jedno zdanie. Te same zdania, co do slowa, stoja w trzech
miejscach:
- ranking.html, sekcja "Zasady" (lista, w tej kolejnosci),
- ranking.html, rozdzialy Wyrownanie / Wynik / Zmiana sily (jako <strong> nad
  akapitem ze szczegolami),
- sciaga na dole karty gracza (SCIAGA w karta_pdf.py, budowana stad).

Zasada: na karcie sa dokladnie te zdania — nic wiecej i nic mniej. Co jest za
drobne na zasade, idzie do szczegolow pod nia na stronie i na karte nie trafia.
Zgodnosci pilnuje tools/test_zasady.py (pre-commit hook w tools/githooks).

Sila gracza to jedna liczba, skaczaca po polowce — pol to typowa zmiana po grze.
Jednostki nie nazywamy: rubryka mowi, ze chodzi o sile, wiec przy liczbie nic nie
stoi. Roznica 1 znaczy tyle samo na kazdej planszy, ale w punktach gry wychodzi
rozne: 2 na 9x9, 5 na 13x13, 13 na 19x19. Dlatego wyrownanie czyta sie z tabeli
swojej planszy (tools/wyrownanie/), a nie z jednej dla wszystkich.

Kolumna "typ gry" zbiera gry, ktore licza sie inaczej niz zwykla — dzis tylko
kalibracyjne. Dotycza czesci stolika i trzech pierwszych gier nowego gracza, wiec
reszta moze przeczytac te kolumne raz i wiecej do niej nie wracac.

Podzial na kolumny odpowiada kolejnosci wypelniania wiersza karty:
wyrownanie -> typ gry -> wynik -> zmiana sily. Rozdzialy strony ida
kolumnami, a nie wierszem karty: typ gry stoi na koncu, bo w wiekszosci gier
nie ma w nim nic do czytania.
"""

KOLUMNY: tuple[str, ...] = ("wyrównanie", "wynik", "zmiana siły", "typ gry")

ZASADY: list[tuple[str, str]] = [
    ("wyrównanie", "Różnica siły to siła silniejszego minus siła słabszego; silniejszy gra Białymi."),
    ("wyrównanie", "Startowe ruchy Czarnego i dodatkowych jeńców, liczonych na koniec jak zbite w grze, odczytajcie z tabeli swojej planszy i przepiszcie na obie karty."),
    ("wyrównanie", "Jeżeli różnica siły jest mniejsza niż pierwsza kratka tabeli, gra jest równa: kolory rozstrzyga nigiri, a zapisujecie 1 ruch i −6,5 jeńca — minus, bo to Biały dostaje 6 jeńców i wygrywa remisy."),
    ("wynik", "Wynik wpisujecie w punktach ze znakiem: + u zwycięzcy, − u przegranego, remis jako 0; po poddaniu +R i −R."),
    ("wynik", "Ta sama gra stoi na dwóch kartach: różnica siły jednakowa, wynik z przeciwnymi znakami."),
    ("zmiana siły", "Zwycięzca +½, przegrany −½, remis 0 — w grze równej remisu nie ma, bo wyklucza go połówka komi."),
    ("zmiana siły", "Wygrana o 20 punktów lub więcej albo przez poddanie daje zwycięzcy +1; przegrany traci ½ jak zawsze."),
    ("zmiana siły", "Szybką korektę siły przyznaje silny gracz w klubie: skorygowaną wartość zapisujecie z wykrzyknikiem w rubryce moja siła w następnej grze."),
    ("typ gry", "Dopóki nowy gracz się kalibruje, w kolumnie typ gry stoi u niego K, a jego przeciwnik wpisuje P albo pomija tę grę, bo nic mu ona nie zmienia; w zwyczajnej grze oboje stawiają myślnik."),
    ("typ gry", "W grze kalibracyjnej nowy gracz dostaje ±1, a po wyraźnej wygranej lub przegranej ±2; przeciwnik przy P nie zmienia swojej siły."),
    ("typ gry", "Kalibracja może się skończyć dopiero wtedy, gdy są w niej i wygrane, i przegrane — a silny gracz w klubie może ją przedłużyć albo przyspieszyć szybką korektą."),
]

assert [k for k, _ in ZASADY] == sorted(
    (k for k, _ in ZASADY), key=KOLUMNY.index
), "zasady musza byc pogrupowane w kolejnosci KOLUMNY — tak ida kolumny sciagi"
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
