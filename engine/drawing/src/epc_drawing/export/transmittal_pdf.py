"""Render a delivery (transmittal) document to an A4 PDF with matplotlib: title, key/value header, a table of the delivered documents, closing lines.

The caller supplies every text (any language) as data, so this module has no wording of its own:

  python -m epc_drawing.export.transmittal_pdf <data.json> <out.pdf>

data = {"title": "TRANSMITTAL", "subtitle": "TR-002", "header": [["Proyecto", "..."], ...],
        "columns": [["N°", 0.06], ["Código", 0.24], ...],      # label and share of the table width
        "rows": [["1", "PRJ-ELE-001", ...], ...],
        "sections": [["Observaciones", "text"], ...],             # optional blocks after the table
        "footer": "left footer text", "page_label": "Página {n} de {total}"}
"""
import json
import sys
import textwrap
from pathlib import Path
from typing import List

W, H = 595.0, 842.0          # A4 in points
M = 50.0                     # margin
FS, FS_SMALL = 9.0, 8.0
CHAR = 0.56                  # average character width as a fraction of the font size (DejaVu Sans)
LINE = 12.0


def _wrap(text: str, width_pt: float, size: float) -> List[str]:
    chars = max(int(width_pt / (CHAR * size)), 4)
    lines: List[str] = []
    for part in str(text).split("\n"):
        lines += textwrap.wrap(part, chars, break_long_words=True) or [""]
    return lines


def layout(data: dict) -> List[list]:
    """Pages of drawing operations; y grows downward."""
    pages: List[list] = [[]]
    y = M

    def new_page():
        nonlocal y
        pages.append([])
        y = M

    ops = lambda: pages[-1]
    ops().append(("text", M, y + 14, data.get("title", ""), 17, "bold", "#111111", "left"))
    ops().append(("text", W - M, y + 14, data.get("subtitle", ""), 17, "bold", "#1f4e8c", "right"))
    y += 26
    ops().append(("line", M, y, W - M, y, 1.4, "#1f4e8c"))
    y += 16
    for label, value in data.get("header", []):
        vl = _wrap(value, W - M - 190, FS)
        ops().append(("text", M, y + 9, label, FS_SMALL, "bold", "#666666", "left"))
        for i, line in enumerate(vl):
            ops().append(("text", 190, y + 9 + i * LINE, line, FS, "normal", "#111111", "left"))
        y += max(len(vl), 1) * LINE + 3
    y += 10

    cols = data.get("columns", [])
    tw = W - 2 * M
    xs = [M]
    for _, share in cols:
        xs.append(xs[-1] + share * tw)

    def header_row():
        nonlocal y
        ops().append(("rect", M, y, tw, 20, "#e8edf4"))
        for (label, _), x in zip(cols, xs):
            ops().append(("text", x + 4, y + 13.5, label, FS_SMALL, "bold", "#222222", "left"))
        y += 20

    header_row()
    for row in data.get("rows", []):
        cells = [_wrap(c, (xs[i + 1] - xs[i]) - 8, FS) for i, c in enumerate(row)]
        h = max(len(c) for c in cells) * LINE + 8
        if y + h > H - 70:
            new_page()
            header_row()
        for i, lines in enumerate(cells):
            for j, line in enumerate(lines):
                ops().append(("text", xs[i] + 4, y + 13 + j * LINE, line, FS, "normal", "#111111", "left"))
        y += h
        ops().append(("line", M, y, W - M, y, 0.5, "#c8cdd5"))
    y += 18

    for title, body in data.get("sections", []):
        lines = _wrap(body, tw, FS)
        need = (len(lines) + 1) * LINE + 10
        if y + need > H - 70:
            new_page()
        ops().append(("text", M, y + 9, title, FS, "bold", "#222222", "left"))
        y += LINE + 2
        for line in lines:
            ops().append(("text", M, y + 9, line, FS, "normal", "#111111", "left"))
            y += LINE
        y += 10

    total = len(pages)
    for n, p in enumerate(pages, 1):
        p.append(("line", M, H - 44, W - M, H - 44, 0.5, "#c8cdd5"))
        p.append(("text", M, H - 30, data.get("footer", ""), FS_SMALL, "normal", "#777777", "left"))
        p.append(("text", W - M, H - 30, data.get("page_label", "{n}/{total}").format(n=n, total=total), FS_SMALL, "normal", "#777777", "right"))
    return pages


def render(data: dict, dst: Path) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.patches import Rectangle

    pages = layout(data)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(str(dst), metadata={"Title": f"{data.get('title', '')} {data.get('subtitle', '')}".strip()}) as pdf:
        for ops in pages:
            fig = plt.figure(figsize=(W / 72, H / 72))
            try:
                ax = fig.add_axes([0, 0, 1, 1])
                ax.set_xlim(0, W)
                ax.set_ylim(H, 0)
                ax.axis("off")
                for op in ops:
                    if op[0] == "text":
                        _, x, y, s, size, weight, color, ha = op
                        ax.text(x, y, s, fontsize=size, fontweight=weight, color=color, ha=ha, va="baseline")
                    elif op[0] == "line":
                        _, x1, y1, x2, y2, lw, color = op
                        ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, solid_capstyle="butt")
                    else:
                        _, x, y, w, h, color = op
                        ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor="none"))
                pdf.savefig(fig, facecolor="white")
            finally:
                plt.close(fig)
    return Path(dst)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    render(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), Path(sys.argv[2]))
    print("OK", sys.argv[2])
