# Terminy i ogłoszenia spotkań z kalendarza Google

Data: 2026-07-29. Stan: **zaprojektowane, nie zaimplementowane** — nic z tego nie
jest jeszcze w repo.

## Problem

Terminy spotkań klubu są zapisane na sztywno w `index.html`. Chcemy, żeby mogła
je zmieniać osoba, która **nie edytuje HTML-a i nie używa gita**, a do tego mogła
dopisywać kilkuzdaniowe ogłoszenia do konkretnych spotkań („zaczynamy godzinę
później", „turniej błyskawiczny", „w tym tygodniu nie gramy").

Osoba umie obsłużyć Kalendarz Google — i to jest jedyne narzędzie, jakiego ma
potrzebować.

## Decyzja

**Publiczny kalendarz Google jako źródło + Calendar API v3 + `fetch` w
przeglądarce.** Bez build-stepu, bez GitHub Action, bez serwera.

### Dlaczego nie inaczej

Warianty rozważone i odrzucone — nie wracać do nich bez nowego argumentu:

- **Arkusz Google + `fetch`** — arkusz jest gorszym edytorem terminów niż
  kalendarz i nie wyraża wyjątków (odwołany tydzień, inna godzina raz).
- **GitHub Action przepisująca HTML** — poprawniejsza technicznie (metadane
  zostają prawdziwe), ale osoba pisząca ogłoszenie czeka do kilkunastu minut na
  efekt i nie wie, czy dobrze zapisała. Dla nietechnicznego edytora to różnica
  między „działa" a „chyba działa". Odrzucone **dlatego, że ogłoszenia i tak nie
  idą do metadanych** — patrz niżej — więc główny argument za Action upada.
- **Prywatny kalendarz + prywatny adres iCal** — kusi brakiem Google Cloud, ale
  ICS (publiczny i prywatny) nie wysyła nagłówków CORS, więc przeglądarka go nie
  pobierze. Działałoby tylko przez Action, czyli z opóźnieniem. Do tego prywatny
  adres iCal jest de facto hasłem i nie może trafić do kodu strony.
- **Własne proxy na Cloudflare Workers** — rozwiązuje CORS bez Google Cloud, ale
  zamienia jedną platformę na drugą.
- **CMS na gicie (Pages CMS, Decap)** — najlepszy interfejs edycji, ale wymaga
  konta GitHub i zwykle generatora stron statycznych; strona jest pisana ręcznie.

Publiczny kalendarz ma przy tym samoistną zaletę: ludzie mogą go sobie
zasubskrybować i mieć środy w swoim telefonie.

## Jak pracuje osoba edytująca

Spotkanie jest w kalendarzu **wydarzeniem cyklicznym**. Przy zapisie Google pyta
„to wydarzenie" czy „wszystkie" — wybranie **„to wydarzenie"** tworzy wyjątek w
serii i o to chodzi: zmiana przykleja się do jednej środy i sama znika, gdy ta
środa minie.

| pole wydarzenia | co daje na stronie |
|---|---|
| opis | treść ogłoszenia, kilka zdań |
| tytuł | krótki wyróżnik na jedno spotkanie, np. „Turniej błyskawiczny" |
| godzina | inna pora na jeden tydzień — dopisek generuje się sam |
| data | przeniesienie na inny dzień — dopisek generuje się sam |
| lokalizacja | jednorazowa zmiana miejsca |

Zmiana stałego rytmu (np. środy → czwartki na stałe) to edycja „wszystkich
wydarzeń" **plus** ręczna poprawka w `index.html`, bo rytm jest tam wpisany na
sztywno. To jest rzadkie i świadomie zostawione ludziom.

## Co widać na stronie

Wersja **B** — lista najbliższych spotkań pod stałym rytmem, w sekcji
`#gdzie-kiedy` na `index.html`, między linią z godzinami a linkiem do Discorda:

```
Zielona Góra, Mediateka Góra Mediów („Norwid"), piętro 1, mapa
Środy 17:00–19:00

środa 5 sierpnia, 18:00 — zaczynamy godzinę później, sala jest zajęta wcześniej.
środa 12 sierpnia — turniej błyskawiczny, zapisy na Discordzie.
wtorek 19 sierpnia — wyjątkowo we wtorek. Reszta opisu z kalendarza.

Klubowy Discord
```

### Zasady renderowania

1. **Linijka pojawia się tylko wtedy, gdy jest co powiedzieć.** Zwykła środa bez
   opisu nie dostaje wiersza — mówi o niej rytm wyżej. Wiersz dostają instancje z
   opisem, ze zmienionym tytułem, z inną godziną albo w innym dniu tygodnia. Bez
   tej zasady lista rosłaby w nieskończoność, bo cykl jest nieskończony.
2. **Bez ograniczenia w przyszłość.** Ogłoszenie o spotkaniu za dwa miesiące
   pokazuje się od razu.
3. **Dzień tygodnia zawsze**, właśnie dlatego, że bywa inny.
4. **Godzina tylko wtedy, gdy różni się od standardowej.** Powtarzanie
   „17:00–19:00" pod napisem „Środy 17:00–19:00" byłoby szumem, a brak godziny
   przy zmienionej porze byłby pułapką.
5. **Dopiski o innym dniu i innej godzinie generuje kod**, bo da się to wykryć
   (instancja kontra reguła cykliczna). Osoba nie musi o tym pamiętać.
6. **Bez limitu długości ogłoszeń** — ufamy, że nikt nie wklei trzech akapitów.

### Iteracja po tygodniach, nie po datach

Wykrywanie „spotkania nie ma" i „przeniesione na inny dzień" wymaga liczenia
**per tygodnia**, nie per daty. Dla każdego tygodnia od bieżącego do ostatniego
objętego danymi: jest instancja → wiersz (jeśli ma co powiedzieć); nie ma
instancji → tydzień bez spotkania. Inaczej przeniesienie środy na wtorek
wyglądałoby jednocześnie jako odwołana środa i dodatkowy wtorek.

Tygodnie, których spotkanie już minęło, pomijamy. `timeMin` = początek dziś, żeby
spotkanie dzisiejsze jeszcze się liczyło.

## Metadane zostają nietknięte

Godzina spotkań stoi w `index.html` w **czterech** miejscach:

| gdzie | po co |
|---|---|
| `<meta name="description">` | wynik w Google |
| `<meta property="og:description">` | podgląd linku na Facebooku i Discordzie |
| JSON-LD `schema.org` | wizytówka Google, mapy |
| `<p><strong>Środy 17:00–19:00</strong></p>` | to, co widać |

JavaScript podmienia tylko czwarte — trzy pierwsze czyta robot, który JS-u nie
uruchamia. Dlatego **ogłoszenia nie trafiają do metadanych nigdy**: te niosą
stały rytm i zmieniają się tylko wtedy, gdy zmieni się sama reguła cykliczna.
Gdyby ogłoszenia lądowały w `og:description`, przepisywalibyśmy je co tydzień,
mieląc historię repo i mieszając robotom.

## Łagodna awaria

**Stały rytm zostaje w HTML-u na sztywno.** JS dokłada wyłącznie ogłoszenia, do
kontenera, który startuje ukryty i odkrywa się dopiero po udanym pobraniu.

Skutki: brak internetu, padnięte API, wygasły klucz albo wyłączony JavaScript
oznaczają, że strona nadal mówi gdzie, kiedy i o której — brakuje tylko dodatków.
Nigdy nie pokazujemy pustego nagłówka „Ogłoszenia" ani komunikatu o błędzie.

Cena tego wariantu, świadoma: **awaria jest cicha**. Jeśli klucz przestanie
działać, sekcja po prostu zniknie i nikt się nie dowie. Warto o tym pamiętać przy
odnawianiu czegokolwiek w Google Cloud.

## Higiena techniczna

- **Sanityzacja opisu.** Kalendarz ma formatowanie tekstu i zwraca `description`
  jako HTML. Przepuścić przez białą listę znaczników (`b`, `strong`, `i`, `em`,
  `a`, `br`, `p`, `ul`, `ol`, `li`), skasować wszystkie atrybuty poza `href` na
  `<a>`, wymusić `rel="noopener"`, dopuścić tylko schematy `http`, `https`,
  `mailto`. Wklejenie z Worda przynosi pół arkusza stylów, a wstrzykiwanie
  cudzego HTML-u bez filtra to zły nawyk niezależnie od tego, komu ufamy.
- **Strefa czasowa** `Europe/Warsaw` przy formatowaniu, niezależnie od strefy
  odwiedzającego — godzina spotkania jest lokalna dla klubu.
- **Wydarzenia całodniowe** przychodzą jako `start.date` zamiast
  `start.dateTime`; obsłużyć bez pokazywania godziny.
- **Klucz API** jest widoczny w źródle strony i to jest normalne dla publicznych
  danych tylko do czytania. Ograniczyć go w konsoli Google do domeny `zg-go.pl`.
- **Stały rytm dla porównań** (dzień tygodnia, godziny) podać w `data-`
  atrybutach kontenera w `index.html`, żeby stał obok widocznego napisu, a nie w
  drugim pliku.
- **Zapytanie**: `events.list` z `singleEvents=true`, `orderBy=startTime`,
  `timeMin=` początek dziś, `maxResults` na tyle, żeby objąć kilka miesięcy.
- Kod w osobnym pliku (np. `spotkania.js`), nie w `index.html` — w `index.html`
  jest już inline'owy skrypt na baner Winobrania i nie ma go po co rozdymać.

## Jednorazowe czynności użytkownika (interaktywne, do wyklikania)

1. Utworzyć **nowy** kalendarz, np. „Semedori — spotkania". Nie używać
   prywatnego kalendarza osobistego.
2. Ustawienia kalendarza → udostępnić publicznie („Udostępnij wszystkim,
   zobacz wszystkie szczegóły wydarzenia").
3. Skopiować **identyfikator kalendarza** z ustawień.
4. Dodać wydarzenie cykliczne: środy 17:00–19:00, Mediateka.
5. Nadać osobie prowadzącej ogłoszenia prawo **wprowadzania zmian**.
6. Konsola Google Cloud: nowy projekt → włączyć Google Calendar API → utworzyć
   klucz API → ograniczyć go do witryny `zg-go.pl`. Bez karty płatniczej, Calendar
   API jest w tych ilościach darmowe.
7. Przekazać identyfikator kalendarza i klucz do wpisania w `spotkania.js`.

## Do rozstrzygnięcia przy implementacji

1. **Jak odwołuje się spotkanie.** Osoba prawdopodobnie **skasuje** wydarzenie, a
   wtedy API go nie zwróci i strona nic nie napisze — ktoś przyjdzie pod
   zamknięte drzwi. Dwa wyjścia: (A) instrukcja „nie kasuj, napisz w opisie, że
   spotkania nie ma", (B) kod liczy, które środy powinny być, i brakującą
   renderuje jako „środa 19 sierpnia — spotkania nie ma". **Rekomendacja: B** —
   kasowanie jest odruchem, którego nie da się oduczyć, a cisza na stronie
   kosztuje kogoś wieczór. Nierozstrzygnięte.
2. Dokładne brzmienie dopisków generowanych automatycznie („wyjątkowo we
   wtorek", forma godziny).
3. Co zrobić z polem lokalizacji, gdy różni się od stałego miejsca — dopisek czy
   pominięcie.

## Poza zakresem

- Ogłoszenia na innych podstronach niż `index.html`.
- Archiwum minionych ogłoszeń.
- Formularz zapisów na turnieje.
- Jakakolwiek edycja treści strony innej niż terminy i ogłoszenia.

## Testowanie

W środowisku jest `node` v20, więc logikę (iteracja po tygodniach, wykrywanie
wyjątków, sanityzacja, formatowanie po polsku) da się przetestować na atrapie
odpowiedzi `events.list` bez prawdziwego kalendarza i bez klucza. Warto to
zrobić — repo ma już testy w `tools/` (stdlibowy `unittest`) odpalane przez
pre-commit hook z `tools/githooks`, patrz `README.md`.

Uwaga: testy JS wymagałyby drugiego runnera obok pythonowego. Do rozważenia, czy
warto — alternatywą jest wydzielenie czystych funkcji i przetestowanie ich
jednorazowo ręcznie przez `node`.
