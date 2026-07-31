/* Testy klasyfikacji klikniec z analityka.js.
 *
 * Odpalanie:  node --test tools/test_analityka.mjs
 *
 * Nazwy zdarzen sa jedynym, co widac potem w panelu Umami, i zmiana literki w
 * nazwie rozbija ciag danych na dwa slupki bez zadnego ostrzezenia. Stad testy
 * na doslowne napisy, a nie na "cos sie zwrocilo".
 *
 * Import samego modulu nie tyka DOM-u: wstrzykiwanie licznikow i naslychy
 * siedza za `if (typeof document !== 'undefined')`, tak jak w spotkania.js.
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { adresyDostawcow, idZCiasteczka, nazwaKlikniecia } from '../analityka.js';

const GOSPODARZ = 'zg-go.pl';

const nazwa = (adres, wMenu = false) => nazwaKlikniecia(adres, GOSPODARZ, wMenu);

test('pobranie karty gracza jest zdarzeniem', () => {
  assert.equal(nazwa('https://zg-go.pl/karta.pdf'), 'plik: karta.pdf');
  assert.equal(nazwa('https://zg-go.pl/karta-przyklad.pdf'), 'plik: karta-przyklad.pdf');
});

test('wyjscie na cudzy serwis nazywa sie jego domena, bez www', () => {
  assert.equal(nazwa('https://www.youtube.com/watch?v=WXuK6gekU1Y'), 'wyjscie: youtube.com');
  assert.equal(nazwa('https://online-go.com/'), 'wyjscie: online-go.com');
  assert.equal(nazwa('https://discord.gg/abc123'), 'wyjscie: discord.gg');
});

test('mail i kalendarz maja wlasne nazwy, bo nie sa strona', () => {
  assert.equal(nazwa('mailto:klub@zg-go.pl'), 'mail');
  assert.equal(nazwa('webcal://calendar.google.com/calendar/ical/x'), 'kalendarz');
});

test('przejscie miedzy podstronami nie jest zdarzeniem — widac je w odslonach', () => {
  assert.equal(nazwa('https://zg-go.pl/ranking.html'), null);
  assert.equal(nazwa('https://zg-go.pl/ranking.html#kalkulator'), null);
  assert.equal(nazwa('https://zg-go.pl/'), null);
});

test('to samo przejscie z menu juz jest — mowi, ktoredy ludzie chodza', () => {
  assert.equal(nazwa('https://zg-go.pl/ranking.html', true), 'menu: ranking.html');
  assert.equal(nazwa('https://zg-go.pl/', true), 'menu: index.html');
});

test('plik na cudzym serwerze liczy sie jako wyjscie, nie jako pobranie', () => {
  assert.equal(nazwa('https://example.com/cennik.pdf'), 'wyjscie: example.com');
});

test('identyfikator wylawiamy z ciasteczek po pelnej nazwie', () => {
  assert.equal(idZCiasteczka('semedori-id=abc-123'), 'abc-123');
  assert.equal(idZCiasteczka('inne=1; semedori-id=abc-123; jeszcze=2'), 'abc-123');
});

test('brak naszego ciasteczka to null, a nie cudza wartosc', () => {
  assert.equal(idZCiasteczka(''), null);
  assert.equal(idZCiasteczka('inne=1; jeszcze=2'), null);
  /* Nazwa musi zgadzac sie w calosci — inaczej pierwsze ciasteczko o zblizonej
   * nazwie podstawiloby goscowi cudzy identyfikator. */
  assert.equal(idZCiasteczka('semedori-identyfikator=nie-ten'), null);
});

test('lista uslug w polityce prywatnosci powstaje z adresow skryptow', () => {
  /* Dzieki temu dopisanie licznika do DOSTAWCY aktualizuje polityke samo —
   * nazwa uslugi nie jest nigdzie przepisana recznie. */
  assert.deepEqual(adresyDostawcow([
    { src: 'https://cloud.umami.is/script.js', 'data-website-id': 'x' },
    { src: 'https://static.cloudflareinsights.com/beacon.min.js', type: 'module' },
  ]), ['cloud.umami.is', 'static.cloudflareinsights.com']);
});

test('nazwa zdarzenia miesci sie w limicie Umami (50 znakow)', () => {
  const najdluzsze = [
    nazwa('https://zg-go.pl/karta-wycinek-bianka.svg'),
    nazwa('https://www.europeangodatabase.eu/EGD/'),
    nazwa('https://zg-go.pl/hikaru-no-go.html', true),
  ];
  for (const n of najdluzsze) assert.ok(n.length <= 50, `za dluga nazwa: ${n}`);
});
