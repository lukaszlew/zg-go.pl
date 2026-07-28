# Ranking na żywo — pozostały zakres

> **PORZUCONE 2026-07-27. Nie wdrażamy.**
>
> Powód: papierowe karty działają za dobrze. Prowadzenie własnego dziennika
> gier okazało się częścią przyjemności, a nie niedogodnością do usunięcia —
> gracz widzi na karcie własną historię zamiast liczby w cudzej bazie.
> Karta ma przy tym wbudowany audyt (ta sama gra na dwóch kartach, łańcuch
> `moje PS` → `nowe PS`), więc arkusz nie jest potrzebny nawet jako kontrola.
> Karty zostają w klubie pod opieką opiekuna, więc nie giną między środami.
> Do tego cały argument „samograj" — zero serwera, konta i aplikacji —
> osłabłby, gdyby ranking wymagał wpisywania gier do formularza.
>
> Uzasadnienie w wersji dla czytelnika: `ranking.html`, sekcja
> „Dla innych klubów". Dokument zostaje jako zapis rozważanego wariantu.

Data: 2026-07-15 (zaktualizowany po wdrożeniu karty gracza i przykładu).
Zrobione i poza tym dokumentem: karta gracza PDF (`tools/karta_pdf.py`,
`make`), karty przykładowe i wycinki SVG na ranking.html, zasady PS.

## Cel

Prezentacja aktualnego rankingu (PS per plansza) na zg-go.pl oraz
wpisywanie gier, z historią umożliwiającą później wykresy.

## Architektura

- **Arkusz Google** — backend. Źródłem prawdy jest **log gier**
  (1 wiersz = 1 gra); bieżący ranking i historia są pochodną logu.
- **zg-go.pl** — widok: sekcja "Aktualny ranking" na ranking.html
  czyta opublikowany CSV arkusza (vanilla JS).
- **Wpis gry** — formularz WWW na zg-go.pl POST-ujący do Apps Script
  Web App (`doPost` dopisuje wiersz do logu). Kod skryptu w repo,
  zarządzany claspem (`clasp push` + `clasp deploy`; web app działa
  w wersji z ostatniego deployu, nie pusha).

## Arkusz: zakładki i kolumny

1. **Gracze** — `nick | start 9×9 | start 13×13 | start 19×19`.
2. **Gry** — `timestamp | plansza | zwycięzca | przegrany |
   wygrana o 12+ kamieni lub poddanie? (tak/nie)`.
3. **Ranking** — wyliczana z logu.

Uwaga po zmianie zasad: reguła serii (trzecia wygrana z rzędu na
danej planszy i kolejne podwajają zmianę zwycięzcy) wprowadza
zależność od kolejności gier — zwykłe SUMIFS już nie wystarczą.
Opcje: kolumny pomocnicze per wiersz (bieżąca seria gracza na
planszy, liczona po wierszach wyżej) albo replay logu w Apps Script.
Do rozstrzygnięcia przy wdrożeniu.

## Strona: sekcja "Aktualny ranking"

- Na górze ranking.html (nad przykładem) przełącznik plansz
  `9×9 | 13×13 | 19×19` (domyślnie 9×9) + tabela `miejsce | nick |
  PS` w stylu `table.sila`, sortowanie malejąco.
- Fetch opublikowanego CSV zakładki Ranking (~30–40 linii vanilla
  JS); `<noscript>` i błąd pobierania → link do arkusza.

## Formularz wpisu gry

- Wybór planszy, zwycięzcy i przegranego z żywej listy graczy,
  przełącznik "12+ kamieni / poddanie"; podgląd wyliczonego handi
  i komi przed grą.
- Odpowiedź JSON z web appa potwierdza zapis (bez cichej utraty).

## Jednorazowe czynności użytkownika (interaktywne logowania)

1. Utworzenie arkusza + publikacja CSV (File → Share → Publish to web).
2. Włączenie Apps Script API (script.google.com/home/usersettings).
3. `clasp login` (OAuth w przeglądarce).
4. Zgody OAuth przy pierwszym deployu web appa.

## Etapy

1. **Arkusz** — zakładki, wyliczanie Rankingu, publikacja CSV.
2. **ranking.html** — sekcja "Aktualny ranking" (zależy tylko od
   URL-a CSV).
3. **Endpoint + formularz wpisu** — clasp, `doPost`, strona wpisu;
   droga wpisu wymienna (tymczasowo może być zwykły Google Form
   piszący do zakładki Gry).

## Poza zakresem (YAGNI)

- OCR kart (log umożliwia późniejsze hurtowe uzupełnienie).
- Wykresy historii (dane będą w logu).
- Konta, logowanie, ochrona endpointu przed spamem.

## Kwestie otwarte

1. Streak w arkuszu: formuły per wiersz czy replay w Apps Script?
2. Nazwa i umiejscowienie strony wpisu gry (osobna podstrona vs
   sekcja na ranking.html).
