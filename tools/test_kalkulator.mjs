/* Testy kalkulatora z wyrownanie.js.
 *
 * Odpalanie:  node --test tools/test_*.mjs   (albo `make test`)
 *
 * Kalkulator jest jedynym miejscem w repo, gdzie zasady sa policzone, a nie
 * przepisane — wiec najwazniejszy test nie sprawdza go wobec drugiego rachunku
 * w kodzie, tylko wobec tabeli wyrownania stojacej na ranking.html. Jesli kiedys
 * rozjada sie jedno z drugim, czytelnik i kalkulator przestana mowic to samo.
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { KROK, parsujWynik, wyrownanie, zeZnakiem, zmianaPS } from '../wyrownanie.js';

const STRONA = new URL('../ranking.html', import.meta.url);

/* Tabela ze strony jako mapa: roznica PS -> { ruchy, jency }.
 * Wiersz to piec roznic z tym samym numerem jencow, a numer kolumny to liczba
 * pierwszych ruchow Czarnego. */
function tabelaZeStrony() {
  const html = readFileSync(STRONA, 'utf8');
  const tabela = html.match(/<table class="sila komp"[^>]*>([\s\S]*?)<\/table>/)[1];
  const mapa = new Map();
  for (const [, wiersz] of tabela.matchAll(/<tr>([\s\S]*?)<\/tr>/g)) {
    const komorki = [...wiersz.matchAll(/<td[^>]*>(-?\d+)<\/td>/g)].map((m) => Number(m[1]));
    if (komorki.length !== 6) continue;                 // wiersz naglowkowy
    const jency = komorki[5];
    komorki.slice(0, 5).forEach((roznica, i) => mapa.set(roznica, { ruchy: i + 1, jency }));
  }
  return mapa;
}

// --- wyrownanie --------------------------------------------------------------

test('kalkulator zgadza sie z tabela na stronie, komorka po komorce', () => {
  const tabela = tabelaZeStrony();
  assert.equal(tabela.size, 65, 'tabela ma 13 wierszy po 5 roznic');
  for (const [roznica, oczekiwane] of tabela) {
    const wyliczone = wyrownanie(100 + roznica, 100);
    assert.deepEqual(
      { ruchy: wyliczone.ruchy, jency: wyliczone.jency }, oczekiwane,
      `roznica ${roznica}`,
    );
  }
});

test('roznica 0-5 to gra rowna, niezaleznie od tego, kto ma wiecej', () => {
  for (let d = 0; d <= 5; d++) {
    for (const w of [wyrownanie(60 + d, 60), wyrownanie(60, 60 + d)]) {
      assert.equal(w.rowna, true, `roznica ${d}`);
      assert.equal(w.roznica, d);
      assert.equal(w.ruchy, 1);
      assert.equal(w.jency, -6, 'Czarny odklada Bialemu szesciu jencow');
    }
  }
});

test('powyzej tabeli rachunek biegnie dalej co 13 punktow', () => {
  // "odejmujcie po 13 PS, az wynik znajdzie sie w tabeli, a do ruchow dodajcie
  // tyle, ile razy odejmowaliscie" — 71 to 58 z tabeli plus jedno odejmowanie.
  assert.deepEqual(wyrownanie(171, 100), { roznica: 71, rowna: false, ruchy: 6, jency: 0 });
  const dalekie = wyrownanie(300, 100);
  assert.equal(dalekie.ruchy, Math.floor((200 - 6) / KROK) + 1);
  assert.ok(dalekie.jency >= 0 && dalekie.jency < KROK);
});

// --- wynik -------------------------------------------------------------------

test('wynik czyta sie tak, jak wpisuje sie go na karte', () => {
  assert.deepEqual(parsujWynik('+15'), { poddanie: false, znak: 1, punkty: 15 });
  assert.deepEqual(parsujWynik('-15'), { poddanie: false, znak: -1, punkty: -15 });
  assert.deepEqual(parsujWynik('−15'), { poddanie: false, znak: -1, punkty: -15 });  // minus typograficzny
  assert.deepEqual(parsujWynik('0'), { poddanie: false, znak: 0, punkty: 0 });
  assert.deepEqual(parsujWynik('r'), { poddanie: true, znak: 1, punkty: null });
  assert.deepEqual(parsujWynik('-R'), { poddanie: true, znak: -1, punkty: null });
  assert.equal(parsujWynik('nie wiem'), null);
  assert.equal(parsujWynik(''), null);
});

// --- zmiana PS ---------------------------------------------------------------

const zmiana = (tekst, opcje) => zmianaPS(parsujWynik(tekst), opcje);

test('zwykla wygrana to +1 i -1', () => {
  assert.equal(zmiana('+5').moja, 1);
  assert.equal(zmiana('+5').przeciwnika, -1);
  assert.equal(zmiana('-5').moja, -1);
  assert.equal(zmiana('-5').przeciwnika, 1);
});

test('remis nie zmienia nic', () => {
  assert.deepEqual(
    { moja: zmiana('0').moja, przeciwnika: zmiana('0').przeciwnika }, { moja: 0, przeciwnika: 0 },
  );
});

test('wygrana o 13 punktow i poddanie daja ±2', () => {
  assert.equal(zmiana('+12').moja, 1, 'dwanascie to jeszcze zwykla wygrana');
  assert.equal(zmiana('+13').moja, 2);
  assert.equal(zmiana('+13').przeciwnika, -2);
  assert.equal(zmiana('R').moja, 2);
  assert.equal(zmiana('-R').moja, -2);
});

test('seria podwaja zmiane zwyciezcy i tylko jego', () => {
  // przypadek Czarka z przykladu na stronie: +15 w czwartej grze z rzedu
  const z = zmiana('+15', { seria: true });
  assert.equal(z.moja, 4, '+2 za wyrazna wygrana, razy dwa za serie');
  assert.equal(z.przeciwnika, -2, 'przegrany traci tyle, ile zwykle');
  // seria zwyciezcy dziala tak samo, gdy to on wpisuje przegrana
  const przegrana = zmiana('-15', { seria: true });
  assert.equal(przegrana.moja, -2);
  assert.equal(przegrana.przeciwnika, 4);
});

test('gra kalibracyjna dzieli wynik nowego gracza, w strone zera', () => {
  const moja = zmiana('+15', { kalibracja: { kto: 'ja', numer: 2 } });
  assert.equal(moja.moja, 7, '+15 / 2 to +7');
  assert.equal(moja.przeciwnika, -1, 'przeciwnik dokladnie ±1, bez ±2');
  const jego = zmiana('-15', { kalibracja: { kto: 'on', numer: 2 } });
  assert.equal(jego.przeciwnika, 7, 'to on jest nowy i to on dzieli');
  assert.equal(jego.moja, -1);
  assert.equal(zmiana('-15', { kalibracja: { kto: 'ja', numer: 2 } }).moja, -7, '−15 / 2 to −7');
});

test('kalibracja nie zna podwojen ani serii', () => {
  const z = zmiana('+15', { seria: true, kalibracja: { kto: 'ja', numer: 1 } });
  assert.equal(z.moja, 15, 'pierwsza poprawka jest pelna');
  assert.equal(z.przeciwnika, -1);
  assert.ok(z.uwagi.some((u) => u.includes('poza serią')));
});

test('poddanej gry nie ma czym dzielic, wiec nie jest kalibracyjna', () => {
  const z = zmiana('R', { kalibracja: { kto: 'ja', numer: 3 } });
  assert.equal(z.moja, 2, 'liczy sie jak zwykla wygrana przez poddanie');
  assert.ok(z.uwagi.some((u) => u.includes('poddaniem')));
});

test('znak wypisuje sie tak, jak stoi na karcie', () => {
  assert.equal(zeZnakiem(4), '+4');
  assert.equal(zeZnakiem(-2), '-2');
  assert.equal(zeZnakiem(0), '0');
});
