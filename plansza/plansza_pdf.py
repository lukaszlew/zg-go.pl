#!/usr/bin/env python3
"""Plansza rankingowa klubu Semedori — wydruk na laminat magnetyczny.

Uruchomienie: python3 plansza/plansza_pdf.py   (zapisuje plansza/plansza.pdf w skali 1:1)

Uklad: naglowek jednym pasem — nazwa klubu z logo po lewej, tytul "Ranking
Siły", tabele wyrownania (te same co na karcie gracza, z karta_pdf.draw_siatka;
9x9 pod para 19x19/13x13) dosuniete w prawo do kodow QR (zasady rankingu
u gory, pod nimi Discord i opinia w Mapach Google) — pod nim siatka 10x6 kratek
dla sil 1-60: wiersze po dziesiec, dolny 1-10, gorny 51-60, im wyzej tym
silniejszy; ostatnia kratka to otwarte "60+". Na dole zaproszenie dla nowych.
Nazwiska wisza na magnesach 80x30 mm wewnatrz kratek: kratka 90 mm szerokosci
(5 mm luzu z boku) i 100 mm wysokosci (pasek z numerem 30 mm + pole 70 mm,
czyli dwa magnesy z 10 mm luzu).

Szerokosc wydruku musi zmiescic sie w 1000 mm (szerokosc rolki laminatu).
Wymaga: reportlab, czcionki DejaVu (pakiet fonts-dejavu).
"""

import re
import sys
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
SILA = HexColor("#2e7d32")              # --kolor-sily: numery sil

FONT = "DejaVu"
FONT_BOLD = "DejaVu-Bold"
FONT_SERIF = "DejaVu-Serif"
FONT_SERIF_BOLD = "DejaVu-Serif-Bold"
FONT_RANKING = "Lato-Black"             # bezszeryfowy kontrast dla "Ranking Siły"

MAKS_SZEROKOSC = 1000 * mm              # szerokosc rolki laminatu magnetycznego

MAGNES_W, MAGNES_H = 80 * mm, 30 * mm   # magnes z nazwiskiem gracza
KRATKA_SZER = 90 * mm                   # magnes + 5 mm luzu z kazdej strony
POLE = 70 * mm                          # puste pole: dwa magnesy + 10 mm luzu
PASEK = 30 * mm                         # pasek z numerem u gory kratki
KRATKA_WYS = PASEK + POLE               # razem 100 mm
ODSTEP = 8 * mm                         # przerwa miedzy kratkami
PROMIEN = 3 * mm                        # zaokraglenie rogow kratek
KRESKA = 0.5 * mm                       # grubosc krawedzi kratek
KOLUMNY = 10                            # wiersz to pelna dziesiatka sil
WIERSZE = 6                             # 1-10 na dole ... 51-60+ na gorze

SIATKA_W = KOLUMNY * KRATKA_SZER + (KOLUMNY - 1) * ODSTEP
PAGE_W = 1000 * mm                      # cala szerokosc rolki, na styk
MARGINES_BOK = (PAGE_W - SIATKA_W) / 2
MARGINES = 24 * mm                      # gorny i dolny
NAGLOWEK_H = 128 * mm                   # nazwa klubu, Ranking Siły, tabele i kody QR
SEKCJA = 16 * mm                        # przerwa miedzy sekcjami

assert KRATKA_SZER > MAGNES_W, "magnes nie wchodzi w kratke na szerokosc"
assert POLE > 2 * MAGNES_H, "dwa magnesy nie wchodza w puste pole kratki"
assert MARGINES_BOK > 0, f"siatka szersza niz rolka: {SIATKA_W / mm:.0f} mm"


def wymiary_siatki(plansza: str) -> tuple[float, float]:
    """(szerokosc, wysokosc) jednej siatki wyrownania w jednostkach karty gracza."""
    pola = siatka(plansza)
    jency = len({j for j, _ in pola})
    ruchy = len({r for _, r in pola})
    return (jency * karta_pdf.KRATKA_W + karta_pdf.BRZEG_W,
            (ruchy + 2) * karta_pdf.WIERSZ_H)


# Trzy siatki wyrownania z karty gracza, w naglowku. Skala stala, dobrana pod
# czytelnosc (cyfry okolo 5 mm).
WYR_SKALA = 2.5

QR = 40 * mm                            # bok kodu QR w naglowku
NOTKA_H = 20 * mm                       # zaproszenie dla nowych pod siatka

PAGE_H = (MARGINES + NAGLOWEK_H + SEKCJA
          + WIERSZE * KRATKA_WYS + (WIERSZE - 1) * ODSTEP
          + NOTKA_H + MARGINES)

NUMER_FS = 62                           # numer sily na pasku kratki (cyfry ~22 mm)
TYTUL_FS = 120                          # "Semedori"
PODTYTUL_FS = 40                        # "Gramy w Go w Zielonej Górze"
ADRES_FS = 36                           # zg-go.pl nad kodami QR
RANKING_FS = 54                         # "Ranking Siły" na lewo od tabel
NAZWA_WCIECIE = 28 * mm                 # blok nazwy z logo odsuniety od lewego marginesu
NOTKA_FS = 20                           # zaproszenie dla nowych pod siatka
QR_PODPIS_FS = 12
QR_GAP = 14 * mm                        # odstep miedzy kodami w rzedzie
QR_PODPIS_ODSTEP = 6 * mm               # kod -> jego podpis
QR_RZAD_H = QR + 12 * mm                # kod z podpisem
ADRES_ODSTEP = 22 * mm                  # adres -> gorna krawedz pierwszego kodu
LOGO = 80 * mm
TABELA_GAP = 12 * mm                    # tabele wyrownania stoja kolo siebie

NOTKA = "pierwszy raz?  nauczymy cię zasad w 15 minut"
KODY_QR: list[tuple[str, str]] = [
    ("https://zg-go.pl/ranking.html", "zasady rankingu"),
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


def sciezka_logo(d: str) -> list[tuple[str, list[float]]]:
    """Rozbija atrybut d na komendy; logo uzywa wylacznie absolutnych M, L, C i Z."""
    czesci = re.findall(r"([A-Za-z])([^A-Za-z]*)", d)
    nieznane = {cmd for cmd, _ in czesci} - set("MLCZ")
    assert not nieznane, f"nieobslugiwane komendy SVG w logo: {nieznane}"
    return [(cmd, [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", args)]) for cmd, args in czesci]


def rysuj_logo(c: Canvas, x0: float, y0: float, rozmiar: float) -> None:
    """Rysuje img/logo.svg (winogrono ZG) w kwadracie o boku rozmiar, lewy dolny rog w (x0, y0)."""
    svg = (REPO / "img" / "logo.svg").read_text()
    vb = [float(x) for x in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
    sciezki = re.findall(r'<path d="([^"]+)"([^/]*)/>', svg)
    assert len(sciezki) == 2, f"logo.svg ma {len(sciezki)} sciezek zamiast 2"
    skala = rozmiar / vb[2]

    def pkt(x: float, y: float) -> tuple[float, float]:
        return x0 + (x - vb[0]) * skala, y0 + rozmiar - (y - vb[1]) * skala

    for d, atrybuty in sciezki:
        p = c.beginPath()
        for cmd, args in sciezka_logo(d):
            if cmd == "M":
                assert len(args) == 2
                p.moveTo(*pkt(args[0], args[1]))
            elif cmd == "L":
                assert len(args) == 2
                p.lineTo(*pkt(args[0], args[1]))
            elif cmd == "C":
                assert len(args) % 6 == 0
                for i in range(0, len(args), 6):
                    p.curveTo(*pkt(args[i], args[i + 1]), *pkt(args[i + 2], args[i + 3]),
                              *pkt(args[i + 4], args[i + 5]))
            else:
                p.close()
        wypelniona = 'fill="none"' not in atrybuty
        if wypelniona:
            c.setFillColor(INK)
            c.drawPath(p, stroke=0, fill=1)
        else:
            c.setStrokeColor(INK)
            c.setLineWidth(0.363 * skala)
            c.drawPath(p, stroke=1, fill=0)


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


def rysuj_kratke(c: Canvas, x: float, y: float, w: float, h: float, etykieta: str,
                 czcionka: str, fs: float, pasek: HexColor, kolor: HexColor) -> None:
    """Biala kratka z kolorowym paskiem i etykieta u gory; (x, y) to lewy dolny rog."""
    c.setFillColor(CARD)
    c.drawPath(zaokraglony(c, x, y, w, h, PROMIEN), stroke=0, fill=1)
    c.saveState()
    c.clipPath(zaokraglony(c, x, y, w, h, PROMIEN), stroke=0, fill=0)
    c.setFillColor(pasek)
    c.rect(x, y + h - PASEK, w, PASEK, stroke=0, fill=1)
    c.restoreState()
    c.setStrokeColor(INK)
    c.setLineWidth(KRESKA)
    c.line(x, y + h - PASEK, x + w, y + h - PASEK)
    c.drawPath(zaokraglony(c, x, y, w, h, PROMIEN), stroke=1, fill=0)
    c.setFillColor(kolor)
    c.setFont(czcionka, fs)
    wys_cyfr = 0.72 * fs                # przyblizona wysokosc wersalikow DejaVu
    c.drawCentredString(x + w / 2, y + h - PASEK + (PASEK - wys_cyfr) / 2, etykieta)


def rysuj_qr(c: Canvas, srodek_x: float, gora_y: float, url: str, podpis: str) -> None:
    """Kod QR z podpisem pod spodem, wysrodkowany na srodek_x, gorna krawedz w gora_y."""
    karta_pdf.draw_qr(c, srodek_x - QR / 2, gora_y - QR, QR, url)
    c.setFillColor(MUTED)
    c.setFont(FONT, QR_PODPIS_FS)
    c.drawCentredString(srodek_x, gora_y - QR - QR_PODPIS_ODSTEP, podpis)


def rysuj_naglowek(c: Canvas, gora_y: float) -> None:
    """Jeden pas: nazwa klubu z logo po lewej, tytul Ranking Siły, tabele
    wyrownania (9x9 pod para 19x19/13x13) dosuniete w prawo, kody QR na koncu."""
    tytul = "Semedori"
    podtytul = "Gramy w Go w Zielonej Górze"
    adres = "zg-go.pl"
    przerwa = 10 * mm
    (w19, h19), (w13, h13), (w9, h9) = (
        tuple(w * WYR_SKALA for w in wymiary_siatki(p)) for p in PLANSZE)
    grupa_w = max(w19 + TABELA_GAP + w13, w9)
    grupa_h = max(h19, h13) + TABELA_GAP + h9
    assert grupa_h <= NAGLOWEK_H, f"tabele wyzsze niz naglowek: {grupa_h / mm:.0f} mm"

    # Kody QR dosuniete do prawej, w dwoch rzedach: zasady rankingu same u gory,
    # bo po to plansza wisi, a Discord i Mapy pod spodem. Szerokosc bloku wyznacza
    # szerszy, dolny rzad; gorny kod stoi na jego srodku.
    gorny, dolny = KODY_QR[:1], KODY_QR[1:]
    qr_w = len(dolny) * QR + (len(dolny) - 1) * QR_GAP
    qr_blok_h = ADRES_ODSTEP + 2 * QR_RZAD_H
    assert qr_blok_h <= NAGLOWEK_H, f"kody QR wyzsze niz naglowek: {qr_blok_h / mm:.0f} mm"
    x_qr = PAGE_W - MARGINES_BOK - qr_w
    gora_bloku = gora_y - (NAGLOWEK_H - qr_blok_h) / 2
    c.setFillColor(ACCENT)
    c.setFont(FONT_SERIF_BOLD, ADRES_FS)
    c.drawCentredString(x_qr + qr_w / 2, gora_bloku - 14 * mm, adres)
    y_rzedu = gora_bloku - ADRES_ODSTEP
    for rzad in (gorny, dolny):
        szer = len(rzad) * QR + (len(rzad) - 1) * QR_GAP
        x = x_qr + (qr_w - szer) / 2
        for url, podpis in rzad:
            rysuj_qr(c, x + QR / 2, y_rzedu, url, podpis)
            x += QR + QR_GAP
        y_rzedu -= QR_RZAD_H

    # tabele wyrownania tuz na lewo od kodow QR
    x_tabel = x_qr - 24 * mm - grupa_w
    gora_grupy = gora_y - (NAGLOWEK_H - grupa_h) / 2
    gorny_w = w19 + TABELA_GAP + w13
    pozycje = [(x_tabel + (grupa_w - gorny_w) / 2, gora_grupy, PLANSZE[0]),
               (x_tabel + (grupa_w - gorny_w) / 2 + w19 + TABELA_GAP, gora_grupy, PLANSZE[1]),
               (x_tabel + (grupa_w - w9) / 2, gora_grupy - max(h19, h13) - TABELA_GAP, PLANSZE[2])]
    for tab_x, tab_y, plansza in pozycje:
        c.saveState()
        c.translate(tab_x, tab_y)
        c.scale(WYR_SKALA, WYR_SKALA)
        karta_pdf.draw_siatka(c, 0, 0, plansza)
        c.restoreState()

    # nazwa klubu po lewej, wysrodkowana w pionie pasa
    x = MARGINES_BOK + NAZWA_WCIECIE
    tytul_w = pdfmetrics.stringWidth(tytul, FONT_SERIF_BOLD, TYTUL_FS)
    nazwa_w = LOGO + przerwa + tytul_w
    nazwa_h = LOGO + 22 * mm            # wiersz logo+tytul, pod nim podtytul
    gora_nazwy = gora_y - (NAGLOWEK_H - nazwa_h) / 2
    rysuj_logo(c, x, gora_nazwy - LOGO, LOGO)
    c.setFillColor(INK)
    c.setFont(FONT_SERIF_BOLD, TYTUL_FS)
    c.drawString(x + LOGO + przerwa, gora_nazwy - LOGO / 2 - 0.36 * TYTUL_FS, tytul)
    c.setFillColor(CIEMNY)
    c.setFont(FONT_SERIF, PODTYTUL_FS)
    c.drawCentredString(x + nazwa_w / 2, gora_nazwy - LOGO - 18 * mm, podtytul)

    # Ranking Siły miedzy nazwa a tabelami, na wysokosci srodka tabelki 9x9
    srodek_rankingu = (x + nazwa_w + x_tabel) / 2
    ranking_w = pdfmetrics.stringWidth("Ranking Siły", FONT_RANKING, RANKING_FS)
    assert srodek_rankingu - ranking_w / 2 > x + nazwa_w + 6 * mm, \
        "Ranking Siły nachodzi na nazwe klubu"
    srodek_9x9 = gora_grupy - max(h19, h13) - TABELA_GAP - h9 / 2
    c.setFillColor(INK)
    c.setFont(FONT_RANKING, RANKING_FS)
    c.drawCentredString(srodek_rankingu, srodek_9x9 - 0.36 * RANKING_FS, "Ranking Siły")


def generuj(sciezka: Path) -> None:
    assert PAGE_W <= MAKS_SZEROKOSC, f"wydruk {PAGE_W / mm:.0f} mm szerszy niz rolka laminatu"
    zarejestruj_czcionki()
    c = Canvas(str(sciezka), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Plansza rankingowa Semedori")
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    rysuj_naglowek(c, PAGE_H - MARGINES)

    gora_siatki = PAGE_H - MARGINES - NAGLOWEK_H - SEKCJA
    for wiersz in range(WIERSZE):
        y = gora_siatki - (wiersz + 1) * KRATKA_WYS - wiersz * ODSTEP
        for kolumna in range(KOLUMNY):
            sila = 10 * (WIERSZE - 1 - wiersz) + kolumna + 1
            x = MARGINES_BOK + kolumna * (KRATKA_SZER + ODSTEP)
            # pelne dziesiatki to kamienie milowe: zielony pasek, biala cyfra;
            # skala jest otwarta z gory, wiec ostatnia kratka zbiera wszystko od 60 wzwyz
            prog = sila % 10 == 0
            etykieta = "60+" if sila == 60 else str(sila)
            rysuj_kratke(c, x, y, KRATKA_SZER, KRATKA_WYS, etykieta, FONT_BOLD, NUMER_FS,
                         SILA if prog else RULE, CARD if prog else SILA)

    dol_siatki = gora_siatki - WIERSZE * KRATKA_WYS - (WIERSZE - 1) * ODSTEP
    c.setFillColor(MUTED)
    c.setFont(FONT_SERIF, NOTKA_FS)
    c.drawCentredString(PAGE_W / 2, dol_siatki - NOTKA_H + 6 * mm, NOTKA)
    assert abs(dol_siatki - NOTKA_H - MARGINES) < 0.01, \
        f"siatka nie domyka strony: {(dol_siatki - NOTKA_H) / mm:.1f} mm"
    c.showPage()
    c.save()


if __name__ == "__main__":
    generuj(REPO / "plansza" / "plansza.pdf")
    print(f"plansza/plansza.pdf: {PAGE_W / mm:.0f} x {PAGE_H / mm:.0f} mm")
