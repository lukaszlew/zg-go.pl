#!/usr/bin/env python3
"""Wycinki tablicy sily jako osobne pliki SVG dla strony ranking: slupki
srodka skali i kazda tabela wyrownania osobno.

Uruchomienie: python3 tablica/wycinki_svg.py   (robi to tez `make`)

Kadry licza sie z geometrii generatora (tablica_kyu_pdf), wiec kazda zmiana
ukladu tablicy przesuwa je automatycznie. Kazdy wycinek powstaje z kopii
PDF-a z CropBoxem ustawionym przez ghostscript (pdftocairo -svg nie umie
ciac sam) — prostokat kadru interpretuje wiec silnik PDF, nie zalozenia
o plotnie SVG.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tablica"))

import tablica_kyu_pdf as t
import zasady_tablicy
from reportlab.lib.units import mm


def kadry() -> dict[str, tuple[float, float, float, float]]:
    """{nazwa: (x, y od gory strony, szerokosc, wysokosc)} w punktach PDF."""
    t.zarejestruj_czcionki()
    granice = t.granice_sekcji()
    gora_dolu = granice[-1][1] - t.SEKCJA
    kol_w = {k: t.szerokosc_kolumny(k) for k in zasady_tablicy.KOLUMNY}
    wymiary = [tuple(w * t.WYR_SKALA for w in t.wymiary_siatki(p)) for p in t.PLANSZE]
    tresc_w = (sum(kol_w.values()) + 2 * t.ODSTEP_KOLUMN_ZASAD + t.ODSTEP_ZASADY_TABELE
               + sum(sz for sz, _ in wymiary) + 2 * 8 * mm)
    margines_pasa = (t.PAGE_W - tresc_w) / 2
    koniec_kolumn = margines_pasa + sum(kol_w.values()) + 2 * t.ODSTEP_KOLUMN_ZASAD
    start_tabel = koniec_kolumn + t.ODSTEP_ZASADY_TABELE

    def kadr(x0: float, x1: float, y_gora: float, y_dol: float) -> tuple[float, float, float, float]:
        assert x0 < x1 and y_dol < y_gora, "pusty kadr"
        return (x0, t.PAGE_H - y_gora, x1 - x0, y_gora - y_dol)

    kadry_ = {
        # slupki srodka skali: pietro polowek (30-34) i jedynek (25-29),
        # sasiedzi widoczni czesciowo — tu mieszka przykladowa gra ze strony
        "tablica": kadr(t.MARGINES_BOK - 3 * mm, t.PAGE_W - t.MARGINES_BOK + 3 * mm,
                        granice[4][0] + 14 * mm, granice[5][1] - 14 * mm),
    }
    # Kazda tabela wyrownania osobno, bez kafelkow przelicznika pod 9x9:
    # na telefonie tabela idzie w naturalnej wielkosci i przewija sie w poziomie.
    x = start_tabel
    for (szer, wys), plansza in zip(wymiary, t.PLANSZE):
        kadry_[f"tabela-{plansza}"] = kadr(x - 2 * mm, x + szer + 2 * mm,
                                           gora_dolu + 2 * mm, gora_dolu - wys - 2 * mm)
        x += szer + 8 * mm
    return kadry_


def main() -> None:
    import subprocess
    import tempfile

    pdf = REPO / "tablica" / "ranking_table-660x950mm.pdf"
    wysokosc = t.PAGE_H
    for nazwa, (x, y, w, h) in kadry().items():
        cel = REPO / "tablica" / f"wycinek-{nazwa}.svg"
        # CropBox w ukladzie PDF (y od dolu); kadry() daja y od gory strony.
        llx, lly, urx, ury = x, wysokosc - y - h, x + w, wysokosc - y
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
            subprocess.run(
                # AutoRotatePages: pdfwrite obraca strone wedlug dominujacego
                # kierunku pisma, a pionowe napisy paskow robia z tablicy
                # "strone pozioma" — wycinek wychodzilby obrocony o 90 stopni.
                ["gs", "-q", "-o", tmp.name, "-sDEVICE=pdfwrite", "-dAutoRotatePages=/None",
                 "-c", f"[/CropBox [{llx:.2f} {lly:.2f} {urx:.2f} {ury:.2f}] /PAGES pdfmark",
                 "-f", str(pdf)],
                check=True)
            subprocess.run(["pdftocairo", "-svg", tmp.name, str(cel)], check=True)
        mm_ = 72 / 25.4
        print(f"{cel.relative_to(REPO)}: {w / mm_:.0f} x {h / mm_:.0f} mm")


if __name__ == "__main__":
    main()
