#!/usr/bin/env python3
"""Karta czarno-biala ma byc czarno-biala naprawde — w pliku, nie tylko w kodzie.

Uruchomienie:  python3 -m unittest discover -s tools
Odpala sie tez jako pre-commit hook (tools/githooks/pre-commit).

Paleta CZARNO_BIALA w karta_pdf.py pilnuje sama siebie assertem; ten test
rasteryzuje gotowy karta-cb.pdf z repo i patrzy na piksele, bo jeden
zapomniany HexColor poza paleta nie zmienilby tamtego asserta.
"""

import io
import subprocess
import unittest
from pathlib import Path

from PIL import Image

KARTA_CB = Path(__file__).resolve().parent.parent / "karta-cb.pdf"


class TestCzarnoBiala(unittest.TestCase):
    def test_karta_cb_w_repo_nie_ma_szarosci(self) -> None:
        """Bez antyaliasingu kazdy piksel pochodzi wprost z koloru w PDF-ie, wiec
        szary piksel = szary kolor w pliku (tlo, kreska albo tekst)."""
        self.assertTrue(KARTA_CB.is_file(), f"brak {KARTA_CB.name} — uruchom `make`")
        png = subprocess.run(
            ["pdftocairo", "-png", "-singlefile", "-antialias", "none", "-r", "150",
             str(KARTA_CB), "-"],
            check=True, capture_output=True,
        ).stdout
        obraz = Image.open(io.BytesIO(png)).convert("L")
        wartosci = {wartosc for _, wartosc in obraz.getcolors()}
        self.assertLessEqual(wartosci, {0, 255}, f"szarosci na karcie: {sorted(wartosci)}")


if __name__ == "__main__":
    unittest.main()
