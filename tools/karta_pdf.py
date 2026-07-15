#!/usr/bin/env python3
"""Generuje karta.pdf: karta gracza klubu Semedori, pionowe A4.

Uruchomienie:  python3 tools/karta_pdf.py   (zapisuje karta.pdf w korzeniu repo)
Wymaga: reportlab, czcionki DejaVu (pakiet fonts-dejavu).
"""

from pathlib import Path

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
TITLE_GRAY = HexColor("#6b6b6b")        # --muted ze style.css (kolor tytulow strony)
HEADER_BG = HexColor("#d9c896")         # --rule ze style.css
PKT_SILY = HexColor("#1e5fa8")          # --pkt-sily ze style.css (niebieskie punkty sily)

FONT = "DejaVu"
FONT_BOLD = "DejaVu-Bold"
FONT_SERIF = "DejaVu-Serif"

ROWS = 26
ROW_H = 8 * mm
HEAD_H = 13 * mm
NICK_MAX = 40 * mm                      # nick nie zabiera calej reszty szerokosci
HEAD_FS = 6.0                           # naglowki kolumn (wersaliki)
SUB_FS = 5.2                            # naglowki podkolumn (wersaliki)

# (naglowek grupy, [(podkolumna, szerokosc)]) — pojedyncza podkolumna "" = kolumna
# bez podzialu; szerokosc 0.0 = reszta szerokosci karty (nick przeciwnika)
COLUMNS: list[tuple[str, list[tuple[str, float]]]] = [
    ("data", [("", 9 * mm)]),
    ("plansza", [("", 12.5 * mm)]),
    ("moje\npkt siły", [("", 12 * mm)]),
    ("przeciwnik", [("nick", 0.0), ("pkt siły", 10.5 * mm), ("silniejszy o", 15 * mm)]),
    ("dodatkowe\nruchy\nCzarnego", [("", 17.5 * mm)]),
    ("komi dla\nBiałego", [("", 13.5 * mm)]),
    ("wynik", [("", 12 * mm)]),
    ("zmiana\npkt siły", [("", 12 * mm)]),
    ("nowe\npkt siły", [("", 12 * mm)]),
]

# przed tymi grupami biegnie gruba kreska: moje dane | przeciwnik i handicap | po grze
THICK_BEFORE = {"przeciwnik", "zmiana\npkt siły"}

# nadruk do zakreslania w kazdym wierszu kolumny
PREPRINT = {"plansza": "9·13·19"}

NOTKI = (
    "Zapis ze znakiem: silniejszy o — ujemne, gdy to ja jestem silniejszy · komi — dla Białego, "
    "ujemne, gdy dostaje je Czarny · wynik — w kamieniach, + wygrana, − przegrana"
)

ZASADY = (
    "Za każde pełne 13 pkt siły różnicy: dodatkowy ruch dla Czarnego · Komi: Czarny daje "
    "Białemu 6 czarnych kamieni · Resztę różnicy Biały spłaca kamieniami · "
    "Zmiana: ±1 pkt siły, a przy wygranej o 13 kamieni lub więcej albo poddaniu ±2 · "
    "Remis: bez zmiany pkt siły · Trzecia wygrana z rzędu i kolejne: zmiana zwycięzcy ×2 · "
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
        c.setFillColor(PKT_SILY if "PKT SIŁY" in label else MUTED)
        c.setFont(FONT, 5.5)
        c.drawString(x + 1.5 * mm, top - 3 * mm, label)
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
    c.setFillColor(PKT_SILY if "PKT SIŁY" in text else INK)
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
            for (sub_label, _), sub_w in zip(subs, sub_ws):
                draw_header_text(c, sx + sub_w / 2, top - 3 * HEAD_H / 4 - 0.8 * mm,
                                 sub_label, SUB_FS, sub_w)
                sx += sub_w
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

    draw_card(c, MARGIN, PAGE_W - 2 * MARGIN)

    c.showPage()
    c.save()
    print(f"OK: {out} ({out.stat().st_size} B)")


if __name__ == "__main__":
    main()
