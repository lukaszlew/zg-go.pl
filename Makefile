# Regeneracja kart gracza i zadania pomocnicze. `make` odswieza wszystko po
# zmianach w tools/. `make help` wypisuje cele.
# Wymaga: python3 + reportlab i Pillow, pdftocairo (poppler-utils), fonty DejaVu.

all: karta.pdf karta-wycinek-czarek.svg  ## przegeneruj karte i karty przykladowe

help:  ## wypisz dostepne cele
	@awk -F':.*##' '/^[a-z-]+:.*##/ { printf "  make %-8s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# sciaga na karcie idzie z zasady.py, wiec zmiana zasad tez odswieza karte
karta.pdf: tools/karta_pdf.py tools/zasady.py tools/fonts/Caveat-Bold.ttf
	python3 tools/karta_pdf.py

# jeden przebieg tworzy tez: karta-przyklad.pdf, karta-wycinek.pdf,
# karta-wycinek-bianka.svg
karta-wycinek-czarek.svg: tools/karta_przyklad.py tools/karta_pdf.py tools/zasady.py tools/fonts/Caveat-Bold.ttf
	python3 tools/karta_przyklad.py

# Jedyna definicja testow w repo: wola ja hook pre-commit i CI, zeby nie mogly
# sie rozejsc z tym, co odpalasz recznie.
#
# -B nie zapisuje bajtkodu. Python uznaje .pyc za swiezy po parze (mtime,
# dlugosc) zrodla, wiec cofniecie zmiany w tej samej sekundzie na tekst tej
# samej dlugosci potrafi przemycic stary kod do testow. Zdarzylo sie raz.
#
# Glob zamiast jawnej sciezki, bo `node --test` sam szuka plikow po wzorcu
# `*.test.js` i nie znalazlby nazw w konwencji tego repo — a tak nowy plik
# testow wchodzi do zestawu bez dopisywania czegokolwiek.
test:  ## odpal wszystkie testy (to samo robi hook pre-commit)
	python3 -B -m unittest discover -s tools
	node --test tools/test_*.mjs

# Hooki nie wlaczaja sie same po sklonowaniu repo — to jedno polecenie na maszyne.
hooks:  ## wlacz hook pre-commit w tym klonie
	git config core.hooksPath tools/githooks
	@echo "hook pre-commit wlaczony"

# Podglad lokalny. Strona jest statyczna, wiec wystarczy zwykly serwer plikow —
# ale z pliku (file://) nie zadzialalby modul spotkania.js ani sciezki absolutne.
# Terminy z Kalendarza Google wczytuja sie tu tak samo jak na produkcji.
serwuj:  ## podglad na http://127.0.0.1:8000/
	@echo "Podglad: http://127.0.0.1:8000/   (Ctrl+C konczy)"
	@python3 -m http.server 8000 --bind 127.0.0.1 --directory .

.PHONY: all help test hooks serwuj
