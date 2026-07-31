# TODO

## Treść

- [ ] **Social proof** w sekcji „Dla kogo": od kiedy klub działa, jaka jest frekwencja
- [ ] **AlphaGo** — dokończyć artykuł, zdjąć `noindex` i wpuścić do menu na wszystkich
      stronach; wtedy znika też jego wyjątek w teście nawigacji
- [ ] **Hikaru** — dopisać, gdzie obejrzeć anime
- [ ] **Gdzie się uczyć** — rozszerzyć listę: Go Magic, playgo.to/iwtg, Sensei's Library,
      AI Sensei
- [ ] **Zasady Go w 15 minut** — osobna strona. Obiecujemy to w „Dla kogo", a w całym
      serwisie nie ma zasad samej gry; do tego to najczęstsze pytanie w wyszukiwarce

## Zdjęcia

- [ ] Gracze z Zielonej Góry przy planszy — do sekcji „Dla kogo"
- [ ] Zaproszenie na koniec strony
- [ ] Galeria ze spotkań, gdy będą zdjęcia (siatka była kiedyś zaimplementowana,
      do odgrzebania z gita)

## Kod

- [ ] **Kalkulator wyrównania** na `ranking.html`: dwa pola PS → kolory, pierwsze ruchy
      i dodatkowi jeńcy; drugi kalkulator na zmianę PS
- [ ] **Tłumaczenia** — angielski i ukraiński; prawdopodobnie razem z generatorem stron,
      bo cztery pliki HTML już teraz mają przepisane te same bloki
- [ ] **Karta dla obcego klubu** — zrobić, gdy zgłosi się pierwszy; co jest w karcie
      lokalne, opisuje komentarz w `tools/karta_pdf.py`
- [ ] Trzy słabości układu: próg `820px` wpisany w dwóch miejscach, `.przyklad`
      wychodzący poza kolumnę przez `transform`, justowanie akapitów na wąskim telefonie
- [ ] Self-host fontów — nie dla szybkości (CSS fontów waży 0,7 kB), tylko żeby nie
      zależeć od Google i nie wysyłać tam odwiedzających

## Poza repo

- [ ] **Bus factor** — drugi administrator na OVH, GitHubie, Google Cloud, kalendarzu
      i Discordzie. Dziś klub traci stronę razem z jedną osobą
- [ ] Cloudflare przed GitHub Pages, gdyby kiedyś były potrzebne nagłówki bezpieczeństwa
