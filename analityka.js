/* Liczniki odwiedzin i zdarzenia klikniec — jedno miejsce dla calej analityki.
 *
 * Strona jest pisana recznie i nie ma build-stepu, wiec snippet wklejony wprost
 * do HTML-a zylby w czterech kopiach na czterech podstronach. Rozjechane kopie
 * tego samego bloku juz raz nas kosztowaly (patrz tools/test_strona.py), a
 * licznik, ktory po cichu wypadl z jednej strony, klamie w statystykach zamiast
 * krzyczec. Tutaj dopisanie kolejnego licznika to jeden obiekt na liscie
 * DOSTAWCY i zadnej zmiany w HTML-u.
 *
 * Kazdy obiekt to komplet atrybutow znacznika <script>, przepisany 1:1 ze
 * snippetu dostawcy — bez tlumaczenia na wlasne nazwy, zeby porownanie z
 * dokumentacja dostawcy bylo doslowne.
 *
 * Pomijamy tylko `defer` i `async`: znacznik tworzony z JS i tak nie blokuje
 * parsowania, wiec te atrybuty nic by tu nie zmienily.
 */

const DOSTAWCY = [
  /* Cloudflare Web Analytics. Pokazuje wylacznie kraj, ale nic nie kosztuje i
   * dziala od dawna — zostaje jako punkt odniesienia dla nowszych licznikow. */
  {
    src: 'https://static.cloudflareinsights.com/beacon.min.js',
    type: 'module',
    'data-cf-beacon': '{"token": "be0997012f154acba2d726d888c5293b"}',
  },
  /* Umami Cloud. Pokazuje miasta i liste pojedynczych wizyt, czyli to, czego
   * Cloudflare nie umie.
   *
   * Samo Umami niczego nie zapisuje w przegladarce: tozsamosc goscia liczy jako
   * hash z jego IP i przegladarki. Ta sama osoba z innej sieci byla wiec dla
   * niego kims nowym — i wlasnie dlatego doklejamy wlasny identyfikator (patrz
   * `tozsamosc` nizej). `data-before-send` wpina go w kazde zdarzenie jeszcze
   * przed wyslaniem, wiec dostaje go takze pierwsza odslona wizyty. */
  {
    src: 'https://cloud.umami.is/script.js',
    'data-website-id': '38006ee0-aaf1-410a-9a4b-4af1c9cd6f9a',
    'data-before-send': 'semedoriTozsamosc',
  },
];

/* Trwala tozsamosc goscia i zgoda na nia.
 *
 * Bez ciasteczka Umami rozpoznaje goscia po hashu z IP i przegladarki, wiec ta
 * sama osoba z domu, z komorki i z Mediateki to trzy rozne osoby. Wlasny
 * identyfikator w ciasteczku sklada je z powrotem w jedna — i to jest jedyny
 * powod, dla ktorego strona w ogole ma banner.
 *
 * Podzial obowiazkow jest wiec taki: liczniki chodza zawsze, bo bez ciasteczek
 * nie potrzebuja zgody i statystyka podstawowa obejmuje 100% ruchu; samo
 * rozpoznawanie powracajacych wlacza sie dopiero po kliknieciu "Zgadzam sie".
 * Odmowa nie wylacza wiec pomiaru — tylko rozmywa go z powrotem w anonimowosc.
 *
 * 400 dni to maksimum, jakie przegladarki zostawiaja z zyciorysu ciasteczka;
 * odswiezamy je przy kazdej wizycie, wiec staly bywalec nie wypada z listy.
 */

const CIASTECZKO = 'semedori-id';
const ZGODA = 'semedori-zgoda';
const DNI = 400;

/* Czysta, wiec sprawdzalna bez przegladarki. Nazwa musi zgadzac sie w calosci:
 * `semedori-id-cos=` nie jest naszym ciasteczkiem. */
export function idZCiasteczka(ciasteczka) {
  const wpis = ciasteczka.split('; ').find((c) => c.startsWith(`${CIASTECZKO}=`));
  return wpis ? wpis.slice(CIASTECZKO.length + 1) : null;
}

let identyfikator = null;

function wlaczTozsamosc() {
  identyfikator = idZCiasteczka(document.cookie) ?? crypto.randomUUID();
  document.cookie = `${CIASTECZKO}=${identyfikator}; max-age=${DNI * 86400}; path=/; SameSite=Lax; Secure`;
}

function zapomnijTozsamosc() {
  identyfikator = null;
  document.cookie = `${CIASTECZKO}=; max-age=0; path=/`;
}

/* Tekst banera jest napisany pod czlowieka, ktory sie waha, i trzyma trzy rzeczy
 * naraz: po co ta strona istnieje, co my z tego mamy i gdzie jest granica.
 * Zdanie "nie dowiemy sie, kim jestes" nie tlumaczy zadnego mechanizmu — stawia
 * sufit, a to jedyne, co realnie uspokaja kogos, kto nie wie, o co jest pytany.
 * Obietnica o reklamach idzie przed nim, bo to jej brak ludzie zakladaja
 * domyslnie: baner zgody kojarzy sie z targetowaniem, zanim ktokolwiek go
 * przeczyta. Obie obietnice musza zostac prawdziwe — jesli kiedys pojawi sie
 * tu licznik reklamowy, to zdanie trzeba usunac, a nie naciagnac.
 * Mechanizmu (losowy numer, nazwa ciasteczka, czas zycia) celowo tu nie ma:
 * kogo to interesuje, ten klika w Prywatnosc. */
const TRESC = 'Robimy tę stronę dla ludzi, którzy tu trafiają — zgoda pozwala nam policzyć, '
  + 'ilu ich jest. Te liczby to jedyna nagroda za wieczory nad rankingiem i resztą. '
  + 'Nie zasilą żadnych reklam, nie dowiemy się z nich, kim jesteś, a decyzję możesz '
  + 'zmienić w każdej chwili.';

function pokazBaner() {
  const baner = document.createElement('div');
  baner.className = 'zgoda';
  baner.setAttribute('role', 'region');
  baner.setAttribute('aria-label', 'Zgoda na rozpoznawanie powracających');

  const tresc = document.createElement('p');
  const szczegoly = document.createElement('a');
  szczegoly.href = 'prywatnosc.html';
  szczegoly.textContent = 'Prywatność';
  tresc.append(`${TRESC} `, szczegoly);

  const zapamietaj = (decyzja) => {
    localStorage.setItem(ZGODA, decyzja);
    baner.remove();
    if (decyzja === 'tak') wlaczTozsamosc();
  };

  /* Oba przyciski wygladaja tak samo i stoja obok siebie: zgoda wymuszona
   * ukryciem odmowy nie jest zgoda. */
  const przycisk = (napis, decyzja) => {
    const p = document.createElement('button');
    p.type = 'button';
    p.textContent = napis;
    p.addEventListener('click', () => zapamietaj(decyzja));
    return p;
  };

  /* "Jasne, liczcie" to gest, "Zgadzam sie" to oswiadczenie; "Wole anonimowo"
   * to wybor, a "Nie, dziekuje" to odmowa akwizytorowi. Ta sama decyzja, inny
   * ciezar — a ludzie chetniej robia gesty niz podpisuja zgody. */
  baner.append(tresc, przycisk('Jasne, liczcie', 'tak'), przycisk('Wolę anonimowo', 'nie'));
  document.body.append(baner);
}

/* Szczegoly na prywatnosc.html pisze kod, nie czlowiek.
 *
 * Polityka prywatnosci starzeje sie dokladnie w tych miejscach, w ktorych ktos
 * przepisal do niej nazwe ciasteczka, liczbe dni albo liste uslug — bo zmiana
 * w kodzie nie przypomina o zmianie w tekscie i strona zaczyna po cichu klamac.
 * Reszta podstrony jest wiec napisana ogolnie i nie wymaga ruszania, a te dwa
 * akapity powstaja z tych samych stalych, ktorych uzywa reszta pliku. Dopisanie
 * trzeciego licznika aktualizuje polityke samo.
 *
 * Bez JS zostaje zdanie odsylajace do kodu — krotsze, ale nadal prawdziwe.
 */
export function adresyDostawcow(dostawcy) {
  return dostawcy.map(({ src }) => new URL(src).hostname);
}

function wpiszSzczegolyPrywatnosci() {
  const liczniki = document.getElementById('prywatnosc-liczniki');
  if (liczniki) {
    const lista = document.createElement('ul');
    lista.className = 'links';
    lista.append(...adresyDostawcow(DOSTAWCY).map((adres) => {
      const pozycja = document.createElement('li');
      pozycja.textContent = adres;
      return pozycja;
    }));
    liczniki.replaceChildren(lista);
  }

  const ciasteczko = document.getElementById('prywatnosc-ciasteczko');
  if (ciasteczko) {
    const zdanie = document.createElement('p');
    zdanie.textContent = `Numer nazywa się ${CIASTECZKO} i wygasa po ${DNI} dniach `
      + `od ostatniej wizyty. Decyzję zapisujemy pod nazwą ${ZGODA}.`;
    ciasteczko.replaceChildren(zdanie);
  }
}

/* Panel decyzji na prywatnosc.html. Zgoda, ktorej nie da sie cofnac, nie jest
 * zgoda — a baner pokazuje sie tylko raz, wiec musi byc gdzies stale miejsce,
 * gdzie widac stan i da sie go odwrocic. Podstrona daje pusty <div>, cala tresc
 * powstaje tutaj, bo tylko tutaj wiadomo, jak decyzja jest przechowywana. */
function wpiszUstawieniaZgody() {
  const miejsce = document.getElementById('zgoda-ustawienia');
  if (!miejsce) return;

  const wlaczona = localStorage.getItem(ZGODA) === 'tak';
  const stan = document.createElement('p');
  stan.textContent = wlaczona
    ? 'Rozpoznajemy Twoją przeglądarkę — ciasteczko semedori-id jest zapisane.'
    : 'Nie rozpoznajemy Cię. Twoje wizyty liczymy anonimowo.';

  const przycisk = document.createElement('button');
  przycisk.type = 'button';
  przycisk.textContent = wlaczona ? 'Wycofaj zgodę' : 'Zgadzam się na rozpoznawanie';
  przycisk.addEventListener('click', () => {
    localStorage.setItem(ZGODA, wlaczona ? 'nie' : 'tak');
    if (wlaczona) zapomnijTozsamosc(); else wlaczTozsamosc();
    wpiszUstawieniaZgody();
  });

  miejsce.replaceChildren(stan, przycisk);
}

/* Umami liczy same odslony — ani pobrania karty, ani wyjscia na Discorda nie
 * pojawiaja sie w panelu, dopoki ich nie zglosimy. Alternatywa dla tego pliku
 * to atrybut data-umami-event przy kazdym <a>, czyli znowu dziesiatki kopii tej
 * samej decyzji rozsypanych po HTML-u — i cichy brak pomiaru wszedzie tam, gdzie
 * ktos zapomni go dopisac. Jeden nasluch na dokumencie klasyfikuje klikniecie po
 * samym adresie, wiec nowy link jest liczony bez pamietania o czymkolwiek.
 */

const PLIK = /\.(pdf|svg|png|zip)$/i;

const nazwaPliku = (sciezka) => sciezka.split('/').pop() || 'index.html';

/* Adres wychodzi z DOM-u (`a.href`), wiec jest juz absolutny — funkcja jest
 * czysta i dlatego sprawdzalna w tools/test_analityka.mjs bez przegladarki.
 *
 * `null` znaczy "nie zglaszaj": przejscie miedzy podstronami widac juz w
 * odslonach i drugi raz go nie liczymy. Kolejnosc warunkow ma znaczenie —
 * plik na cudzym serwerze jest przede wszystkim wyjsciem ze strony.
 */
export function nazwaKlikniecia(adresDocelowy, gospodarz, wMenu) {
  const adres = new URL(adresDocelowy);
  if (adres.protocol === 'mailto:') return 'mail';
  if (adres.protocol === 'webcal:') return 'kalendarz';
  if (adres.hostname !== gospodarz) return `wyjscie: ${adres.hostname.replace(/^www\./, '')}`;
  if (PLIK.test(adres.pathname)) return `plik: ${nazwaPliku(adres.pathname)}`;
  if (wMenu) return `menu: ${nazwaPliku(adres.pathname)}`;
  return null;
}

function zglos(nazwa) {
  /* Skrypt Umami wstrzykujemy asynchronicznie, wiec przy bardzo wczesnym
   * klikniecu moze go jeszcze nie byc i zdarzenie przepada. Swiadomie:
   * kolejkowanie kosztowaloby wiecej kodu, niz warte jest jedno klikniecie. */
  if (nazwa) window.umami?.track(nazwa);
}

function start() {
  const zgoda = localStorage.getItem(ZGODA);
  if (zgoda === 'tak') wlaczTozsamosc();

  /* Umami wola te funkcje przed kazdym wyslaniem (data-before-send), wiec musi
   * stac na window, zanim wstrzykniemy skrypt. Bez zgody `identyfikator` jest
   * pusty i ladunek idzie nietkniety. */
  window.semedoriTozsamosc = (typ, ladunek) => (identyfikator ? { ...ladunek, id: identyfikator } : ladunek);

  for (const atrybuty of DOSTAWCY) {
    const znacznik = document.createElement('script');
    for (const [nazwa, wartosc] of Object.entries(atrybuty)) znacznik.setAttribute(nazwa, wartosc);
    document.head.append(znacznik);
  }

  document.addEventListener('click', (zdarzenie) => {
    const cel = zdarzenie.target.closest?.('a[href], .spotkania-wiecej');
    if (!cel) return;
    zglos(cel.matches('.spotkania-wiecej')
      ? 'spotkania: wiecej'
      : nazwaKlikniecia(cel.href, location.hostname, Boolean(cel.closest('nav.hb-menu'))));
  });

  /* Kalkulator wyrownania przelicza sie przy kazdym wcisnietym klawiszu, a nas
   * interesuje tylko to, czy ktos go w ogole uzyl — stad `once`. */
  document.getElementById('kalkulator')
    ?.addEventListener('input', () => zglos('kalkulator'), { once: true });

  wpiszSzczegolyPrywatnosci();
  wpiszUstawieniaZgody();
  if (!zgoda) pokazBaner();
}

if (typeof document !== 'undefined') start();
