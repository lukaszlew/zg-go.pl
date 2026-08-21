#!/usr/bin/env python3
"""Trzy zwiezle tabele HTML z wyrownaniem Semedori — po jednej na plansze.

Uklad jest ten sam, co tabeli wyrownania na ranking.html: w kratkach stoi roznica
stopni, a to, co z niej wynika, czyta sie z brzegow — z ostatniej kolumny punkty,
z ostatniego wiersza ruchy. Dzieki temu jedna kratka niesie caly wiersz tabeli
liniowej i nie trzeba powtarzac ruchow ani punktow przy kazdym stopniu.

Siatka
------
Wiersz to punkty, kolumna to ruchy, w srodku roznica stopni. Wszystkie trzy
plansze trafiaja w nia rowno, bo na kazdej ruch przypada po calej liczbie
polowek stopnia: na 19x19 po dwoch, na 13x13 po pieciu (drabinka w zg.py), na
9x9 po trzynastu. Zadna siatka nie ma przez to ani jednej dziury.

Tyle samo mowi liczba wierszy: ile roznych koncowek punktowych da sie dostac na
danej planszy. 19x19 ma ich dwie (0 i 7) i zapada sie do dwoch wierszy — dalej
nie ma czego pokazywac, bo stopien to ruch, a polowka stopnia to ruch bez
punktow. 13x13 ma piec, 9x9 wszystkie trzynascie.

Gry rowne
---------
Zadna z tabel ich nie pokazuje i nie musi: kratka niesie to, co Czarny dostaje,
a w grze rownej nie dostaje nic. Gry rowne to zawsze poczatkowy kawalek zakresu,
wiec mieszcza sie w jednym zdaniu pod tabela.

Tabele nosza klasy "sila komp" i te same klasy wierszy co tabela na ranking.html
("komp-jency" na kolumnie brzegowej, "komp-ruchy" na wierszu brzegowym), wiec
sam <table> mozna stad wyciac i wkleic na strone — zlapie gotowe reguly ze
style.css. Styl w naglowku pliku jest tylko po to, zeby plik otwarty osobno tez
byl czytelny.
"""

from . import zg
from .tabela import KATALOG_PAKIETU

PLIK = KATALOG_PAKIETU / "tabela-zg.html"

SKOK = 0.5              # o tyle stopni rosnie kolejny wiersz
# Polowka pisana pionowo: 1 nad 2, kreska miedzy. Wezsza od "½" po przekatnej,
# bo zajmuje szerokosc jednej cyfry zamiast poltorej, i czytelniejsza w malym
# piśmie. Skladana recznie, bo zaden znak Unicode tego nie daje.
POLOWKA = '<span class="pol"><span>1</span><span>2</span></span>'
# Pusta polowka zajmuje tyle samo miejsca, co pelna. Bez niej cyfra w kratce bez
# ulamka przesuwalaby sie w prawo i kolumna bylaby poszarpana.
BEZ_POLOWKI = '<span class="pol"></span>'

# Podpisy brzegow. Strzalka stoi przed slowem i pokazuje, w ktora strone patrzec:
# to ona, a nie opis nad tabelami, tlumaczy uklad.
RUCHY = "↓ ruchy"
JENCY = "← jeńcy"

# Od ktorego ruchu zaczyna sie tabela. Ruch nr 1 to nie wyrownanie, tylko zwykle
# prawo Czarnego do pierwszego ruchu — na 19x19 caly ten wiersz miesci sie w
# jednym stopniu roznicy, wiec zamiast rozdawac za niego 7 jencow klub gra po
# prostu rowno, a tabela zaczyna sie od pierwszego prawdziwie darmowego ruchu.
# Na 13x13 i 9x9 ten sam wiersz obejmuje kilka stopni i do 12 jencow, wiec stoi.
PIERWSZY_RUCH: dict[str, int] = {"19x19": 2, "13x13": 1, "9x9": 1}

# Plansza -> do ilu ruchow siega tabela, czyli ile ma wierszy. Dalej rachunek
# biegnie bez konca, wiec kazda tabela urywa sie wierszem z wielokropkiem.
RUCHOW: dict[str, int] = {"19x19": 8, "13x13": 7, "9x9": 5}

# Trzy tabele obok siebie, od najwiekszej planszy — tak sie o nich mysli i tak
# stoi stosunek 13 / 5 / 2, z ktorego cala arytmetyka wynika (patrz zg.py).
# Po transpozycji ich wysokosci sa podobne, wiec rzad czyta sie lepiej niz
# prostokat: kazda tabela zaczyna sie na tej samej linii.
#
# Odstep jest maly, ale jest — siatki maja stac osobno, bo kazda ma wlasne brzegi
# i wlasna miare stopnia.
PLANSZE: tuple[str, ...] = ("19x19", "13x13", "9x9")


STYL = """\
  body { font: 15px/1.5 system-ui, sans-serif; margin: 2rem 1rem; color: #222; }
  .tabele { display: flex; gap: 1rem; align-items: flex-start; }
  p.opis { max-width: 44rem; margin: 0 0 1.4rem; }
  p.opis b { font-weight: 600; }
  table { border-collapse: collapse; table-layout: fixed; font-size: 0.85rem; }
  /* Szerokosci z <col>, nie z komorek: kratki maja byc waskie, a kolumna brzegowa
     na tyle szeroka, zeby zmiescil sie w niej podpis "↓ ruchy". */
  col { width: 2.1em; }
  col.brzeg { width: 3.5em; }
  th, td { box-sizing: border-box; border: 1px solid #c4c4c4;
           padding: 0.15rem 0.15rem; text-align: center; }
  th { background: #e8e8e8; font-weight: 600; }
  tr:nth-child(even) td { background: #f4f4f4; }
  /* Brzegi: to z nich czyta sie, co kratka znaczy. Kreska ledwie grubsza od
     zwyklej — ma dzielic, a nie przecinac tabeli na pol. */
  th.komp-jency { background: #dcdcdc; border-top: 2px solid #777; }
  th.komp-ruchy { background: #dcdcdc; border-left: 2px solid #777; }
  /* Rogi nalezą do swoich brzegow, wiec i szarzeja razem z nimi — tlo bierze sie
     z komp-jency i komp-ruchy, tu zostaje samo pismo: mniejsze i bledsze, bo to
     podpis, a nie liczba. Ciemne tlo ma wylacznie nazwa planszy. */
  th.rog { color: #666; font-size: 0.62rem; font-weight: 600;
           letter-spacing: 0; padding: 0.15rem 0.1rem; }
  /* Ciemne tlo obejmuje sam napis, a nie cala kratke — nazwa ma byc plakietka
     nad siatka, a nie belka dotykajaca jej bokow. */
  th.plansza { background: none; padding: 0.2rem 0.15rem; }
  th.plansza span { display: inline-block; background: #3a3a3a; color: #fff;
                    font-size: 0.8rem; letter-spacing: 0.06em; border-radius: 2px;
                    padding: 0.05rem 0.55rem; }
  /* Ulamek pionowy: obie cyfry jedna pod druga, kreska z koloru tekstu. */
  /* Ulamek jest wyzszy niz cyfra obok, wiec rownanie do linii pisma wypycha go
     w gore — stad wyrownanie do srodka, zeby stal na tej samej wysokosci co "1". */
  /* Stala szerokosc, takze gdy pusta: kratka bez ulamka ma trzymac cyfre w tym
     samym miejscu, co kratka z ulamkiem. */
  span.ca { display: inline-block; width: 1.15em; text-align: right; }
  span.pol { display: inline-block; width: 0.85em; font-size: 0.5em;
             line-height: 1.06; vertical-align: middle; text-align: center; }
  span.pol span { display: block; padding: 0 0.1em; }
  span.pol span + span { border-top: 1px solid currentColor; }"""


def _stopien(roznica: float) -> str:
    """Polowka jednym znakiem: 3, 3½, 41½ — o caly znak wezej niz "3,5".

    Przy polowce bez calosci zostaje samo ½: zero z przodu nic nie wnosi, a
    kolumna musialaby byc pod nie szersza.
    """
    calosc = int(roznica)
    if roznica == calosc:
        return str(calosc)
    return f"{calosc}{POLOWKA}" if calosc else POLOWKA


def rowne(plansza: str) -> list[float]:
    """Roznice, przy ktorych gra jest rowna — Czarny nie dostaje nic.

    Zawsze poczatkowy kawalek zakresu, wiec wystarczy je wypisac raz pod tabela.
    """
    stopnie, roznica = [], 0.0
    while True:
        _, ruchy, komi = zg.wiersz(plansza, roznica)
        # Rowne z rachunku (Czarny nic nie dostaje) albo z decyzji klubu
        # (jeszcze zaden darmowy ruch — patrz PIERWSZY_RUCH).
        if -komi >= 0 and ruchy >= PIERWSZY_RUCH[plansza]:
            return stopnie
        stopnie.append(roznica)
        roznica += SKOK


def siatka(plansza: str) -> dict[tuple[int, int], float]:
    """{(punkty, ruchy): roznica} — uklad tabeli wyrownania z ranking.html.

    Kazda para (punkty, ruchy) ma dokladnie jedna roznice, wiec siatka wychodzi
    pelna: idziemy od pierwszej roznicy, ktora nie jest gra rowna, i wpisujemy
    kolejne, dopoki nie zapelnimy wszystkich kolumn.
    """
    pola: dict[tuple[int, int], float] = {}
    roznica = len(rowne(plansza)) * SKOK
    while True:
        _, ruchy, komi = zg.wiersz(plansza, roznica)
        if ruchy > RUCHOW[plansza]:
            return pola
        pola[(-komi, ruchy)] = roznica
        roznica += SKOK


def _kratka(roznica: float) -> str:
    """Roznica w kratce: calosc dosunieta do prawej, polowka zawsze w swoim miejscu."""
    calosc = int(roznica)
    return (
        f'<span class="ca">{calosc or ""}</span>'
        + (POLOWKA if roznica != calosc else BEZ_POLOWKI)
    )


def _tabela_siatki(plansza: str) -> str:
    """Wiersz to ruchy, kolumna to punkty, w kratkach roznica stopni.

    Ruchy stoja w wierszach, bo to one biegna bez konca — i tylko wtedy urwanie
    tabeli da sie pokazac jednym wierszem z wielokropkiem na dole. Punktow jest
    za to na kazdej planszy skonczenie wiele, wiec mieszcza sie w naglowku.
    """
    pola = siatka(plansza)
    punkty = sorted({p for p, _ in pola})
    ruchy = sorted({r for _, r in pola})
    wiersze = [
        "        <tr>"
        + "".join(
            f"<td>{_kratka(pola[(p, r)])}</td>" if (p, r) in pola else "<td></td>"
            for p in punkty
        )
        + f'<th class="komp-ruchy" scope="row">{r}</th></tr>'
        for r in ruchy
    ]
    # Oba rogi niosa nazwe swojego brzegu ze strzalka w jego strone: gorny w dol,
    # po ruchach, dolny w lewo, po jencach. Nad siatka zostaje przez to pas na
    # cala szerokosc — i to on bierze nazwe planszy, bez osobnego naglowka.
    #
    # Kazdy rog nalezy do brzegu, ktory nazywa, i tylko do niego. Gorny stoi nad
    # kolumna ruchow, wiec gruba kreska pionowa idzie przez niego az pod czapke.
    # Dolny nalezy do wiersza jencow — gdyby dostal te sama kreske, odcialaby go
    # od liczb, ktore podpisuje.
    # colgroup, bo przy table-layout: fixed szerokosci bierze sie z pierwszego
    # wiersza — a tam stoi czapka na cala siatke i sama rozdzielilaby ja po rowno.
    kolumny = (
        f'        <colgroup><col span="{len(punkty)}"><col class="brzeg"></colgroup>'
    )
    czapka = (
        f'        <tr><th class="plansza" colspan="{len(punkty)}"><span>{plansza}</span></th>'
        f'<th class="rog komp-ruchy">{RUCHY}</th></tr>'
    )
    stopka = (
        "        <tr>"
        + "".join(f'<th class="komp-jency" scope="col">{p}</th>' for p in punkty)
        + f'<th class="rog komp-jency">{JENCY}</th></tr>'
    )
    return "\n".join([kolumny, czapka, *wiersze, stopka])


# Wszystkie trzy tabele czyta sie tak samo i wszystkie tak samo milcza o grach
# rownych, wiec mowi sie o tym raz, nad calym prostokatem. Zdanie o grze rownej
# nie potrzebuje przy tym zadnej liczby: kazda siatka zaczyna sie dokladnie tam,
# gdzie koncza sie gry rowne, wiec "mniejsza niz pierwsza kratka" trafia w co do
# polowki stopnia na kazdej planszy. Pilnuje tego test.
# Rogi nazywaja juz oba brzegi i pokazuja strzalkami, gdzie patrzec, wiec opisowi
# zostaje tylko to, czego z samej tabeli odczytac sie nie da: co znaczy kratka
# i co dzieje sie przed pierwsza z nich.
OPIS = "W kratkach różnica stopni. Mniejsza niż pierwsza kratka to gra równa."


def tabela(plansza: str) -> str:
    """Sam <table> jednej planszy — do wklejenia na ranking.html.

    Strona jest pisana recznie i nie ma build-stepu, wiec markup wkleja sie tam
    raz, a pilnuje go test: ma byc znak w znak tym, co zwraca ta funkcja.
    """
    return (
        f'<table class="sila komp" id="wyrownanie-{plansza}">\n'
        + _tabela_siatki(plansza)
        + "\n        </table>"
    )


def _sekcja(plansza: str) -> str:
    return f"""\
    <section id="plansza-{plansza}">
      <table class="sila komp" id="wyrownanie-{plansza}">
{_tabela_siatki(plansza)}
      </table>
    </section>"""


def jako_html() -> str:
    """Caly plik HTML, z koncowa nowa linia."""
    sekcje = "\n".join(_sekcja(plansza) for plansza in PLANSZE)
    return f"""\
<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wyrównanie Semedori — {', '.join(PLANSZE)}</title>
<style>
{STYL}
</style>
</head>
<body>
  <h1>Wyrównanie Semedori</h1>
  <p class="opis">{OPIS}</p>
  <div class="tabele">
{sekcje}
  </div>
</body>
</html>
"""
