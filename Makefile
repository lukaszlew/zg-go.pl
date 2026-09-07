# Regeneracja kart gracza i zadania pomocnicze. `make` odswieza wszystko po
# zmianach w tools/. `make help` wypisuje cele.
# Wymaga: python3 + reportlab i Pillow, pdftocairo (poppler-utils), fonty DejaVu.

all: karta.pdf karta-klub-przyklad.pdf karta-wycinek-czarek.svg wyrownanie wersje  ## przegeneruj karty, karty przykladowe i tabele wyrownania

# linki do zasobow dostaja ?v=<odcisk pliku> — swiezy deploy nie sklada sie
# w przegladarce ze stara kopia stylu ani skryptu z cache
wersje:  ## odswiez ?v= przy zasobach w HTML
	python3 tools/wersjonuj.py

help:  ## wypisz dostepne cele
	@awk -F':.*##' '/^[a-z-]+:.*##/ { printf "  make %-11s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# sciaga na karcie idzie z zasady.py, wiec zmiana zasad tez odswieza karte.
# Jeden przebieg pisze obie wersje: karta.pdf (kolor) i karta-cb.pdf (czarno-biala,
# na ksero i drukarke laserowa).
karta.pdf: tools/karta_pdf.py tools/zasady.py tools/fonts/Caveat-Bold.ttf img/logo.svg
	python3 tools/karta_pdf.py

# przyklad karty obcego klubu: inna nazwa w naglowku, bez logo
karta-klub-przyklad.pdf: tools/karta_klub.py tools/karta_pdf.py tools/zasady.py tools/fonts/Caveat-Bold.ttf
	python3 tools/karta_klub.py

WYCINKI = tablica/wycinek-zasady.svg tablica/wycinek-tabele.svg tablica/wycinek-tablica.svg

tablica-pdf: tablica/ranking_table-660x950mm.pdf tablica/tablica.svg $(WYCINKI) wersje  ## przegeneruj tablice siły

# podglad tablicy na stronie ranking: ten sam wydruk jako SVG (glify ida w sciezki)
tablica/tablica.svg: tablica/ranking_table-660x950mm.pdf
	pdftocairo -svg $< $@

# trzy wycinki dla strony ranking: pelny SVG z kadrem liczonym z geometrii generatora
$(WYCINKI) &: tablica/tablica.svg tablica/wycinki_svg.py tablica/tablica_kyu_pdf.py tablica/zasady_tablicy.py
	python3 tablica/wycinki_svg.py

# tablica siły (slupki progresji sily z cwiartkami), wydruk 660 x 950 mm na mala
# tablice magnetyczna; generator importuje draw_siatka z karta_pdf, wiec zmiana karty
# odswieza tez tablice
tablica/ranking_table-660x950mm.pdf: tablica/tablica_kyu_pdf.py tablica/zasady_tablicy.py tools/karta_pdf.py img/logo.svg
	python3 tablica/tablica_kyu_pdf.py

# jeden przebieg tworzy tez: karta-przyklad.pdf, karta-wycinek.pdf,
# karta-wycinek-bianka.svg
karta-wycinek-czarek.svg: tools/karta_przyklad.py tools/karta_pdf.py tools/zasady.py tools/fonts/Caveat-Bold.ttf
	python3 tools/karta_przyklad.py

# Tabele wyrownania na male plansze. Jeden przebieg pisze caly zestaw, wiec
# odpowiada za niego jeden cel. Wszystko w tools/wyrownanie/: wyrownanie-*.json
# (dla kodu, kazde zrodlo osobno) i zestawienie-*.txt (dla czlowieka, zrodla
# obok siebie, po jednym pliku na plansze). Swiezosci pilnuje test_wyrownanie.py
# — plik rozjechany z tabela nie przejdzie przez testy ani przez hook.
TABELE_WYROWNANIA = $(wildcard tools/wyrownanie/*.py)

wyrownanie: tools/wyrownanie/wyrownanie-bga.json  ## przegeneruj tabele wyrownania na 9x9 i 13x13

tools/wyrownanie/wyrownanie-bga.json: $(TABELE_WYROWNANIA)
# -B tak samo jak w `make test`: generator nie ma prawa zostawic po sobie .pyc,
# bo cofnieta zmiana tej samej dlugosci w tej samej sekundzie przemycilaby
# stary kod do testow. Zdarzylo sie i tutaj.
	PYTHONPATH=tools python3 -B -m wyrownanie.generuj

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

# Podglad lokalny. Terminy z Kalendarza Google wczytuja sie tu tak samo jak na
# produkcji. Port szuka sie sam, bo zajeta osemka to nie blad — patrz tools/podglad.py.
serve:  ## podglad na pierwszym wolnym porcie od 8000
	@python3 -B tools/podglad.py

.PHONY: all help test hooks serve wyrownanie
