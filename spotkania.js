/* Najblizsze spotkania klubu, czytane z publicznego Kalendarza Google.
 *
 * Strona nie twierdzi juz, ze spotkania sa cotygodniowe - pokazuje wylacznie to,
 * co stoi w kalendarzu. Dzieki temu osoba prowadzaca ogloszenia nie musi ruszac
 * HTML-a ani gita: przenosi wydarzenie albo dopisuje opis i strona nadaza.
 *
 * Klucz API jest widoczny w zrodle strony i to jest w porzadku - ograniczyliśmy
 * go w konsoli Google do jednego API (Calendar) i jednej domeny (zg-go.pl),
 * a dane sa publiczne i tylko do odczytu.
 *
 * Wartosci porownawcze (domyslny tytul i miejsce) siedza w atrybutach data-
 * kontenera w index.html, zeby staly obok widocznego adresu, a nie w drugim pliku.
 */

const API = 'https://www.googleapis.com/calendar/v3/calendars';
const KALENDARZ = '9687fb38db60e421a2b447fa45aa4ccfb90372f762a48205a3f2a55a7022b9c1@group.calendar.google.com';
const KLUCZ = 'AIzaSyCteIwt-0UHjCEyx1Wl6Z1n7utuyZeQ0-4';

export const STREFA = 'Europe/Warsaw';
export const WIDOCZNE_OD_RAZU = 3;
export const POBIERAJ = 20;

export const BRAK_SPOTKAN = 'Brak zaplanowanych spotkań.';

/* Awaria jest dla odwiedzajacego cicha - sekcja po prostu nie ma czego pokazac.
 * Jedyna osoba, ktora moze nas o niej powiadomic, to wlasnie on, wiec komunikat
 * prosi o zgloszenie zamiast tlumaczyc, co sie stalo. Adres Discorda bierzemy
 * z atrybutu data- kontenera, zeby zaproszenie nie mialo drugiej kopii w kodzie. */
export const BLAD_PRZED = 'Nie udało się wczytać terminów — powiedz nam o tym na ';
export const BLAD_LINK = 'Discordzie';
export const BLAD_PO = ', a naprawimy.';

/* Trzy kropki zamiast napisu: lista jest krotka i wystarczy cichy znak, ze cos
 * jest dalej. Czytnik ekranu przeczytalby jednak "kropka kropka kropka", wiec
 * prawdziwa etykieta idzie w aria-label i w title. */
export const WIECEJ = '···';
export const WIECEJ_OPIS = 'Pokaż dalsze terminy';

/* Google dokleja kraj do adresu wybranego z map. Na stronie o klubie w Zielonej
 * Gorze slowo "Poland" nie niesie nic. */
const OGON_KRAJU = /,\s*(Poland|Polska)\s*$/i;

// --- formatowanie terminu ----------------------------------------------------

/* Dzien tygodnia jest zawsze, bo bywa inny niz zwykle - to jedyny sposob, w jaki
 * czytelnik dowiaduje sie o przenosinach, skoro nie generujemy juz dopiskow. */
function dzienIData(chwila, strefa) {
  const czesci = new Intl.DateTimeFormat('pl-PL', {
    timeZone: strefa, weekday: 'long', day: 'numeric', month: 'long',
  }).formatToParts(chwila);
  const we = (typ) => czesci.filter((c) => c.type === typ).map((c) => c.value).join('');
  return `${we('weekday')} ${we('day')} ${we('month')}`;
}

function godzina(chwila, strefa) {
  return new Intl.DateTimeFormat('pl-PL', {
    timeZone: strefa, hour: '2-digit', minute: '2-digit', hour12: false,
  }).format(chwila);
}

/* Wydarzenie calodniowe przychodzi jako start.date ("2026-08-05") zamiast
 * start.dateTime i nie ma godziny do pokazania.
 *
 * Taka data nie jest chwila w czasie, tylko kartka z kalendarza, wiec czytamy
 * ja doslownie w UTC i swiadomie ignorujemy strefe. Przeliczanie jej przez
 * Warszawe zdawaloby sie dzialac, dopoki ktos nie otworzy strony na wschod od
 * UTC+12 - tam 5 sierpnia zrobiloby sie 6 sierpnia. */
export function formatujTermin(start, strefa) {
  if (start.date) return dzienIData(new Date(`${start.date}T00:00:00Z`), 'UTC');
  const chwila = new Date(start.dateTime);
  return `${dzienIData(chwila, strefa)}, ${godzina(chwila, strefa)}`;
}

/* timeMin = poczatek dzisiejszego dnia w Warszawie, zeby dzisiejsze spotkanie
 * jeszcze sie liczylo, a wczorajsze juz nie. */
export function poczatekDnia(teraz, strefa) {
  const data = new Intl.DateTimeFormat('sv-SE', { timeZone: strefa }).format(teraz);
  const nazwa = new Intl.DateTimeFormat('en-US', { timeZone: strefa, timeZoneName: 'longOffset' })
    .formatToParts(teraz).find((c) => c.type === 'timeZoneName').value;
  const przesuniecie = nazwa.replace('GMT', '') || '+00:00';
  return `${data}T00:00:00${przesuniecie}`;
}

// --- sanityzacja opisu -------------------------------------------------------

/* Kalendarz ma formatowanie tekstu i zwraca description jako HTML. Wklejenie
 * z Worda przynosi pol arkusza stylow, a wstrzykiwanie cudzego HTML-u bez filtra
 * to zly nawyk niezaleznie od tego, komu ufamy. */
export const DOZWOLONE = new Set(['B', 'STRONG', 'I', 'EM', 'A', 'BR', 'P', 'UL', 'OL', 'LI']);
export const SCHEMATY = ['http:', 'https:', 'mailto:'];

/* Znacznik spoza bialej listy tracimy, ale jego tekst zostaje - z tych dwoma
 * wyjatkami. Parser wsadza zawartosc <script> i <style> jako zwykly tekst, wiec
 * bez tego na stronie wyladowalby kod zrodlowy w postaci widocznego napisu. */
const WYTNIJ_Z_TRESCIA = new Set(['SCRIPT', 'STYLE']);

/* Klasyczne obejscia filtra schematu to biale znaki i znaki sterujace wewnatrz
 * slowa ("java\tscript:") oraz zmiana wielkosci liter. Usuwamy jedno i drugie
 * przed sprawdzeniem, zamiast ufac, ze URL przyszedl w formie kanonicznej. */
export function czyLinkBezpieczny(href) {
  if (typeof href !== 'string') return false;
  const czysty = href.replace(/[\u0000-\u0020\u007F-\u00A0]/g, '').toLowerCase();
  if (czysty.startsWith('#') || czysty.startsWith('/')) return true;
  const dwukropek = czysty.indexOf(':');
  if (dwukropek === -1) return true;               // adres wzgledny, bez schematu
  return SCHEMATY.includes(czysty.slice(0, dwukropek + 1));
}

/* Chodzimy po drzewie i przepisujemy wylacznie to, co jest na bialej liscie.
 * Znacznik spoza listy znika, ale jego tekst zostaje - inaczej wklejka z Worda,
 * w ktorej wszystko siedzi w <span>, wyparowalaby w calosci.
 *
 * Wezel musi wystawiac nodeType / nodeName / childNodes / textContent oraz
 * getAttribute na elementach. Prawdziwy DOM to spelnia; testy podstawiaja atrapy. */
export function oczyscWezel(wezel, dokument) {
  if (wezel.nodeType === 3) return [dokument.createTextNode(wezel.textContent)];

  if (wezel.nodeType !== 1) return [];
  if (WYTNIJ_Z_TRESCIA.has(wezel.nodeName)) return [];

  const dzieci = Array.from(wezel.childNodes || []).flatMap((d) => oczyscWezel(d, dokument));
  if (!DOZWOLONE.has(wezel.nodeName)) return dzieci;

  const nowy = dokument.createElement(wezel.nodeName.toLowerCase());
  if (wezel.nodeName === 'A') {
    /* Link o niedozwolonym schemacie gubi kotwice, ale zachowuje swoj tekst -
     * czytelnik widzi, co bylo napisane, tylko nie da sie w to kliknac. */
    const href = wezel.getAttribute('href');
    if (!czyLinkBezpieczny(href)) return dzieci;
    nowy.setAttribute('href', href);
    nowy.setAttribute('target', '_blank');
    nowy.setAttribute('rel', 'noopener');
  }
  dzieci.forEach((d) => nowy.appendChild(d));
  return [nowy];
}

export function oczyscOpis(html, dokument, parser) {
  const zrodlo = parser.parseFromString(`<body>${html}</body>`, 'text/html');
  const wynik = dokument.createDocumentFragment();
  Array.from(zrodlo.body.childNodes)
    .flatMap((w) => oczyscWezel(w, dokument))
    .forEach((w) => wynik.appendChild(w));
  return wynik;
}

// --- dobor tresci wiersza ----------------------------------------------------

/* Tytul i miejsce powtarzajace sie na kazdym spotkaniu sa szumem - nazwa klubu
 * stoi w banerze, adres linijke wyzej. Pokazujemy je dopiero, gdy odstaja. */
export function przygotujWiersz(wydarzenie, konfig) {
  const tytul = wydarzenie.summary && wydarzenie.summary !== konfig.tytulDomyslny
    ? wydarzenie.summary : null;
  const miejsce = wydarzenie.location && wydarzenie.location !== konfig.miejsceDomyslne
    ? wydarzenie.location.replace(OGON_KRAJU, '') : null;
  return {
    termin: formatujTermin(wydarzenie.start, konfig.strefa),
    dopisek: [tytul, miejsce].filter(Boolean).join(', ') || null,
    opis: wydarzenie.description || null,
  };
}

// --- strona ------------------------------------------------------------------

function komunikat(kontener, tresc) {
  const p = document.createElement('p');
  p.className = 'spotkania-brak';
  p.textContent = tresc;
  kontener.replaceChildren(p);
}

function komunikatBledu(kontener) {
  const p = document.createElement('p');
  p.className = 'spotkania-brak';
  const link = document.createElement('a');
  link.href = kontener.dataset.discord;
  link.target = '_blank';
  link.rel = 'noopener';
  link.textContent = BLAD_LINK;
  p.append(BLAD_PRZED, link, BLAD_PO);
  kontener.replaceChildren(p);
}

function wierszDoDom(wiersz, indeks) {
  const blok = document.createElement('div');
  blok.className = 'spotkanie';
  if (indeks >= WIDOCZNE_OD_RAZU) blok.hidden = true;

  const termin = document.createElement('p');
  termin.className = 'spotkanie-termin';
  const mocny = document.createElement('strong');
  mocny.textContent = wiersz.termin;
  termin.appendChild(mocny);
  if (wiersz.dopisek) termin.appendChild(document.createTextNode(` — ${wiersz.dopisek}`));
  blok.appendChild(termin);

  if (wiersz.opis) {
    const opis = document.createElement('div');
    opis.className = 'spotkanie-opis';
    opis.appendChild(oczyscOpis(wiersz.opis, document, new DOMParser()));
    blok.appendChild(opis);
  }
  return blok;
}

function przyciskWiecej(kontener, ukryte) {
  const przycisk = document.createElement('button');
  przycisk.type = 'button';
  przycisk.className = 'spotkania-wiecej';
  przycisk.textContent = WIECEJ;
  przycisk.setAttribute('aria-label', WIECEJ_OPIS);
  przycisk.title = WIECEJ_OPIS;
  przycisk.addEventListener('click', () => {
    ukryte.forEach((b) => { b.hidden = false; });
    przycisk.remove();
  });
  kontener.appendChild(przycisk);
}

async function start() {
  const kontener = document.getElementById('spotkania');
  if (!kontener) return;
  const konfig = {
    strefa: STREFA,
    tytulDomyslny: kontener.dataset.tytul,
    miejsceDomyslne: kontener.dataset.miejsce,
  };

  let wydarzenia;
  try {
    const adres = new URL(`${API}/${encodeURIComponent(KALENDARZ)}/events`);
    adres.search = new URLSearchParams({
      key: KLUCZ,
      singleEvents: 'true',
      orderBy: 'startTime',
      maxResults: String(POBIERAJ),
      timeMin: poczatekDnia(new Date(), STREFA),
    });
    const odpowiedz = await fetch(adres);
    if (!odpowiedz.ok) throw new Error(`Calendar API: HTTP ${odpowiedz.status}`);
    wydarzenia = (await odpowiedz.json()).items || [];
  } catch (blad) {
    /* Awaria jest cicha dla odwiedzajacego, ale nie dla nas - bez tego wygasly
     * klucz objawilby sie wylacznie znikniecien sekcji i nikt by sie nie dowiedzial. */
    console.error('[spotkania]', blad);
    komunikatBledu(kontener);
    kontener.hidden = false;
    return;
  }

  if (wydarzenia.length === 0) {
    komunikat(kontener, BRAK_SPOTKAN);
    kontener.hidden = false;
    return;
  }

  const bloki = wydarzenia.map((w, i) => wierszDoDom(przygotujWiersz(w, konfig), i));
  kontener.replaceChildren(...bloki);
  const ukryte = bloki.filter((b) => b.hidden);
  if (ukryte.length > 0) przyciskWiecej(kontener, ukryte);
  kontener.hidden = false;
}

if (typeof document !== 'undefined') start();
