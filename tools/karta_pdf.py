#!/usr/bin/env python3
"""Karta gracza klubu Semedori (pionowe A4) — biblioteka + generator karta.pdf.

Uruchomienie:  python3 tools/karta_pdf.py   (zapisuje pusta karte: karta.pdf w korzeniu repo)
Jako biblioteka: generuj_karte(sciezka, [KartaDane(...), ...]) — karta na strone,
z wypelnionym naglowkiem i wierszami gier (np. karty przykladowe).
Wymaga: reportlab, czcionki DejaVu (pakiet fonts-dejavu).
"""

from dataclasses import dataclass
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
GRID = HexColor("#9a9a9a")              # wewnetrzne linie siatki (jasniejsze od krawedzi)
TITLE_GRAY = HexColor("#6b6b6b")        # --muted ze style.css (kolor tytulow strony)
HEADER_BG = HexColor("#d9c896")         # --rule ze style.css
PKT_SILY = HexColor("#0d9488")          # --pkt-sily ze style.css (morskie punkty sily, jasniejszy teal)

FONT = "DejaVu"
FONT_BOLD = "DejaVu-Bold"
FONT_SERIF = "DejaVu-Serif"
FONT_HAND = "Caveat"                    # "odreczne" wpisy na kartach przykladowych
HAND_FS = 14                            # rozmiar wpisow w wierszach
HAND_FS_FIELDS = 16                     # rozmiar wpisow w rubrykach naglowka

WERSJA = "15.07.2026"                   # stopka karty; podbij przy zmianie zasad/ukladu
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
    ("kompensacja", [("handi\nCzarnego", 13 * mm), ("komi dla\nBiałego", 13.5 * mm)]),
    ("wynik", [("", 12 * mm)]),
    ("zmiana\npkt siły", [("", 12 * mm)]),
    ("nowe\npkt siły", [("", 12 * mm)]),
]

# przed tymi grupami biegnie gruba kreska — sekcje jak w przykladzie na stronie:
# przed gra | przeciwnik i wyrownanie | po grze
THICK_BEFORE = {"przeciwnik", "wynik"}

# nadruk do zakreslania w kazdym wierszu kolumny
PREPRINT = {"plansza": "9·13·19"}

@dataclass(frozen=True)
class Wiersz:
    """Jedna gra na karcie; wartosci jako napisy, dokladnie jak wpisalby je gracz."""
    data: str
    plansza: str            # "9" | "13" | "19" — zakreslana w nadruku
    moje_pkt: str
    przeciwnik_nick: str
    przeciwnik_pkt: str
    silniejszy_o: str
    dodatkowe_ruchy: str
    komi: str
    wynik: str
    zmiana: str
    nowe_pkt: str


@dataclass(frozen=True)
class KartaDane:
    """Wypelnienie naglowka karty + wiersze gier."""
    nick: str
    pkt_9: str
    pkt_13: str
    pkt_19: str
    wiersze: list[Wiersz]


# indeksy podkolumn (w kolejnosci COLUMNS) z wartosciami w kolorze pkt sily
BLUE_LEAFS = {2, 4, 5, 9, 10}   # moje pkt, pkt sily przeciwnika, silniejszy o, zmiana, nowe

# sciaga na dole karty: (tytul kolumny, punkty)
SCIAGA: list[tuple[str, list[str]]] = [
    ("kompensacja różnicy", [
        "pełne 13 pkt siły → handi: dodatkowy ruch Czarnego",
        "komi: Czarny daje Białemu 6 kamieni",
        "resztę Biały spłaca kamieniami — 1 za każdy pkt siły",
        "otrzymane kamienie liczą się przy podliczaniu",
    ]),
    ("zmiana pkt siły", [
        "zwycięzca +1, przegrany −1",
        "wygrana o 13+ kamieni albo poddanie: ±2",
        "remis: bez zmiany",
        "3. wygrana z rzędu na planszy i kolejne: zwycięzca ×2",
    ]),
    ("zapis ze znakiem", [
        "SILNIEJSZY O: minus, gdy to ja jestem silniejszy",
        "KOMI DLA BIAŁEGO: minus, gdy dostaje je Czarny",
        "WYNIK: w kamieniach, + wygrana, − przegrana",
    ]),
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
    ("PKT SIŁY 9×9", 21 * mm),
    ("PKT SIŁY 13×13", 23 * mm),
    ("PKT SIŁY 19×19", 23 * mm),
]


def draw_fields(c: Canvas, x0: float, top: float, card_w: float,
                dane: KartaDane | None) -> float:
    """Rubryki Nick / pkt sily na plansze jako obramowany pasek; zwraca y pod nim."""
    fixed = sum(w for _, w in FIELDS)
    nick_w = card_w - fixed
    assert nick_w > 30 * mm, f"za malo miejsca na rubryke nicku: {nick_w / mm:.1f} mm"
    widths = [w if w > 0 else nick_w for _, w in FIELDS]
    values = ["", "", "", ""] if dane is None else [dane.nick, dane.pkt_9, dane.pkt_13, dane.pkt_19]

    bottom = top - FIELD_H
    c.setStrokeColor(INK)
    c.setLineWidth(0.6)
    c.rect(x0, bottom, card_w, FIELD_H, stroke=1, fill=0)
    x = x0
    for (label, _), w, value in zip(FIELDS, widths, values):
        c.line(x, top, x, bottom)
        c.setFillColor(PKT_SILY if "PKT SIŁY" in label else MUTED)
        c.setFont(FONT, 5.5)
        c.drawString(x + 1.5 * mm, top - 3 * mm, label)
        c.setFillColor(PKT_SILY if "PKT SIŁY" in label else INK)
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


def draw_plansza_kolko(c: Canvas, leaf: tuple[float, float], y: float, plansza: str) -> None:
    """Zakresla wybrana plansze w nadruku 9·13·19."""
    text = PREPRINT["plansza"]
    assert plansza in text.split("·"), f"nieznana plansza: {plansza}"
    lx, lw = leaf
    start = lx + lw / 2 - pdfmetrics.stringWidth(text, FONT, 6.5) / 2
    x1 = start + pdfmetrics.stringWidth(text[: text.index(plansza)], FONT, 6.5)
    num_w = pdfmetrics.stringWidth(plansza, FONT, 6.5)
    cx, cy = x1 + num_w / 2, y + 1.1 * mm
    rx, ry = num_w / 2 + 1.4 * mm, 2.7 * mm
    c.setStrokeColor(INK)
    c.setLineWidth(1.5)
    c.ellipse(cx - rx, cy - ry, cx + rx, cy + ry, stroke=1, fill=0)


def draw_wiersze(c: Canvas, x0: float, top: float, widths: list[list[float]],
                 wiersze: list[Wiersz]) -> None:
    """Wypelnione wiersze gier (karty przykladowe)."""
    leaves = leaf_geometry(x0, widths)
    assert len(leaves) == 11, len(leaves)
    for row, w in enumerate(wiersze):
        y = row_baseline(top, row)
        values = [w.data, "", w.moje_pkt, w.przeciwnik_nick, w.przeciwnik_pkt, w.silniejszy_o,
                  w.dodatkowe_ruchy, w.komi, w.wynik, w.zmiana, w.nowe_pkt]
        for li, ((lx, lw), value) in enumerate(zip(leaves, values)):
            if not value:
                continue
            c.setFillColor(PKT_SILY if li in BLUE_LEAFS else INK)
            c.setFont(FONT_HAND, HAND_FS)
            c.drawCentredString(lx + lw / 2, y, value)
        draw_plansza_kolko(c, leaves[1], y, w.plansza)


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

    c.setFont(FONT, 6.5)
    c.setFillColor(MUTED)
    for col_label, text in PREPRINT.items():
        idx = [i for i, (label, _) in enumerate(COLUMNS) if label == col_label]
        assert len(idx) == 1, f"dokladnie jedna kolumna '{col_label}'"
        col_w = sum(widths[idx[0]])
        assert pdfmetrics.stringWidth(text, FONT, 6.5) <= col_w - 1 * mm, f"nadruk '{text}' za szeroki"
        cx = x0 + sum(sum(ws) for ws in widths[: idx[0]]) + col_w / 2
        for row in range(int(n_rows)):
            c.drawCentredString(cx, row_baseline(top, row), text)

    draw_wiersze(c, x0, top, widths, wiersze)
    draw_grid(c, x0, top, card_w, widths, n_rows)
    return bottom - 4 * mm


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
        c.setFillColor(PKT_SILY if "PKT SIŁY" in t else INK)
        c.drawString(x, y0, t)
        c.setStrokeColor(HEADER_BG)
        c.setLineWidth(0.8)
        c.line(x, y0 - 1.6 * mm, x + col_w, y0 - 1.6 * mm)
        y = y0 - 5 * mm
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
    c.setFont(FONT, 6)
    c.setFillColor(MUTED)
    c.drawString(x0, y, "Pełne zasady: zg-go.pl/ranking.html")
    c.drawRightString(x0 + card_w, y, f"wersja karty {WERSJA}")
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
