/* Testy kalkulatora z wyrownanie.js.
 *
 * Odpalanie:  node --test tools/test_*.mjs   (albo `make test`)
 *
 * Najwazniejszy test zestawia kalkulator z tools/wyrownanie/zg.py: ta sama zasada
 * policzona dwa razy, w dwoch jezykach, na trzech planszach. Tego, czy tabela na
 * ranking.html zgadza sie z generatorem, pilnuje test po stronie Pythona.
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { KROK, POLOWKA, parsujWynik, stopnie, wyrownanie, zeZnakiem, zmianaStopni } from '../wyrownanie.js';

const STRONA = new URL('../ranking.html', import.meta.url);

/* Kalkulator i tools/wyrownanie/zg.py to dwa kody w dwoch jezykach liczace jedna
 * zasade. Test karmi oba tymi samymi stopniami i zada tych samych jencow — na
 * kazdej z trzech plansz, bo zasada jest jedna, a krok planszy inny. */
test('kalkulator zgadza sie z zg.py na kazdej planszy, wiersz po wierszu', () => {
  const dane = JSON.parse(readFileSync(new URL('./wyrownanie/wyrownanie-zg.json', import.meta.url), 'utf8'));
  assert.deepEqual(Object.keys(dane.tabele).sort(), Object.keys(KROK).sort(),
    'kalkulator zna dokladnie te plansze, co modul');
  for (const [plansza, tabela] of Object.entries(dane.tabele)) {
    assert.ok(tabela.length >= 15, `${plansza}: tabela ma siegac przynajmniej pietnastu stopni`);
    for (const [roznica, ruchy, komi] of tabela) {
      // "|| 0", bo -komi przy komi === 0 daje w JS -0, a deepStrictEqual odroznia
      // -0 od 0. Bez tego test pada na kazdej kratce z zerem jencow.
      const jency = -komi || 0;
      const w = wyrownanie(roznica, 0, plansza);
      // Ponizej pierwszego wyrownania klub trzyma plaskie 6 jencow (zasada 2),
      // a zg schodzi po jednym — tam porownujemy tylko to, ze gra jest rowna.
      if (jency < 0) {
        assert.equal(w.rowna, true, `${plansza}, roznica ${roznica}: gra rowna`);
        continue;
      }
      assert.deepEqual({ ruchy: w.ruchy, jency: w.jency }, { ruchy, jency },
        `${plansza}, roznica ${roznica} stopni`);
    }
  }
});

test('gra rowna siega tam, gdzie na danej planszy nie ma jeszcze czego dac', () => {
  // Na 9x9 stopien wart jest dwa punkty, wiec szesc jencow gry rownej starcza na
  // dwa i pol stopnia; na 19x19 stopien to caly ruch i pas konczy sie znacznie wczesniej.
  for (const [plansza, ostatnia] of [['9x9', 2.5], ['13x13', 1], ['19x19', 0]]) {
    for (const w of [wyrownanie(60 + ostatnia, 60, plansza), wyrownanie(60, 60 + ostatnia, plansza)]) {
      assert.equal(w.rowna, true, `${plansza}: roznica ${ostatnia} to jeszcze gra rowna`);
      assert.equal(w.ruchy, 1);
      assert.equal(w.jency, -6, 'Czarny odklada Bialemu szesciu jencow');
    }
    assert.equal(wyrownanie(60 + ostatnia + POLOWKA, 60, plansza).rowna, false,
      `${plansza}: pol stopnia dalej to juz wyrownanie`);
  }
});

test('rachunek biegnie dalej, kiedy tabela sie konczy', () => {
  const daleko = wyrownanie(100, 0, '9x9');
  assert.equal(daleko.ruchy, 1 + Math.floor((KROK['9x9'] * 100 - 6) / 13));
  assert.ok(daleko.jency >= 0 && daleko.jency < 13, 'jency to zawsze reszta z dzielenia');
  // Ta sama roznica stopni na wiekszej planszy to wiecej ruchow, nie wiecej jencow.
  assert.ok(wyrownanie(10, 0, '19x19').ruchy > wyrownanie(10, 0, '9x9').ruchy);
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

// --- zmiana stopni ---------------------------------------------------------------

const zmiana = (tekst, opcje) => zmianaStopni(parsujWynik(tekst), opcje);

test('zwykla wygrana to pol stopnia w gore i pol w dol', () => {
  assert.equal(zmiana('+5').moja, POLOWKA);
  assert.equal(zmiana('+5').przeciwnika, -POLOWKA);
  assert.equal(zmiana('-5').moja, -POLOWKA);
  assert.equal(zmiana('-5').przeciwnika, POLOWKA);
});

test('remis nie zmienia nic', () => {
  assert.deepEqual(
    { moja: zmiana('0').moja, przeciwnika: zmiana('0').przeciwnika }, { moja: 0, przeciwnika: 0 },
  );
});

test('wygrana o 20 punktow i poddanie daja caly stopien', () => {
  assert.equal(zmiana('+19').moja, POLOWKA, 'dziewietnascie to jeszcze zwykla wygrana');
  assert.equal(zmiana('+20').moja, 1);
  assert.equal(zmiana('+20').przeciwnika, -1);
  assert.equal(zmiana('R').moja, 1);
  assert.equal(zmiana('-R').moja, -1);
});

test('gra kalibracyjna mnozy zmiane nowego gracza, przeciwnik przy K dostaje ±pol', () => {
  const moja = zmiana('+5', { kalibracja: { kto: 'ja', mnoznik: 3 } });
  assert.equal(moja.moja, 1.5, 'pol stopnia razy mnoznik 3');
  assert.equal(moja.przeciwnika, -POLOWKA, 'przeciwnik przy K dokladnie ±pol stopnia');
  const jego = zmiana('-5', { kalibracja: { kto: 'on', mnoznik: 3 } });
  assert.equal(jego.przeciwnika, 1.5, 'to on jest nowy i to on mnozy');
  assert.equal(jego.moja, -POLOWKA);
  assert.equal(zmiana('-5', { kalibracja: { kto: 'ja', mnoznik: 3 } }).moja, -1.5, 'przegrana tez razy mnoznik');
});

test('mnoznik kalibracji kumuluje sie z ×2 za wyrazna wygrana i poddanie', () => {
  assert.equal(zmiana('+25', { kalibracja: { kto: 'ja', mnoznik: 4 } }).moja, 4, 'caly stopien razy 4');
  assert.equal(zmiana('+15', { kalibracja: { kto: 'ja', mnoznik: 4 } }).moja, 2, 'zwykla wygrana razy 4');
  assert.equal(zmiana('R', { kalibracja: { kto: 'ja', mnoznik: 2 } }).moja, 2, 'poddanie liczy sie jak zawsze');
  assert.equal(zmiana('+25', { kalibracja: { kto: 'ja', mnoznik: 4 } }).przeciwnika, -POLOWKA,
    'przeciwnika nie mnozy nic, nawet ×2');
});

test('stopnie pisze sie polowkami, tak jak stawia sie je na karcie', () => {
  assert.equal(stopnie(0), '0');
  assert.equal(stopnie(0.5), '½');
  assert.equal(stopnie(1), '1');
  assert.equal(stopnie(1.5), '1½');
  assert.equal(stopnie(-0.5), '-½');
  assert.equal(zeZnakiem(POLOWKA), '+½', 'typowa zmiana po grze');
  assert.equal(zeZnakiem(-2), '-2');
  assert.equal(zeZnakiem(0), '0');
});
