# Regeneracja kart gracza. `make` odswieza wszystko po zmianach w tools/.
# Wymaga: python3 + reportlab, pdftocairo (poppler-utils), fonty DejaVu.

all: karta.pdf karta-wycinek-czarek.svg

karta.pdf: tools/karta_pdf.py tools/fonts/Caveat-Bold.ttf
	python3 tools/karta_pdf.py

# jeden przebieg tworzy tez: karta-przyklad.pdf, karta-wycinek.pdf,
# karta-wycinek-bianka.svg
karta-wycinek-czarek.svg: tools/karta_przyklad.py tools/karta_pdf.py tools/fonts/Caveat-Bold.ttf
	python3 tools/karta_przyklad.py

.PHONY: all
