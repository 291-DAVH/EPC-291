#!/usr/bin/env python3
"""Extract the text layer of a standard's PDFs into dev-knowledge (never versioned).

  python extract_standard.py <standard_dir | CC/ID | ID> [--force]

Writes, per PDF, under <standard_dir>/extracted/<pdf-stem>/:
  pages/pNNNN.txt   text of each page (text-layer PDFs only)
  extraction.json   pages, mode (text | scanned | mixed), empty pages
  clauses.json      clause headings found (number, title, pdf page)
  tables.json       table captions found ("Tabla ...")
  needs_vision.json pages without text: read them as images (render_pages.py) or with Claude's PDF reader

Scanned PDFs (no text layer) are detected from a sample and not extracted: no OCR engine is bundled.
Requires: pypdf.
"""
import argparse
import re
import sys
from pathlib import Path

from common import read_json, standard_dir, write_json

CLAUSE = re.compile(r"^(\d{1,3}(?:\.\d+){1,6})\s+([A-ZÁÉÍÓÚÑ¿(].{2,120})$")
TABLE = re.compile(r"^(Tabla|Table)\s+([0-9A-Za-z.\-]+(?:\s*\.\s*[IVX]+)?)\s*[–—-]\s*(.+)$")
SAMPLE_PAGES = 8
MIN_CHARS = 40


def extract_pdf(pdf: Path, out: Path, force: bool):
    import pypdf
    if (out / "extraction.json").exists() and not force:
        print(f"  skip (already extracted): {pdf.name}")
        return read_json(out / "extraction.json")
    reader = pypdf.PdfReader(str(pdf))
    n = len(reader.pages)
    sample = [(reader.pages[i].extract_text() or "") for i in range(min(n, SAMPLE_PAGES))]
    info = {"file": pdf.name, "pages": n, "size_mb": round(pdf.stat().st_size / 1e6, 1)}
    if all(len(t.strip()) < MIN_CHARS for t in sample):
        info.update(mode="scanned", text_pages=0, empty_pages=list(range(1, n + 1)))
        out.mkdir(parents=True, exist_ok=True)
        write_json(out / "extraction.json", info)
        write_json(out / "needs_vision.json", {"reason": "no text layer (scanned)", "pages": f"1-{n}"})
        print(f"  {pdf.name}: SCANNED, {n} pages, no text layer -> use render_pages.py / Claude PDF reader")
        return info
    (out / "pages").mkdir(parents=True, exist_ok=True)
    clauses, tables, empty = [], [], []
    for i in range(n):
        txt = reader.pages[i].extract_text() or ""
        (out / "pages" / f"p{i + 1:04d}.txt").write_text(txt, encoding="utf-8")
        if len(txt.strip()) < MIN_CHARS:
            empty.append(i + 1)
        for line in (l.strip() for l in txt.splitlines()):
            m = CLAUSE.match(line)
            if m:
                clauses.append({"clause": m.group(1), "title": m.group(2), "pdf_page": i + 1})
            m = TABLE.match(line)
            if m:
                tables.append({"id": m.group(2).replace(" ", ""), "title": m.group(3), "pdf_page": i + 1})
    info.update(mode="mixed" if empty else "text", text_pages=n - len(empty), empty_pages=empty)
    write_json(out / "extraction.json", info)
    write_json(out / "clauses.json", clauses)
    write_json(out / "tables.json", tables)
    if empty:
        write_json(out / "needs_vision.json", {"reason": "pages without text", "pages": empty})
    print(f"  {pdf.name}: {info['mode']}, {n} pages, {len(clauses)} clause headings, {len(tables)} table captions, {len(empty)} empty pages")
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("standard")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    sdir = standard_dir(a.standard)
    pdfs = sorted((sdir / "source").glob("*.pdf"))
    if not pdfs:
        print(f"no PDF in {sdir / 'source'}")
        return 1
    print(f"{sdir.name}:")
    for pdf in pdfs:
        extract_pdf(pdf, sdir / "extracted" / pdf.stem, a.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
