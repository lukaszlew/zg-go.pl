# Wyrównanie na małe plansze — założenia

Ten plik jest po to, żeby dało się wrócić do tych tabel za rok i wiedzieć, **dlaczego**
wyglądają tak, a nie inaczej. Kod mówi, co się dzieje; tutaj stoi, co było wybierane
świadomie i co ten wybór kosztował.

## Po co to jest

Klub ma własny system wyrównania na 19x19 — stoi na `ranking.html` i liczy go
`wyrownanie.js`. Na 9x9 i 13x13 nie miał żadnego. Te tabele domykają lukę: jedną
zasadą dla wszystkich trzech plansz, a nie trzema osobnymi.

Obok stoją cztery cudze tabele (BGA, LSG, Ishikura, Hunt) przepisane co do liczby.
Nie są konkurencją dla klubowej — są punktem odniesienia i to z nich wyszedł stosunek,
na którym wszystko stoi.

## Zasada

Jeden ruch jest wart **13 punktów** na każdej planszy. Ile wart jest jeden stopień
różnicy sił — zależy od planszy:

| plansza | 19x19 | 13x13 | 9x9 |
|---------|------:|------:|----:|
| punktów na stopień | 13 | 5 | 2 |

Stosunek nie jest zgadnięty. Wychodzi ten sam u każdego, kto liczył: LSG 9x9 i Hunt
9x9 idą po 2, LSG 13x13 i Ishikura 13x13 po 5, a `wyrownanie.js` liczy 19x19 po 13.

Rachunek:

```
punkty = -6 + krok * różnica        (-6, bo gra równa to 6 jeńców dla Białego)
ruchy  = max(1, 1 + punkty // 13)
jeńcy  = punkty - (ruchy - 1) * 13  (zawsze 0..12 — trzynasty punkt kupuje ruch)
```

Kolumna 19x19 odtwarza `wyrownanie.js` co do wiersza. Pilnuje tego test w drugim
języku (`tools/test_kalkulator.mjs`), więc rozjazd zapali się od razu.

## Decyzje, które kosztowały

Każda z nich jest przybita testem — nie po to, żeby nie dało się jej zmienić, tylko
żeby zmiana była świadoma i żeby widać było rachunek.

**Pół stopnia, zaokrąglane ku zeru.** Między stopniami też się gra. Połówka daje pół
punktu na 13x13 i 19x19; obcinamy je ku zeru, więc słabszy nigdy nie traci na
zaokrągleniu. Dla stopni całkowitych obcięcie nie ma czego uciąć, więc pliki JSON i
zestawienia wychodzą identyczne jak bez niego.

**13x13 schodzi z drabinki `0 3 5 8 10`, a nie z samego rachunku.** Bo 5 nie dzieli
13 i końcówki punktów płynęłyby z bloku na blok — raz `1/4/6/9/11`, raz `1/3/6/8/11`.
Tabela nie miałaby powtarzalnego kształtu. Drabinka daje 13 punktów na 2,5 stopnia,
czyli **5,2 punktu na stopień zamiast 5**: przy różnicy 20 stopni to 2 punkty nadwyżki,
przy 39 — sześć, mniej niż pół ruchu.

Sama drabinka też była wybierana. Wszystkie możliwe mają te same przerwy `{2,2,3,3,3}`
(13 nie składa się z piątki kroków inaczej), więc różnią się wyłącznie kolejnością —
jest ich dziesięć. `0 3 5 8 10` wygrywa na trzech osiach naraz: najmniejszy rozrzut
odchyłki od stosunku (0,5), symetria względem 13 (`{13-x}` to ten sam zbiór), i
podwójna trójka — nie do uniknięcia, bo trzy trójki w cyklu piątki muszą gdzieś
sąsiadować — wypada dokładnie na styku ruchów, gdzie wiersz i tak się łamie.

**Drabinka nie sięga gier równych.** Nie umie trafić w −6: z jednego ruchu w dół ląduje
na −8 albo −5. Poniżej pierwszego stopnia 13x13 liczy się więc zwykłym rachunkiem.
Reguła jest dwuczęściowa i musi taka zostać.

**19x19 nie pokazuje wiersza „1 ruch".** Jeden ruch to nie wyrównanie, tylko zwykłe
prawo Czarnego do pierwszego ruchu. Na 19x19 cały ten wiersz mieści się w jednym
stopniu różnicy, więc zamiast rozdawać za niego jeńców klub gra po prostu równo.
**Kosztuje to 7 jeńców przy różnicy 1.** Na 13x13 i 9x9 ten sam wiersz obejmuje kilka
stopni i do 12 jeńców — tam zostaje.

## Tabela

Układ jest ten sam, co tabeli wyrównania na `ranking.html`: **w kratkach stoi różnica
stopni**, a co z niej wynika, czyta się z brzegów. Jedna kratka niesie przez to cały
wiersz tabeli liniowej.

- **Ruchy w wierszach, jeńcy w kolumnach.** Nie odwrotnie: ruchy biegną bez końca i
  tabela musi się na nich urywać, a jeńców jest na każdej planszy skończenie wiele
  (dwóch na 19x19, pięciu na 13x13, trzynastu na 9x9). Liczba wierszy tabeli to
  właśnie tyle, ile różnych końcówek punktowych da się na niej dostać.
- **Ruchy po prawej, jeńcy pod spodem.** Oba brzegi są podpisane w rogach, strzałką
  w swoją stronę: `↓ ruchy`, `← jeńcy`.
- **Każdy róg należy do brzegu, który nazywa, i tylko do niego.** Górny stoi nad
  kolumną ruchów, więc kreska pionowa idzie przez niego aż pod czapkę. Dolny należy
  do wiersza jeńców — gdyby dostał tę samą kreskę, odcięłaby go od jego własnych liczb.
- **Nazwa planszy w pasie nad siatką**, jako plakietka na ciemnym tle — nie na całą
  szerokość kratki, żeby nie dotykała jej boków. Ciemne tło ma wyłącznie ona.
- **Kreski brzegowe ledwie grubsze od zwykłych.** Mają dzielić, a nie przecinać tabelę
  na pół.
- **Gier równych w tabelach nie ma.** Kratka niesie to, co Czarny dostaje, a w grze
  równej nie dostaje nic. Wystarczy o tym jedno zdanie, bez żadnej liczby: każda siatka
  zaczyna się dokładnie tam, gdzie kończą się gry równe, więc „mniejsza niż pierwsza
  kratka" trafia co do połówki stopnia na wszystkich trzech planszach.
- **Trzy tabele w jednym rzędzie**, mały odstęp — osobne siatki, każda z własnymi
  brzegami.

### Zwięzłość

To był stały kierunek i warto go trzymać:

- Nic, co widać z samej tabeli, nie stoi w tekście nad nią. Opis mówi wyłącznie to,
  czego siatka pokazać nie może: co znaczy kratka i co dzieje się przed pierwszą z nich.
- Co wspólne dla trzech tabel — mówi się raz. Co różne (nazwa planszy) — musi być przy
  każdej, więc dostaje jedyne miejsce, które nic nie kosztuje: róg.
- Połówka stopnia to ułamek pionowy (1 nad 2, kreska między), a nie „,5" ani ukośne ½.
  Zajmuje szerokość jednej cyfry — i to od niej zależy szerokość całej kolumny.
- Kratki tak wąskie, jak pozwala treść. Szerokości idą z `<colgroup>`, bo przy
  `table-layout: fixed` pierwszy wiersz (czapka na całą siatkę) rozdzieliłby je po równo.

### Zasięg

Ile ruchów pokazuje która tabela — do ustawienia w `RUCHOW` i `PIERWSZY_RUCH`.
Kolumna znaczy co innego na każdej planszy, więc te same „siedem ruchów" to różny
zasięg w stopniach; to jest w porządku i nie ma czego wyrównywać.

## Czego pilnują testy

- **Świeżość.** Każdy plik generowany jest składany jeszcze raz i porównywany z dyskiem.
  Zmiana liczby bez `make wyrownanie` nie przejdzie przez hook.
- **Zgodność ze źródłami.** Cztery przepisane tabele — co do liczby, razem z dziwactwami
  oryginałów: dziurą w BGA 9x9, uskokiem LSG 13x13 o 18 punktów przy różnicy 16.
  Dziwactwo źródła ma dać się odróżnić od naszej literówki.
- **Arytmetyka.** Tam, gdzie tabela jest ciągiem arytmetycznym, test przelicza ją co do
  punktu. Gdzie nie jest — ma własny test opisujący, gdzie i o ile się łamie.
- **Dwa języki.** 19x19 liczone przez `wyrownanie.js` musi wyjść tak samo jak przez
  `zg.py`.
- **Układ.** Rogi, kreski, szerokości, kolejność tabel w rzędzie, brak przecinka w
  siatce, jedno wystąpienie opisu.

## Otwarte

- Adres źródłowy tabel Ishikury i Hunta jest zgadnięty (Sensei's Library) i oznaczony
  w obu modułach jako `TODO`. Przyszły z wklejki, nie ze strony.
- `tabela-zg.html` jest na razie materiałem roboczym. Sam `<table>` da się z niego
  wyciąć i wkleić na `ranking.html` — nosi klasy `sila komp` i `komp-jency` /
  `komp-ruchy`, więc złapie gotowe reguły ze `style.css`.

## Jak to przegenerować

```
make wyrownanie     # wszystkie pliki naraz
make test           # to samo, co hook pre-commit
```

Żadnego z plików `wyrownanie-*.json`, `zestawienie-*.txt` ani `tabela-zg.html` nie
poprawia się ręcznie — poprawki wchodzą do `tools/wyrownanie/*.py`.
