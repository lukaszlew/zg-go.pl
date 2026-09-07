#!/usr/bin/env python3
"""Wersjonowanie zasobow w linkach stron — koniec ze stara kopia w cache.

Uruchomienie: python3 tools/wersjonuj.py   (robi to tez `make`)

GitHub Pages cachuje pliki na ~10 minut i nie daje kontroli nad naglowkami,
wiec po deployu przegladarka potrafi zlozyc nowy HTML ze stara kopia
style.css albo skryptu — strona wtedy wyglada na zepsuta. Kazdy link do
zasobu z listy ZASOBY niesie wiec ?v=<odcisk pliku>: zmiana pliku zmienia
adres, a nowy adres nigdy nie siedzi w cache. Zgodnosci wersji w HTML
z plikami pilnuje test w tools/test_strona.py.
"""

import hashlib
import re
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent

# Zasoby, ktorych rozjazd z HTML psuje strone: arkusz, skrypty i wycinki
# tablicy. PDF-y i obrazy dekoracyjne zyja bez wersji — stara kopia nie
# psuje ukladu, a po 10 minutach i tak sie odswieza.
ZASOBY: tuple[str, ...] = (
    "style.css",
    "analityka.js",
    "spotkania.js",
    "wyrownanie.js",
    "tablica/wycinek-zasady.svg",
    "tablica/wycinek-tabele.svg",
    "tablica/wycinek-tablica.svg",
)


def odcisk(zasob: str) -> str:
    """Osiem znakow sha256 zawartosci pliku."""
    return hashlib.sha256((KORZEN / zasob).read_bytes()).hexdigest()[:8]


def wersjonuj(html: str) -> str:
    """Kazde odwolanie do zasobu z listy dostaje aktualne ?v=<odcisk>."""
    for zasob in ZASOBY:
        wzor = rf'((?:src|href)="{re.escape(zasob)})(\?v=[0-9a-f]*)?"'
        html = re.sub(wzor, rf'\g<1>?v={odcisk(zasob)}"', html)
    return html


def main() -> None:
    for strona in sorted(KORZEN.glob("*.html")):
        stare = strona.read_text()
        nowe = wersjonuj(stare)
        if nowe != stare:
            strona.write_text(nowe)
            print(f"zaktualizowane wersje: {strona.name}")


if __name__ == "__main__":
    main()
