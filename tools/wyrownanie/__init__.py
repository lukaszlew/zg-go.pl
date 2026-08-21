"""Tabele wyrownania na male plansze — piec zrodel, jeden format.

Cztery zrodla to osobne moduly z samymi przepisanymi liczbami: bga, lsg,
ishikura, hunt. Piate, zg, jest policzone z jednej zasady i obejmuje tez 19x19 —
i to ono jest tabela klubu, a tamte stoja obok jako punkt odniesienia.
Wspolny uklad pliku i asserty siedza w tabela.py, uklad zestawienia w
zestawienie.py, a generuj.py sklada z tego dwa rodzaje plikow:
- wyrownanie-*.json — dla kodu, kazde zrodlo osobno, liczby
  dokladnie takie, jak stoja w oryginale;
- zestawienie-*.txt — dla czlowieka, zrodla obok siebie, sprowadzone do jednej
  miary ("ruchy"), po jednym wierszu na roznice sil i po jednym pliku na plansze;
- tabela-zg.html — zwiezla tabela klubowa na trzy plansze, gotowa do wydruku
  albo do wyciecia samego <table> i wklejenia na strone.

Katalog jest pakietem nie dla samego porzadku: `python3 -m unittest discover -s
tools` wchodzi do podkatalogu tylko wtedy, gdy stoi w nim __init__.py. Bez tego
pliku test_wyrownanie.py nie odpalilby sie ani z `make test`, ani z hooka
pre-commit — i nikt by tego nie zauwazyl.

Regeneracja plikow (albo `make wyrownanie`):
    PYTHONPATH=tools python3 -m wyrownanie.generuj
"""
