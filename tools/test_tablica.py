#!/usr/bin/env python3
"""Lancuch jednego zrodla prawdy dla tablicy stopni.

Uruchomienie:  python3 -m unittest discover -s tools
Zrodlem zasad tablicy jest tablica/zasady_tablicy.py; z niego powstaje wydruk
ranking_table-660x950mm.pdf. Wydruk jest binarny, wiec pilnuje go zamek
(tablica.lock) zapisywany przez `make` — dokladnie jak karta.lock dla karty.
"""

import sys
import unittest
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "tablica"))

import tablica_kyu_pdf
import zasady_tablicy

STRONA = KORZEN / "ranking.html"

# Podsekcje "Rozwiniecia zasad" na stronie ranking, w kolejnosci ze strony;
# kazda zasada stoi w nich jako <strong> na poczatku akapitu. Kolejnosc musi
# odpowiadac zasady_tablicy.ZASADY — to ona mowi, ktora zasada jest ktora.
ROZDZIALY_ZASAD = ("wyrownanie", "magnes", "gosc", "korekta")


def tekst(html: str) -> str:
    """Goly tekst fragmentu HTML, ze spacjami zwinietymi do jednej."""
    import re
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def sekcja(html: str, ident: str) -> str:
    """Zawartosc <section>/<nav> o danym id."""
    import re
    m = re.search(rf'<(section|nav)[^>]*id="{ident}"[^>]*>(.*?)</\1>', html, re.S)
    assert m, f"brak sekcji o id={ident} w {STRONA.name}"
    return m.group(2)


class TestZasadyNaStronie(unittest.TestCase):
    """Strona ranking mowi dokladnie zdaniami z zasady_tablicy.py."""

    @classmethod
    def setUpClass(cls) -> None:
        import re
        cls.re = re
        cls.html = STRONA.read_text()
        cls.spis = sekcja(cls.html, "zasady")
        cls.zdania = [z for _, z, _ in zasady_tablicy.ZASADY]

    def test_spis_wymienia_zasady_w_kolejnosci(self) -> None:
        pozycje = [tekst(m) for blok in self.re.findall(
                       r'<ul class="zasady"[^>]*>(.*?)</ul>', self.spis, self.re.S)
                   for m in self.re.findall(r"<li>(.*?)</li>", blok, self.re.S)]
        self.assertEqual(pozycje, self.zdania)

    def test_spis_linkuje_kazda_zasade_do_jej_rozwiniecia(self) -> None:
        cele = self.re.findall(r'<li><a href="#(zasada-[\w-]+)">', self.spis)
        self.assertEqual(len(cele), len(self.zdania), "tyle linkow, ile zasad")
        self.assertEqual(len(set(cele)), len(cele), "kazda zasada ma wlasna kotwice")
        for cel in cele:
            self.assertIn(f'id="{cel}"', self.html, f"kotwica {cel} bez celu")
        w_rozdzialach = self.re.findall(r'<p class="zasada" id="(zasada-[\w-]+)"', self.html)
        self.assertEqual(w_rozdzialach, cele, "rozwiniecia w kolejnosci spisu")

    def test_rozdzialy_maja_dokladnie_te_zasady(self) -> None:
        naglowki = [
            tekst(m)
            for ident in ROZDZIALY_ZASAD
            for m in self.re.findall(r'<p class="zasada" id="[\w-]+"><strong>(.*?)</strong>',
                                     sekcja(self.html, ident), self.re.S)
        ]
        self.assertEqual(naglowki, self.zdania, "kolejnosc albo tresc zasad w rozdzialach")


class TestZamekTablicy(unittest.TestCase):
    def test_tablica_w_repo_jest_z_biezacych_zasad(self) -> None:
        """Rozjazd zamka znaczy: ktos zmienil zasady albo uklad i nie zrobil `make`."""
        zamek = tablica_kyu_pdf.czytaj_zamek()
        self.assertTrue(zamek, f"brak {tablica_kyu_pdf.ZAMEK.name} — uruchom `make tablica-pdf`")
        self.assertEqual(zamek["odcisk"], tablica_kyu_pdf.odcisk(),
                         "zasady albo uklad tablicy zmienily sie bez `make tablica-pdf`")
        self.assertEqual(zamek["wersja"], tablica_kyu_pdf.WERSJA)


if __name__ == "__main__":
    unittest.main()
