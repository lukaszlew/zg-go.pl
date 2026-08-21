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

import { KROK, POLOWKA, ROWNA_JENCY, parsujWynik, stopnie, wyrownanie, zapisJencow, zeZnakiem, zmianaStopni } from '../wyrownanie.js';

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
      // Ponizej pierwszego wyrownania klub trzyma plaskie 6 jencow gry rownej,
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
      assert.equal(w.jency, ROWNA_JENCY, 'na karcie stoi jedna liczba: −6,5');
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

test('wyrazna wygrana daje caly stopien zwyciezcy, ale nie zabiera przegranemu wiecej', () => {
  assert.equal(zmiana('+19').moja, POLOWKA, 'dziewietnascie to jeszcze zwykla wygrana');
  assert.equal(zmiana('+20').moja, 1);
  assert.equal(zmiana('+20').przeciwnika, -POLOWKA, 'przegrany traci pol stopnia zawsze');
  assert.equal(zmiana('R').moja, 1);
  assert.equal(zmiana('-R').moja, -POLOWKA, 'to ja sie poddalem: pol stopnia w dol');
  assert.equal(zmiana('-R').przeciwnika, 1);
  // Ranking przestaje byc zerowy: wyrazna wygrana dodaje klubowi pol stopnia.
  const wyrazna = zmiana('+20');
  assert.equal(wyrazna.moja + wyrazna.przeciwnika, POLOWKA);
});

test('gra kalibracyjna liczy sie nowemu graczowi podwojnie, przeciwnikowi wcale', () => {
  const moja = zmiana('+5', { kalibracja: { kto: 'ja' } });
  assert.equal(moja.moja, 1, 'dwa razy tyle, co zwykla wygrana');
  assert.equal(moja.przeciwnika, 0, 'przeciwnik przy P nie zmienia swoich stopni');
  const jego = zmiana('-5', { kalibracja: { kto: 'on' } });
  assert.equal(jego.przeciwnika, 1, 'to on jest kalibrowany i to jemu sie liczy');
  assert.equal(jego.moja, 0);
  assert.equal(zmiana('-5', { kalibracja: { kto: 'ja' } }).moja, -1,
    'w dol tak samo — strzelona liczba bywa za wysoka rownie dobrze jak za niska');
});

test('wyrazny wynik w grze kalibracyjnej to ±2, po obu stronach tak samo', () => {
  assert.equal(zmiana('+25', { kalibracja: { kto: 'ja' } }).moja, 2);
  assert.equal(zmiana('-25', { kalibracja: { kto: 'ja' } }).moja, -2);
  assert.equal(zmiana('R', { kalibracja: { kto: 'ja' } }).moja, 2, 'poddanie liczy sie jak wyrazna');
  assert.equal(zmiana('+15', { kalibracja: { kto: 'ja' } }).moja, 1, 'pietnascie to jeszcze zwykla');
  assert.equal(zmiana('+25', { kalibracja: { kto: 'ja' } }).przeciwnika, 0, 'przeciwnika nie rusza nic');
});

test('stopnie pisze sie polowkami, tak jak stawia sie je na karcie', () => {
  assert.equal(stopnie(0), '0');
  assert.equal(stopnie(0.5), '½');
  assert.equal(stopnie(1), '1');
  assert.equal(stopnie(1.5), '1½');
  assert.equal(stopnie(-0.5), '−½');
  assert.equal(zeZnakiem(POLOWKA), '+½', 'typowa zmiana po grze');
  assert.equal(zeZnakiem(-2), '−2');
  assert.equal(zeZnakiem(0), '0');
});

test('jency ida w punktach, wiec polowka jest przecinkiem, a nie ulamkiem', () => {
  assert.equal(zapisJencow(ROWNA_JENCY), '−6,5');
  assert.equal(zapisJencow(0), '0');
  assert.equal(zapisJencow(5), '5');
});
