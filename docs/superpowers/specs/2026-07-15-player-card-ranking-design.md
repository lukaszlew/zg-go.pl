# Karta gracza + ranking na żywo — projekt

Data: 2026-07-15. Status: do akceptacji.

## Cel

Śledzenie gier i punktów siły graczy klubu Semedori (trzy niezależne
rankingi: 9×9, 13×13, 19×19), z historią umożliwiającą później wykresy,
oraz prezentacja aktualnego rankingu na zg-go.pl.

## Architektura

- **Papierowa karta gracza** (`karta.html`, druk) — dziennik przy stole
  i pomoc rachunkowa; kopia zapasowa danych (zdjęcie / OCR później).
- **Arkusz Google** — backend. Źródłem prawdy jest **log gier**
  (1 wiersz = 1 gra); bieżący ranking i historia są pochodną logu.
- **zg-go.pl** — widok: sekcja "Aktualny ranking" na górze
  `ranking.html` czyta opublikowany CSV arkusza (vanilla JS).
- **Wpis gry** — formularz WWW na zg-go.pl POST-ujący do Apps Script
  Web App (wariant "B2"), który dopisuje wiersz do logu. Kod skryptu
  zarządzany claspem z tego repo (bez przeklejania do edytora Google).

## Arkusz: zakładki i kolumny

1. **Gracze** — `nick | start 9×9 | start 13×13 | start 19×19`
   (wypełnia nauczyciel przy dołączeniu gracza; puste = brak rankingu
   na danej planszy).
2. **Gry** — `timestamp | plansza | zwycięzca | przegrany |
   cały ruch lub poddanie? (tak/nie) | mnożnik (1/2/3) | delta`
   (delta = formuła: `(cały ruch? 2 : 1) × mnożnik`).
3. **Ranking** — wyliczana formułami (bez Apps Script):
   `punkty = start + SUMIFS(delta; zwycięzca=nick; plansza=b)
   − SUMIFS(delta; przegrany=nick; plansza=b)`.
   Lista nicków przez `UNIQUE`/`FILTER` z zakładki Gracze.

Zasada podziału: **ranking liczą formuły** (jawne, bez triggerów,
odporne na ciche awarie), **Apps Script służy wyłącznie jako endpoint
wpisu** (`doPost` dopisujący wiersz). Zmiany punktów w regułach klubu
nie zależą od bieżących punktów (±1/±2 × mnożnik), więc suma warunkowa
wystarcza — replay w skrypcie byłby potrzebny dopiero przy regułach
typu Elo.

## Strona: ranking.html

- Nowa sekcja na samej górze (nad zasadami): przełącznik plansz
  `9×9 | 13×13 | 19×19` (domyślnie 9×9) + tabela `miejsce | nick |
  punkty siły`, sortowanie malejąco, styl `table.sila`.
- Dane: fetch opublikowanego CSV zakładki Ranking (~30–40 linii
  vanilla JS). `<noscript>` i błąd pobierania → link do arkusza.
- Link do `karta.html` i do formularza wpisu gry.

## Strona: karta.html (druk)

- Uniwersalna pusta karta A4 pion, `@media print` chowa
  banner/menu/stopkę.
- Nagłówek do ręcznego wypełnienia: nick, plansza (zakreśl
  9×9 / 13×13 / 19×19), punkty startowe (przepisane z rankingu na
  stronie), data.
- ~20 pustych wierszy: `data | przeciwnik | jego pkt | moje pkt |
  różnica | dodatkowe ruchy | jeńcy | wynik | zmiana | nowe pkt`.
- Stopka drobnym drukiem: skrót zasad (cały ruch 13 pkt, komi 6,
  ±1/±2, remis dla Białego).

## Formularz wpisu gry (B2)

- Strona na zg-go.pl: wybór planszy, zwycięzcy i przegranego z żywej
  listy graczy (z CSV zakładki Gracze/Ranking), przełącznik "wygrana o
  cały ruch / poddanie", mnożnik; **podgląd wyliczonego handicapu
  i komi przed grą** (zastępuje rachunki z karty).
- POST → Apps Script Web App `doPost` → wiersz w zakładce Gry.
  Odpowiedź JSON = potwierdzenie zapisu (brak cichej utraty danych,
  w przeciwieństwie do POST-a na nieoficjalny endpoint Google Forms).
- Kod w repo (np. `apps-script/`), zarządzany claspem:
  `clasp push` + `clasp deploy`. Pułapka do pamiętania: web app działa
  w wersji z ostatniego deployu, nie z ostatniego pusha.

## Jednorazowe czynności użytkownika (interaktywne logowania)

1. Utworzenie arkusza + publikacja CSV (File → Share → Publish to web).
2. Włączenie Apps Script API (script.google.com/home/usersettings).
3. `clasp login` (OAuth w przeglądarce).
4. Zgody OAuth przy pierwszym deployu web appa.

## Etapy wdrożenia

1. **Arkusz** — utworzenie zakładek, formuły Rankingu, publikacja CSV.
2. **ranking.html** — sekcja "Aktualny ranking" + JS czytający CSV.
3. **karta.html** — karta do druku, link z ranking.html.
4. **Endpoint + formularz wpisu** — clasp, `doPost`, strona wpisu gry.

Etapy 2–3 zależą tylko od URL-a CSV; etap 4 jest niezależnie
dokładalny (droga wpisu jest wymienna — w razie potrzeby tymczasowo
zwykły Google Form piszący do tej samej zakładki Gry).

## Poza zakresem (YAGNI)

- OCR kart (projekt logu umożliwia późniejsze hurtowe uzupełnienie).
- Wykresy historii (dane będą w logu; osobny etap kiedyś).
- Konta, logowanie, ochrona endpointu przed spamem.
- Automatyczne liczenie wyniku gry — liczy człowiek przy planszy.

## Kwestie otwarte

1. Czy mnożnik nauczyciela jest polem formularza wpisu, czy poprawką
   nauczyciela bezpośrednio w arkuszu?
2. Ostateczna lista kolumn karty (czy ciąć "różnicę"?).
3. Nazwa i umiejscowienie strony wpisu gry (osobna podstrona vs sekcja
   na ranking.html).
