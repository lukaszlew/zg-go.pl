#!/usr/bin/env python3
"""Obrazek podgladu linku (og:image) dla strony ranking — 1200 x 630.

Uruchomienie: python3 tools/og_tablica.py   (robi to tez `make`)

Kadr to barwny srodek tablicy sily (sekcje 40-44 po 30-34) na cala
szerokosc siatki, renderowany z PDF popplerem i przeskalowany do wymiaru
zalecanego dla podgladow (1200 x 630). Nazwa pliku niesie "tablica" —
inna niz dawne og-karty.png — wiec komunikatory nie podstawia starego
obrazka z wlasnego cache. Swiezosci pilnuje tools/test_tablica.py.
"""

import io
import subprocess
import sys
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "tablica"))

import tablica_kyu_pdf as t
from PIL import Image
from reportlab.lib.units import mm

SZER, WYS = 1200, 630


def generuj(cel: Path) -> None:
    t.zarejestruj_czcionki()
    granice = t.granice_sekcji()
    x0 = t.MARGINES_BOK - 8 * mm
    szer = t.PAGE_W - t.MARGINES_BOK + 8 * mm - x0
    wys = szer * WYS / SZER
    y_gora = t.PAGE_H - (granice[2][0] + 6 * mm)   # nad sekcja 40-44
    SKALA = 150 / 72
    with tempfile.TemporaryDirectory() as katalog:
        prefix = Path(katalog) / "og"
        subprocess.run(
            ["pdftoppm", "-png", "-singlefile", "-r", "150",
             "-x", str(round(x0 * SKALA)), "-y", str(round(y_gora * SKALA)),
             "-W", str(round(szer * SKALA)), "-H", str(round(wys * SKALA)),
             str(KORZEN / "tablica" / "ranking_table-660x950mm.pdf"), str(prefix)],
            check=True)
        obraz = Image.open(prefix.with_suffix(".png")).resize((SZER, WYS), Image.LANCZOS)
    obraz.save(cel, format="PNG", optimize=True)


def main() -> None:
    generuj(KORZEN / "og-tablica.png")
    print(f"og-tablica.png: {SZER} x {WYS}")


if __name__ == "__main__":
    main()
