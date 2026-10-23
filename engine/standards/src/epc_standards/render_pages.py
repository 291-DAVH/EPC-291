#!/usr/bin/env python3
"""Render PDF pages to PNG so Claude can read scanned standards visually.

  python -m epc_standards.render_pages <pdf> <pages> [--out DIR] [--scale 1.5]
  pages: "5", "5-9", "5-9,12,20-22" (1-based PDF pages)

Default output: <standard_dir>/extracted/<pdf-stem>/images/pNNNN.png (dev-knowledge, never versioned).
Requires: pypdfium2.
"""
import argparse
import sys
from pathlib import Path


def parse_pages(spec, total):
    pages = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            pages.extend(range(int(a), int(b) + 1))
        elif part:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= total]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("pages")
    ap.add_argument("--out")
    ap.add_argument("--scale", type=float, default=1.5)
    a = ap.parse_args()
    import pypdfium2 as pdfium
    pdf = Path(a.pdf)
    doc = pdfium.PdfDocument(str(pdf))
    out = Path(a.out) if a.out else pdf.parent.parent / "extracted" / pdf.stem / "images"
    out.mkdir(parents=True, exist_ok=True)
    for p in parse_pages(a.pages, len(doc)):
        img = doc[p - 1].render(scale=a.scale).to_pil()
        f = out / f"p{p:04d}.png"
        img.save(f)
        print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
