#!/usr/bin/env python3
"""Generuje karta.pdf: karta gracza klubu Semedori, 2 x A5 na poziomym A4.

Uruchomienie:  python3 tools/karta_pdf.py   (zapisuje karta.pdf w korzeniu repo)
Wymaga: reportlab, czcionki DejaVu (pakiet fonts-dejavu).
"""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

PAGE_W, PAGE_H = landscape(A4)          # 297 x 210 mm
MARGIN = 7 * mm                         # margines zewnetrzny strony
GUTTER = 4 * mm                         # odstep kazdej karty od linii ciecia
HALF_W = PAGE_W / 2

INK = HexColor("#1a1a1a")
MUTED = HexColor("#555555")
TITLE_GRAY = HexColor("#6b6b6b")        # --muted ze style.css (kolor tytulow strony)
HEADER_BG = HexColor("#d9c896")         # --rule ze style.css

FONT = "DejaVu"
FONT_BOLD = "DejaVu-Bold"
FONT_SERIF = "DejaVu-Serif"

ROWS = 16
ROW_H = 8 * mm
HEAD_H = 9 * mm

# (naglowek grupy, [(podkolumna, szerokosc)]) — pojedyncza podkolumna "" = kolumna
# bez podzialu; szerokosc 0.0 = reszta szerokosci karty (nick przeciwnika)
COLUMNS: list[tuple[str, list[tuple[str, float]]]] = [
    ("data", [("", 9 * mm)]),
    ("plansza\nzakreśl", [("", 12 * mm)]),
    ("moje\npkt siły", [("", 11 * mm)]),
    ("przeciwnik", [("nick", 0.0), ("pkt siły", 11 * mm), ("silniejszy o", 13.5 * mm)]),
    ("dod. ruchy\nCzarnego", [("", 15 * mm)]),
    ("komi\ndla\nBiałego", [("", 11.5 * mm)]),
    ("± wynik", [("", 11.5 * mm)]),
    ("zmiana\npkt siły", [("", 11 * mm)]),
    ("nowe\npkt siły", [("", 11.5 * mm)]),
]

# przed tymi grupami biegnie gruba kreska: moje dane | przeciwnik i handicap | po grze
THICK_BEFORE = {"przeciwnik", "zmiana\npkt siły"}

# nadruk do zakreslania w kazdym wierszu kolumny
PREPRINT = {"plansza\nzakreśl": "9·13·19"}

NOTKI = (
    "Zapis ze znakiem: silniejszy o — ujemne, gdy to ja jestem silniejszy · komi — dla Białego, "
    "ujemne, gdy dostaje je Czarny · wynik — w punktach, + wygrana, − przegrana"
)

ZASADY = (
    "Cały ruch: 13 pkt · Komi: Czarny daje 6 czarnych jeńców · "
    "Za każdy cały ruch w różnicy pkt siły: dodatkowy ruch dla Czarnego · Resztę różnicy Biały spłaca "
    "jeńcami · Remis wygrywa Biały · Zmiana: ±1, a przy wygranej o cały ruch lub poddaniu ±2 · "
    "Zasady: zg-go.pl/ranking.html"
)


def register_fonts() -> None:
    dejavu = Path("/usr/share/fonts/truetype/dejavu")
    assert dejavu.is_dir(), f"brak katalogu czcionek DejaVu: {dejavu}"
    pdfmetrics.registerFont(TTFont(FONT, str(dejavu / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(dejavu / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_SERIF, str(dejavu / "DejaVuSerif.ttf")))


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
    ("PKT SIŁY 9×9", 21 * mm),
    ("PKT SIŁY 13×13", 23 * mm),
    ("PKT SIŁY 19×19", 23 * mm),
]


def draw_fields(c: Canvas, x0: float, top: float, card_w: float) -> float:
    """Rubryki Nick/Plansza/Sila/Data jako obramowany pasek; zwraca y pod nim."""
    fixed = sum(w for _, w in FIELDS)
    nick_w = card_w - fixed
    assert nick_w > 30 * mm, f"za malo miejsca na rubryke nicku: {nick_w / mm:.1f} mm"
    widths = [w if w > 0 else nick_w for _, w in FIELDS]

    bottom = top - FIELD_H
    c.setStrokeColor(INK)
    c.setLineWidth(0.6)
    c.rect(x0, bottom, card_w, FIELD_H, stroke=1, fill=0)
    x = x0
    for (label, _), w in zip(FIELDS, widths):
        c.line(x, top, x, bottom)
        c.setFillColor(MUTED)
        c.setFont(FONT, 5.5)
        c.drawString(x + 1.5 * mm, top - 3 * mm, label)
        x += w
    return bottom - 3 * mm


def group_widths(card_w: float) -> list[list[float]]:
    """Szerokosci podkolumn kazdej grupy; 0.0 (nick) dostaje reszte karty."""
    fixed = sum(w for _, subs in COLUMNS for _, w in subs)
    nick_w = card_w - fixed
    assert nick_w > 20 * mm, f"za malo miejsca na nick przeciwnika: {nick_w / mm:.1f} mm"
    return [[w if w > 0 else nick_w for _, w in subs] for _, subs in COLUMNS]


def draw_header_labels(c: Canvas, x0: float, top: float, widths: list[list[float]]) -> None:
    line_h = 2.9 * mm
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, 6.5)
    x = x0
    for (label, subs), sub_ws in zip(COLUMNS, widths):
        group_w = sum(sub_ws)
        lines = label.split("\n")
        if len(subs) == 1:
            y = top - (HEAD_H - (len(lines) - 1) * line_h) / 2 - 0.8 * mm
            for line in lines:
                line_w = pdfmetrics.stringWidth(line, FONT_BOLD, 6.5)
                assert line_w <= group_w - 1 * mm, f"naglowek '{line}' za szeroki na kolumne"
                c.drawCentredString(x + group_w / 2, y, line)
                y -= line_h
        else:
            assert "\n" not in label, "naglowek grupy z podkolumnami musi byc jednoliniowy"
            c.drawCentredString(x + group_w / 2, top - HEAD_H / 4 - 0.8 * mm, label)
            sx = x
            c.setFont(FONT_BOLD, 5.5)
            for (sub_label, _), sub_w in zip(subs, sub_ws):
                sub_text_w = pdfmetrics.stringWidth(sub_label, FONT_BOLD, 5.5)
                assert sub_text_w <= sub_w - 1 * mm, f"podkolumna '{sub_label}' za waska"
                c.drawCentredString(sx + sub_w / 2, top - 3 * HEAD_H / 4 - 0.8 * mm, sub_label)
                sx += sub_w
            c.setFont(FONT_BOLD, 6.5)
        x += group_w


def draw_grid(c: Canvas, x0: float, top: float, card_w: float, widths: list[list[float]]) -> None:
    bottom = top - HEAD_H - ROWS * ROW_H
    c.setStrokeColor(INK)
    c.setLineWidth(0.6)
    for row in range(ROWS + 2):
        y = top - min(row, 1) * HEAD_H - max(row - 1, 0) * ROW_H
        c.line(x0, y, x0 + card_w, y)
    x = x0
    for (label, _), sub_ws in zip(COLUMNS, widths):
        if label in THICK_BEFORE:                     # granica sekcji karty
            c.setLineWidth(1.8)
        c.line(x, top, x, bottom)                     # granica grupy: pelna wysokosc
        c.setLineWidth(0.6)
        sx = x
        for sub_w in sub_ws[:-1]:
            sx += sub_w
            c.line(sx, top - HEAD_H / 2, sx, bottom)  # granica podkolumny: od polowy naglowka
        if len(sub_ws) > 1:                           # kreska miedzy etykieta grupy a podkolumnami
            c.line(x, top - HEAD_H / 2, x + sum(sub_ws), top - HEAD_H / 2)
        x += sum(sub_ws)
    c.line(x0 + card_w, top, x0 + card_w, bottom)


def draw_table(c: Canvas, x0: float, top: float, card_w: float) -> float:
    """Tabela gier (naglowek dwupoziomowy + wiersze); zwraca y pod tabela."""
    widths = group_widths(card_w)
    bottom = top - HEAD_H - ROWS * ROW_H

    c.setFillColor(HEADER_BG)
    c.rect(x0, top - HEAD_H, card_w, HEAD_H, stroke=0, fill=1)
    draw_header_labels(c, x0, top, widths)

    c.setFont(FONT, 6.5)
    c.setFillColor(MUTED)
    for col_label, text in PREPRINT.items():
        idx = [i for i, (label, _) in enumerate(COLUMNS) if label == col_label]
        assert len(idx) == 1, f"dokladnie jedna kolumna '{col_label}'"
        col_w = sum(widths[idx[0]])
        assert pdfmetrics.stringWidth(text, FONT, 6.5) <= col_w - 1 * mm, f"nadruk '{text}' za szeroki"
        cx = x0 + sum(sum(ws) for ws in widths[: idx[0]]) + col_w / 2
        for row in range(ROWS):
            y_cell = top - HEAD_H - row * ROW_H - ROW_H / 2 - 1
            c.drawCentredString(cx, y_cell, text)

    draw_grid(c, x0, top, card_w, widths)
    return bottom - 4 * mm


def draw_paragraph(c: Canvas, x0: float, top: float, card_w: float, text: str,
                   color: HexColor) -> float:
    c.setFont(FONT, 6)
    c.setFillColor(color)
    lines = simpleSplit(text, FONT, 6, card_w)
    y = top - 3 * mm
    for line in lines:
        c.drawString(x0, y, line)
        y -= 2.9 * mm
    return y


def draw_card(c: Canvas, x0: float, card_w: float) -> None:
    top = PAGE_H - MARGIN
    y = draw_title(c, x0, top, card_w)
    y = draw_fields(c, x0, y, card_w)
    y = draw_table(c, x0, y, card_w)
    y = draw_paragraph(c, x0, y, card_w, NOTKI, INK)
    y = draw_paragraph(c, x0, y, card_w, ZASADY, MUTED)
    assert y > MARGIN, f"karta nie miesci sie na stronie: y={y / mm:.1f} mm"


def main() -> None:
    register_fonts()
    out = Path(__file__).resolve().parent.parent / "karta.pdf"
    c = Canvas(str(out), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Karta gracza — Klub Go Semedori")

    card_w = HALF_W - MARGIN - GUTTER
    draw_card(c, MARGIN, card_w)
    draw_card(c, HALF_W + GUTTER, card_w)

    c.setStrokeColor(MUTED)
    c.setLineWidth(0.4)
    c.setDash(3, 3)
    c.line(HALF_W, MARGIN, HALF_W, PAGE_H - MARGIN)

    c.showPage()
    c.save()
    print(f"OK: {out} ({out.stat().st_size} B)")


if __name__ == "__main__":
    main()
