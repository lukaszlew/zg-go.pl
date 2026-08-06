/* Kalkulator wyrownania i zmiany PS na ranking.html.
 *
 * Liczy dokladnie to, co mowia zasady stojace wyzej na stronie — i nic ponadto.
 * Ma dwie przewagi nad tabela: dziala dla dowolnej roznicy PS, takze powyzej 70,
 * i zna pulapki zmiany PS (wyrazna wygrana, podwojenie serii, kalibracja), o ktore
 * ludzie pytaja najczesciej.
 *
 * Rachunek siedzi w czystych funkcjach, bo to jedyne miejsce w repo, gdzie zasady
 * sa policzone, a nie przepisane — wiec musi byc sprawdzone testami
 * (tools/test_kalkulator.mjs porownuje go z tabela wprost z ranking.html).
 */

export const KROK = 13;        // punktow warty jest jeden darmowy ruch
export const KOMI_JENCY = 6;   // gra rowna: Czarny odklada Bialemu 6 jencow
export const ROWNA_DO = 5;     // roznica PS 0-5 to gra rowna
export const WYRAZNA = 13;     // wygrana o tyle punktow lub wiecej to ±2 PS

// --- wyrownanie (przed gra) --------------------------------------------------

/* Kolumny tabeli zaczynaja sie na roznicy 6, 19, 32... czyli co KROK, i kazda
 * daje Czarnemu jeden ruch wiecej; jency to reszta z dzielenia. Ten sam rachunek
 * przedluza tabele w prawo bez konca, wiec roznica 84 nie jest wyjatkiem. */
export function wyrownanie(mojePS, jegoPS) {
  const roznica = Math.abs(mojePS - jegoPS);
  if (roznica <= ROWNA_DO) {
    return { roznica, rowna: true, ruchy: 1, jency: -KOMI_JENCY };
  }
  const ponad = roznica - (ROWNA_DO + 1);
  return { roznica, rowna: false, ruchy: Math.floor(ponad / KROK) + 1, jency: ponad % KROK };
}

// --- zmiana PS (po grze) -----------------------------------------------------

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

/* Zwraca zmiane PS obu graczy z perspektywy tego, kto wpisal swoj wynik.
 * kalibracja: null albo { kto: 'ja' | 'on', mnoznik: 4 | 3 | 2 } — mnoznik stoi
 * na karcie nowego gracza, na karcie przeciwnika stoi K. */
export function zmianaPS(wynik, { seria = false, kalibracja = null } = {}) {
  if (!wynik) return null;
  const uwagi = [];

  if (wynik.znak === 0) {
    if (kalibracja) uwagi.push('Remis nie zmienia nic — także w grze kalibracyjnej.');
    return { moja: 0, przeciwnika: 0, uwagi };
  }

  const wyrazna = wynik.poddanie || Math.abs(wynik.punkty) >= WYRAZNA;
  const podstawa = wyrazna ? 2 : 1;

  /* Gra kalibracyjna dziala jak zwykla, tylko stoi poza seria: mnoznik z kolumny
   * kalibracja kumuluje sie z ×2 za wyrazna wygrana, a przeciwnik przy K dostaje
   * doslownie ±1 — jego zmiany nie mnozy nic. */
  if (kalibracja) {
    if (seria) uwagi.push('Gra kalibracyjna stoi poza serią: ani do niej nie wchodzi, ani jej nie przerywa.');
    if (wyrazna) uwagi.push('Wygrana o 13 punktów lub więcej albo przez poddanie mnoży zmianę PS nowego gracza ×2 — kumuluje się z mnożnikiem kalibracji; przeciwnik przy K i tak dostaje dokładnie ±1 PS.');
    const nowyZnak = kalibracja.kto === 'ja' ? wynik.znak : -wynik.znak;
    const nowego = nowyZnak * podstawa * kalibracja.mnoznik;
    const drugiego = -nowyZnak;
    return kalibracja.kto === 'ja'
      ? { moja: nowego, przeciwnika: drugiego, uwagi }
      : { moja: drugiego, przeciwnika: nowego, uwagi };
  }

  if (wyrazna) {
    uwagi.push(wynik.poddanie
      ? 'Poddanie liczy się tak samo jak wygrana o 13 punktów: mnoży zmianę PS obu graczy ×2.'
      : 'Wygrana o 13 punktów lub więcej mnoży zmianę PS obu graczy ×2.');
  }
  const zwyciezcy = podstawa * (seria ? 2 : 1);
  if (seria) uwagi.push('Seria — trzecia wygrana z rzędu i każda kolejna — mnoży zmianę zwycięzcy ×2; sama się nie nawarstwia.');
  return wynik.znak > 0
    ? { moja: zwyciezcy, przeciwnika: -podstawa, uwagi }
    : { moja: -podstawa, przeciwnika: zwyciezcy, uwagi };
}

export const zeZnakiem = (n) => (n > 0 ? `+${n}` : `${n}`);

// --- strona ------------------------------------------------------------------

/* Kolory nie maja rubryki na karcie — wynikaja z roznicy PS, wiec stoja pod nia
 * zdaniem, tak jak na stronie wynikaja z zasady 2 i 3. */
function opisKolorow(w, mojePS, jegoPS) {
  if (w.rowna) {
    return `Gra równa: kolory przez nigiri, Czarny odkłada Białemu ${KOMI_JENCY} jeńców `
      + 'i oddaje wygraną przy równym wyniku — razem komi 6,5.';
  }
  return mojePS > jegoPS
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
    const znanePS = moje.value.trim() !== '' && jego.value.trim() !== ''
      && Number.isFinite(a) && Number.isFinite(b);

    if (!znanePS) {
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
    pole('k-o-moje').textContent = b;
    pole('k-o-jego').textContent = a;
    wpisz({
      roznica: [w.roznica, w.roznica],
      ruchy: [w.ruchy, w.ruchy],
      jency: [w.jency, w.jency],
    });
    pole('k-kolory').textContent = opisKolorow(w, a, b);

    const wpisany = parsujWynik(wynik.value);
    // Wartosc to "kto:mnoznik" — kto mnozy swoja zmiane PS, a kto przy K dostaje ±1.
    const [kto, mnoznik] = kalib.value ? kalib.value.split(':') : [];
    const z = zmianaPS(wpisany, {
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
      nowe: [a + z.moja, b + z.przeciwnika],
    });
    pole('k-uwagi').replaceChildren(...z.uwagi.map(uwaga));
  }

  blok.addEventListener('input', przelicz);
  blok.hidden = false;   // bez JS kalkulator nie ma po co stac na stronie
  przelicz();
}

if (typeof document !== 'undefined') start();
