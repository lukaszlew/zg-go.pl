#!/usr/bin/env python3
"""Zasady na stronie i na karcie musza byc dokladnie tymi z zasady.py.

Uruchomienie:  python3 -m unittest discover -s tools
Odpala sie tez jako pre-commit hook (tools/githooks/pre-commit).

Testy porownuja goly tekst, wiec strona moze dowolnie stylowac wnetrze zdania
(<span class="ps">, <a>, ...) — liczy sie to, co widzi czytelnik.
"""

import re
import unittest
from pathlib import Path

import karta_pdf
import zasady

STRONA = Path(__file__).resolve().parent.parent / "ranking.html"

# rozdzialy z zasadami; kazda zasada stoi w nich jako <strong> na poczatku akapitu
ROZDZIALY_ZASAD = ("wyrownanie", "wynik", "zmiana-ps")


def tekst(html: str) -> str:
    """Goly tekst fragmentu HTML, ze spacjami zwinietymi do jednej."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def sekcja(html: str, ident: str) -> str:
    """Zawartosc <section>/<nav> o danym id."""
    m = re.search(rf'<(section|nav)[^>]*id="{ident}"[^>]*>(.*?)</\1>', html, re.S)
    assert m, f"brak sekcji o id={ident} w {STRONA.name}"
    return m.group(2)


def listy_zasad(html: str) -> list[str]:
    """Kolejne bloki <ol class=zasady> ze spisu."""
    return re.findall(r'<ol class="zasady"[^>]*>(.*?)</ol>', html, re.S)


class TestZasady(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = STRONA.read_text()
        cls.spis = sekcja(cls.html, "zasady")
        cls.zdania = [z for _, z in zasady.ZASADY]

    def test_spis_wymienia_zasady_w_kolejnosci(self) -> None:
        pozycje = [tekst(m) for blok in listy_zasad(self.spis)
                   for m in re.findall(r"<li>(.*?)</li>", blok, re.S)]
        self.assertEqual(pozycje, self.zdania)

    def test_spis_linkuje_kazda_zasade_do_jej_rozwiniecia(self) -> None:
        cele = re.findall(r'<li><a href="#(zasada-\d+)">', self.spis)
        self.assertEqual(cele, [f"zasada-{n}" for n in range(1, len(self.zdania) + 1)])
        for cel in cele:
            self.assertIn(f'id="{cel}"', self.html, f"kotwica {cel} bez celu")

    def test_numeracja_spisu_jest_ciagla(self) -> None:
        starty = [int(s or 1) for s in
                  re.findall(r'<ol class="zasady"(?: start="(\d+)")?>', self.spis)]
        oczekiwane, n = [], 1
        for blok in listy_zasad(self.spis):
            oczekiwane.append(n)
            n += len(re.findall(r"<li>", blok))
        self.assertEqual(starty, oczekiwane)
        self.assertEqual(n - 1, len(self.zdania))

    def test_rozdzialy_maja_dokladnie_te_zasady(self) -> None:
        naglowki = [
            tekst(m)
            for ident in ROZDZIALY_ZASAD
            for m in re.findall(r"<strong>(.*?)</strong>", sekcja(self.html, ident), re.S)
        ]
        self.assertEqual(naglowki, self.zdania, "kolejnosc albo tresc zasad w rozdzialach")

    def test_numery_przy_zasadach_zgadzaja_sie_z_kolejnoscia(self) -> None:
        numery = [
            (int(ident), int(nr))
            for r in ROZDZIALY_ZASAD
            for ident, nr in re.findall(
                r'<p class="zasada" id="zasada-(\d+)"><span class="nr">(\d+)\.</span>',
                sekcja(self.html, r))
        ]
        oczekiwane = [(n, n) for n in range(1, len(self.zdania) + 1)]
        self.assertEqual(numery, oczekiwane)

    def test_sciaga_karty_to_te_same_zasady(self) -> None:
        ze_sciagi = [(kolumna, z) for kolumna, punkty in karta_pdf.SCIAGA for _, z in punkty]
        self.assertEqual(ze_sciagi, zasady.ZASADY)

    def test_sciaga_ma_kolumny_w_kolejnosci_wypelniania(self) -> None:
        self.assertEqual([k for k, _ in karta_pdf.SCIAGA], list(zasady.KOLUMNY))

    def test_karta_w_repo_jest_z_biezacych_zasad(self) -> None:
        """Ostatnie ogniwo lancucha jednego zrodla prawdy.

        Zasady -> strona i zasady -> SCIAGA pilnuja testy wyzej, ale karta.pdf
        jest binarna: mogla powstac z zasad sprzed dwoch zmian i diff tego nie
        pokaze. Zamek zapisuje `make`, wiec rozjazd znaczy tyle, ze ktos zmienil
        zasady albo uklad i nie przegenerowal karty.
        """
        zamek = karta_pdf.czytaj_zamek()
        self.assertTrue(zamek, f"brak {karta_pdf.ZAMEK.name} — uruchom `make`")
        self.assertEqual(zamek["odcisk"], karta_pdf.odcisk(),
                         "zasady albo uklad karty zmienily sie bez `make`")
        self.assertEqual(zamek["wersja"], karta_pdf.WERSJA)


if __name__ == "__main__":
    unittest.main()
