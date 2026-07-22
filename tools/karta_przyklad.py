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

from karta_pdf import KartaDane, Wiersz, generuj_karte, generuj_wycinek

# Gra z przykladu: 9x9, Bianka 84 vs Czarek 60,
# roznica PS = 84 - 60 = 24 -> zakres 19-31: Czarny zaczyna 2 ruchami,
# kamienie dla Czarnego = 24 - 19 = 5,
# Czarek wygrywa o 15 kamieni (czwarta wygrana z rzedu -> +2x2), Bianka -2.
CZAREK = KartaDane(
    nick="Czarek", plansza="9×9",
    wiersze=[Wiersz(
        data="15.07", moje_pkt="60",
        przeciwnik_nick="Bianka", przeciwnik_pkt="84", roznica_ps="24",
        ruchy="2", kamienie="5", wynik="+15", zmiana="+2×2", nowe_pkt="64",
    )],
)

BIANKA = KartaDane(
    nick="Bianka", plansza="9×9",
    wiersze=[Wiersz(
        data="15.07", moje_pkt="84",
        przeciwnik_nick="Czarek", przeciwnik_pkt="60", roznica_ps="24",
        ruchy="2", kamienie="5", wynik="−15", zmiana="−2", nowe_pkt="82",
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
    zloz_og_image(root, wycinek)


if __name__ == "__main__":
    main()
