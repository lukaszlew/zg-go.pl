# zg-go.pl

Strona klubu Go **Semedori** w Zielonej Górze → <https://zg-go.pl/>

Czysty HTML i CSS plus jeden moduł JS. Bez frameworka i bez build-stepu; `git push`
publikuje na GitHub Pages. `make help` wypisuje wszystkie polecenia.

Poniżej tylko to, czego nie widać z samego kodu.

## Zasady gry mają jedno źródło prawdy

**`tools/zasady.py`**. Te same zdania, co do słowa, stoją w trzech miejscach: w bloku
„Zasady" na `ranking.html`, jako pogrubione nagłówki w rozdziałach Wyrównanie / Wynik /
Zmiana PS, oraz na ściądze na dole karty gracza.

Ściąga to dokładnie zasady — nic więcej i nic mniej. Co jest za drobne na zasadę, idzie
do szczegółów pod nią na stronie i na kartę nie trafia.

Kolejność przy zmianie zasady: `tools/zasady.py` → `ranking.html` → `make`.
`karta.lock` trzyma odcisk zasad i układu karty, a `make` odmówi jego zapisu, gdy treść
się zmieniła, a `WERSJA` w `tools/karta_pdf.py` została ta sama — dwa pokolenia
wydrukowanych kart muszą dać się odróżnić.

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
- **Baner strony głównej sam zmienia się na Bachusa** w sezonie Winobrania.
- **`img/hikaru/` i `img/alphago/` to cudze materiały** — źródła podane w stopkach tych
  stron. Nie są nasze do rozdawania.
