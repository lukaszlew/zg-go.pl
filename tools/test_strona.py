#!/usr/bin/env python3
"""Inwarianty samych stron: zasoby, kotwice, powtorzone bloki.

Uruchomienie:  python3 -m unittest discover -s tools
Odpala sie tez jako pre-commit hook (tools/githooks/pre-commit).

Strony sa pisane recznie i nie ma build-stepu, wiec nic samo nie pilnuje, czy
odnosnik prowadzi dokadkolwiek i czy ta sama stopka stoi na kazdej podstronie.
Testy sa tekstowe — czytaja pliki, nie renderuja ich — bo szukamy literowek,
a nie bledow ukladu.
"""

import re
import unittest
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent

# Podstrony serwisu. alphago.html jest szkicem: nie linkuje jej nic, ma noindex
# i wlasna, czwarta pozycje w menu. Zasoby i kotwice sprawdzamy w niej tak samo
# jak wszedzie, ale z porownania nawigacji jest wylaczona — do czasu, az artykul
# zostanie dokonczony i wejdzie do menu na kazdej stronie.
STRONY = ["index.html", "ranking.html", "hikaru-no-go.html", "alphago.html", "prywatnosc.html"]
SZKICE = ["alphago.html"]

LOKALNY_ZASOB = re.compile(r'(?:src|href)="((?!https?:|mailto:|webcal:|#|//)[^"]+)"')
KOTWICA = re.compile(r'href="([a-z0-9-]*\.html)?#([a-z0-9-]+)"')
IDENTYFIKATOR = re.compile(r'id="([^"]+)"')
ZAPROSZENIE = re.compile(r'https://discord\.gg/[A-Za-z0-9]+')
WIZYTOWKA = re.compile(r'https://maps\.app\.goo\.gl/[A-Za-z0-9]+')
ZEWNETRZNY_SKRYPT = re.compile(r'<script[^>]*src=[\'"]https?:[^\'"]*')


def tresc(strona: str) -> str:
    return (KORZEN / strona).read_text()


def blok(html: str, wzorzec: str) -> str:
    """Fragment strony zwiniety do jednej linii — do porownan miedzy plikami."""
    m = re.search(wzorzec, html, re.S)
    assert m, f"brak fragmentu {wzorzec}"
    return re.sub(r"\s+", " ", m.group(0)).strip()


class TestZasoby(unittest.TestCase):
    def test_kazdy_lokalny_zasob_istnieje(self) -> None:
        """Literowka w sciezce to na statycznej stronie dziura, nie wyjatek.

        Najtanszy test w repo i jedyny, ktory lapie masowa zmiane nazw plikow —
        np. podmiane wszystkich zdjec na WebP.
        """
        for strona in STRONY:
            for sciezka in set(LOKALNY_ZASOB.findall(tresc(strona))):
                cel = KORZEN / sciezka.split("#")[0]
                self.assertTrue(cel.is_file(), f"{strona} wskazuje na nieistniejace {sciezka}")


class TestKotwice(unittest.TestCase):
    def test_kazda_kotwica_ma_cel(self) -> None:
        """Spis tresci i odsylacze miedzy zasadami zyja z tego, ze cel istnieje."""
        for strona in STRONY:
            for plik, kotwica in set(KOTWICA.findall(tresc(strona))):
                docelowa = plik or strona
                cele = set(IDENTYFIKATOR.findall(tresc(docelowa)))
                self.assertIn(kotwica, cele, f"{strona}: #{kotwica} nie ma celu w {docelowa}")


class TestDiscord(unittest.TestCase):
    """Zaproszenia Discorda wygasaja, wiec adres ma byc dokladnie w jednym miejscu."""

    def test_adres_stoi_tylko_na_stronie_glownej(self) -> None:
        for strona in STRONY:
            if strona == "index.html":
                continue
            self.assertEqual(ZAPROSZENIE.findall(tresc(strona)), [],
                             f"{strona} ma wlasna kopie zaproszenia — linkuj sekcje na index.html")

    def test_data_discord_zgadza_sie_z_linkiem_w_sekcji(self) -> None:
        """spotkania.js bierze adres z data-discord i wstawia go w komunikat bledu.

        Gdyby rozjechal sie z linkiem widocznym w sekcji, czytelnik dostalby
        przy awarii martwe zaproszenie — czyli dokladnie wtedy, gdy chcemy,
        zeby nas znalazl.
        """
        adresy = set(ZAPROSZENIE.findall(tresc("index.html")))
        self.assertEqual(len(adresy), 1, f"rozne adresy Discorda na index.html: {adresy}")


class TestWizytowka(unittest.TestCase):
    """Adres wizytowki w Mapach stoi w kilku miejscach naraz: przy adresie klubu,
    w prosbie o opinie i w danych strukturalnych.

    Skrot nie mowi, dokad prowadzi, wiec kopia z literowka nie rzuca sie w oczy
    ani w kodzie, ani na stronie — prowadzi po prostu donikad. Stad test na to,
    ze wszystkie kopie sa jednym adresem.
    """

    def test_wszystkie_kopie_to_ten_sam_adres(self) -> None:
        adresy = {a for s in STRONY for a in WIZYTOWKA.findall(tresc(s))}
        self.assertEqual(len(adresy), 1, f"rozne adresy wizytowki w serwisie: {adresy}")


class TestAnalityka(unittest.TestCase):
    """Liczniki wchodza na strone wylacznie przez analityka.js.

    Snippet wklejony wprost do HTML-a natychmiast ma cztery kopie, a dopisany
    tylko do trzech stron daje statystyki, ktore po cichu gubia czesc ruchu —
    czyli klamia zamiast krzyczec. Stad zakaz zewnetrznych <script> na stronach:
    kolejny licznik dopisuje sie do listy w analityka.js.
    """

    def test_polityka_ma_miejsce_na_szczegoly_z_kodu(self) -> None:
        """Nazwy uslug, nazwe ciasteczka i czas jego zycia wpisuje analityka.js.

        Polityka prywatnosci starzeje sie dokladnie tam, gdzie ktos przepisal do
        niej szczegol z kodu — zmiana w kodzie nie przypomina o zmianie w tekscie.
        Skoro wiec pisze je kod, to skasowanie pojemnika zabiera je bez sladu:
        strona zostaje z ogolnikami i przestaje mowic, co naprawde zapisuje.
        """
        html = tresc("prywatnosc.html")
        for pojemnik in ["prywatnosc-liczniki", "prywatnosc-ciasteczko", "zgoda-ustawienia"]:
            self.assertIn(f'id="{pojemnik}"', html,
                          f"prywatnosc.html straciła pojemnik #{pojemnik} wypełniany przez analityka.js")

    def test_zaden_licznik_nie_stoi_wprost_w_html(self) -> None:
        for strona in STRONY:
            self.assertEqual(ZEWNETRZNY_SKRYPT.findall(tresc(strona)), [],
                             f"{strona}: licznik dopisz do analityka.js, nie do HTML-a")


class TestPowtorzoneBloki(unittest.TestCase):
    """Cztery pliki maja przepisane te same bloki i nikt tego nie pilnuje.

    Nawigacja juz sie kiedys rozjechala, wiec test nie jest teoretyczny.
    """

    def porownaj(self, wzorzec: str, strony: list[str]) -> None:
        wzorcowy = blok(tresc(strony[0]), wzorzec)
        for strona in strony[1:]:
            self.assertEqual(blok(tresc(strona), wzorzec), wzorcowy,
                             f"{strona} rozni sie od {strony[0]}")

    def test_stopka_jest_wszedzie_ta_sama(self) -> None:
        self.porownaj(r'<footer class="site-footer">.*?</footer>', STRONY)

    def test_analityka_wpieta_wszedzie_tak_samo(self) -> None:
        self.porownaj(r'<script[^>]*analityka\.js[^>]*>.*?</script>', STRONY)

    def test_fonty_ladowane_wszedzie_tak_samo(self) -> None:
        self.porownaj(r'<link href="https://fonts\.googleapis\.com[^>]*>', STRONY)

    def test_menu_prowadzi_do_tych_samych_stron(self) -> None:
        """Porownujemy cele, nie znaczniki: klasa `active` z natury sie rozni."""
        widoczne = [s for s in STRONY if s not in SZKICE]
        menu = {s: re.findall(r'<a href="([^"]+)"', blok(tresc(s), r'<nav class="hb-menu">.*?</nav>'))
                for s in widoczne}
        wzorcowe = menu[widoczne[0]]
        for strona, cele in menu.items():
            self.assertEqual(cele, wzorcowe, f"menu na {strona} rozni sie od {widoczne[0]}")


if __name__ == "__main__":
    unittest.main()
