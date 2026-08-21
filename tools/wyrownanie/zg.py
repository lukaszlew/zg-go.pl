#!/usr/bin/env python3
"""Tabele wyrownania Semedori — jedyne policzone, a nie przepisane.

Cztery pozostale moduly przepisuja cudze tabele. Ten liczy wlasna, z jednej
zasady, ktora stoi juz na ranking.html i w wyrownanie.js — tyle ze dla malych
planszy przelicza sie ja innym krokiem.

Zasada
------
Ile wart jest jeden stopien roznicy sil, zalezy od planszy. Stosunek bierze sie
z tabel przepisanych w sasiednich modulach i wychodzi ten sam u kazdego, kto je
liczyl:

    plansza   19x19   13x13   9x9
    handi        13       5     2      (na 13 stopni)

Podzielone przez 13 daje zmiane wyrownania na jeden stopien, a po przeliczeniu
na punkty przy RUCH = 13 — po prostu 13, 5 i 2 punkty na stopien. Ze zrodlami
zgadza sie to co do punktu: LSG 9x9 i Hunt 9x9 ida po 2, LSG 13x13 i Ishikura
13x13 po 5, a wyrownanie.js liczy 19x19 po 13 (KROK).

Rachunek
--------
    punkty = ROWNA + KROK[plansza] * roznica
    ruchy  = max(1, 1 + punkty // RUCH)
    komi   = (ruchy - 1) * RUCH - punkty

13x13 idzie tak tylko do gier rownych wlacznie, a wyzej schodzi z drabinki
PETLA_13X13 — patrz komentarz przy niej. Powod jest tabelaryczny: 5 nie dzieli
13, wiec koncowki punktow plynelyby z bloku na blok i tabela nie mialaby
powtarzalnego ksztaltu. Drabinka kosztuje 5,2 punktu na stopien zamiast 5,
czyli szesc punktow nadwyzki przy roznicy 39 — mniej niz pol ruchu.

Gra rowna zaczyna od ROWNA, czyli szesciu jencow dla Bialego — dokladnie tego,
co mowia zasady: Bialy dostaje szesciu jencow i wygrywa remisy. Potem komi schodzi w dol az do -12 i dopiero
trzynasty punkt kupuje Czarnemu caly ruch, bo tyle wlasnie ruch jest wart.
Dlatego komi nigdy nie stoi nizej niz -12: nadwyzka zamienia sie w ruch.

19x19 wychodzi z tego z komi -7 na kazdym stopniu od pierwszego wzwyz. Nie jest
to dziwactwo, tylko skutek tego, ze stopien wart jest tam dokladnie jeden ruch:
reszta z dzielenia nie ma jak sie zmienic, wiec szesciu jencow gry rownej jedzie
przez cala tabele jako stale 7 punktow dla Czarnego. Kolumna ruchow zgadza sie
za to ze zwyklym handicapem: stopien roznicy to ruch wiecej.

Zgodnosci 19x19 z kalkulatorem pilnuje tools/test_kalkulator.mjs — liczy to samo
drugim kodem, w drugim jezyku, i wynik musi wyjsc ten sam.
"""

import math

from .tabela import Arytmetyka, Tabela, UWAGA_KOMI, sprawdz

NAZWA = "zg"

RUCH = 13        # tyle punktow wart jest jeden dodatkowy ruch Czarnego, na kazdej planszy
ROWNA = -6       # gra rowna: Czarny odklada Bialemu 6 jencow (KOMI_JENCY w wyrownanie.js)

# Ile punktow wyrownania dokłada jeden stopien roznicy sil — stosunek ze zrodel.
KROK: dict[str, int] = {"9x9": 2, "13x13": 5, "19x19": 13}

# Drabinka punktow na 13x13. Krok 5 nie dzieli 13, wiec sam rachunek dawalby tam
# koncowki, ktore plyna z bloku na blok: raz 1/4/6/9/11, raz 1/3/6/8/11, raz
# 0/3/5/8/10. Do tabeli to sie nie nadaje, bo kazdy blok wygladalby inaczej.
# Dlatego 13x13 dostaje jedna z tych koncowek na stale: co pol stopnia Czarny
# przesuwa sie o jedna pozycje w dol drabinki, a po pieciu pozycjach ma caly ruch
# wiecej. Tabela robi sie przez to gesta i powtarzalna — piec wierszy i tyle.
#
# Cena: piec pozycji na 2,5 stopnia to 13 punktow, czyli 5,2 punktu na stopien
# zamiast 5. Przy roznicy 20 stopni daje to 2 punkty wiecej niz sam stosunek,
# przy 39 — szesc, czyli mniej niz pol ruchu. Tyle warto zaplacic za tabele,
# ktora ma jeden ksztalt na wszystkie trzy plansze.
PETLA_13X13: tuple[int, ...] = (0, 3, 5, 8, 10)

# Drabinka zaczyna sie za grami rownymi. Nizej nie siega, bo nie umie trafic
# w gre rowna: -13 + 5 to -8, -13 + 8 to -5, a potrzebne jest ROWNA, czyli -6.
# Ponizej tej roznicy 13x13 liczy sie wiec tak jak reszta plansz.
PIERWSZY_STOPIEN_13X13 = 1.5

POLOWKA = 0.5

# Tyle stopni, ile ma najdluzsza z przepisanych tabel (Ishikura) — zeby w
# zestawieniu kolumna Semedori nie konczyla sie przed cudzymi.
DLUGOSC = 31

ZRODLA: dict[str, str] = {plansza: "https://zg-go.pl/ranking.html" for plansza in KROK}

UWAGA = (
    UWAGA_KOMI
    + " Tabela jest policzona, nie przepisana:"
    + f" {ROWNA} punktu w grze równej i {'/'.join(str(k) for k in KROK.values())} punktu"
    + f" na stopień różnicy dla {'/'.join(KROK)}, przy ruchu wartym {RUCH} punktów."
    + " Komi nigdy nie schodzi poniżej -12, bo trzynasty punkt kupuje cały ruch."
)


def wiersz(plansza: str, roznica: float) -> tuple[float, int, int]:
    """(roznica, ruchy, komi) dla jednego stopnia — caly rachunek modulu.

    Roznica moze byc polowkowa, bo miedzy stopniami tez sie gra. Polowka stopnia
    daje polowke kroku, a wiec na 13x13 i 19x19 pol punktu — i to pol punktu
    obcinamy do zera, zeby tabela zostala w liczbach calkowitych. Obciecie idzie
    ku zeru, wiec slabszy nigdy nie traci na zaokragleniu: przy ujemnym wyrownaniu
    Czarny odklada o pol punktu mniej, przy dodatnim dostaje o pol punktu mniej.

    Dla stopni calkowitych trunc nie ma czego uciac (KROK jest calkowite), wiec
    tabele w TABELE, w JSON-ie i w zestawieniu wychodza co do liczby te same.
    """
    assert plansza in KROK, f"nieznana plansza: {plansza}"
    assert roznica * 2 == int(roznica * 2), f"roznica idzie co pol stopnia: {roznica}"
    if plansza == "13x13" and roznica >= PIERWSZY_STOPIEN_13X13:
        return (roznica, *_z_drabinki(roznica))
    punkty = math.trunc(ROWNA + KROK[plansza] * roznica)
    ruchy = max(1, 1 + punkty // RUCH)
    return roznica, ruchy, (ruchy - 1) * RUCH - punkty


def _z_drabinki(roznica: float) -> tuple[int, int]:
    """(ruchy, komi) dla 13x13 — pozycja w PETLA_13X13 i ruch co pelna petle."""
    pozycja = round((roznica - PIERWSZY_STOPIEN_13X13) / POLOWKA)
    ruchy, w_petli = divmod(pozycja, len(PETLA_13X13))
    return 1 + ruchy, -PETLA_13X13[w_petli]


TABELE: dict[str, Tabela] = {
    plansza: [wiersz(plansza, roznica) for roznica in range(DLUGOSC)] for plansza in KROK
}

# 13x13 wypada z arytmetyki: na drabince pol stopnia to raz 3, raz 2 punkty,
# wiec staly krok tam nie obowiazuje. Pilnuje jej wlasny test.
ARYTMETYKA: dict[str, Arytmetyka] = {
    plansza: Arytmetyka(wartosc_kamienia=RUCH, krok=krok)
    for plansza, krok in KROK.items()
    if plansza != "13x13"
}

sprawdz(TABELE)

# Rachunek ma sam siebie pilnowac juz przy imporcie: komi ponizej -12 znaczy, ze
# nadwyzka nie zamienila sie w ruch, a to jedyny blad, ktory ten modul moze zrobic.
for _plansza, _tabela in TABELE.items():
    assert all(-12 <= komi <= -ROWNA for _, _, komi in _tabela), \
        f"tabela {_plansza}: komi wyszlo poza [-12, {-ROWNA}]"
    assert _tabela[0][1:] == (1, -ROWNA), f"tabela {_plansza}: gra rowna to jeden ruch i {-ROWNA} komi"
