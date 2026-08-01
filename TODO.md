# TODO

## Treść

- [ ] **Social proof** w sekcji „Dla kogo": od kiedy klub działa, jaka jest frekwencja.
      Do tego kto klub prowadzi — imię, twarz, kontakt bezpośredni. Dziś strona nie ma
      po drugiej stronie żadnego człowieka, a rodzic decydujący o dziecku i ktoś, kto
      ma przyjść sam do obcego budynku, potrzebują dokładnie tego
- [ ] **AlphaGo** — artykuł wygląda na skończony; blokuje go to, że nic go nie linkuje.
      Zdjąć `noindex`, wpuścić do menu na wszystkich stronach (znika wtedy jego wyjątek
      w teście nawigacji) i przekierować „Czemu Go" na własny tekst — dziś ta sekcja
      wysyła czytelnika prosto na YouTube, mijając nasz artykuł. Dorobić `og:image`
- [ ] **Hikaru** — dopisać, gdzie obejrzeć anime. Przy okazji dwie rzeczy: strona czyta
      się jak cudza recenzja (bo nią jest — sekcje „Animacja", „Muzyka", „Werdykt" to
      język recenzenta anime), więc dodać zdanie własne: kto u nas zaczął od tej serii.
      I zakończyć zaproszeniem na spotkanie, tak jak kończy się AlphaGo — dziś ostatnim
      akapitem jest przypis o prawach autorskich
- [ ] **Gdzie się uczyć** — rozszerzyć listę: Go Magic, playgo.to/iwtg, Sensei's Library,
      AI Sensei
- [ ] **Zasady Go w 15 minut** — osobna strona. Obiecujemy to w „Dla kogo", a w całym
      serwisie nie ma zasad samej gry; do tego to najczęstsze pytanie w wyszukiwarce
- [ ] **Ranking na eksport.** To najbardziej oryginalna rzecz na tej stronie i najgorzej
      wyeksponowana: 15 tysięcy znaków po polsku, bez streszczenia. Trzy rzeczy —
      TL;DR na górze (pięć zdań: co to jest, czemu działa, karta do druku), wersja
      angielska (idzie razem z „Tłumaczeniami" w sekcji Kod) i wpis na Sensei's Library,
      bo tylko tą drogą system trafi poza Polskę. Do tego `<title>` i `description`
      celują dziś we frazę „Ranking Semedori", której nikt nie szuka — szuka się
      „system rankingowy klub go" i „handicap go"

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
- [ ] **Kanały dotarcia.** Wizytówka w Mapach i wpis na liście klubów PSG są, reszta
      nie: Instagram, Facebook, zdjęcia, godziny i telefon na wizytówce, opinie
- [ ] Cloudflare przed GitHub Pages, gdyby kiedyś były potrzebne nagłówki bezpieczeństwa
