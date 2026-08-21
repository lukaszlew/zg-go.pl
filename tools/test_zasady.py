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

# Podsekcje "Rozwiniecia zasad", w kolejnosci ze strony; kazda zasada stoi w nich jako
# <strong> na poczatku akapitu. Kolejnosc musi byc ta sama, co w zasady.KOLUMNY —
# to ona, a nie numer, mowi ktora zasada jest ktora.
ROZDZIALY_ZASAD = ("wyrownanie", "wynik", "zmiana-st", "korekta", "kalibracja")


def tekst(html: str) -> str:
    """Goly tekst fragmentu HTML, ze spacjami zwinietymi do jednej."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def sekcja(html: str, ident: str) -> str:
    """Zawartosc <section>/<nav> o danym id."""
    m = re.search(rf'<(section|nav)[^>]*id="{ident}"[^>]*>(.*?)</\1>', html, re.S)
    assert m, f"brak sekcji o id={ident} w {STRONA.name}"
    return m.group(2)


def listy_zasad(html: str) -> list[str]:
    """Kolejne bloki <ul class=zasady> ze spisu."""
    return re.findall(r'<ul class="zasady"[^>]*>(.*?)</ul>', html, re.S)


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
        """Kazda pozycja spisu ma swoje rozwiniecie, i na odwrot — bez sierot."""
        cele = re.findall(r'<li><a href="#(zasada-[\w-]+)">', self.spis)
        self.assertEqual(len(cele), len(self.zdania), "tyle linkow, ile zasad")
        self.assertEqual(len(set(cele)), len(cele), "kazda zasada ma wlasna kotwice")
        for cel in cele:
            self.assertIn(f'id="{cel}"', self.html, f"kotwica {cel} bez celu")
        w_rozdzialach = re.findall(r'<p class="zasada" id="(zasada-[\w-]+)"', self.html)
        self.assertEqual(w_rozdzialach, cele, "rozwiniecia w kolejnosci spisu")

    def test_rozdzialy_maja_dokladnie_te_zasady(self) -> None:
        naglowki = [
            tekst(m)
            for ident in ROZDZIALY_ZASAD
            for m in re.findall(r"<strong>(.*?)</strong>", sekcja(self.html, ident), re.S)
        ]
        self.assertEqual(naglowki, self.zdania, "kolejnosc albo tresc zasad w rozdzialach")

    def test_sciaga_karty_to_te_same_zasady(self) -> None:
        ze_sciagi = [(kolumna, z) for kolumna, punkty in karta_pdf.SCIAGA for z in punkty]
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
