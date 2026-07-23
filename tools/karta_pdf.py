#!/usr/bin/env python3
"""Karta gracza klubu Semedori (pionowe A4) — biblioteka + generator karta.pdf.

Uruchomienie:  python3 tools/karta_pdf.py   (zapisuje pusta karte: karta.pdf w korzeniu repo)
Jako biblioteka: generuj_karte(sciezka, [KartaDane(...), ...]) — karta na strone,
z wypelnionym naglowkiem i wierszami gier (np. karty przykladowe).
Wymaga: reportlab, czcionki DejaVu (pakiet fonts-dejavu).
"""

from dataclasses import dataclass
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

PAGE_W, PAGE_H = A4                     # 210 x 297 mm, pion
MARGIN = 10 * mm                        # margines zewnetrzny strony

INK = HexColor("#1a1a1a")
MUTED = HexColor("#555555")
GRID = HexColor("#9a9a9a")              # wewnetrzne linie siatki (jasniejsze od krawedzi)
TITLE_GRAY = HexColor("#6b6b6b")        # --muted ze style.css (kolor tytulow strony)
HEADER_BG = HexColor("#d9c896")         # --rule ze style.css
PKT_SILY = HexColor("#2e7d32")          # --pkt-sily ze style.css (zielone punkty sily)

FONT = "DejaVu"
FONT_BOLD = "DejaVu-Bold"
FONT_SERIF = "DejaVu-Serif"
FONT_HAND = "Caveat"                    # "odreczne" wpisy na kartach przykladowych
HAND_FS = 14                            # rozmiar wpisow w wierszach
HAND_FS_FIELDS = 16                     # rozmiar wpisow w rubrykach naglowka

WERSJA = "23.07.2026"                   # stopka karty; podbij przy zmianie zasad/ukladu
ROWS = 23                               # mini-tabela wyrownania w sciadze kosztuje 3 wiersze
ROW_H = 8 * mm
HEAD_H = 13 * mm
NICK_MAX = 40 * mm                      # nick nie zabiera calej reszty szerokosci
HEAD_FS = 6.0                           # naglowki kolumn (wersaliki)
SUB_FS = 5.2                            # naglowki podkolumn (wersaliki)

# INWARIANT: nazwy rubryk/kolumn (FIELDS, COLUMNS) i tresc SCIAGA musza byc zgodne
# z terminologia przykladu i zasad na ranking.html — sprawdzaj przy kazdej edycji.
#
# (naglowek grupy, [(podkolumna, szerokosc)]) — pojedyncza podkolumna "" = kolumna
# bez podzialu; szerokosc 0.0 = reszta szerokosci karty (nick przeciwnika)
COLUMNS: list[tuple[str, list[tuple[str, float]]]] = [
    ("data", [("", 9 * mm)]),
    ("moje PS", [("", 12 * mm)]),
    ("przeciwnik", [("nick", 0.0), ("PS", 8 * mm)]),
    ("wyrównanie", [("różnica PS", 15 * mm), ("ruchy\nCzarnego", 13 * mm),
                    ("jeńcy\ndla Czarnego", 15.5 * mm)]),
    ("wynik", [("", 12 * mm)]),
    ("zmiana PS", [("", 13 * mm)]),
    ("nowe PS", [("", 12.5 * mm)]),
]

# przed tymi grupami biegnie gruba kreska — sekcje jak w przykladzie na stronie:
# przed gra | przeciwnik i wyrownanie | po grze
THICK_BEFORE = {"przeciwnik", "wynik"}

# nadruk planszy w naglowku karty — zakresla sie jedna z trzech
PLANSZA_PREPRINT = "9×9 · 13×13 · 19×19"
PLANSZA_FS = 9                          # nadruk wyraznie wiekszy od etykiet rubryk

@dataclass(frozen=True)
class Wiersz:
    """Jedna gra na karcie; wartosci jako napisy, dokladnie jak wpisalby je gracz."""
    data: str
    moje_pkt: str
    przeciwnik_nick: str
    przeciwnik_pkt: str
    roznica_ps: str
    ruchy: str              # ruchy Czarnego na start (1 = zwykla gra)
    jency: str              # jency dla Czarnego (liczba ujemna = dla Bialego)
    wynik: str
    zmiana: str
    nowe_pkt: str


@dataclass(frozen=True)
class KartaDane:
    """Wypelnienie naglowka karty + wiersze gier; cala karta dotyczy jednej planszy."""
    nick: str
    plansza: str            # "9×9" | "13×13" | "19×19" — zakreslana w naglowku
    wiersze: list[Wiersz]


# indeksy podkolumn (w kolejnosci COLUMNS) z wartosciami w kolorze PS
BLUE_LEAFS = {1, 3, 4, 8, 9}    # moje PS, PS przeciwnika, roznica PS, zmiana, nowe

# sciaga na dole karty: (tytul kolumny, punkty); kolumny w rytmie wypelniania
# karty (wyrownanie -> wynik -> zmiana PS); w kolumnie "wyrownanie" nad
# punktami rysowana jest mini-tabela KOMP_TABELA
SCIAGA: list[tuple[str, list[str]]] = [
    ("wyrównanie", [
        "różnica PS = silniejszy − słabszy; jednakowa na obu kartach",
        "np. różnica 24 → ruchy 2, jeńcy 24 − 19 = 5",
        "gra równa (0–5): kolory nigiri",
        "powyżej 70: odejmuj po 13, każde odjęcie to dodatkowy ruch",
    ]),
    ("wynik", [
        "w punktach: + wygrana, − przegrana",
        "na obu kartach ta sama liczba, przeciwne znaki",
        "przy podliczaniu dolicz jeńców — każdy to punkt",
        "remis przy grze równej: wygrywa Biały",
    ]),
    ("zmiana PS", [
        "zwycięzca +1, przegrany −1",
        "wygrana o 13+ punktów albo poddanie: ±2",
        "remis (przy różnicy PS ≥ 6): PS bez zmian",
        "trzecia wygrana z rzędu (i kolejne): zwycięzca ×2",
    ]),
]

# mini-tabela wyrownania: zakres roznicy PS -> ruchy Czarnego na start
# i formula na jencow dla Czarnego; zgodna z tabelami na ranking.html
KOMP_TABELA_HEAD = ("różnica PS", "ruchy Czarnego", "jeńcy dla Czarnego")
KOMP_TABELA: list[tuple[str, str, str]] = [
    ("0–5", "1", "−6 (gra równa)"),
    ("6–18", "1", "różnica − 6"),
    ("19–31", "2", "różnica − 19"),
    ("32–44", "3", "różnica − 32"),
    ("45–57", "4", "różnica − 45"),
    ("58–70", "5", "różnica − 58"),
]


def register_fonts() -> None:
    dejavu = Path("/usr/share/fonts/truetype/dejavu")
    assert dejavu.is_dir(), f"brak katalogu czcionek DejaVu: {dejavu}"
    pdfmetrics.registerFont(TTFont(FONT, str(dejavu / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(dejavu / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_SERIF, str(dejavu / "DejaVuSerif.ttf")))
    hand = Path(__file__).resolve().parent / "fonts" / "Caveat-Bold.ttf"
    assert hand.is_file(), f"brak fontu odrecznego: {hand}"
    pdfmetrics.registerFont(TTFont(FONT_HAND, str(hand)))


def draw_title(c: Canvas, x0: float, top: float, card_w: float) -> float:
    """Tytul karty jak naglowek strony zg-go.pl; zwraca y pod nim."""
    y = top - 6 * mm
    c.setFillColor(TITLE_GRAY)
    c.setFont(FONT_SERIF, 14)
    c.drawString(x0, y, "Karta gracza")
    c.setFont(FONT, 7)
    c.drawRightString(x0 + card_w, y, "Klub Go Semedori · zg-go.pl")
    c.setStrokeColor(HEADER_BG)
    c.setLineWidth(0.8)
    c.line(x0, y - 3 * mm, x0 + card_w, y - 3 * mm)
    return y - 6 * mm


FIELD_H = 11 * mm

# (etykieta rubryki, szerokosc) — nick dostaje reszte szerokosci karty
FIELDS: list[tuple[str, float]] = [
    ("NICK", 0.0),
    ("PLANSZA (ZAKREŚL JEDNĄ)", 50 * mm),
]


def draw_fields(c: Canvas, x0: float, top: float, card_w: float,
                dane: KartaDane | None) -> float:
    """Rubryki Nick / plansza jako obramowany pasek; zwraca y pod nim."""
    fixed = sum(w for _, w in FIELDS)
    nick_w = card_w - fixed
    assert nick_w > 30 * mm, f"za malo miejsca na rubryke nicku: {nick_w / mm:.1f} mm"
    widths = [w if w > 0 else nick_w for _, w in FIELDS]
    values = ["", ""] if dane is None else [dane.nick, ""]

    bottom = top - FIELD_H
    c.setStrokeColor(INK)
    c.setLineWidth(0.6)
    c.rect(x0, bottom, card_w, FIELD_H, stroke=1, fill=0)
    x = x0
    for (label, _), w, value in zip(FIELDS, widths, values):
        c.line(x, top, x, bottom)
        c.setFillColor(MUTED)
        c.setFont(FONT, 5.5)
        c.drawString(x + 1.5 * mm, top - 3 * mm, label)
        if label.startswith("PLANSZA"):
            assert pdfmetrics.stringWidth(PLANSZA_PREPRINT, FONT_BOLD, PLANSZA_FS) <= w - 6 * mm, \
                "nadruk planszy za szeroki na rubryke"
            c.setFillColor(INK)
            c.setFont(FONT_BOLD, PLANSZA_FS)
            c.drawCentredString(x + w / 2, bottom + 3 * mm, PLANSZA_PREPRINT)
            if dane is not None:
                draw_plansza_kolko(c, x, w, bottom + 3 * mm, dane.plansza)
        else:
            c.setFillColor(INK)
            c.setFont(FONT_HAND, HAND_FS_FIELDS)
            c.drawString(x + 2 * mm, bottom + 2.5 * mm, value)
        x += w
    return bottom - 3 * mm


def group_widths(card_w: float) -> list[list[float]]:
    """Szerokosci podkolumn; 0.0 (nick) dostaje reszte karty do NICK_MAX,
    nadwyzka rozchodzi sie po rowno na pozostale kolumny (luz naglowkow)."""
    fixed = sum(w for _, subs in COLUMNS for _, w in subs)
    nick_w = min(card_w - fixed, NICK_MAX)
    assert nick_w > 20 * mm, f"za malo miejsca na nick przeciwnika: {nick_w / mm:.1f} mm"
    n_rest = sum(len(subs) for _, subs in COLUMNS) - 1
    extra = (card_w - fixed - nick_w) / n_rest
    assert extra >= 0, f"ujemny luz kolumn: {extra / mm:.2f} mm"
    return [[w + extra if w > 0 else nick_w for _, w in subs] for _, subs in COLUMNS]


def draw_header_text(c: Canvas, cx: float, y: float, text: str, fs: float, max_w: float) -> None:
    """Jedna linia naglowka: wersaliki, niebieskie gdy dotyczy pkt sily."""
    text = text.upper()
    text_w = pdfmetrics.stringWidth(text, FONT_BOLD, fs)
    assert text_w <= max_w - 1 * mm, f"naglowek '{text}' za szeroki na kolumne {max_w / mm:.1f} mm"
    c.setFillColor(PKT_SILY if "PS" in text.split() else INK)
    c.setFont(FONT_BOLD, fs)
    c.drawCentredString(cx, y, text)


def draw_header_labels(c: Canvas, x0: float, top: float, widths: list[list[float]]) -> None:
    line_h = 3.5 * mm
    x = x0
    for (label, subs), sub_ws in zip(COLUMNS, widths):
        group_w = sum(sub_ws)
        lines = label.split("\n")
        if len(subs) == 1:
            y = top - (HEAD_H - (len(lines) - 1) * line_h) / 2 - 0.8 * mm
            for line in lines:
                draw_header_text(c, x + group_w / 2, y, line, HEAD_FS, group_w)
                y -= line_h
        else:
            assert "\n" not in label, "naglowek grupy z podkolumnami musi byc jednoliniowy"
            draw_header_text(c, x + group_w / 2, top - HEAD_H / 4 - 0.8 * mm, label, HEAD_FS, group_w)
            sx = x
            sub_line_h = 2.9 * mm
            for (sub_label, _), sub_w in zip(subs, sub_ws):
                sub_lines = sub_label.split("\n")
                y = top - HEAD_H / 2 - (HEAD_H / 2 - (len(sub_lines) - 1) * sub_line_h) / 2 - 0.8 * mm
                for line in sub_lines:
                    draw_header_text(c, sx + sub_w / 2, y, line, SUB_FS, sub_w)
                    y -= sub_line_h
                sx += sub_w
        x += group_w


def draw_grid(c: Canvas, x0: float, top: float, card_w: float, widths: list[list[float]],
              n_rows: float) -> None:
    """Siatka tabeli; ulamkowe n_rows -> ostatni wiersz uciety, bez dolnej krawedzi.

    Czarne sa tylko krawedzie: obrys, spod naglowka i grube granice sekcji;
    wewnetrzne linie wierszy i podkolumn sa jasnoszare.
    """
    bottom = top - HEAD_H - n_rows * ROW_H
    last = int(n_rows) + 1
    for row in range(last + 1):
        y = top - min(row, 1) * HEAD_H - max(row - 1, 0) * ROW_H
        edge = row <= 1 or (row == last and n_rows == int(n_rows))
        c.setStrokeColor(INK if edge else GRID)
        c.setLineWidth(0.6 if edge else 0.4)
        c.line(x0, y, x0 + card_w, y)
    x = x0
    for i, ((label, _), sub_ws) in enumerate(zip(COLUMNS, widths)):
        if label in THICK_BEFORE:                     # granica sekcji karty
            c.setStrokeColor(INK)
            c.setLineWidth(1.8)
        elif i == 0:                                  # lewa krawedz tabeli
            c.setStrokeColor(INK)
            c.setLineWidth(0.6)
        else:
            c.setStrokeColor(GRID)
            c.setLineWidth(0.5)
        c.line(x, top, x, bottom)                     # granica grupy: pelna wysokosc
        c.setStrokeColor(GRID)
        c.setLineWidth(0.4)
        sx = x
        for sub_w in sub_ws[:-1]:
            sx += sub_w
            c.line(sx, top - HEAD_H / 2, sx, bottom)  # granica podkolumny: od polowy naglowka
        if len(sub_ws) > 1:                           # kreska miedzy etykieta grupy a podkolumnami
            c.line(x, top - HEAD_H / 2, x + sum(sub_ws), top - HEAD_H / 2)
        x += sum(sub_ws)
    c.setStrokeColor(INK)
    c.setLineWidth(0.6)
    c.line(x0 + card_w, top, x0 + card_w, bottom)     # prawa krawedz tabeli


def leaf_geometry(x0: float, widths: list[list[float]]) -> list[tuple[float, float]]:
    """(x, szerokosc) kazdej podkolumny, w kolejnosci od lewej."""
    out: list[tuple[float, float]] = []
    x = x0
    for sub_ws in widths:
        for w in sub_ws:
            out.append((x, w))
            x += w
    return out


def row_baseline(top: float, row: int) -> float:
    return top - HEAD_H - row * ROW_H - ROW_H / 2 - 1


def draw_plansza_kolko(c: Canvas, x: float, w: float, y: float, plansza: str) -> None:
    """Zakresla wybrana plansze w nadruku PLANSZA_PREPRINT (naglowek karty)."""
    assert plansza in PLANSZA_PREPRINT.split(" · "), f"nieznana plansza: {plansza}"
    start = x + w / 2 - pdfmetrics.stringWidth(PLANSZA_PREPRINT, FONT_BOLD, PLANSZA_FS) / 2
    prefix = PLANSZA_PREPRINT[: PLANSZA_PREPRINT.index(plansza)]
    x1 = start + pdfmetrics.stringWidth(prefix, FONT_BOLD, PLANSZA_FS)
    num_w = pdfmetrics.stringWidth(plansza, FONT_BOLD, PLANSZA_FS)
    cx, cy = x1 + num_w / 2, y + 1.4 * mm
    rx, ry = num_w / 2 + 1.6 * mm, 3.1 * mm
    c.setStrokeColor(INK)
    c.setLineWidth(1.5)
    c.ellipse(cx - rx, cy - ry, cx + rx, cy + ry, stroke=1, fill=0)


def draw_wiersze(c: Canvas, x0: float, top: float, widths: list[list[float]],
                 wiersze: list[Wiersz]) -> None:
    """Wypelnione wiersze gier (karty przykladowe)."""
    leaves = leaf_geometry(x0, widths)
    assert len(leaves) == 10, len(leaves)
    for row, w in enumerate(wiersze):
        y = row_baseline(top, row)
        values = [w.data, w.moje_pkt, w.przeciwnik_nick, w.przeciwnik_pkt, w.roznica_ps,
                  w.ruchy, w.jency, w.wynik, w.zmiana, w.nowe_pkt]
        for li, ((lx, lw), value) in enumerate(zip(leaves, values)):
            if not value:
                continue
            c.setFillColor(PKT_SILY if li in BLUE_LEAFS else INK)
            c.setFont(FONT_HAND, HAND_FS)
            c.drawCentredString(lx + lw / 2, y, value)


def draw_table(c: Canvas, x0: float, top: float, card_w: float,
               wiersze: list[Wiersz], n_rows: float) -> float:
    """Tabela gier (naglowek dwupoziomowy + wiersze); zwraca y pod tabela.

    Ulamkowe n_rows (np. 1.5) rysuje wycinek: ostatni, niepelny wiersz zostaje
    pusty (bez nadruku planszy) i bez dolnej krawedzi — tabela "biegnie dalej".
    """
    assert len(wiersze) <= int(n_rows), f"za duzo wierszy: {len(wiersze)} > {int(n_rows)}"
    widths = group_widths(card_w)
    bottom = top - HEAD_H - n_rows * ROW_H

    c.setFillColor(HEADER_BG)
    c.rect(x0, top - HEAD_H, card_w, HEAD_H, stroke=0, fill=1)
    draw_header_labels(c, x0, top, widths)

    draw_wiersze(c, x0, top, widths, wiersze)
    draw_grid(c, x0, top, card_w, widths, n_rows)
    return bottom - 4 * mm


def draw_qr(c: Canvas, x: float, y: float, size: float, url: str) -> None:
    """Kod QR o boku size, lewym dolnym rogiem w (x, y)."""
    qr = QrCodeWidget(url, barLevel="M")
    x0, y0, x1, y1 = qr.getBounds()
    d = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    d.add(qr)
    renderPDF.draw(d, c, x, y)


def draw_komp_tabela(c: Canvas, x: float, top: float, col_w: float) -> float:
    """Mini-tabela wyrownania w kolumnie sciagi; zwraca y dolnej krawedzi."""
    ws = [0.22 * col_w, 0.32 * col_w, 0.46 * col_w]
    assert abs(sum(ws) - col_w) < 0.01 * mm, f"szerokosci podkolumn != {col_w / mm:.1f} mm"
    head_h, row_h = 3.8 * mm, 3.4 * mm
    bottom = top - head_h - len(KOMP_TABELA) * row_h
    c.setFillColor(HEADER_BG)
    c.rect(x, top - head_h, col_w, head_h, stroke=0, fill=1)
    hx = x
    for head, w in zip(KOMP_TABELA_HEAD, ws):
        draw_header_text(c, hx + w / 2, top - head_h + 1.2 * mm, head, 4.8, w)
        hx += w
    for r, row in enumerate(KOMP_TABELA):
        y = top - head_h - (r + 1) * row_h + 1.0 * mm
        vx = x
        for i, (value, w) in enumerate(zip(row, ws)):
            c.setFillColor(PKT_SILY if i == 0 else INK)
            c.setFont(FONT, 6)
            c.drawCentredString(vx + w / 2, y, value)
            vx += w
    c.setStrokeColor(GRID)
    c.setLineWidth(0.4)
    for r in range(len(KOMP_TABELA)):
        ly = top - head_h - r * row_h
        c.line(x, ly, x + col_w, ly)
    vx = x
    for w in ws[:-1]:
        vx += w
        c.line(vx, top, vx, bottom)
    c.rect(x, bottom, col_w, top - bottom, stroke=1, fill=0)
    return bottom


def draw_sciaga(c: Canvas, x0: float, top: float, card_w: float) -> float:
    """Trzykolumnowa sciaga z mini-naglowkami i punktami; zwraca y pod nia."""
    gap = 6 * mm
    col_w = (card_w - (len(SCIAGA) - 1) * gap) / len(SCIAGA)
    y0 = top - 4 * mm
    line_h = 2.7 * mm
    bottoms: list[float] = []
    for i, (title, items) in enumerate(SCIAGA):
        x = x0 + i * (col_w + gap)
        t = title.upper()
        c.setFont(FONT_BOLD, 6)
        c.setFillColor(PKT_SILY if "PS" in t.split() else INK)
        c.drawString(x, y0, t)
        c.setStrokeColor(HEADER_BG)
        c.setLineWidth(0.8)
        c.line(x, y0 - 1.6 * mm, x + col_w, y0 - 1.6 * mm)
        y = y0 - 5 * mm
        if title == "wyrównanie":
            y = draw_komp_tabela(c, x, y0 - 2.4 * mm, col_w) - 3.2 * mm
        for item in items:
            c.setFillColor(MUTED)
            c.circle(x + 0.7 * mm, y + 0.7 * mm, 0.5 * mm, stroke=0, fill=1)
            c.setFont(FONT, 6)
            c.setFillColor(INK)
            for line in simpleSplit(item, FONT, 6, col_w - 3 * mm):
                c.drawString(x + 2.8 * mm, y, line)
                y -= line_h
            y -= 0.7 * mm
        bottoms.append(y)
    y = min(bottoms) - 1.5 * mm
    qr_size = 14 * mm
    draw_qr(c, x0 + card_w - qr_size, y, qr_size, "https://zg-go.pl/ranking.html")
    c.setFont(FONT, 6)
    c.setFillColor(MUTED)
    c.drawString(x0, y, "PS = punkty siły · Pełne zasady: zg-go.pl/ranking.html")
    c.drawRightString(x0 + card_w - qr_size - 2 * mm, y, f"wersja karty {WERSJA}")
    return y


def draw_card(c: Canvas, x0: float, card_w: float, dane: KartaDane | None) -> None:
    top = PAGE_H - MARGIN
    y = draw_title(c, x0, top, card_w)
    y = draw_fields(c, x0, y, card_w, dane)
    y = draw_table(c, x0, y, card_w, [] if dane is None else dane.wiersze, ROWS)
    y = draw_sciaga(c, x0, y, card_w)
    assert y > 5 * mm, f"karta nie miesci sie na stronie: y={y / mm:.1f} mm"


CUT_MARGIN = 2 * mm


def generuj_wycinek(out: Path, karty: list[KartaDane], n_rows: float) -> None:
    """Zapisuje PDF-wycinek karty (naglowek + n_rows wierszy) do osadzenia na stronie.

    Jedna karta na strone; strona ma dokladnie rozmiar wycinka.
    """
    assert karty, "co najmniej jedna karta"
    register_fonts()
    card_w = PAGE_W - 2 * MARGIN
    page_w = card_w + 2 * CUT_MARGIN
    page_h = 2 * CUT_MARGIN + FIELD_H + 3 * mm + HEAD_H + n_rows * ROW_H
    c = Canvas(str(out), pagesize=(page_w, page_h))
    c.setTitle("Karta gracza (przykład) — Klub Go Semedori")
    for dane in karty:
        y = draw_fields(c, CUT_MARGIN, page_h - CUT_MARGIN, card_w, dane)
        draw_table(c, CUT_MARGIN, y, card_w, dane.wiersze, n_rows)
        c.showPage()
    c.save()
    print(f"OK: {out} ({out.stat().st_size} B)")


def generuj_karte(out: Path, karty: list[KartaDane | None]) -> None:
    """Zapisuje PDF: jedna karta na strone; None = pusta karta do druku."""
    assert karty, "co najmniej jedna karta"
    register_fonts()
    c = Canvas(str(out), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Karta gracza — Klub Go Semedori")
    for dane in karty:
        draw_card(c, MARGIN, PAGE_W - 2 * MARGIN, dane)
        c.showPage()
    c.save()
    print(f"OK: {out} ({out.stat().st_size} B)")


def main() -> None:
    generuj_karte(Path(__file__).resolve().parent.parent / "karta.pdf", [None])


if __name__ == "__main__":
    main()
