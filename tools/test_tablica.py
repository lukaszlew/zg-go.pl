#!/usr/bin/env python3
"""Lancuch jednego zrodla prawdy dla tablicy siły.

Uruchomienie:  python3 -m unittest discover -s tools
Zrodlem zasad tablicy jest tablica/zasady_tablicy.py; z niego powstaje wydruk
ranking_table-660x950mm.pdf. Wydruk jest binarny, wiec pilnuje go zamek
(tablica.lock) zapisywany przez `make` — dokladnie jak karta.lock dla karty.
"""

import sys
import unittest
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "tablica"))

import tablica_kyu_pdf
import zasady_tablicy

STRONA = KORZEN / "ranking.html"

# Podsekcje "Rozwiniecia zasad" na stronie ranking, w kolejnosci ze strony;
# kazda zasada stoi w nich jako <strong> na poczatku akapitu. Kolejnosc musi
# odpowiadac zasady_tablicy.ZASADY — to ona mowi, ktora zasada jest ktora.
ROZDZIALY_ZASAD = ("wyrownanie", "magnes", "gosc", "korekta")


def tekst(html: str) -> str:
    """Goly tekst fragmentu HTML, ze spacjami zwinietymi do jednej."""
    import re
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def sekcja(html: str, ident: str) -> str:
    """Zawartosc <section>/<nav> o danym id."""
    import re
    m = re.search(rf'<(section|nav)[^>]*id="{ident}"[^>]*>(.*?)</\1>', html, re.S)
    assert m, f"brak sekcji o id={ident} w {STRONA.name}"
    return m.group(2)


class TestZasadyNaStronie(unittest.TestCase):
    """Strona ranking mowi dokladnie zdaniami z zasady_tablicy.py."""

    @classmethod
    def setUpClass(cls) -> None:
        import re
        cls.re = re
        cls.html = STRONA.read_text()
        cls.zdania = [z for _, z, _ in zasady_tablicy.ZASADY]

    def test_rozdzialy_maja_dokladnie_te_zasady(self) -> None:
        naglowki = [
            tekst(m)
            for ident in ROZDZIALY_ZASAD
            for m in self.re.findall(r'<p class="zasada" id="[\w-]+"><strong>(.*?)</strong>',
                                     sekcja(self.html, ident), self.re.S)
        ]
        self.assertEqual(naglowki, self.zdania, "kolejnosc albo tresc zasad w rozdzialach")


class TestStanKanwy(unittest.TestCase):
    def test_rysowanie_nie_zostawia_przeksztalcen(self) -> None:
        """Kazde translate/rotate/scale zyje miedzy saveState a restoreState,
        a po narysowaniu calej strony stany musza sie bilansowac — inaczej
        jedna strzalka obraca albo przesuwa cala reszte tablicy."""
        import io
        from reportlab.pdfgen.canvas import Canvas

        tablica_kyu_pdf.zarejestruj_czcionki()
        c = Canvas(io.BytesIO(), pagesize=(tablica_kyu_pdf.PAGE_W, tablica_kyu_pdf.PAGE_H))
        glebokosc = 0
        oryginalne = {m: getattr(c, m) for m in
                      ("saveState", "restoreState", "translate", "rotate", "scale")}

        def saveState() -> None:
            nonlocal glebokosc
            glebokosc += 1
            oryginalne["saveState"]()

        def restoreState() -> None:
            nonlocal glebokosc
            glebokosc -= 1
            self.assertGreaterEqual(glebokosc, 0, "restoreState bez saveState")
            oryginalne["restoreState"]()

        def przeksztalcenie(metoda: str):
            def wywolanie(*args: float) -> None:
                self.assertGreater(glebokosc, 0, f"{metoda} poza saveState/restoreState")
                oryginalne[metoda](*args)
            return wywolanie

        c.saveState, c.restoreState = saveState, restoreState
        c.translate = przeksztalcenie("translate")
        c.rotate = przeksztalcenie("rotate")
        c.scale = przeksztalcenie("scale")

        tablica_kyu_pdf.rysuj_strone(c, tablica_kyu_pdf.PAGE_H, None,
                                     tablica_kyu_pdf.WYBRANA[1])
        self.assertEqual(glebokosc, 0, "saveState bez restoreState")


class TestZamekTablicy(unittest.TestCase):
    def test_tablica_w_repo_jest_z_biezacych_zasad(self) -> None:
        """Rozjazd zamka znaczy: ktos zmienil zasady albo uklad i nie zrobil `make`."""
        zamek = tablica_kyu_pdf.czytaj_zamek()
        self.assertTrue(zamek, f"brak {tablica_kyu_pdf.ZAMEK.name} — uruchom `make tablica-pdf`")
        self.assertEqual(zamek["odcisk"], tablica_kyu_pdf.odcisk(),
                         "zasady albo uklad tablicy zmienily sie bez `make tablica-pdf`")
        self.assertEqual(zamek["wersja"], tablica_kyu_pdf.WERSJA)


class TestKadryWycinkow(unittest.TestCase):
    """Kadry wycinkow SVG nie ucinaja tresci wydruku.

    Test renderuje prostokat kadru wprost z PDF (ten sam silnik poppler,
    ktory tnie wycinki przez CropBox) i sprawdza piksele: przy krawedziach
    ma byc czyste tlo (margines istnieje), a tuz pod gornym marginesem —
    farba (naglowki sa w kadrze). Lapie rozjazd geometrii kadrow z ukladem
    tablicy, zanim trafi na strone.
    """

    @staticmethod
    def _piksele(x: float, y: float, w: float, h: float) -> tuple[int, int, bytes]:
        import subprocess
        SKALA = 40 / 72                 # punkty PDF -> piksele przy 40 dpi
        wynik = subprocess.run(
            ["pdftoppm", "-r", "40",
             "-x", str(round(x * SKALA)), "-y", str(round(y * SKALA)),
             "-W", str(round(w * SKALA)), "-H", str(round(h * SKALA)),
             str(tablica_kyu_pdf.REPO / "tablica" / "ranking_table-660x950mm.pdf")],
            capture_output=True, check=True).stdout
        naglowek, dane = wynik.split(b"255\n", 1)
        wymiary = naglowek.split(b"\n")[1]
        szer, wys = map(int, wymiary.split())
        return szer, wys, dane

    def test_kadry_maja_margines_i_tresc(self) -> None:
        import wycinki_svg
        for nazwa, (x, y, w, h) in wycinki_svg.kadry().items():
            if nazwa == "tablica":
                continue        # ten kadr celowo ucina czesciowo sasiednie slupki
            with self.subTest(kadr=nazwa):
                szer, wys, dane = self._piksele(x, y, w, h)
                tlo = dane[0:3]

                def farba(x0: int, x1: int, y0: int, y1: int) -> bool:
                    return any(
                        max(abs(dane[3 * (yy * szer + xx) + k] - tlo[k]) for k in range(3)) > 40
                        for yy in range(y0, y1) for xx in range(x0, x1))

                self.assertFalse(farba(0, szer, 0, 1), f"{nazwa}: tresc przycieta u gory")
                self.assertFalse(farba(0, szer, wys - 1, wys), f"{nazwa}: tresc przycieta u dolu")
                self.assertFalse(farba(0, 1, 0, wys), f"{nazwa}: tresc przycieta z lewej")
                self.assertFalse(farba(szer - 1, szer, 0, wys), f"{nazwa}: tresc przycieta z prawej")
                pas = round(10 / 25.4 * 40)     # 10 mm ponizej gornej krawedzi
                self.assertTrue(farba(0, szer, 1, pas), f"{nazwa}: kadr bez tresci pod gora")


if __name__ == "__main__":
    unittest.main()
