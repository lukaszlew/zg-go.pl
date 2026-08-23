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

from PIL import Image

from karta_pdf import KOLOROWA, SEMEDORI, KartaDane, Wiersz, generuj_karte, generuj_wycinek

# Gra z przykladu: 9x9, sila Bianki 42, sila Czarka 30.
# Roznica 12 -> 9x9 daje 2 ruchy i 5 jencow dla Czarnego.
# Czarek wygrywa o 21 punktow — wyrazna wygrana, wiec dostaje cale 1, a Bianka
# traci pol: przyklad ma pokazywac wlasnie te niesymetrie, a nie najczestszy wypadek.
CZAREK = KartaDane(
    nick="Czarek", plansza="9×9",
    wiersze=[Wiersz(
        data="15.07", moja_sila="30",
        przeciwnik_nick="Bianka", sila_przeciwnika="42", roznica="12",
        ruchy="2", jency="5", typ_gry="—", wynik="+21", zmiana="+1", nowa_sila="31",
    )],
)

BIANKA = KartaDane(
    nick="Bianka", plansza="9×9",
    wiersze=[Wiersz(
        data="15.07", moja_sila="42",
        przeciwnik_nick="Czarek", sila_przeciwnika="30", roznica="12",
        ruchy="2", jency="5", typ_gry="—", wynik="−21", zmiana="−½", nowa_sila="41½",
    )],
)


def zloz_og_image(root: Path, wycinek: Path) -> None:
    """Sklejka obu wycinkow na tle strony jako og:image (1200x630 PNG)."""
    prefix = root / "og-tmp"
    subprocess.run(["pdftocairo", "-png", "-r", "150", str(wycinek), str(prefix)], check=True)
    pages = sorted(root.glob("og-tmp-*.png"))
    assert len(pages) == 2, pages
    w, h, margines = 1200, 630, 30
    plansza = Image.new("RGB", (w, h), "#f4e9cf")
    karty = []
    for page in pages:
        im = Image.open(page)
        target_w = w - 2 * margines
        karty.append(im.resize((target_w, round(im.height * target_w / im.width))))
        page.unlink()
    total_h = sum(im.height for im in karty)
    assert total_h + 3 * margines <= h, f"wycinki za wysokie na og:image: {total_h}"
    gap = (h - total_h) / 3
    y = gap
    for im in karty:
        plansza.paste(im, (margines, round(y)))
        y += im.height + gap
    out = root / "og-karty.png"
    plansza.save(out)
    print(f"OK: {out} ({out.stat().st_size} B)")


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    generuj_karte(root / "karta-przyklad.pdf", [CZAREK, BIANKA], KOLOROWA, SEMEDORI)

    wycinek = root / "karta-wycinek.pdf"
    generuj_wycinek(wycinek, [CZAREK, BIANKA], n_rows=1.5, p=KOLOROWA)
    for page, nick in [(1, "czarek"), (2, "bianka")]:
        svg = root / f"karta-wycinek-{nick}.svg"
        subprocess.run(
            ["pdftocairo", "-svg", "-f", str(page), "-l", str(page), str(wycinek), str(svg)],
            check=True,
        )
        print(f"OK: {svg} ({svg.stat().st_size} B)")
    zloz_og_image(root, wycinek)


if __name__ == "__main__":
    main()
