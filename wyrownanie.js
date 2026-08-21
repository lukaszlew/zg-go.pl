/* Kalkulator wyrownania i zmiany stopni na ranking.html.
 *
 * Liczy dokladnie to, co mowia zasady stojace wyzej na stronie — i nic ponadto.
 * Ma dwie przewagi nad tabela: dziala dla dowolnej roznicy stopni, takze poza tabela,
 * i zna pulapki zmiany stopni (wyrazna wygrana, kalibracja), o ktore
 * ludzie pytaja najczesciej.
 *
 * Rachunek siedzi w czystych funkcjach, bo to jedyne miejsce w repo, gdzie zasady
 * sa policzone, a nie przepisane — wiec musi byc sprawdzone testami
 * (tools/test_kalkulator.mjs porownuje go z tabela wprost z ranking.html).
 */

export const RUCH = 13;        // punktow warty jest jeden darmowy ruch — na kazdej planszy
export const KOMI_JENCY = 6;   // gra rowna: Czarny odklada Bialemu 6 jencow
export const WYRAZNA = 20;     // wygrana o tyle punktow lub wiecej liczy sie jak poddanie
export const POLOWKA = 0.5;    // rozdzielczosc stopni i typowa zmiana po grze

/* Gra rowna idzie na karte jedna liczba: szesc odlozonych jencow plus pol punktu
 * za wygrana Bialego przy rownym wyniku. Rachunek wyrownania trzyma sie calych
 * szesciu (KOMI_JENCY) — polowka rozstrzyga wynik, a nie wyrownanie. */
export const ROWNA_JENCY = -6.5;

/* Ile punktow wyrownania dokłada jeden stopien roznicy — zalezy od planszy, bo
 * stopien znaczy wszedzie to samo, ale na mniejszej planszy jest wart mniej.
 * Stosunek i cala tabela stoja w tools/wyrownanie/ (SPEC.md tlumaczy, skad). */
export const KROK = { '9x9': 2, '13x13': 5, '19x19': 13 };
export const DOMYSLNA_PLANSZA = '9x9';

/* 13x13 nie schodzi z samego wzoru, tylko z drabinki: 5 nie dzieli 13, wiec
 * koncowki jencow plynelyby z bloku na blok i tabela nie mialaby powtarzalnego
 * ksztaltu. Po pieciu polowkach stopnia Czarny ma caly ruch wiecej. Wyprowadzenie
 * i cena tego wyboru stoja w tools/wyrownanie/SPEC.md. */
export const PETLA_13X13 = [0, 3, 5, 8, 10];
export const PIERWSZY_13X13 = 1.5;   // drabinka zaczyna sie za grami rownymi

// --- wyrownanie (przed gra) --------------------------------------------------

/* Ten sam rachunek, co w tools/wyrownanie/zg.py — jedna zasada na trzy plansze.
 * Roznica stopni idzie na punkty krokiem planszy, potem trzynasty punkt kupuje
 * Czarnemu caly ruch, a reszta zostaje jencami. Rachunek nie ma konca, wiec
 * tabela na stronie urywa sie tylko dlatego, ze papier sie konczy.
 *
 * Gra rowna trzyma plaskie 6 jencow, a nie to, co wyszloby z samego
 * wzoru — ponizej pierwszego wyrownania klub nie stopniuje komi. */
export function wyrownanie(mojeSt, jegoSt, plansza = DOMYSLNA_PLANSZA) {
  const roznica = Math.abs(mojeSt - jegoSt);
  if (plansza === '13x13' && roznica >= PIERWSZY_13X13) {
    const pozycja = Math.round((roznica - PIERWSZY_13X13) / POLOWKA);
    const ruchy = 1 + Math.floor(pozycja / PETLA_13X13.length);
    return { roznica, rowna: false, ruchy, jency: PETLA_13X13[pozycja % PETLA_13X13.length] };
  }
  const punkty = Math.trunc(-KOMI_JENCY + KROK[plansza] * roznica);
  if (punkty < 0) {
    return { roznica, rowna: true, ruchy: 1, jency: ROWNA_JENCY };
  }
  const ruchy = 1 + Math.floor(punkty / RUCH);
  return { roznica, rowna: false, ruchy, jency: punkty - (ruchy - 1) * RUCH };
}

// --- zmiana stopni (po grze) -----------------------------------------------------

/* Wynik tak, jak wpisuje sie go na karte: liczba ze znakiem albo R po poddaniu. */
export function parsujWynik(tekst) {
  const t = String(tekst).trim().toUpperCase().replace('−', '-');
  if (t === 'R' || t === '+R') return { poddanie: true, znak: 1, punkty: null };
  if (t === '-R') return { poddanie: true, znak: -1, punkty: null };
  const n = Number(t);
  if (t === '' || !Number.isFinite(n)) return null;
  const punkty = Math.trunc(n);
  return { poddanie: false, znak: Math.sign(punkty), punkty };
}

/* Zwraca zmiane stopni obu graczy z perspektywy tego, kto wpisal swoj wynik.
 * kalibracja: null albo { kto: 'ja' | 'on' } — na karcie kalibrowanego stoi K,
 * na karcie jego przeciwnika P. */
export function zmianaStopni(wynik, { kalibracja = null } = {}) {
  if (!wynik) return null;
  const uwagi = [];

  if (wynik.znak === 0) {
    if (kalibracja) uwagi.push('Remis nie zmienia nic — także w grze kalibracyjnej.');
    return { moja: 0, przeciwnika: 0, uwagi };
  }

  // Wygrana o WYRAZNA punktow lub przez poddanie to przewaga wieksza niz darmowy
  // ruch — starczyloby jej nawet o ruch mniej.
  const wyrazna = wynik.poddanie || Math.abs(wynik.punkty) >= WYRAZNA;

  /* Trzy pierwsze gry nowego gracza licza sie jemu podwojnie i symetrycznie: ±1,
   * a po wyraznej ±2. Przeciwnik przy P stoi w miejscu — gra przeciwko sile, ktora
   * dopiero jest zgadywana, nic o jego wlasnej nie mowi. */
  if (kalibracja) {
    uwagi.push(wyrazna
      ? 'Gra kalibracyjna po wyraźnej wygranej lub przegranej: nowy gracz ±2 St, przeciwnik przy P bez zmian.'
      : 'Gra kalibracyjna: nowy gracz ±1 St, przeciwnik przy P bez zmian.');
    const nowego = (kalibracja.kto === 'ja' ? wynik.znak : -wynik.znak) * (wyrazna ? 2 : 1);
    return kalibracja.kto === 'ja'
      ? { moja: nowego, przeciwnika: 0, uwagi }
      : { moja: 0, przeciwnika: nowego, uwagi };
  }

  /* Wyrazna wygrana daje zwyciezcy caly stopien, ale przegranemu zabiera dalej pol:
   * nagradza sie przewage, a nie karze podwojnie tego, kto ja przyjal. */
  const zwyciezcy = wyrazna ? 1 : POLOWKA;
  if (wyrazna) {
    uwagi.push(wynik.poddanie
      ? 'Poddanie liczy się tak samo jak wygrana o 20 punktów: zwycięzca +1 St, przegrany −½ St.'
      : 'Wygrana o 20 punktów lub więcej daje zwycięzcy +1 St; przegrany traci ½ St jak zawsze.');
  }
  return wynik.znak > 0
    ? { moja: zwyciezcy, przeciwnika: -POLOWKA, uwagi }
    : { moja: -POLOWKA, przeciwnika: zwyciezcy, uwagi };
}

/* Stopnie pisze sie polowkami: 0, ½, 1, 1½ — tak, jak stawia sie je na karcie. */
export function stopnie(n) {
  const znak = n < 0 ? '−' : '';   // minus typograficzny, ten sam co w zasadach
  const ile = Math.abs(n);
  const calosc = Math.floor(ile);
  const pol = ile - calosc >= 0.5 ? '½' : '';
  if (!pol) return `${znak}${calosc}`;
  return `${znak}${calosc || ''}${pol}`;
}

export const zeZnakiem = (n) => (n > 0 ? `+${stopnie(n)}` : stopnie(n));

/* Jency licza sie w punktach, nie w stopniach: polowka trafia sie w nich tylko w
 * grze rownej i pisze sie ja po polsku, przecinkiem. */
export const zapisJencow = (n) => String(n).replace('-', '−').replace('.', ',');

// --- strona ------------------------------------------------------------------

/* Kolory nie maja rubryki na karcie — wynikaja z roznicy stopni, wiec stoja pod nia
 * zdaniem, tak jak na stronie wynikaja z opisu pod tabelami. */
function opisKolorow(w, mojeSt, jegoSt) {
  if (w.rowna) {
    return `Gra równa: kolory przez nigiri, Biały otrzyma ${KOMI_JENCY} jeńców `
      + 'i wygrywa remisy — czyli komi 6,5.';
  }
  return mojeSt > jegoSt
    ? `Grasz Białymi, przeciwnik Czarnymi — silniejszy zawsze gra Białymi.`
    : `Grasz Czarnymi, przeciwnik Białymi — silniejszy zawsze gra Białymi.`;
}

function start() {
  const blok = document.getElementById('kalkulator');
  if (!blok) return;
  const pole = (id) => document.getElementById(id);
  const [moje, jego, wynik, kalib] =
    ['k-moje', 'k-jego', 'k-wynik', 'k-kalibracja'].map(pole);

  const uwaga = (tekst) => {
    const li = document.createElement('li');
    li.textContent = tekst;
    return li;
  };

  /* Wypelnia obie karty naraz: klucz to nazwa rubryki, wartosci to para
   * (moja karta, karta przeciwnika). Rubryki wspolne obu kartom dostaja te sama
   * wartosc dwa razy — i o to chodzi, bo tak wlasnie wyglada to na papierze. */
  function wpisz(rubryki) {
    for (const [rubryka, [mojaWartosc, jegoWartosc]] of Object.entries(rubryki)) {
      pole(`k-${rubryka}`).textContent = mojaWartosc;
      pole(`k-o-${rubryka}`).textContent = jegoWartosc;
    }
  }

  /* Rubryka, ktorej nie da sie jeszcze policzyc, stoi pusta ze znakiem zapytania —
   * dokladnie tak, jak wyglada karta przed wpisaniem czegokolwiek. */
  const PUSTO = '?';

  function przelicz() {
    const a = Number(moje.value);
    const b = Number(jego.value);
    const znaneSt = moje.value.trim() !== '' && jego.value.trim() !== ''
      && Number.isFinite(a) && Number.isFinite(b);

    if (!znaneSt) {
      pole('k-o-moje').textContent = PUSTO;
      pole('k-o-jego').textContent = PUSTO;
      wpisz({
        roznica: [PUSTO, PUSTO], ruchy: [PUSTO, PUSTO], jency: [PUSTO, PUSTO],
        zmiana: [PUSTO, PUSTO], nowe: [PUSTO, PUSTO],
      });
      pole('k-o-wynik').textContent = PUSTO;
      pole('k-kolory').textContent = '';
      pole('k-uwagi').replaceChildren();
      return;
    }

    const w = wyrownanie(a, b);
    // Wszystko, co jest w stopniach, idzie przez stopnie(): rubryka ma wygladac
    // tak, jak stawia sie ja na karcie, czyli "42½", a nie "42.5".
    pole('k-o-moje').textContent = stopnie(b);
    pole('k-o-jego').textContent = stopnie(a);
    wpisz({
      roznica: [stopnie(w.roznica), stopnie(w.roznica)],
      ruchy: [w.ruchy, w.ruchy],
      jency: [zapisJencow(w.jency), zapisJencow(w.jency)],
    });
    pole('k-kolory').textContent = opisKolorow(w, a, b);

    const wpisany = parsujWynik(wynik.value);
    // Wartosc pola to "ja" albo "on" — kto z dwojga jest kalibrowany.
    const kto = kalib.value;
    const z = zmianaStopni(wpisany, { kalibracja: kto ? { kto } : null });
    // K stoi na karcie kalibrowanego, P na karcie jego przeciwnika.
    pole('k-o-kalibracja').textContent = !kto ? '—' : (kto === 'ja' ? 'P' : 'K');

    if (!z) {
      wpisz({ zmiana: [PUSTO, PUSTO], nowe: [PUSTO, PUSTO] });
      pole('k-o-wynik').textContent = PUSTO;
      // Podpowiedz tylko wtedy, gdy ktos cos wpisal i sie nie udalo — puste pole
      // nie jest bledem, tylko rubryka, do ktorej jeszcze nie doszlismy.
      pole('k-uwagi').replaceChildren(...(wynik.value.trim()
        ? [uwaga('Wynik wpisuje się w punktach ze znakiem albo jako R po poddaniu.')]
        : []));
      return;
    }
    const przeciwny = wpisany.poddanie
      ? (wpisany.znak > 0 ? '−R' : '+R')
      : zeZnakiem(-wpisany.punkty);
    pole('k-o-wynik').textContent = przeciwny;
    wpisz({
      zmiana: [zeZnakiem(z.moja), zeZnakiem(z.przeciwnika)],
      nowe: [stopnie(a + z.moja), stopnie(b + z.przeciwnika)],
    });
    pole('k-uwagi').replaceChildren(...z.uwagi.map(uwaga));
  }

  blok.addEventListener('input', przelicz);
  blok.hidden = false;   // bez JS kalkulator nie ma po co stac na stronie
  przelicz();
}

if (typeof document !== 'undefined') start();
