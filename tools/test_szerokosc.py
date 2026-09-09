#!/usr/bin/env python3
"""Zadna strona nie rozpycha sie poza ekran, takze bardzo waski.

Uruchomienie:  python3 -m unittest discover -s tools
Headless Chrome laduje kazda strone w <iframe> o zadanej szerokosci i mierzy
document.scrollWidth: jesli przekracza szerokosc okna, jakis element jest
sztywniejszy niz ekran (tabela bez przewijania, obraz o stalej szerokosci,
slowo bez mozliwosci zlamania, kolumna siatki z min-width: auto). Test
wypisuje winowajcow: elementy, ktore wystaja poza okno.

Pomiar idzie przez jedna strone-opakowanie (pomiar.html w katalogu
tymczasowym) czytana z --dump-dom — bez dodatkowych bibliotek, wystarczy
sam Chrome. Iframe'y laduja sie po kolei, a wynik wraca jako JSON w <pre>.
"""

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
STRONY = sorted(p.name for p in KORZEN.glob("*.html"))
SZEROKOSCI = (320, 200)     # typowy telefon i zapas ponizej najwezszych ekranow

OPAKOWANIE = """<!doctype html><meta charset="utf-8"><title>pomiar</title>
<iframe id="f" style="height:1200px;border:0"></iframe>
<pre id="out"></pre>
<script>
const zadania = %s;          // [[strona, szerokosc], ...]
const wyniki = [];
const f = document.getElementById('f');
function nastepne() {
  if (!zadania.length) {
    document.getElementById('out').textContent = JSON.stringify(wyniki);
    return;
  }
  const [strona, szer] = zadania.shift();
  f.style.width = szer + 'px';
  f.onload = () => {
    const d = f.contentDocument;
    const winne = [];
    for (const el of d.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect();
      if (r.right > szer + 0.5) {
        const klasa = typeof el.className === 'string' && el.className.trim()
          ? '.' + el.className.trim().replace(/\\s+/g, '.') : '';
        winne.push(`${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${klasa} ` +
                   `${Math.round(r.width)}px, prawa krawedz ${Math.round(r.right)}px`);
      }
    }
    wyniki.push({strona, szer, scrollWidth: d.documentElement.scrollWidth, winne});
    nastepne();
  };
  f.src = strona;
}
nastepne();
</script>
"""


def chrome() -> str:
    for nazwa in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        sciezka = shutil.which(nazwa)
        if sciezka:
            return sciezka
    raise AssertionError("brak przegladarki Chrome/Chromium w PATH — test szerokosci stron jej wymaga")


def zmierz() -> list[dict]:
    """Wyniki pomiaru wszystkich stron we wszystkich szerokosciach."""
    zadania = [[f"file://{KORZEN / strona}", szer] for strona in STRONY for szer in SZEROKOSCI]
    with tempfile.TemporaryDirectory() as katalog:
        opakowanie = Path(katalog) / "pomiar.html"
        opakowanie.write_text(OPAKOWANIE % json.dumps(zadania))
        wynik = subprocess.run(
            [chrome(), "--headless=new", "--disable-gpu", "--no-sandbox",
             "--allow-file-access-from-files", f"--virtual-time-budget={4000 * len(zadania)}",
             "--dump-dom", f"file://{opakowanie}"],
            capture_output=True, text=True, check=True, timeout=300).stdout
    m = re.search(r'<pre id="out">(.*?)</pre>', wynik, re.S)
    assert m and m.group(1), "opakowanie nie zapisalo wyniku — Chrome nie doczekal koncow ladowania"
    wyniki = json.loads(m.group(1))
    assert len(wyniki) == len(zadania), f"zmierzono {len(wyniki)} z {len(zadania)} zadan"
    return wyniki


class TestSzerokoscStron(unittest.TestCase):
    def test_zadna_strona_nie_wystaje_poza_ekran(self) -> None:
        for w in zmierz():
            strona = Path(w["strona"]).name
            with self.subTest(strona=strona, szerokosc=w["szer"]):
                self.assertLessEqual(
                    w["scrollWidth"], w["szer"],
                    f"{strona} przy {w['szer']}px ma scrollWidth {w['scrollWidth']}px; wystaja:\n  "
                    + "\n  ".join(w["winne"][:12]))


if __name__ == "__main__":
    unittest.main()
