#!/usr/bin/env python3
"""Tablica rankingowa klubu Semedori — biblioteka + generator duzego wydruku.

Uruchomienie: python3 tablica/tablica_pdf.py   (zapisuje tablica/tablica.pdf w skali 1:1)
Wariant na mala tablice magnetyczna generuje tablica/tablica_mala_pdf.py.

Uklad: naglowek jednym pasem — nazwa klubu z logo po lewej, tytul "Ranking
Siły", tabele wyrownania (te same co na karcie gracza, z karta_pdf.draw_siatka;
9x9 pod para 19x19/13x13) dosuniete w prawo do kodow QR (zasady rankingu
u gory, pod nimi Discord i opinia w Mapach Google) — pod nim siatka 10x6 kratek
dla sil 1-60: wiersze po dziesiec, dolny 1-10, gorny 51-60, im wyzej tym
silniejszy; ostatnia kratka to otwarte "60+". Na dole zaproszenie dla nowych.
Nazwiska wisza na magnesach wewnatrz kratek: kratka miesci magnes z 5 mm luzu
z boku, a jej puste pole — dwa magnesy z luzem.

Wszystkie wymiary i stopnie pisma siedza w dataclass Uklad; kazda rysujaca
funkcja dostaje uklad jawnie, wiec jeden kod obsluguje oba wydruki.
Wymaga: reportlab, czcionki DejaVu (pakiet fonts-dejavu).
"""

import sys
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfgen.pathobject import PDFPathObject

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import karta_pdf
from wyrownanie.tabela_html import PLANSZE, siatka

# paleta ze style.css — ta sama co strona i karta gracza
BG = HexColor("#f4e9cf")                # --bg: krem calej planszy
INK = HexColor("#1a1a1a")               # --fg: krawedzie i logo
MUTED = HexColor("#666666")             # --muted: podpisy i notki
CIEMNY = HexColor("#444444")            # podtytul: ciemniejszy od --muted
ACCENT = HexColor("#9c2a2a")            # --accent: wyeksponowany adres zg-go.pl
RULE = HexColor("#d9c896")              # --rule: zloty pasek z numerem kratki
CARD = HexColor("#ffffff")              # --card: wnetrze kratek
SILA = karta_pdf.KOLOROWA.sila          # kolor sily, ten sam co na karcie

FONT = "DejaVu"
FONT_BOLD = "DejaVu-Bold"
FONT_SERIF = "DejaVu-Serif"
FONT_SERIF_BOLD = "DejaVu-Serif-Bold"
FONT_RANKING = "Lato-Black"             # bezszeryfowy kontrast dla "Ranking Siły"

KOLUMNY = 10                            # wiersz to pelna dziesiatka sil
WIERSZE = 6                             # 1-10 na dole ... 51-60+ na gorze
PROMIEN = 3 * mm                        # zaokraglenie rogow kratek
KRESKA = 0.5 * mm                       # grubosc krawedzi kratek


def wymiary_siatki(plansza: str) -> tuple[float, float]:
    """(szerokosc, wysokosc) jednej siatki wyrownania w jednostkach karty gracza."""
    pola = siatka(plansza)
    jency = len({j for j, _ in pola})
    ruchy = len({r for _, r in pola})
    return (jency * karta_pdf.KRATKA_W + karta_pdf.BRZEG_W,
            (ruchy + 2) * karta_pdf.WIERSZ_H)


@dataclass(frozen=True)
class Uklad:
    """Wymiary i stopnie pisma jednego wydruku tablicy; rozklad jest wspolny.

    Dwie instancje: DUZA (rolka laminatu 1000 mm) i MALA w tablica_mala_pdf.py
    (mala tablica magnetyczna 67 x 93,5 cm). Pola pochodne licza sie same,
    a __post_init__ pilnuje, ze magnesy i strona miesza sie w zadane granice.
    """
    maks_w: float           # twarda granica szerokosci wydruku (rolka / tablica)
    maks_h: float           # twarda granica wysokosci wydruku
    page_w: float
    magnes_w: float         # magnes z nazwiskiem gracza
    magnes_h: float
    kratka_szer: float      # magnes + luz z kazdej strony
    pole: float             # puste pole kratki: dwa magnesy + luz
    pasek: float            # pasek z numerem u gory kratki
    odstep: float           # przerwa miedzy kratkami
    margines: float         # gorny i dolny
    naglowek_h: float       # nazwa klubu, Ranking Siły, tabele i kody QR
    sekcja: float           # przerwa miedzy sekcjami
    # Trzy siatki wyrownania z karty gracza, w naglowku; skala dobrana pod
    # czytelnosc z odleglosci, z jakiej czyta sie zawieszona tablice.
    wyr_skala: float
    qr: float               # bok kodu QR w naglowku
    notka_h: float          # zaproszenie dla nowych pod siatka
    numer_fs: float         # numer sily na pasku kratki
    tytul_fs: float         # "Semedori"
    podtytul_fs: float      # "Gramy w Go w Zielonej Górze"
    adres_fs: float         # zg-go.pl nad kodami QR
    ranking_fs: float       # "Ranking Siły" na lewo od tabel
    nazwa_wciecie: float    # blok nazwy z logo odsuniety od lewego marginesu
    notka_fs: float
    qr_podpis_fs: float
    qr_gap: float           # odstep miedzy kodami w rzedzie
    qr_podpis_odstep: float  # kod -> jego podpis
    adres_odstep: float     # adres -> gorna krawedz pierwszego kodu
    logo: float
    tabela_gap: float       # tabele wyrownania stoja kolo siebie

    @property
    def kratka_wys(self) -> float:
        return self.pasek + self.pole

    @property
    def siatka_w(self) -> float:
        return KOLUMNY * self.kratka_szer + (KOLUMNY - 1) * self.odstep

    @property
    def margines_bok(self) -> float:
        return (self.page_w - self.siatka_w) / 2

    @property
    def qr_rzad_h(self) -> float:
        return self.qr + self.qr_podpis_odstep + 6 * mm   # kod z podpisem

    @property
    def page_h(self) -> float:
        return (self.margines + self.naglowek_h + self.sekcja
                + WIERSZE * self.kratka_wys + (WIERSZE - 1) * self.odstep
                + self.notka_h + self.margines)

    def __post_init__(self) -> None:
        assert self.kratka_szer > self.magnes_w, "magnes nie wchodzi w kratke na szerokosc"
        assert self.pole > 2 * self.magnes_h, "dwa magnesy nie wchodza w puste pole kratki"
        assert self.margines_bok > 0, f"siatka szersza niz wydruk: {self.siatka_w / mm:.0f} mm"
        assert self.page_w <= self.maks_w, f"wydruk za szeroki: {self.page_w / mm:.0f} mm"
        assert self.page_h <= self.maks_h, f"wydruk za wysoki: {self.page_h / mm:.0f} mm"


DUZA = Uklad(
    maks_w=1000 * mm,                   # szerokosc rolki laminatu magnetycznego
    maks_h=1000 * mm,
    page_w=1000 * mm,                   # cala szerokosc rolki, na styk
    magnes_w=80 * mm, magnes_h=30 * mm,
    kratka_szer=90 * mm,
    pole=70 * mm,
    pasek=30 * mm,
    odstep=8 * mm,
    margines=24 * mm,
    naglowek_h=128 * mm,
    sekcja=16 * mm,
    wyr_skala=2.5,                      # cyfry okolo 5 mm
    qr=40 * mm,
    notka_h=20 * mm,
    numer_fs=62,                        # cyfry ~22 mm
    tytul_fs=120,
    podtytul_fs=40,
    adres_fs=36,
    ranking_fs=54,
    nazwa_wciecie=28 * mm,
    notka_fs=20,
    qr_podpis_fs=12,
    qr_gap=14 * mm,
    qr_podpis_odstep=6 * mm,
    adres_odstep=22 * mm,
    logo=80 * mm,
    tabela_gap=12 * mm,
)

NOTKA = "pierwszy raz?  nauczymy cię zasad w 15 minut"
KODY_QR: list[tuple[str, str]] = [
    ("https://zg-go.pl/ranking", "zasady rankingu"),
    ("https://discord.gg/EB5at7kM9v", "klubowy Discord"),
    ("https://maps.app.goo.gl/zrGynDtGVZLG2zVd7", "opinia w Mapach Google"),
]


def zarejestruj_czcionki() -> None:
    dejavu = Path("/usr/share/fonts/truetype/dejavu")
    assert dejavu.is_dir(), f"brak katalogu czcionek DejaVu: {dejavu}"
    pdfmetrics.registerFont(TTFont(FONT, str(dejavu / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(dejavu / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_SERIF, str(dejavu / "DejaVuSerif.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_SERIF_BOLD, str(dejavu / "DejaVuSerif-Bold.ttf")))
    lato = Path("/usr/share/fonts/truetype/lato")
    assert lato.is_dir(), f"brak katalogu czcionek Lato: {lato}"
    pdfmetrics.registerFont(TTFont(FONT_RANKING, str(lato / "Lato-Black.ttf")))


def zaokraglony(c: Canvas, x: float, y: float, w: float, h: float, r: float) -> PDFPathObject:
    p = c.beginPath()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.arcTo(x + w - 2 * r, y, x + w, y + 2 * r, 270, 90)
    p.lineTo(x + w, y + h - r)
    p.arcTo(x + w - 2 * r, y + h - 2 * r, x + w, y + h, 0, 90)
    p.lineTo(x + r, y + h)
    p.arcTo(x, y + h - 2 * r, x + 2 * r, y + h, 90, 90)
    p.lineTo(x, y + r)
    p.arcTo(x, y, x + 2 * r, y + 2 * r, 180, 90)
    p.close()
    return p


def rysuj_kratke(c: Canvas, u: Uklad, x: float, y: float, w: float, h: float, etykieta: str,
                 czcionka: str, fs: float, pasek: HexColor, kolor: HexColor) -> None:
    """Biala kratka z kolorowym paskiem i etykieta u gory; (x, y) to lewy dolny rog."""
    c.setFillColor(CARD)
    c.drawPath(zaokraglony(c, x, y, w, h, PROMIEN), stroke=0, fill=1)
    c.saveState()
    c.clipPath(zaokraglony(c, x, y, w, h, PROMIEN), stroke=0, fill=0)
    c.setFillColor(pasek)
    c.rect(x, y + h - u.pasek, w, u.pasek, stroke=0, fill=1)
    c.restoreState()
    c.setStrokeColor(INK)
    c.setLineWidth(KRESKA)
    c.line(x, y + h - u.pasek, x + w, y + h - u.pasek)
    c.drawPath(zaokraglony(c, x, y, w, h, PROMIEN), stroke=1, fill=0)
    c.setFillColor(kolor)
    c.setFont(czcionka, fs)
    wys_cyfr = 0.72 * fs                # przyblizona wysokosc wersalikow DejaVu
    c.drawCentredString(x + w / 2, y + h - u.pasek + (u.pasek - wys_cyfr) / 2, etykieta)


def rysuj_qr(c: Canvas, u: Uklad, srodek_x: float, gora_y: float, url: str, podpis: str) -> None:
    """Kod QR z podpisem pod spodem, wysrodkowany na srodek_x, gorna krawedz w gora_y."""
    karta_pdf.draw_qr(c, srodek_x - u.qr / 2, gora_y - u.qr, u.qr, url)
    c.setFillColor(MUTED)
    c.setFont(FONT, u.qr_podpis_fs)
    c.drawCentredString(srodek_x, gora_y - u.qr - u.qr_podpis_odstep, podpis)


def rysuj_naglowek(c: Canvas, u: Uklad, gora_y: float) -> None:
    """Jeden pas: nazwa klubu z logo po lewej, tytul Ranking Siły, tabele
    wyrownania (9x9 pod para 19x19/13x13) dosuniete w prawo, kody QR na koncu."""
    tytul = "Semedori"
    podtytul = "Gramy w Go w Zielonej Górze"
    adres = "zg-go.pl"
    przerwa = u.logo / 8
    (w19, h19), (w13, h13), (w9, h9) = (
        tuple(w * u.wyr_skala for w in wymiary_siatki(p)) for p in PLANSZE)
    grupa_w = max(w19 + u.tabela_gap + w13, w9)
    grupa_h = max(h19, h13) + u.tabela_gap + h9
    assert grupa_h <= u.naglowek_h, f"tabele wyzsze niz naglowek: {grupa_h / mm:.0f} mm"

    # Kody QR dosuniete do prawej, w dwoch rzedach: zasady rankingu same u gory,
    # bo po to tablica wisi, a Discord i Mapy pod spodem. Szerokosc bloku wyznacza
    # szerszy, dolny rzad; gorny kod stoi na jego srodku.
    gorny, dolny = KODY_QR[:1], KODY_QR[1:]
    qr_w = len(dolny) * u.qr + (len(dolny) - 1) * u.qr_gap
    qr_blok_h = u.adres_odstep + 2 * u.qr_rzad_h
    assert qr_blok_h <= u.naglowek_h, f"kody QR wyzsze niz naglowek: {qr_blok_h / mm:.0f} mm"
    x_qr = u.page_w - u.margines_bok - qr_w
    gora_bloku = gora_y - (u.naglowek_h - qr_blok_h) / 2
    c.setFillColor(ACCENT)
    c.setFont(FONT_SERIF_BOLD, u.adres_fs)
    c.drawCentredString(x_qr + qr_w / 2, gora_bloku - 0.39 * u.adres_fs - 4 * mm, adres)
    y_rzedu = gora_bloku - u.adres_odstep
    for rzad in (gorny, dolny):
        szer = len(rzad) * u.qr + (len(rzad) - 1) * u.qr_gap
        x = x_qr + (qr_w - szer) / 2
        for url, podpis in rzad:
            rysuj_qr(c, u, x + u.qr / 2, y_rzedu, url, podpis)
            x += u.qr + u.qr_gap
        y_rzedu -= u.qr_rzad_h

    # tabele wyrownania tuz na lewo od kodow QR
    x_tabel = x_qr - 2 * u.tabela_gap - grupa_w
    gora_grupy = gora_y - (u.naglowek_h - grupa_h) / 2
    gorny_w = w19 + u.tabela_gap + w13
    pozycje = [(x_tabel + (grupa_w - gorny_w) / 2, gora_grupy, PLANSZE[0]),
               (x_tabel + (grupa_w - gorny_w) / 2 + w19 + u.tabela_gap, gora_grupy, PLANSZE[1]),
               (x_tabel + (grupa_w - w9) / 2, gora_grupy - max(h19, h13) - u.tabela_gap, PLANSZE[2])]
    for tab_x, tab_y, plansza in pozycje:
        c.saveState()
        c.translate(tab_x, tab_y)
        c.scale(u.wyr_skala, u.wyr_skala)
        karta_pdf.draw_siatka(c, karta_pdf.KOLOROWA, 0, 0, plansza, "½")
        c.restoreState()

    # nazwa klubu po lewej, wysrodkowana w pionie pasa
    x = u.margines_bok + u.nazwa_wciecie
    tytul_w = pdfmetrics.stringWidth(tytul, FONT_SERIF_BOLD, u.tytul_fs)
    nazwa_w = u.logo + przerwa + tytul_w
    nazwa_h = u.logo + 0.65 * u.podtytul_fs + 8 * mm   # wiersz logo+tytul, pod nim podtytul
    gora_nazwy = gora_y - (u.naglowek_h - nazwa_h) / 2
    karta_pdf.rysuj_logo(c, karta_pdf.SEMEDORI.logo, x, gora_nazwy - u.logo, u.logo, INK)
    c.setFillColor(INK)
    c.setFont(FONT_SERIF_BOLD, u.tytul_fs)
    c.drawString(x + u.logo + przerwa, gora_nazwy - u.logo / 2 - 0.36 * u.tytul_fs, tytul)
    c.setFillColor(CIEMNY)
    c.setFont(FONT_SERIF, u.podtytul_fs)
    c.drawCentredString(x + nazwa_w / 2, gora_nazwy - u.logo - 0.45 * u.podtytul_fs - 4 * mm, podtytul)

    # Ranking Siły miedzy nazwa a tabelami, na wysokosci srodka tabelki 9x9
    srodek_rankingu = (x + nazwa_w + x_tabel) / 2
    ranking_w = pdfmetrics.stringWidth("Ranking Siły", FONT_RANKING, u.ranking_fs)
    assert srodek_rankingu - ranking_w / 2 > x + nazwa_w + 6 * mm, \
        "Ranking Siły nachodzi na nazwe klubu"
    srodek_9x9 = gora_grupy - max(h19, h13) - u.tabela_gap - h9 / 2
    c.setFillColor(INK)
    c.setFont(FONT_RANKING, u.ranking_fs)
    c.drawCentredString(srodek_rankingu, srodek_9x9 - 0.36 * u.ranking_fs, "Ranking Siły")


def generuj(sciezka: Path, u: Uklad) -> None:
    zarejestruj_czcionki()
    c = Canvas(str(sciezka), pagesize=(u.page_w, u.page_h))
    c.setTitle("Tablica rankingowa Semedori")
    c.setFillColor(BG)
    c.rect(0, 0, u.page_w, u.page_h, stroke=0, fill=1)

    rysuj_naglowek(c, u, u.page_h - u.margines)

    gora_siatki = u.page_h - u.margines - u.naglowek_h - u.sekcja
    for wiersz in range(WIERSZE):
        y = gora_siatki - (wiersz + 1) * u.kratka_wys - wiersz * u.odstep
        for kolumna in range(KOLUMNY):
            sila = 10 * (WIERSZE - 1 - wiersz) + kolumna + 1
            x = u.margines_bok + kolumna * (u.kratka_szer + u.odstep)
            # pelne dziesiatki to kamienie milowe: zielony pasek, biala cyfra;
            # skala jest otwarta z gory, wiec ostatnia kratka zbiera wszystko od 60 wzwyz
            prog = sila % 10 == 0
            etykieta = "60+" if sila == 60 else str(sila)
            rysuj_kratke(c, u, x, y, u.kratka_szer, u.kratka_wys, etykieta, FONT_BOLD,
                         u.numer_fs, SILA if prog else RULE, CARD if prog else SILA)

    dol_siatki = gora_siatki - WIERSZE * u.kratka_wys - (WIERSZE - 1) * u.odstep
    c.setFillColor(MUTED)
    c.setFont(FONT_SERIF, u.notka_fs)
    c.drawCentredString(u.page_w / 2, dol_siatki - u.notka_h + 0.3 * u.notka_h, NOTKA)
    assert abs(dol_siatki - u.notka_h - u.margines) < 0.01, \
        f"siatka nie domyka strony: {(dol_siatki - u.notka_h) / mm:.1f} mm"
    c.showPage()
    c.save()
    print(f"{sciezka.relative_to(REPO)}: {u.page_w / mm:.0f} x {u.page_h / mm:.0f} mm")


if __name__ == "__main__":
    generuj(REPO / "tablica" / "tablica.pdf", DUZA)
