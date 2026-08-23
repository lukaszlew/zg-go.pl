#!/usr/bin/env python3
"""Lokalny podglad strony — zwykly serwer plikow na pierwszym wolnym porcie.

Uruchomienie:  make serve

Strona jest statyczna, wiec serwer plikow wystarczy. Z pliku (file://) nie
zadzialalby natomiast modul spotkania.js ani sciezki absolutne, wiec podgladu nie
da sie zastapic otwarciem HTML-a z dysku.

Port szuka sie sam. Drugi podglad w sasiednim terminalu, zapomniany proces po
Ctrl-Z, cudzy serwer na 8000 — kazde z tego konczylo sie wczesniej wysypka
"Address already in use" zamiast dzialajacym podgladem. Zajety port to nie blad,
tylko powod, zeby wziac nastepny.

Wolny port bierze sie przez proba zajecia, a nie przez sprawdzenie: miedzy
sprawdzeniem a zajeciem port zdazylby zniknac.
"""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

KATALOG = Path(__file__).resolve().parent.parent
ADRES = "127.0.0.1"
PIERWSZY_PORT = 8000
ILE_PORTOW = 20


class Obsluga(SimpleHTTPRequestHandler):
    """Serwer plikow plus adresy bez rozszerzenia, jak na GitHub Pages.

    Strona linkuje podstrony bez ".html" (/ranking), a tak samo robi produkcja —
    wiec i podglad musi: /ranking podaje ranking.html. Bez tego kazdy klik w menu
    podgladu konczylby sie 404 i podglad nie sprawdzalby prawdziwych linkow.
    """

    def translate_path(self, path: str) -> str:
        plik = Path(super().translate_path(path))
        strona = plik.with_suffix(".html")
        if not plik.suffix and not plik.is_dir() and strona.is_file():
            return str(strona)
        return str(plik)


def serwer() -> ThreadingHTTPServer:
    """Serwer na pierwszym wolnym porcie od PIERWSZY_PORT."""
    obsluga = partial(Obsluga, directory=str(KATALOG))
    for port in range(PIERWSZY_PORT, PIERWSZY_PORT + ILE_PORTOW):
        try:
            return ThreadingHTTPServer((ADRES, port), obsluga)
        except OSError:
            continue
    raise SystemExit(
        f"wszystkie porty {PIERWSZY_PORT}-{PIERWSZY_PORT + ILE_PORTOW - 1} zajete — "
        "zamknij ktorys podglad albo zmien PIERWSZY_PORT"
    )


def main() -> None:
    with serwer() as s:
        print(f"Podglad: http://{ADRES}:{s.server_port}/   (Ctrl+C konczy)", flush=True)
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            print()          # zeby "^C" nie zostalo sklejone z zacheta powloki
            sys.exit(0)


if __name__ == "__main__":
    main()
