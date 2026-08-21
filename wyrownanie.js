/* Kalkulator wyrownania i zmiany stopni na ranking.html.
 *
 * Liczy dokladnie to, co mowia zasady stojace wyzej na stronie — i nic ponadto.
 * Ma dwie przewagi nad tabela: dziala dla dowolnej roznicy stopni, takze poza tabela,
 * i zna pulapki zmiany stopni (wyrazna wygrana, podwojenie serii, kalibracja), o ktore
 * ludzie pytaja najczesciej.
 *
 * Rachunek siedzi w czystych funkcjach, bo to jedyne miejsce w repo, gdzie zasady
 * sa policzone, a nie przepisane — wiec musi byc sprawdzone testami
 * (tools/test_kalkulator.mjs porownuje go z tabela wprost z ranking.html).
 */

export const RUCH = 13;        // punktow warty jest jeden darmowy ruch — na kazdej planszy
export const KOMI_JENCY = 6;   // gra rowna: Czarny odklada Bialemu 6 jencow
export const WYRAZNA = 13;     // wygrana o tyle punktow lub wiecej mnozy zmiane ×2
export const POLOWKA = 0.5;    // rozdzielczosc stopni i typowa zmiana po grze

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
 * Gra rowna trzyma plaskie 6 jencow (zasada 2), a nie to, co wyszloby z samego
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
    return { roznica, rowna: true, ruchy: 1, jency: -KOMI_JENCY };
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
 * kalibracja: null albo { kto: 'ja' | 'on', mnoznik: 4 | 3 | 2 } — mnoznik stoi
 * na karcie nowego gracza, na karcie przeciwnika stoi K. */
export function zmianaStopni(wynik, { seria = false, kalibracja = null } = {}) {
  if (!wynik) return null;
  const uwagi = [];

  if (wynik.znak === 0) {
    if (kalibracja) uwagi.push('Remis nie zmienia nic — także w grze kalibracyjnej.');
    return { moja: 0, przeciwnika: 0, uwagi };
  }

  // Zwykla wygrana to pol stopnia, wyrazna — caly. Mnozniki serii i kalibracji
  // ida na tym samym, wiec cala arytmetyka zostaje w polowkach stopnia.
  const wyrazna = wynik.poddanie || Math.abs(wynik.punkty) >= WYRAZNA;
  const podstawa = (wyrazna ? 2 : 1) * POLOWKA;

  /* Gra kalibracyjna dziala jak zwykla, tylko stoi poza seria: mnoznik z kolumny
   * kalibracja kumuluje sie z ×2 za wyrazna wygrana, a przeciwnik przy K dostaje
   * doslownie ±1 — jego zmiany nie mnozy nic. */
  if (kalibracja) {
    if (seria) uwagi.push('Gra kalibracyjna stoi poza serią: ani do niej nie wchodzi, ani jej nie przerywa.');
    if (wyrazna) uwagi.push('Wygrana o 13 punktów lub więcej albo przez poddanie mnoży zmianę stopni nowego gracza ×2 — kumuluje się z mnożnikiem kalibracji; przeciwnik przy K i tak dostaje dokładnie ±½ stopnia.');
    const nowyZnak = kalibracja.kto === 'ja' ? wynik.znak : -wynik.znak;
    const nowego = nowyZnak * podstawa * kalibracja.mnoznik;
    const drugiego = -nowyZnak * POLOWKA;   // zasada 10: przy K dokladnie ±½ stopnia
    return kalibracja.kto === 'ja'
      ? { moja: nowego, przeciwnika: drugiego, uwagi }
      : { moja: drugiego, przeciwnika: nowego, uwagi };
  }

  if (wyrazna) {
    uwagi.push(wynik.poddanie
      ? 'Poddanie liczy się tak samo jak wygrana o 13 punktów: mnoży zmianę stopni obu graczy ×2.'
      : 'Wygrana o 13 punktów lub więcej mnoży zmianę stopni obu graczy ×2.');
  }
  const zwyciezcy = podstawa * (seria ? 2 : 1);
  if (seria) uwagi.push('Seria — trzecia wygrana z rzędu i każda kolejna — mnoży zmianę zwycięzcy ×2; sama się nie nawarstwia.');
  return wynik.znak > 0
    ? { moja: zwyciezcy, przeciwnika: -podstawa, uwagi }
    : { moja: -podstawa, przeciwnika: zwyciezcy, uwagi };
}

/* Stopnie pisze sie polowkami: 0, ½, 1, 1½ — tak, jak stawia sie je na karcie. */
export function stopnie(n) {
  const znak = n < 0 ? '-' : '';
  const ile = Math.abs(n);
  const calosc = Math.floor(ile);
  const pol = ile - calosc >= 0.5 ? '½' : '';
  if (!pol) return `${znak}${calosc}`;
  return `${znak}${calosc || ''}${pol}`;
}

export const zeZnakiem = (n) => (n > 0 ? `+${stopnie(n)}` : stopnie(n));

// --- strona ------------------------------------------------------------------

/* Kolory nie maja rubryki na karcie — wynikaja z roznicy stopni, wiec stoja pod nia
 * zdaniem, tak jak na stronie wynikaja z zasady 2 i 3. */
function opisKolorow(w, mojeSt, jegoSt) {
  if (w.rowna) {
    return `Gra równa: kolory przez nigiri, Czarny odkłada Białemu ${KOMI_JENCY} jeńców `
      + 'i oddaje wygraną przy równym wyniku — razem komi 6,5.';
  }
  return mojeSt > jegoSt
    ? `Grasz Białymi, przeciwnik Czarnymi — silniejszy zawsze gra Białymi.`
    : `Grasz Czarnymi, przeciwnik Białymi — silniejszy zawsze gra Białymi.`;
}

function start() {
  const blok = document.getElementById('kalkulator');
  if (!blok) return;
  const pole = (id) => document.getElementById(id);
  const [moje, jego, wynik, seria, kalib] =
    ['k-moje', 'k-jego', 'k-wynik', 'k-seria', 'k-kalibracja'].map(pole);

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
      jency: [w.jency, w.jency],
    });
    pole('k-kolory').textContent = opisKolorow(w, a, b);

    const wpisany = parsujWynik(wynik.value);
    // Wartosc to "kto:mnoznik" — kto mnozy swoja zmiane stopni, a kto przy K dostaje ±½.
    const [kto, mnoznik] = kalib.value ? kalib.value.split(':') : [];
    const z = zmianaStopni(wpisany, {
      seria: seria.checked,
      kalibracja: mnoznik ? { kto, mnoznik: Number(mnoznik) } : null,
    });
    // Mnoznik stoi na karcie nowego gracza, K na karcie jego przeciwnika.
    pole('k-o-kalibracja').textContent = !mnoznik ? '—' : (kto === 'ja' ? 'K' : `×${mnoznik}`);

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
