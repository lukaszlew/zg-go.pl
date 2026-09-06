#!/usr/bin/env python3
"""Trzy wycinki tablicy sily jako osobne pliki SVG dla strony ranking.

Uruchomienie: python3 tablica/wycinki_svg.py   (po wygenerowaniu tablica.svg)

Kazdy wycinek to pelna tresc tablica.svg z podmienionym viewBoxem — kadry
licza sie z geometrii generatora (tablica_kyu_pdf), wiec kazda zmiana ukladu
tablicy przesuwa je automatycznie i zaden kadr nie przycina tresci.
"""

import re
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
    sekcje = t.sekcje_tablicy()
    y = t.PAGE_H - t.margines_gorny() - t.NAGLOWEK_H - t.SEKCJA
    granice = []
    for nr, (grupa, wys) in enumerate(sekcje):
        y -= (t.ODSTEP_GRUP if nr > 0 else 0) + t.wysokosc_slupka(len(grupa), wys)
        granice.append((y + t.wysokosc_slupka(len(grupa), wys), y))

    gora_dolu = granice[-1][1] - t.SEKCJA
    kol_w = {k: t.szerokosc_kolumny(k) for k in zasady_tablicy.KOLUMNY}
    wymiary = [tuple(w * t.WYR_SKALA for w in t.wymiary_siatki(p)) for p in t.PLANSZE]
    tresc_w = (sum(kol_w.values()) + 2 * t.ODSTEP_KOLUMN_ZASAD + t.ODSTEP_ZASADY_TABELE
               + sum(sz for sz, _ in wymiary) + 2 * 8 * mm)
    margines_pasa = (t.PAGE_W - tresc_w) / 2
    koniec_kolumn = margines_pasa + sum(kol_w.values()) + 2 * t.ODSTEP_KOLUMN_ZASAD
    wys_kolumny = max(
        7.5 * mm + sum(linie for _, linie in zasady_tablicy.zasady_kolumny(k)) * t.ZASADY_LINIA_H
        + len(zasady_tablicy.zasady_kolumny(k)) * 1.2 * mm
        for k in zasady_tablicy.KOLUMNY)
    start_tabel = koniec_kolumn + t.ODSTEP_ZASADY_TABELE - t.ODSTEP_KOLUMN_ZASAD
    kafle_dol = gora_dolu - wymiary[-1][1] - 5 * mm - t.KAFEL_H

    def kadr(x0: float, x1: float, y_gora: float, y_dol: float) -> tuple[float, float, float, float]:
        assert x0 < x1 and y_dol < y_gora, "pusty kadr"
        return (x0, t.PAGE_H - y_gora, x1 - x0, y_gora - y_dol)

    return {
        # slupki srodka skali: pietro jedynek i polowek, sasiedzi widoczni czesciowo
        "tablica": kadr(t.MARGINES_BOK - 3 * mm, t.PAGE_W - t.MARGINES_BOK + 3 * mm,
                        granice[3][0] + 14 * mm, granice[4][1] - 14 * mm),
        "zasady": kadr(margines_pasa - 6 * mm, koniec_kolumn + 5 * mm,
                       gora_dolu + 5 * mm, gora_dolu - wys_kolumny - 4 * mm),
        "tabele": kadr(start_tabel - 2 * mm, t.PAGE_W - margines_pasa + 3 * mm,
                       gora_dolu + 2 * mm, kafle_dol - 3 * mm),
    }


def main() -> None:
    pelny = (REPO / "tablica" / "tablica.svg").read_text()
    for nazwa, (x, y, w, h) in kadry().items():
        naglowek = f'width="{w:.3f}" height="{h:.3f}" viewBox="{x:.3f} {y:.3f} {w:.3f} {h:.3f}"'
        tresc, n = re.subn(r'width="[\d.]+" height="[\d.]+" viewBox="[^"]+"', naglowek, pelny, count=1)
        assert n == 1, "naglowek svg nie pasuje do wzorca"
        cel = REPO / "tablica" / f"wycinek-{nazwa}.svg"
        cel.write_text(tresc)
        mm_ = 72 / 25.4
        print(f"{cel.relative_to(REPO)}: {w/mm_:.0f} x {h/mm_:.0f} mm")


if __name__ == "__main__":
    main()
