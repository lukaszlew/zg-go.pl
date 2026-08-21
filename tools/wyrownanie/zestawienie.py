#!/usr/bin/env python3
"""Zrodla obok siebie — jeden plik tekstowy na plansze.

Pliki JSON sa dla kodu: kazde zrodlo osobno, liczby dokladnie takie, jak stoja
w oryginale. Zestawienie jest dla czlowieka: jeden wiersz na roznice sil, po
parze kolumn na zrodlo, wszystko w jednej mierze — zeby bylo widac, gdzie zrodla sie
zgadzaja, a gdzie rozchodza.

Ta jedna miara to "ruchy": ile pierwszych ruchow z rzedu ma Czarny. Gra rowna to
1 ruch, bo Czarny i tak zaczyna. Zrodla licza to na dwa sposoby — BGA i LSG pisza
gre rowna jako 0 kamieni, Ishikura i Hunt jako 1 kamien — i dopiero po
sprowadzeniu do ruchow kolumny znacza to samo. Tak samo nazywa to reszta repo:
wyrownanie.js zwraca "ruchy", a tabela na ranking.html ma kolumne "pierwsze ruchy".

Komi zostaje takie, jak w zrodle, bo tu przeliczac nie ma czego: dodatnie idzie
do Bialego, ujemne do Czarnego.
"""

from pathlib import Path

from .tabela import KATALOG_PAKIETU, Tabela, rozbij

BRAK = "-"          # zrodlo nie siega tak daleko
ODSTEP = "   "      # miedzy kolumnami

ETYKIETY: dict[str, str] = {
    "zg": "Semedori",
    "bga": "BGA",
    "lsg": "LSG",
    "ishikura": "Ishikura",
    "hunt": "Hunt",
}


def plik_zestawienia(plansza: str) -> Path:
    """Sciezka pliku zestawienia — obok modulow, bo to material roboczy, nie strona."""
    return KATALOG_PAKIETU / f"zestawienie-{plansza}.txt"


def ruchy(kamienie: int) -> int:
    """Ile pierwszych ruchow z rzedu ma Czarny przy tylu kamieniach wyrownania.

    Zero kamieni i jeden kamien to ta sama gra rowna — Czarny stawia jeden kamien
    i oddaje ruch. Dopiero drugi kamien jest ruchem darmowym. Dlatego max(k, 1),
    a nie k albo k + 1: tabele licza od zera albo od jedynki, a ruchow zawsze tyle
    samo.
    """
    assert kamienie >= 0, f"kamieni nie moze byc ujemnie: {kamienie}"
    return max(kamienie, 1)


def _zrodel(ile: int) -> str:
    """Polska odmiana liczebnika: jedno zrodlo, 2-4 zrodla, 5 i wiecej zrodel."""
    if ile == 1:
        return "jedno zrodlo"
    mnoga = 2 <= ile % 10 <= 4 and not 12 <= ile % 100 <= 14
    return f"{ile} " + ("zrodla" if mnoga else "zrodel")


def _kolumna(naglowek: str, wartosci: list[float | None]) -> tuple[str, list[str]]:
    """Naglowek i komorki jednej kolumny, wszystkie tej samej szerokosci.

    Cyfry stoja jedna pod druga tak samo jak w plikach JSON: calosc dosuwa sie do
    prawej, ulamek do lewej, wiec ani minus, ani ".5" nie ruszaja kolumny.
    """
    pola = [rozbij(w) for w in wartosci if w is not None]
    assert pola, f"kolumna {naglowek} nie ma ani jednej liczby"
    szer_calosci = max(len(c) for c, _ in pola)
    szer_ulamka = max(len(u) for _, u in pola)

    def komorka(wartosc: float | None) -> str:
        if wartosc is None:
            return BRAK.rjust(szer_calosci) + " " * szer_ulamka
        calosc, ulamek = rozbij(wartosc)
        return f"{calosc:>{szer_calosci}}{ulamek:<{szer_ulamka}}"

    szerokosc = max(len(naglowek), szer_calosci + szer_ulamka)
    return naglowek.rjust(szerokosc), [komorka(w).rjust(szerokosc) for w in wartosci]


def zestawienie(plansza: str, zrodla_danych: tuple) -> str:
    """Caly plik zestawienia dla jednej planszy, z koncowa nowa linia."""
    tabele: dict[str, Tabela] = {m.NAZWA: m.TABELE[plansza] for m in zrodla_danych}
    roznice = list(range(max(len(t) for t in tabele.values())))

    naglowki, kolumny, nad_kolumnami = [], [], []
    naglowek, komorki = _kolumna("roznica", [float(r) for r in roznice])
    naglowki.append(naglowek)
    kolumny.append(komorki)
    nad_kolumnami.append(" " * len(naglowek))

    for modul in zrodla_danych:
        wiersze = {r: (k, komi) for r, k, komi in tabele[modul.NAZWA]}
        para = [
            _kolumna("ruchy", [float(ruchy(wiersze[r][0])) if r in wiersze else None for r in roznice]),
            _kolumna("komi", [wiersze[r][1] if r in wiersze else None for r in roznice]),
        ]
        naglowki.extend(n for n, _ in para)
        kolumny.extend(k for _, k in para)
        # Nazwa zrodla stoi nad swoja para kolumn, wysrodkowana na ich laczna szerokosc.
        nad_kolumnami.append(
            ETYKIETY[modul.NAZWA].center(sum(len(n) for n, _ in para) + len(ODSTEP))
        )

    linie = [
        ODSTEP.join(nad_kolumnami).rstrip(),
        ODSTEP.join(naglowki),
        *(ODSTEP.join(kolumna[numer] for kolumna in kolumny) for numer in range(len(roznice))),
    ]

    adresy = "\n".join(
        f"  {ETYKIETY[m.NAZWA]:9s} {m.ZRODLA[plansza]}" for m in zrodla_danych
    )
    # Zdanie o myslnikach ma stac tylko wtedy, gdy myslniki naprawde sa — przy
    # jednym zrodle albo przy tabelach rownej dlugosci nie ma o czym mowic.
    o_myslnikach = [f"Para {BRAK} {BRAK} znaczy, ze tabela zrodla konczy sie wczesniej."] * (
        len({len(t) for t in tabele.values()}) > 1
    )
    akapity = [
        f"Wyrownanie na planszy {plansza} — " + (
            f"tabela: {ETYKIETY[zrodla_danych[0].NAZWA]}."
            if len(zrodla_danych) == 1
            else f"{_zrodel(len(zrodla_danych))} obok siebie."
        ),
        '"ruchy" to liczba pierwszych ruchow z rzedu Czarnego: 1 to gra rowna, 2 to jeden\n'
        "ruch darmowy, i tak dalej. Zrodla licza kamienie roznie — jedne pisza gre rowna\n"
        "jako 0 kamieni, inne jako 1 — wiec tutaj sa sprowadzone do jednej miary i kolumny\n"
        "znacza to samo. Komi stoi tak, jak w zrodle: dodatnie idzie do Bialego, ujemne do\n"
        "Czarnego. " + " ".join(o_myslnikach),
        "Plik jest generowany — poprawki wchodza do tools/wyrownanie/*.py, nie tutaj.",
        adresy,
        "\n".join(linie),
    ]
    return "\n\n".join(a.rstrip() for a in akapity) + "\n"
