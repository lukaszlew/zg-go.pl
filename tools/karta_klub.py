#!/usr/bin/env python3
"""Karta dla obcego klubu — przyklad podmiany nazwy i logo.

Uruchomienie:  python3 tools/karta_klub.py   (zapisuje karta-klub-przyklad.pdf
w korzeniu repo: pusta karta fikcyjnego klubu Tengen, bez logo)

Cala lokalnosc karty siedzi w Klub(nazwa, logo):
- nazwa idzie do naglowka ("Ranking <nazwa> · zg-go.pl"),
- logo to prosty SVG ze sciezkami M/L/C/Z (jak img/logo.svg) albo None.
Stopka i kod QR zawsze kieruja na zg-go.pl/ranking — zasady sa jedne.
Wersja czarno-biala: podmien KOLOROWA na CZARNO_BIALA.
"""

from karta_pdf import KOLOROWA, KORZEN, Klub, generuj_karte

TENGEN = Klub(nazwa="Tengen", logo=None)


def main() -> None:
    generuj_karte(KORZEN / "karta-klub-przyklad.pdf", [None], KOLOROWA, TENGEN)


if __name__ == "__main__":
    main()
