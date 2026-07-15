#!/usr/bin/env python3
"""Generuje karty przykladowe: gra Bianka-Czarek z przykladu na ranking.html.

Uruchomienie:  python3 tools/karta_przyklad.py
Zapisuje w korzeniu repo:
- karta-przyklad.pdf — pelne karty A4 (strona 1: Czarek, strona 2: Bianka),
- karta-wycinek.pdf — wycinki (naglowek + 1.5 wiersza; polwiersz pusty),
- karta-wycinek-czarek.svg / karta-wycinek-bianka.svg — wycinki do osadzenia
  na stronie (pdftocairo, fonty jako krzywe).
"""

import subprocess
from pathlib import Path

from karta_pdf import KartaDane, Wiersz, generuj_karte, generuj_wycinek

# Gra z przykladu: 9x9, Bianka 81 vs Czarek 60, roznica 21 = 13 + 8,
# 1 dodatkowy ruch, komi netto -2 dla Bialej, Czarek wygrywa o 15 kamieni
# (czwarta wygrana z rzedu -> zmiana podwojona: +4), Bianka -2.
CZAREK = KartaDane(
    nick="Czarek", pkt_9="60", pkt_13="", pkt_19="",
    wiersze=[Wiersz(
        data="15.07", plansza="9", moje_pkt="60",
        przeciwnik_nick="Bianka", przeciwnik_pkt="81", silniejszy_o="21",
        dodatkowe_ruchy="1", komi="−2", wynik="+15", zmiana="+4", nowe_pkt="64",
    )],
)

BIANKA = KartaDane(
    nick="Bianka", pkt_9="81", pkt_13="", pkt_19="",
    wiersze=[Wiersz(
        data="15.07", plansza="9", moje_pkt="81",
        przeciwnik_nick="Czarek", przeciwnik_pkt="60", silniejszy_o="−21",
        dodatkowe_ruchy="1", komi="−2", wynik="−15", zmiana="−2", nowe_pkt="79",
    )],
)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    generuj_karte(root / "karta-przyklad.pdf", [CZAREK, BIANKA])

    wycinek = root / "karta-wycinek.pdf"
    generuj_wycinek(wycinek, [CZAREK, BIANKA], n_rows=1.5)
    for page, nick in [(1, "czarek"), (2, "bianka")]:
        svg = root / f"karta-wycinek-{nick}.svg"
        subprocess.run(
            ["pdftocairo", "-svg", "-f", str(page), "-l", str(page), str(wycinek), str(svg)],
            check=True,
        )
        print(f"OK: {svg} ({svg.stat().st_size} B)")


if __name__ == "__main__":
    main()
