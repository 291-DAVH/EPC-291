"""Corre el motor sobre cada muestra de `samples/` y deja los resultados numerados en `out/`: out_01.svg, out_02.svg... (+ out_NN.json), un `indice.md` que dice qué muestra es cada número y
un `index.html` con el original y el resultado lado a lado.

Uso: python scripts/generar_salidas.py [--fondo]
Las salidas nunca se suben a git (`out/` está en .gitignore).
"""
import argparse
import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from epc_arch import ArchError, Options, pdf_to_png, recognize   # noqa: E402

MUESTRAS = RAIZ / "samples"
SALIDA = RAIZ / "out"


def _leer(p: Path) -> bytes:
    datos = p.read_bytes()
    if p.suffix.lower() in (".webp", ".avif"):                       # el motor lee PNG, JPEG...; estos se convierten antes
        b = io.BytesIO()
        Image.open(io.BytesIO(datos)).convert("RGB").save(b, "PNG")
        return b.getvalue()
    return datos


def _miniatura(p: Path) -> str:
    try:
        im = Image.open(io.BytesIO(pdf_to_png(p.read_bytes(), 0, 900))) if p.suffix.lower() == ".pdf" else Image.open(p)
        im = im.convert("RGB")
        im.thumbnail((700, 900))
        b = io.BytesIO()
        im.save(b, "JPEG", quality=70)
        return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
    except Exception:                                                # noqa: BLE001 - la miniatura es un adorno: sin ella el resto sigue
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fondo", action="store_true", help="dibuja el trazado original muy tenue debajo")
    a = ap.parse_args()
    SALIDA.mkdir(exist_ok=True)
    for viejo in SALIDA.glob("out_*"):
        viejo.unlink()
    archivos = sorted(p for p in MUESTRAS.rglob("*") if p.is_file() and p.name != "registro.json" and p.suffix.lower() in (".pdf", ".dxf", ".png", ".jpg", ".jpeg", ".webp", ".avif", ".bmp", ".tif", ".tiff"))
    filas, html = ["| n.º | muestra | muros | puertas | ventanas | huecos | grosor | nota |", "|---|---|---|---|---|---|---|---|"], []
    for n, p in enumerate(archivos, 1):
        nombre = f"out_{n:02d}"
        rel = p.relative_to(MUESTRAS).as_posix()
        try:
            r = recognize(_leer(p), p.name, Options(background=a.fondo))
        except ArchError as e:
            filas.append(f"| {nombre} | {rel} | - | - | - | - | - | no se lee: {e} |")
            html.append(f"<h3>{nombre} · {rel}</h3><p>{e}</p>")
            continue
        d = r.as_dict()
        c = d["counts"]
        (SALIDA / f"{nombre}.svg").write_text(r.svg, encoding="utf-8")
        (SALIDA / f"{nombre}.json").write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        nota = d["warnings"][-1][:70] if d["warnings"] else ""
        filas.append(f"| {nombre} | {rel} | {c['walls']} | {c['doors']} | {c['windows']} | {c['openings']} | {d['wall_thickness']} | {nota} |")
        svg = r.svg.replace("<svg ", '<svg style="width:100%;height:auto;border:1px solid #ccc" ', 1)
        html.append(f"<h3>{nombre} · {rel}</h3><div style='display:flex;gap:6px'><img style='width:49%;object-fit:contain;align-self:flex-start' src='{_miniatura(p)}'><div style='width:49%'>{svg}</div></div>")
    (SALIDA / "indice.md").write_text("\n".join(filas) + "\n", encoding="utf-8")
    (SALIDA / "index.html").write_text("<html><meta charset='utf-8'><body style='font:13px sans-serif;margin:6px'>" + "".join(html) + "</body></html>", encoding="utf-8")
    print(f"{len(archivos)} muestras -> {SALIDA} (out_01 ... out_{len(archivos):02d})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
