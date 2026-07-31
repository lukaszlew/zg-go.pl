# zg-go.pl

Strona klubu Go **Semedori** w Zielonej Górze.
Hostowana na GitHub Pages → <https://zg-go.pl/>

Pliki źródłowe: `index.html`, `ranking.html`, `hikaru-no-go.html` (czysty HTML + CSS, bez frameworka).
Deploy: `git push` → GitHub Pages auto-deploy.

## Karta gracza i zasady

`make` generuje `karta.pdf` oraz karty i wycinki przykładowe (wymaga `reportlab`,
`pdftocairo`, fontów DejaVu).

Zasady gry mają jedno źródło prawdy: **`tools/zasady.py`**. Te same zdania, co do
słowa, stoją w trzech miejscach: w bloku „Wszystkie zasady" na `ranking.html`,
jako pogrubione nagłówki w rozdziałach Wyrównanie / Wynik / Zmiana PS, oraz na
ściądze na dole karty (`SCIAGA` budowana z `zasady.py`). Ściąga to dokładnie
zasady — nic więcej i nic mniej; co jest za drobne na zasadę, idzie do
szczegółów pod nią na stronie.

Pilnują tego testy na stdlibowym `unittest`, więc działają bez instalowania
czegokolwiek:

```
make test
```

Te same testy odpala hook `pre-commit` — wywołuje `make test`, żeby definicja
stała w jednym miejscu. Po sklonowaniu repo trzeba go raz włączyć:

```
make hooks
```

Po zmianie zasad podbij `WERSJA` w `tools/karta_pdf.py` i uruchom `make`.

## TODO

### Treść / zdjęcia
- [ ] **Duże logo** klubu — zastąpić tekstowy placeholder ("gdyby tylko klub miał logo…") realnym znakiem (SVG lub PNG, najlepiej kwadratowe)
- [ ] **Galeria** — przywrócić sekcję `#galeria` w `index.html`, kiedy będą realne zdjęcia ze spotkań (siatka zdjęć była już zaimplementowana, można odgrzebać z gita)
- [ ] **Osobna sekcja "AlphaGo i Hikaru no Go"** ze zdjęciami / klatkami z filmów — obecnie obie wzmianki siedzą jednym akapitem w "Czemu Go". Sekcja mogłaby mieć poster filmu + kadr z anime, krótki opis każdego.
- [ ] **Zdjęcia Go** — z turniejów, partii, kamieni na drewnie — do hera lub jako tło sekcji "Czemu Go"

### Tekst
- [ ] **Zakończenie "Czemu Go"** — obecne "Ale my po prostu lubimy w nią grać" jest chłodne. Przepisać na konkretną sensorykę / efekt po grze (np. "wychodzisz w piątek wieczór z głową lżejszą inaczej niż po Netflixie").
- [ ] **Social proof** — uzupełnić placeholder w sekcji "Dla kogo" (`<p class="placeholder">[ tu wejdzie info o frekwencji / od kiedy działa klub ]</p>`) realnymi danymi: od kiedy klub działa, średnia frekwencja, ew. udział w turniejach.

### Nice-to-have
- [ ] **Obrazek na koniec strony** — pod "Wpadnij raz, zobaczysz." w sekcji "Kontakt" (np. duże zdjęcie partii Go, kamieni na drewnianej planszy — wizualne zamknięcie strony)
- [ ] Discord — dorzucić info, czy aktywny / ilu członków
- [ ] OG image (1200×630) dla podglądu na social media
- [ ] Favicon
