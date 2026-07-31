# Regeneracja kart gracza. `make` odswieza wszystko po zmianach w tools/.
# Wymaga: python3 + reportlab, pdftocairo (poppler-utils), fonty DejaVu.

all: karta.pdf karta-wycinek-czarek.svg

# sciaga na karcie idzie z zasady.py, wiec zmiana zasad tez odswieza karte
karta.pdf: tools/karta_pdf.py tools/zasady.py tools/fonts/Caveat-Bold.ttf
	python3 tools/karta_pdf.py

# jeden przebieg tworzy tez: karta-przyklad.pdf, karta-wycinek.pdf,
# karta-wycinek-bianka.svg
karta-wycinek-czarek.svg: tools/karta_przyklad.py tools/karta_pdf.py tools/zasady.py tools/fonts/Caveat-Bold.ttf
	python3 tools/karta_przyklad.py

# Podglad lokalny. Strona jest statyczna, wiec wystarczy zwykly serwer plikow —
# ale z pliku (file://) nie zadzialalby modul spotkania.js ani sciezki absolutne.
# Terminy z Kalendarza Google wczytuja sie tu tak samo jak na produkcji.
serwuj:
	@echo "Podglad: http://127.0.0.1:8000/   (Ctrl+C konczy)"
	@python3 -m http.server 8000 --bind 127.0.0.1 --directory .

.PHONY: all serwuj
