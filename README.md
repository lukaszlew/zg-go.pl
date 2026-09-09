# zg-go.pl

Strona klubu Go **Semedori** w Zielonej Górze → <https://zg-go.pl/>

Czysty HTML i CSS plus jeden moduł JS. Bez frameworka i bez build-stepu; `git push`
publikuje na GitHub Pages. `make help` wypisuje wszystkie polecenia.

Poniżej tylko to, czego nie widać z samego kodu.

## Zasady rankingu mają jedno źródło prawdy

**`tablica/zasady_tablicy.py`**. Te same zdania, co do słowa, stoją w dwóch miejscach:
jako pogrubione nagłówki w rozdziałach Gra i wyrównanie / Magnes / Nowy gracz na
`ranking.html` oraz w pasie zasad na dole wydruku tablicy siły. Ten sam plik nazywa
paski pola (WYGRANA, SERIA, PRZEGRANA), więc tablica nie pokazuje niczego, czego
zasady nie tłumaczą.

Zasady mówią wyłącznie o tym, co widać przy tablicy. Co jest za drobne na zasadę, idzie
do szczegółów pod nią na stronie i na tablicę nie trafia.

Kolejność przy zmianie zasady: `tablica/zasady_tablicy.py` → `ranking.html` →
`make tablica-pdf`. `tablica/tablica.lock` trzyma odcisk zasad i układu tablicy, a `make`
odmówi jego zapisu, gdy treść się zmieniła, a `WERSJA` w `tablica/tablica_kyu_pdf.py`
została ta sama — dwa pokolenia wydruków muszą dać się odróżnić.

Archiwalny ranking na kartach gracza (`ranking-karta.html`, `karta.pdf`) ma własne
źródło: `tools/zasady.py`, pilnowane tak samo przez `karta.lock`.

## Terminy spotkań idą z Kalendarza Google

`spotkania.js` czyta publiczny kalendarz, więc osoba prowadząca ogłoszenia nie dotyka
HTML-a ani gita.

Klucz API stoi jawnie w źródle i to jest w porządku: dane są publiczne i tylko do
odczytu, a klucz jest ograniczony do samego Calendar API. Ograniczenia po adresie
strony **celowo nie ma** — odcinało odwiedzających, których przeglądarka nie wysyła
nagłówka `Referer`.

Awaria jest cicha dla odwiedzającego: zamiast listy pojawia się prośba o zgłoszenie na
Discordzie. Nikt inny nam o niej nie powie.

INWARIANT: `data-tytul` i `data-miejsce` w `index.html` muszą zgadzać się co do znaku
z tym, co stoi w kalendarzu — po to, żeby powtarzalny tytuł i adres nie zaśmiecały listy.

## Czego pilnują testy

`make test`, to samo robi hook pre-commit. Hook trzeba raz włączyć w każdym klonie:
`make hooks`.

Poza zasadami i logiką kalendarza testy pilnują samych stron: czy każdy lokalny plik
istnieje, czy każda kotwica ma cel, czy stopka, analityka, fonty i menu są wszędzie
takie same i czy zaproszenie na Discorda stoi dokładnie w jednym miejscu.

## Rzeczy, które zaskakują

- **`alphago.html` to szkic.** Nie linkuje go nic, ma `noindex` i własną, czwartą
  pozycję w menu — dlatego jest wyłączony z testu nawigacji. Wyłączenie znika razem
  z dokończeniem artykułu.
- **Zaproszenie na Discorda jest w jednym miejscu**, w sekcji „Między spotkaniami" na
  `index.html`. Reszta strony linkuje do tej sekcji, bo zaproszenia wygasają.
- **Zdjęcia są w WebP**, bez zapasowego `<picture>`.
- **Adresy podstron są bez `.html`** (`zg-go.pl/ranking`) — tak je rozwiązuje GitHub
  Pages i tak samo robi lokalny podgląd (`tools/podglad.py`). Stare adresy z `.html`
  dalej działają, ale linkujemy i kanonizujemy formę bez rozszerzenia.
- **Baner strony głównej sam zmienia się na Bachusa** w sezonie Winobrania.
- **`img/hikaru/` i `img/alphago/` to cudze materiały** — źródła podane w stopkach tych
  stron. Nie są nasze do rozdawania.
