"""Render a structured report (title, key/value blocks, headings, paragraphs, bullet lists, tables) to an A4 PDF with matplotlib.

The caller supplies every text; this module has no wording of its own (management reports in any language and methodology).

  python -m epc_drawing.export.report_pdf <report.json> <out.pdf>

report = {"title": "Informe de Estado", "subtitle": "STATUS-01", "footer": "...", "page_label": "Página {n} de {total}",
          "blocks": [{"type": "kv", "rows": [["Proyecto", "..."]]},
                     {"type": "h", "text": "Estado general"},
                     {"type": "p", "text": "..."},
                     {"type": "bullets", "items": ["..."]},
                     {"type": "table", "columns": [["Hito", 0.4], ["Fecha", 0.2], ...], "rows": [[...]], "empty": "Sin registros"},
                     {"type": "figure", "title": "...", "caption": "...", "bounds": [x0, y0, x1, y1], "max_height": 300,
                      "shapes": [{"s": "poly", "points": [[x, y], ...], "fill": "#rrggbb" | null, "stroke": "#rrggbb", "lw": 0.8}, {"s": "rect", "x": 0, "y": 0, "w": 1, "h": 1, "fill": "#rrggbb"},
                                 {"s": "circle", "x": 0, "y": 0, "r": 1, "fill": "#rrggbb" | null, "stroke": "#rrggbb"}, {"s": "line", "points": [[x, y], [x, y]], "stroke": "#rrggbb", "lw": 0.8},
                                 {"s": "text", "x": 0, "y": 0, "text": "...", "size": 8, "color": "#rrggbb"}]}]}

A figure is drawn from shapes in the coordinates of whatever it shows (a plan, in its own units, y growing downwards): it is scaled to the width of the page, or to `max_height`, whichever is smaller.
"""
import json
import sys
import textwrap
from pathlib import Path
from typing import List

W, H = 595.0, 842.0
M = 50.0
FS, FS_SMALL = 9.0, 8.0
CHAR = 0.56
LINE = 12.0
BOTTOM = H - 62


def _wrap(text, width_pt: float, size: float) -> List[str]:
    chars = max(int(width_pt / (CHAR * size)), 4)
    lines: List[str] = []
    for part in str(text).split("\n"):
        lines += textwrap.wrap(part, chars, break_long_words=True) or [""]
    return lines


def _shape(s: dict, at, scale: float, ops) -> None:
    """One shape of a figure as the drawing operations of the page."""
    kind = s.get("s")
    if kind == "poly":
        ops().append(("poly", [at(*p) for p in s["points"]], s.get("fill"), s.get("stroke"), float(s.get("lw", 0.8))))
    elif kind == "rect":
        x, y = at(s["x"], s["y"])
        ops().append(("rect", x, y, s["w"] * scale, s["h"] * scale, s["fill"]))
    elif kind == "circle":
        x, y = at(s["x"], s["y"])
        ops().append(("circle", x, y, s["r"] * scale, s.get("fill"), s.get("stroke"), float(s.get("lw", 0.8))))
    elif kind == "line":
        (xa, ya), (xb, yb) = at(*s["points"][0]), at(*s["points"][1])
        ops().append(("line", xa, ya, xb, yb, float(s.get("lw", 0.8)), s.get("stroke", "#111111")))
    elif kind == "text":
        x, y = at(s["x"], s["y"])
        ops().append(("text", x, y, s["text"], float(s.get("size", 8)), "bold" if s.get("bold") else "normal", s.get("color", "#111111"), s.get("align", "left")))


def layout(rep: dict) -> List[list]:
    pages: List[list] = [[]]
    y = M
    tw = W - 2 * M

    def ops():
        return pages[-1]

    def need(h):
        nonlocal y
        if y + h > BOTTOM:
            pages.append([])
            y = M
            return True
        return False

    ops().append(("text", M, y + 14, rep.get("title", ""), 17, "bold", "#111111", "left"))
    ops().append(("text", W - M, y + 14, rep.get("subtitle", ""), 14, "bold", "#1f4e8c", "right"))
    y += 26
    ops().append(("line", M, y, W - M, y, 1.4, "#1f4e8c"))
    y += 14

    def _bullets(items, y):
        for item in items:
            lines = _wrap(item, tw - 14, FS)
            if need(len(lines) * LINE):                                               # a new page starts at the top: the caller's y is not the one of the page any more
                y = M
            ops().append(("text", M + 2, y + 9, "•", FS, "normal", "#111111", "left"))
            for i, line in enumerate(lines):
                ops().append(("text", M + 14, y + 9 + i * LINE, line, FS, "normal", "#111111", "left"))
            y += len(lines) * LINE
        return y + 6

    def _figure(b, ops, need, y, tw):
        x0, y0, x1, y1 = b["bounds"]
        bw, bh = max(x1 - x0, 1e-9), max(y1 - y0, 1e-9)
        scale = min(tw / bw, float(b.get("max_height", 300)) / bh)
        height = bh * scale
        heading = 24 if b.get("title") else 0                                          # the heading is part of the figure: it never stays alone at the foot of a page
        if need(height + 30 + heading):
            y = M
        if heading:
            ops().append(("text", M, y + 17, b["title"], 11.5, "bold", "#1f4e8c", "left"))
        top = y + heading
        at = lambda px, py: (M + (px - x0) * scale, top + (py - y0) * scale)               # noqa: E731
        ops().append(("rect", M, top, bw * scale, height, "#fbfbfd"))
        for s in b.get("shapes", []):
            _shape(s, at, scale, ops)
        y = top + height + 4
        if b.get("caption"):
            ops().append(("text", M, y + 9, b["caption"], FS_SMALL, "italic", "#555555", "left"))
            y += LINE
        return y + 8

    def table_header(cols, xs):
        nonlocal y
        ops().append(("rect", M, y, tw, 20, "#e8edf4"))
        for (label, _), x in zip(cols, xs):
            ops().append(("text", x + 4, y + 13.5, label, FS_SMALL, "bold", "#222222", "left"))
        y += 20

    for b in rep.get("blocks", []):
        kind = b.get("type")
        if kind == "kv":
            for label, value in b["rows"]:
                lines = _wrap(value, W - M - 190, FS)
                need(len(lines) * LINE + 4)
                ops().append(("text", M, y + 9, label, FS_SMALL, "bold", "#666666", "left"))
                for i, line in enumerate(lines):
                    ops().append(("text", 190, y + 9 + i * LINE, line, FS, "normal", "#111111", "left"))
                y += max(len(lines), 1) * LINE + 3
            y += 8
        elif kind == "h":
            need(60)
            y += 6
            ops().append(("text", M, y + 11, b["text"], 11.5, "bold", "#1f4e8c", "left"))
            y += 18
        elif kind == "p":
            for line in _wrap(b["text"], tw, FS):
                need(LINE)
                ops().append(("text", M, y + 9, line, FS, "normal", "#111111", "left"))
                y += LINE
            y += 6
        elif kind == "bullets":
            y = _bullets(b["items"], y)
        elif kind == "figure":
            y = _figure(b, ops, need, y, tw)
        elif kind == "table":
            cols = b["columns"]
            xs = [M]
            for _, share in cols:
                xs.append(xs[-1] + share * tw)
            rows = b.get("rows", [])
            if not rows:
                need(30)
                ops().append(("text", M, y + 9, b.get("empty", "-"), FS, "italic", "#777777", "left"))
                y += LINE + 8
                continue
            need(20 + 30)
            table_header(cols, xs)
            for row in rows:
                cells = [_wrap(c, (xs[i + 1] - xs[i]) - 8, FS) for i, c in enumerate(row)]
                h = max(len(c) for c in cells) * LINE + 8
                if need(h):
                    table_header(cols, xs)
                for i, lines in enumerate(cells):
                    for j, line in enumerate(lines):
                        ops().append(("text", xs[i] + 4, y + 13 + j * LINE, line, FS, "normal", "#111111", "left"))
                y += h
                ops().append(("line", M, y, W - M, y, 0.5, "#c8cdd5"))
            y += 10
    total = len(pages)
    for n, p in enumerate(pages, 1):
        p.append(("line", M, H - 44, W - M, H - 44, 0.5, "#c8cdd5"))
        p.append(("text", M, H - 30, rep.get("footer", ""), FS_SMALL, "normal", "#777777", "left"))
        p.append(("text", W - M, H - 30, rep.get("page_label", "{n}/{total}").format(n=n, total=total), FS_SMALL, "normal", "#777777", "right"))
    return pages


def _paint_text(ax, op, patches) -> None:
    _, x, y, text, size, weight, color, ha = op
    ax.text(x, y, text, fontsize=size, fontweight="bold" if weight == "bold" else "normal", fontstyle="italic" if weight == "italic" else "normal", color=color, ha=ha, va="baseline")


def _paint_line(ax, op, patches) -> None:
    _, x1, y1, x2, y2, lw, color = op
    ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, solid_capstyle="butt")


def _paint_poly(ax, op, patches) -> None:
    _, pts, fill, stroke, lw = op
    ax.add_patch(patches.Polygon(pts, closed=True, facecolor=fill or "none", edgecolor=stroke or "none", linewidth=lw))


def _paint_circle(ax, op, patches) -> None:
    _, x, y, r, fill, stroke, lw = op
    ax.add_patch(patches.Circle((x, y), r, facecolor=fill or "none", edgecolor=stroke or "none", linewidth=lw))


def _paint_rect(ax, op, patches) -> None:
    _, x, y, w, h, color = op
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=color, edgecolor="none"))


_PAINTERS = {"text": _paint_text, "line": _paint_line, "poly": _paint_poly, "circle": _paint_circle, "rect": _paint_rect}       # operation of a page -> how it is drawn


def render(rep: dict, dst: Path) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib import patches

    pages = layout(rep)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(str(dst), metadata={"Title": f"{rep.get('title', '')} {rep.get('subtitle', '')}".strip()}) as pdf:
        for page in pages:
            fig = plt.figure(figsize=(W / 72, H / 72))
            try:
                ax = fig.add_axes([0, 0, 1, 1])
                ax.set_xlim(0, W)
                ax.set_ylim(H, 0)
                ax.axis("off")
                for op in page:
                    _PAINTERS.get(op[0], _paint_rect)(ax, op, patches)
                pdf.savefig(fig, facecolor="white")
            finally:
                plt.close(fig)
    return Path(dst)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    render(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), Path(sys.argv[2]))
    print("OK", sys.argv[2])
