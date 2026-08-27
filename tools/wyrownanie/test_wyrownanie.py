#!/usr/bin/env python3
"""Pliki wyrownanie-*.json i zestawienie-*.txt musza byc swieze, czytelne i zgodne.

Uruchomienie:  python3 -m unittest discover -s tools
Odpala sie tez jako pre-commit hook (tools/githooks/pre-commit).

Same liczby sa przepisane recznie ze zrodel, wiec zaden test nie udowodni, ze sa
prawdziwe — moze za to zlapac literowke. Sluzy do tego arytmetyka tabeli:
w regularnym zrodle jedna jednostka roznicy to zawsze tyle samo punktow, wiec
przestawiona cyfra od razu wychodzi z rytmu. Tabele, ktore rytmu nie trzymaja,
maja tu wlasny test opisujacy dokladnie, gdzie i o ile sie lamia — zeby dziwactwo
zrodla dalo sie odroznic od naszego bledu.
"""

import json
import pathlib
import re
import unittest

from . import bga, hunt, lsg, tabela_html, zg
from .tabela import KOLUMNY, plik_json, przewaga
from .generuj import PLANSZE, ZRODLA_DANYCH, tresc, tresc_zestawienia, zrodla_planszy
from .zestawienie import BRAK, plik_zestawienia, ruchy

# Kazda para zrodlo+plansza osobno: osiem tabel, kazda sprawdzana z osobna.
KAZDA_TABELA = [(modul, plansza) for modul in ZRODLA_DANYCH for plansza in modul.TABELE]


def wiersze_tabeli(zawartosc: str, plansza: str) -> list[str]:
    """Same wiersze z liczbami jednej tabeli, tak jak stoja w pliku."""
    blok = re.search(rf'"{re.escape(plansza)}": \[\n(.*?)\n    \]', zawartosc, re.S)
    assert blok, f"w pliku nie ma tabeli {plansza}"
    return [w for w in blok.group(1).splitlines() if w.strip()]


class Swiezosc(unittest.TestCase):
    def test_pliki_json_zgadzaja_sie_z_tabelami(self):
        """Zmiana liczby bez `make wyrownanie` ma nie przejsc przez pre-commit."""
        for modul in ZRODLA_DANYCH:
            with self.subTest(zrodlo=modul.NAZWA):
                plik = plik_json(modul.NAZWA)
                self.assertTrue(plik.exists(), f"brak {plik.name} — odpal `make wyrownanie`")
                self.assertEqual(
                    plik.read_text(encoding="utf-8"), tresc(modul),
                    f"{plik.name} rozjechal sie z tools/wyrownanie/{modul.NAZWA}.py",
                )

    def test_json_wraca_do_tych_samych_liczb(self):
        """Wyrownanie kolumn nie moze zepsuc ani skladni, ani wartosci."""
        for modul in ZRODLA_DANYCH:
            with self.subTest(zrodlo=modul.NAZWA):
                dane = json.loads(tresc(modul))
                self.assertEqual(list(dane["kolumny"]), list(KOLUMNY))
                self.assertEqual(dane["zrodlo"], modul.ZRODLA)
                self.assertEqual(dane["uwaga"], modul.UWAGA)
                self.assertEqual(
                    {p: [tuple(w) for w in t] for p, t in dane["tabele"].items()},
                    {p: [tuple(w) for w in t] for p, t in modul.TABELE.items()},
                )


class Czytelnosc(unittest.TestCase):
    def test_cyfry_stoja_jedna_pod_druga(self):
        """Minus i koncowka ".5" zwisaja poza kolumne cyfr, a nie przesuwaja jej."""
        for modul, plansza in KAZDA_TABELA:
            with self.subTest(zrodlo=modul.NAZWA, plansza=plansza):
                # Ostatni wiersz nie ma przecinka na koncu, wiec porownujemy bez niego.
                wiersze = [w.rstrip(",") for w in wiersze_tabeli(tresc(modul), plansza)]
                self.assertEqual(len({len(w) for w in wiersze}), 1, "wiersze roznej dlugosci")
                przecinki = {tuple(m.start() for m in re.finditer(",", w)) for w in wiersze}
                self.assertEqual(len(przecinki), 1, "kolumny nie stoja pod soba")
                self.assertEqual(len(przecinki.pop()), len(KOLUMNY) - 1)

    def test_wyglad_wiersza_z_minusem_i_polowka(self):
        """Zapis na przykladzie 9x9 BGA — jedyna tabela z minusem i ".5" naraz."""
        wiersze = wiersze_tabeli(tresc(bga), "9x9")
        self.assertEqual(wiersze[0].strip(), "[ 0, 0,  6  ],")
        self.assertEqual(wiersze[1].strip(), "[ 1, 0,  4.5],")
        self.assertEqual(wiersze[5].strip(), "[ 5, 0, -2  ],")

    def test_puste_linie_dziela_bloki_kamieni(self):
        """Plik lamie sie tam, gdzie tabela w zrodle — inaczej nie da sie go czytac."""
        for modul, plansza in KAZDA_TABELA:
            with self.subTest(zrodlo=modul.NAZWA, plansza=plansza):
                blok = re.search(
                    rf'"{re.escape(plansza)}": \[\n(.*?)\n    \]', tresc(modul), re.S,
                ).group(1)
                kamienie = [k for _, k, _ in modul.TABELE[plansza]]
                self.assertEqual(blok.count("\n\n"), len(set(kamienie)) - 1)


class Zestawienie(unittest.TestCase):
    """Zestawienie ma pokazywac zrodla w jednej mierze i nic po drodze nie gubic."""

    @staticmethod
    def _blok(plansza: str) -> tuple[str, list[str]]:
        """(wiersz naglowkow, wiersze z liczbami) z pliku zestawienia."""
        linie = tresc_zestawienia(plansza).rstrip("\n").splitlines()
        poczatek = next(numer for numer, l in enumerate(linie) if l.startswith("roznica"))
        return linie[poczatek], linie[poczatek + 1:]

    def test_pliki_zestawien_zgadzaja_sie_z_tabelami(self):
        for plansza in PLANSZE:
            with self.subTest(plansza=plansza):
                plik = plik_zestawienia(plansza)
                self.assertTrue(plik.exists(), f"brak {plik.name} — odpal `make wyrownanie`")
                self.assertEqual(plik.read_text(encoding="utf-8"), tresc_zestawienia(plansza))

    def test_gra_rowna_to_u_wszystkich_jeden_ruch(self):
        """Cala miara stoi na tym: 0 kamieni u BGA i 1 kamien u Hunta to to samo."""
        for plansza in PLANSZE:
            for modul in zrodla_planszy(plansza):
                with self.subTest(plansza=plansza, zrodlo=modul.NAZWA):
                    _, kamienie, _ = modul.TABELE[plansza][0]
                    self.assertEqual(ruchy(kamienie), 1)
        self.assertEqual([ruchy(k) for k in (0, 1, 2, 3)], [1, 1, 2, 3], "0 i 1 to ten sam ruch")

    def test_kolumny_stoja_pod_soba_takze_w_zestawieniu(self):
        for plansza in PLANSZE:
            with self.subTest(plansza=plansza):
                naglowek, wiersze = self._blok(plansza)
                self.assertEqual(
                    {len(w) for w in wiersze}, {len(naglowek)},
                    "wiersz musi byc dokladnie tak szeroki jak naglowek",
                )

    def test_ogon_dopelniony_az_do_najdluzszej_tabeli(self):
        """Wiersze ida do konca najdluzszego zrodla, a krotsze dostaja myslniki."""
        for plansza in PLANSZE:
            with self.subTest(plansza=plansza):
                dlugosci = [len(m.TABELE[plansza]) for m in zrodla_planszy(plansza)]
                _, wiersze = self._blok(plansza)
                self.assertEqual(len(wiersze), max(dlugosci))
                self.assertEqual([int(w.split()[0]) for w in wiersze], list(range(max(dlugosci))))
                # Tyle par myslnikow, ile zrodel skonczylo sie przed ostatnim wierszem.
                # Liczymy cale pola, nie znaki: minus w komi tez jest myslnikiem.
                self.assertEqual(
                    wiersze[-1].split().count(BRAK),
                    2 * sum(d < max(dlugosci) for d in dlugosci),
                )
                self.assertNotIn(BRAK, wiersze[0].split(), "przy roznicy 0 mowia wszystkie zrodla")

    def test_liczby_w_zestawieniu_to_te_same_liczby_co_w_tabelach(self):
        """Zestawienie nie ma prawa nic przeliczyc poza sprowadzeniem do ruchow."""
        for plansza in PLANSZE:
            _, wiersze = self._blok(plansza)
            for numer, modul in enumerate(zrodla_planszy(plansza)):
                with self.subTest(plansza=plansza, zrodlo=modul.NAZWA):
                    for roznica, kamienie, komi in modul.TABELE[plansza]:
                        pola = wiersze[roznica].split()
                        self.assertEqual(int(pola[1 + 2 * numer]), ruchy(kamienie))
                        self.assertEqual(float(pola[2 + 2 * numer]), float(komi))


class Arytmetyka(unittest.TestCase):
    def test_tabele_regularne_ida_stalym_krokiem(self):
        for modul in ZRODLA_DANYCH:
            for plansza, opis in modul.ARYTMETYKA.items():
                with self.subTest(zrodlo=modul.NAZWA, plansza=plansza):
                    self.assertIn(plansza, modul.TABELE)
                    punkty = przewaga(modul.TABELE[plansza], opis.wartosc_kamienia)[opis.od:]
                    kroki = [b - a for a, b in zip(punkty, punkty[1:])]
                    self.assertEqual(
                        set(kroki), {opis.krok},
                        f"{modul.NAZWA} {plansza}: wyrownanie nie rosnie po {opis.krok}",
                    )

    def test_komi_maleje_w_bloku_i_odbija_na_granicy(self):
        """Wlasnosc wspolna wszystkim tabelom, takze tym nieregularnym."""
        for modul, plansza in KAZDA_TABELA:
            with self.subTest(zrodlo=modul.NAZWA, plansza=plansza):
                tabela = modul.TABELE[plansza]
                for (_, kamienie_a, komi_a), (roznica, kamienie_b, komi_b) in zip(tabela, tabela[1:]):
                    if kamienie_a == kamienie_b:
                        self.assertLess(komi_b, komi_a, f"roznica {roznica}: komi ma malec")
                    else:
                        # Na granicy komi odbija w gore — chyba ze jednostka warta jest
                        # dokladnie jeden ruch (19x19 Semedori), bo wtedy reszta z
                        # dzielenia sie nie zmienia i komi stoi w miejscu.
                        self.assertGreaterEqual(
                            komi_b, komi_a, f"roznica {roznica}: nowy blok, komi nie moze spasc",
                        )


class Dziwactwa(unittest.TestCase):
    """Kazde dziwactwo zrodla przybite testem — zeby nikt go po cichu nie "naprawil"."""

    def test_bga_9x9_powtarza_wyrownanie_na_granicy_blokow(self):
        """Blok BGA obejmuje 12 punktow komi i tyle samo wart jest kamien."""
        punkty = przewaga(bga.TABELA_9X9, wartosc_kamienia=12)
        for roznica in (7, 14, 21):
            self.assertEqual(
                punkty[roznica], punkty[roznica + 1],
                f"roznice {roznica} i {roznica + 1} daja u BGA to samo wyrownanie",
            )
        # Pierwsze cztery kratki schodza po 1,5 punktu komi, dalsze po 2.
        komi = [k for _, _, k in bga.TABELA_9X9[:8]]
        self.assertEqual([a - b for a, b in zip(komi, komi[1:])], [1.5] * 4 + [2] * 3)

    def test_lsg_13x13_lamie_sie_na_szesnastce(self):
        """Jeden uskok o 18 punktow zamiast 5 — reszta tabeli idzie rowno po 5."""
        roznica_uskoku, uskok = lsg.USKOK_13X13
        komi = [k for _, _, k in lsg.TABELA_13X13]
        kamienie = [k for _, k, _ in lsg.TABELA_13X13]
        self.assertEqual(komi[roznica_uskoku - 1] - komi[roznica_uskoku], uskok)
        self.assertEqual(
            kamienie[roznica_uskoku - 1], kamienie[roznica_uskoku],
            "uskok nie ma zadnego pokrycia w kolumnie kamieni",
        )
        # Poza uskokiem wewnatrz bloku komi schodzi po 5 — czyli wlasnie tam, gdzie
        # kamieni nie przybywa, a spadek jest inny niz 5, stoi dokladnie jeden wiersz.
        inne = [
            roznica for roznica in range(1, len(komi))
            if kamienie[roznica - 1] == kamienie[roznica] and komi[roznica - 1] - komi[roznica] != 5
        ]
        self.assertEqual(inne, [roznica_uskoku])

    def test_hunt_13x13_to_ta_sama_arytmetyka_co_bga(self):
        """Te same punkty wyrownania, inny zapis: mniej kamieni i ujemne komi."""
        punkty_bga = przewaga(bga.TABELA_13X13, wartosc_kamienia=10)
        punkty_hunta = przewaga(hunt.TABELA_13X13, wartosc_kamienia=10)
        self.assertEqual(punkty_bga[:len(punkty_hunta)], punkty_hunta)
        self.assertNotEqual(
            bga.TABELA_13X13[:len(punkty_hunta)], hunt.TABELA_13X13,
            "gdyby zapis byl ten sam, jedna z tabel byla by zbedna",
        )


class Semedori(unittest.TestCase):
    """Tabela Semedori jest policzona, wiec test ma sprawdzac zasade, nie liczby."""

    def test_komi_nigdy_nie_schodzi_ponizej_dwunastu(self):
        """Trzynasty punkt kupuje ruch — na tym stoi cala zasada."""
        for plansza, tabela in zg.TABELE.items():
            with self.subTest(plansza=plansza):
                komi = [k for _, _, k in tabela]
                self.assertGreaterEqual(min(komi), -12)
                self.assertEqual(max(komi), -zg.ROWNA, "wyzej od gry rownej nic nie stoi")

    def test_gra_rowna_to_szesc_jencow_na_kazdej_planszy(self):
        for plansza, tabela in zg.TABELE.items():
            with self.subTest(plansza=plansza):
                self.assertEqual(tabela[0], (0, 1, -zg.ROWNA))

    def test_jednostka_sily_warta_jest_tyle_punktow_ile_mowi_stosunek(self):
        """13 i 2 punkty na jednostke — 13x13 schodzi z drabinki, patrz klasa Drabinka."""
        for plansza in zg.ARYTMETYKA:
            with self.subTest(plansza=plansza):
                punkty = przewaga(zg.TABELE[plansza], zg.RUCH)
                self.assertEqual(punkty[0], zg.ROWNA)
                self.assertEqual(
                    {b - a for a, b in zip(punkty, punkty[1:])}, {zg.KROK[plansza]},
                )

    def test_19x19_ma_stale_komi_bo_jednostka_to_dokladnie_jeden_ruch(self):
        """Nie dziwactwo, tylko skutek KROK == RUCH: reszta z dzielenia nie drgnie."""
        self.assertEqual(zg.KROK["19x19"], zg.RUCH)
        _, _, komi = zip(*zg.TABELE["19x19"])
        self.assertEqual(set(komi[1:]), {-(zg.ROWNA % zg.RUCH)}, "od pierwszej kratki stale -7")
        self.assertEqual(komi[1:], tuple([-7]) * (zg.DLUGOSC - 1))
        ruchy_19 = [r for _, r, _ in zg.TABELE["19x19"]]
        self.assertEqual(ruchy_19[2:], list(range(2, len(ruchy_19))), "jednostka roznicy to ruch wiecej")

    def test_zasieg_siega_najdluzszej_z_przepisanych_tabel(self):
        """Kolumna Semedori nie ma sie konczyc przed cudzymi."""
        najdluzsza = max(
            len(m.TABELE[p]) for m in ZRODLA_DANYCH if m is not zg for p in m.TABELE
        )
        self.assertEqual(zg.DLUGOSC, najdluzsza)
        for plansza, tabela in zg.TABELE.items():
            with self.subTest(plansza=plansza):
                self.assertEqual(len(tabela), zg.DLUGOSC)


class TabelaHtml(unittest.TestCase):
    """Trzy tabele w ukladzie z ranking.html: roznica w kratkach, reszta na brzegach."""

    @staticmethod
    def _plaski(tresc: str) -> str:
        """Sam tekst kratki: ulamek wraca na kropke, reszta znacznikow znika."""
        return re.sub(r"<[^>]+>", "", tresc.replace(tabela_html.POLOWKA, ".5"))

    @classmethod
    def _liczba(cls, tekst: str) -> float:
        """Odwrotnosc _kratka_sily: "3" -> 3.0, "3.5" -> 3.5, ".5" -> 0.5."""
        return float(tekst if tekst[0].isdigit() else "0" + tekst)

    @classmethod
    def _tabele(cls, html: str) -> dict[str, list[list[tuple[str, str]]]]:
        """Plansza -> wiersze -> [(atrybuty komorki, tresc)]."""
        return {
            naglowek: [
                [(a, cls._plaski(t)) for a, t in
                 re.findall(r"<t[dh]([^>]*)>(.*?)</t[dh]>", wiersz)]
                for wiersz in re.findall(r"<tr[^>]*>(.*?)</tr>", tabela, re.S)
            ]
            for naglowek, tabela in re.findall(
                r'<table[^>]*id="wyrownanie-([^"]+)"[^>]*>(.*?)</table>', html, re.S
            )
        }

    def test_plik_zgadza_sie_z_modulem(self):
        plik = tabela_html.PLIK
        self.assertTrue(plik.exists(), f"brak {plik.name} — odpal `make wyrownanie`")
        self.assertEqual(plik.read_text(encoding="utf-8"), tabela_html.jako_html())

    def test_trzy_tabele_po_jednej_na_plansze(self):
        tabele = self._tabele(tabela_html.jako_html())
        self.assertEqual(list(tabele), list(tabela_html.PLANSZE))
        self.assertEqual(list(tabela_html.PLANSZE), ["19x19", "13x13", "9x9"], "od najwiekszej")

    def test_siatka_czyta_sie_z_brzegow(self):
        """Prawy brzeg daje ruchy, gorny punkty, a w kratkach stoi roznica sily.

        Po drabince 13x13 kazda z trzech plansz trafia w siatke rowno, wiec ten
        jeden test opisuje wszystkie trzy tabele.
        """
        tabele = self._tabele(tabela_html.jako_html())
        for plansza in tabela_html.PLANSZE:
            with self.subTest(plansza=plansza):
                czapka, *reszta = tabele[plansza]
                *wiersze, brzeg = reszta
                self.assertNotIn("colgroup", " ".join(a for w in tabele[plansza] for a, _ in w),
                                 "brzegi same sa naglowkami, naglowka tekstowego nie ma")
                punkty = [int(t) for a, t in brzeg if "komp-jency" in a and "rog" not in a]
                self.assertEqual(punkty, sorted(punkty), "punkty rosna w prawo")
                ruchy = [int(t) for w in wiersze for a, t in w
                         if "komp-ruchy" in a and "rog" not in a]
                self.assertEqual(ruchy, list(range(
                    tabela_html.PIERWSZY_RUCH[plansza], tabela_html.RUCHOW[plansza] + 1)))
                for numer, wiersz in enumerate(
                        wiersze, start=tabela_html.PIERWSZY_RUCH[plansza]):
                    for p, (_, tresc) in zip(punkty, wiersz):
                        with self.subTest(ruchy=numer, punkty=p):
                            self.assertTrue(tresc, "siatka ma byc pelna, bez dziur")
                            roznica_sily = self._liczba(tresc)
                            self.assertEqual(zg.wiersz(plansza, roznica_sily), (roznica_sily, numer, -p))

    def test_czapka_niesie_nazwe_planszy(self):
        """Pas nad siatka — jedyne miejsce, gdzie nazwa nie kosztuje ani kratki."""
        html = tabela_html.jako_html()
        self.assertNotIn("<h2>", html, "nazwa planszy zeszla z naglowka na czapke")
        for plansza, wiersze in self._tabele(html).items():
            with self.subTest(plansza=plansza):
                atrybuty, tresc = wiersze[0][0]
                self.assertIn("plansza", atrybuty)
                self.assertEqual(tresc, plansza)
                szerokosc = len(wiersze[1]) - 1
                self.assertIn(f'colspan="{szerokosc}"', atrybuty, "czapka nad cala siatka")

    def test_rogi_nazywaja_swoje_brzegi_ze_strzalka(self):
        """Gorny rog patrzy w dol po ruchach, dolny w lewo po jencach."""
        for plansza, wiersze in self._tabele(tabela_html.jako_html()).items():
            with self.subTest(plansza=plansza):
                self.assertEqual(wiersze[0][-1][1], tabela_html.RUCHY, "gorny rog nad ruchami")
                self.assertEqual(wiersze[-1][-1][1], tabela_html.JENCY, "dolny rog przy jencach")
        self.assertTrue(tabela_html.RUCHY.startswith("↓"), "strzalka przed slowem, w dol")
        # Kazdy rog nalezy do swojego brzegu: gorny do kolumny ruchow (wiec gruba
        # kreska pionowa idzie i przez niego), dolny do wiersza jencow (wiec nie).
        for plansza, wiersze in self._tabele(tabela_html.jako_html()).items():
            with self.subTest(plansza=plansza):
                self.assertIn("komp-ruchy", wiersze[0][-1][0], "gorny rog trzyma z ruchami")
                self.assertNotIn(
                    "komp-ruchy", wiersze[-1][-1][0],
                    "dolnego rogu nie wolno odciac kreska od jego wlasnych liczb",
                )
                self.assertIn("komp-jency", wiersze[-1][-1][0], "ale szarzeje z jencami")
        self.assertTrue(tabela_html.JENCY.startswith("←"), "strzalka przed slowem, w lewo")
        self.assertIn("ruchy", tabela_html.RUCHY)
        self.assertIn("jeńcy", tabela_html.JENCY)

    def test_opis_mowi_tylko_to_czego_tabela_nie_pokazuje(self):
        """Rogi nazywaja brzegi, wiec opisowi zostaje kratka i gra rowna."""
        for slowo in ("ruchy", "jeńcy"):
            with self.subTest(slowo=slowo):
                self.assertNotIn(slowo, tabela_html.OPIS, "brzegi nazywaja sie same, w rogach")
        self.assertLess(len(tabela_html.OPIS), 90, "opis ma sie miescic w jednej linii")

    def test_zadna_tabela_nie_pokazuje_gry_rownej(self):
        """Kratka niesie to, co Czarny dostaje — w grze rownej nie dostaje nic."""
        tabele = self._tabele(tabela_html.jako_html())
        for plansza in tabela_html.PLANSZE:
            with self.subTest(plansza=plansza):
                rowne = set(tabela_html.rowne(plansza))
                self.assertEqual(rowne, {numer * tabela_html.SKOK for numer in range(len(rowne))},
                                 "gry rowne to zawsze poczatek zakresu")
                # Tylko kratki siatki — brzegowe niosa punkty i ruchy, nie roznice.
                widoczne = {
                    self._liczba(tresc)
                    for wiersz in tabele[plansza][1:-1]
                    for atrybuty, tresc in wiersz
                    if tresc and tresc[0].isdigit() and "komp-ruchy" not in atrybuty
                }
                self.assertFalse(widoczne & rowne, "gra rowna nie ma czego pokazac w kratce")

    def test_wyjasnienie_stoi_raz_nad_calym_rzedem(self):
        """Trzy tabele czyta sie tak samo, wiec tlumaczy sie to raz, a nie trzy razy."""
        html = tabela_html.jako_html()
        self.assertEqual(html.count(tabela_html.OPIS), 1)
        self.assertEqual(html.count('<p class="opis">'), 1)
        self.assertNotIn("<caption>", html, "podpisy tabel zlaly sie w jeden opis")
        for slowo in ("różnica siły", "równa"):
            with self.subTest(slowo=slowo):
                self.assertIn(slowo, tabela_html.OPIS)

    def test_kazda_siatka_zaczyna_sie_tam_gdzie_koncza_sie_gry_rowne(self):
        """Na tym stoi wspolne zdanie: "mniejsza niz pierwsza kratka" to gra rowna.

        Gdyby ktoras tabela zaczynala sie dalej, zdanie klamaloby o niej — i wtedy
        trzeba by wrocic do trzech osobnych zdan z liczbami.
        """
        for plansza in tabela_html.PLANSZE:
            with self.subTest(plansza=plansza):
                rowne = tabela_html.rowne(plansza)
                pierwsza = min(tabela_html.siatka(plansza).values())
                self.assertEqual(pierwsza, rowne[-1] + tabela_html.SKOK)
                self.assertEqual(max(rowne), pierwsza - tabela_html.SKOK)

    def test_w_kratkach_nie_ma_ani_jednego_minusa(self):
        for plansza, wiersze in self._tabele(tabela_html.jako_html()).items():
            with self.subTest(plansza=plansza):
                self.assertNotIn("-", " ".join(t for w in wiersze for _, t in w))

    def test_tabele_stoja_w_jednym_rzedzie(self):
        """Trzy tabele obok siebie, od najwiekszej planszy, w kolejnosci PLANSZE."""
        self.assertEqual(tabela_html.PLANSZE, ("19x19", "13x13", "9x9"))
        html = tabela_html.jako_html()
        self.assertIn('class="tabele"', html)
        self.assertNotIn('class="slupek"', html, "rzad nie ma juz slupkow")
        self.assertEqual(
            re.findall(r'<section id="plansza-([^"]+)">', html), list(tabela_html.PLANSZE),
            "kolejnosc w pliku ma byc kolejnoscia w rzedzie",
        )
        self.assertIn("display: flex", tabela_html.STYL)

    def test_dwie_najwieksze_plansze_maja_tyle_samo_wierszy(self):
        """19x19 zaczyna od 2 ruchow, 13x13 od 1 — rowna sie dopiero liczba wierszy."""
        wysokosci = {
            plansza: tabela_html.RUCHOW[plansza] - tabela_html.PIERWSZY_RUCH[plansza] + 1
            for plansza in ("19x19", "13x13")
        }
        self.assertEqual(wysokosci, {"19x19": 7, "13x13": 7})
        self.assertEqual(tabela_html.RUCHOW["19x19"], 8, "od 2 do 8 wlacznie")

    def test_brzegi_nosza_klasy_ze_style_css(self):
        """Zeby <table> wkleic na strone bez dopisywania regul."""
        html = tabela_html.jako_html()
        for klasa in ("sila komp", "komp-jency", "komp-ruchy"):
            with self.subTest(klasa=klasa):
                self.assertIn(klasa, html)
        style = pathlib.Path(tabela_html.KATALOG_PAKIETU).parents[1] / "style.css"
        tresc = style.read_text(encoding="utf-8")
        for klasa in ("komp-jency", "komp-ruchy"):
            with self.subTest(klasa=klasa):
                self.assertIn(klasa, tresc, "klasa musi istniec w arkuszu strony")


class Drabinka(unittest.TestCase):
    """13x13 schodzi z drabinki, a nie z krok razy roznica — i to ma konsekwencje."""

    def test_petla_powtarza_sie_co_do_pozycji(self):
        """Co pol jedna pozycja nizej, co pieta — caly ruch wiecej."""
        for pozycja in range(len(zg.PETLA_13X13) * 4):
            roznica_sily = zg.PIERWSZA_KRATKA_13X13 + pozycja * zg.POLOWKA
            with self.subTest(roznica_sily=roznica_sily):
                _, ruchy, komi = zg.wiersz("13x13", roznica_sily)
                self.assertEqual(ruchy, 1 + pozycja // len(zg.PETLA_13X13))
                self.assertEqual(-komi, zg.PETLA_13X13[pozycja % len(zg.PETLA_13X13)])

    def test_drabinka_zaczyna_sie_dokladnie_za_grami_rownymi(self):
        """Nizej nie siega, bo nie umie trafic w gre rowna — patrz komentarz w zg."""
        tuz_przed = zg.PIERWSZA_KRATKA_13X13 - zg.POLOWKA
        self.assertLess(-zg.wiersz("13x13", tuz_przed)[2], 0, "tuz przed drabinka gra jest rowna")
        self.assertGreaterEqual(-zg.wiersz("13x13", zg.PIERWSZA_KRATKA_13X13)[2], 0)
        self.assertEqual(zg.wiersz("13x13", 0)[1:], (1, -zg.ROWNA), "gra rowna zostaje przy ROWNA")
        self.assertNotIn(
            -zg.ROWNA, [-p for p in zg.PETLA_13X13],
            "gdyby drabinka trafiala w gre rowna, nie trzeba by dwoch czesci",
        )

    def test_drabinka_kosztuje_ulamek_ruchu_na_dalekim_koncu(self):
        """5,2 punktu na jednostke zamiast 5 — nadwyzka ma zostac ponizej jednego ruchu."""
        for roznica_sily, nadwyzka in ((10, 0), (20, 2), (39, 6)):
            with self.subTest(roznica_sily=roznica_sily):
                _, ruchy, komi = zg.wiersz("13x13", roznica_sily)
                z_drabinki = (ruchy - 1) * zg.RUCH - komi
                ze_stosunku = zg.ROWNA + zg.KROK["13x13"] * roznica_sily
                self.assertEqual(z_drabinki - ze_stosunku, nadwyzka)
                self.assertLess(abs(z_drabinki - ze_stosunku), zg.RUCH, "mniej niz caly ruch")

    def test_13x13_nie_deklaruje_juz_stalego_kroku(self):
        """Na drabince pol to raz 3, raz 2 punkty — arytmetyki tam nie ma."""
        self.assertNotIn("13x13", zg.ARYTMETYKA)
        self.assertEqual(set(zg.ARYTMETYKA), {"9x9", "19x19"})
        kroki = [b - a for a, b in zip(zg.PETLA_13X13, zg.PETLA_13X13[1:])]
        # Ostatni krok petli przeskakuje na kolejny ruch, wiec liczy sie przez RUCH.
        zawiniecie = zg.RUCH - zg.PETLA_13X13[-1] + zg.PETLA_13X13[0]
        self.assertEqual(set(kroki + [zawiniecie]), {2, 3}, "pol to raz 2, raz 3 punkty")
        self.assertEqual(sum(kroki) + zawiniecie, zg.RUCH, "cala petla to dokladnie jeden ruch")


class Polowki(unittest.TestCase):
    """Polowka to jeden znak, bo od niej zalezy szerokosc calej kolumny."""

    def test_kratka_pisze_sie_najkrocej_jak_sie_da(self):
        pol = tabela_html.POLOWKA
        self.assertEqual(tabela_html._kratka_sily(0.5), pol, "bez zera z przodu")
        self.assertEqual(tabela_html._kratka_sily(3), "3")
        self.assertEqual(tabela_html._kratka_sily(3.5), "3" + pol)
        self.assertEqual(tabela_html._kratka_sily(41.5), "41" + pol)

    def test_polowka_jest_pionowa_i_waska_jak_cyfra(self):
        """1 nad 2 z kreska — dlatego kolumna moze byc waska na jedna liczbe."""
        self.assertIn("<span>1</span><span>2</span>", tabela_html.POLOWKA)
        self.assertIn("border-top", tabela_html.STYL, "kreska ulamka")
        self.assertIn("span.pol span { display: block", tabela_html.STYL, "cyfry jedna pod druga")
        self.assertNotIn("½", tabela_html.jako_html(), "ukosnej polowki juz nie ma")

    def test_zadna_roznica_nie_zajmuje_wiecej_niz_trzy_miejsca(self):
        """Na tym stoi szerokosc kratki — dluzsza liczba rozepchnelaby cala siatke."""
        for plansza in tabela_html.PLANSZE:
            with self.subTest(plansza=plansza):
                najdluzsza = max(
                    len(tabela_html._kratka_sily(r).replace(tabela_html.POLOWKA, "x"))
                    for r in tabela_html.siatka(plansza).values()
                )
                self.assertLessEqual(najdluzsza, 3)

    def test_przecinek_zniknal_z_tabeli(self):
        self.assertNotIn(",", tabela_html.jako_html().split("<body>")[1])


class BezPierwszegoRuchu(unittest.TestCase):
    """Na 19x19 wiersz "1 ruch" znika: to nie wyrownanie, tylko zwykly pierwszy ruch."""

    def test_19x19_zaczyna_sie_od_pierwszego_darmowego_ruchu(self):
        self.assertEqual(tabela_html.PIERWSZY_RUCH["19x19"], 2)
        self.assertEqual(min(tabela_html.siatka("19x19")), (0, 2))
        self.assertEqual(min(tabela_html.siatka("19x19").values()), 1.5)

    def test_male_plansze_zatrzymuja_swoj_pierwszy_wiersz(self):
        """Tam ten sam wiersz obejmuje kilka jednostek i do 12 jencow — jest za co grac."""
        for plansza in ("13x13", "9x9"):
            with self.subTest(plansza=plansza):
                self.assertEqual(tabela_html.PIERWSZY_RUCH[plansza], 1)
                pierwsze = [r for (_, ruchy), r in tabela_html.siatka(plansza).items() if ruchy == 1]
                self.assertGreater(len(pierwsze), 2, "wiersz wart trzymania")

    def test_wiadomo_ile_jencow_19x19_oddaje_za_ten_wiersz(self):
        """Decyzja kosztuje: przy roznicy 1 Czarny mialby 7 jencow, a gra rowno."""
        self.assertEqual([-zg.wiersz("19x19", r)[2] for r in (0.5, 1.0)], [0, 7])
        self.assertEqual(tabela_html.rowne("19x19"), [0.0, 0.5, 1.0])


class NaStronie(unittest.TestCase):
    """ranking.html nie ma build-stepu, wiec markup wklejamy — i pilnujemy testem."""

    def test_tabele_na_stronie_sa_te_z_generatora(self):
        strona = (pathlib.Path(tabela_html.KATALOG_PAKIETU).parents[1] / "ranking.html")
        html = strona.read_text(encoding="utf-8")
        for plansza in tabela_html.PLANSZE:
            with self.subTest(plansza=plansza):
                oczekiwana = tabela_html.tabela(plansza).replace("\n        ", "\n          ")
                self.assertIn(
                    oczekiwana, html,
                    f"tabela {plansza} na ranking.html rozjechala sie z generatorem "
                    "— wklej ja jeszcze raz zamiast poprawiac recznie",
                )
        self.assertIn('<div class="tabele">', html, "trzy siatki stoja w jednym rzedzie")

    def test_strona_ma_style_dla_klas_z_generatora(self):
        """Markup przynosi wlasne klasy; bez regul w style.css tabela sie rozsypie."""
        arkusz = (pathlib.Path(tabela_html.KATALOG_PAKIETU).parents[1] / "style.css")
        tresc = arkusz.read_text(encoding="utf-8")
        for klasa in ("th.rog", "th.plansza", "span.pol", "col.brzeg"):
            with self.subTest(klasa=klasa):
                self.assertIn(klasa, tresc)


class SiatkiNaKarcie(unittest.TestCase):
    """Karta rysuje te same siatki, co strona — z tego samego zrodla."""

    def test_karta_rysuje_wszystkie_trzy_plansze(self):
        import karta_pdf
        self.assertEqual(karta_pdf.PLANSZE, tabela_html.PLANSZE)
        self.assertIs(karta_pdf.siatka, tabela_html.siatka)

    def test_siatki_mieszcza_sie_w_szerokosc_karty(self):
        """Assert w karcie zlapalby to przy generowaniu; test mowi o tym wczesniej.

        Siatki rozkladaja sie na cala szerokosc karty, a luz idzie w przerwy —
        wiec "miesza sie" znaczy: zostaje przerwa co najmniej 4 mm."""
        import karta_pdf
        szerokosc = sum(
            len({j for j, _ in tabela_html.siatka(p)}) * karta_pdf.KRATKA_W + karta_pdf.BRZEG_W
            for p in tabela_html.PLANSZE
        )
        luz = (karta_pdf.PAGE_W - 2 * karta_pdf.MARGIN - szerokosc) / (len(tabela_html.PLANSZE) - 1)
        self.assertGreaterEqual(luz, 4 * karta_pdf.mm)

    def test_polowka_pisze_sie_tak_samo_jak_na_stronie(self):
        import karta_pdf
        for roznica_sily in (0.5, 3.0, 12.5):
            with self.subTest(roznica_sily=roznica_sily):
                ze_strony = tabela_html._kratka_sily(roznica_sily).replace(tabela_html.POLOWKA, "½")
                self.assertEqual(karta_pdf._kratka_sily(roznica_sily, "½"), ze_strony)
