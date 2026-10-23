"""preview.py — Genera una hoja de muestra PNG de todos los símbolos de una biblioteca.

Uso: python3 preview.py <directorio_plugin> [salida.png] [--px-por-mm=6]

Requiere: cairosvg, Pillow (pip install cairosvg Pillow).
"""
import argparse, json, os, sys, tempfile

try:
    import cairosvg
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Faltan dependencias. Instalar con: pip install cairosvg Pillow")
    sys.exit(1)


def render_svg_to_png(svg_path, px_per_mm):
    png_bytes = cairosvg.svg2png(url=svg_path, dpi=25.4 * px_per_mm)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png_bytes)
        tmp = f.name
    img = Image.open(tmp).convert("RGBA")
    os.unlink(tmp)
    return img


def main():
    parser = argparse.ArgumentParser(description="Preview PNG de una biblioteca de símbolos.")
    parser.add_argument("directorio")
    parser.add_argument("salida", nargs="?")
    parser.add_argument("--px-por-mm", type=float, default=6.0, dest="px_por_mm")
    args = parser.parse_args()

    catalog_path = os.path.join(args.directorio, "_catalog.json")
    if not os.path.exists(catalog_path):
        print(f"Error: no se encontró {catalog_path}"); sys.exit(1)

    with open(catalog_path, encoding="utf-8") as f:
        catalog = json.load(f)

    raw = catalog.get("symbols", catalog) if isinstance(catalog, dict) and "symbols" in catalog else (
        catalog if isinstance(catalog, list) else list(catalog.values()))
    symbols = [s for s in raw if isinstance(s, dict)]

    out_path = args.salida or os.path.join(args.directorio, "_preview.png")
    px = args.px_por_mm
    cols, cell_w, cell_h, label_h, margin = 5, int(50*px), int(55*px), int(10*px), int(5*px)

    rendered = []
    for sym in symbols:
        sym_id = sym.get("id", "?")
        svg_path = os.path.join(args.directorio, sym.get("file", sym_id + ".svg"))
        if not os.path.exists(svg_path):
            continue
        try:
            rendered.append((sym_id, render_svg_to_png(svg_path, px)))
            print(f"  ok {sym_id}")
        except Exception as e:
            print(f"  error {sym_id}: {e}")

    if not rendered:
        print("Sin símbolos."); sys.exit(0)

    rows = (len(rendered) + cols - 1) // cols
    canvas = Image.new("RGBA", (cols*cell_w + 2*margin, rows*cell_h + 2*margin), (255,255,255,255))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", int(4*px))
    except Exception:
        font = ImageFont.load_default()

    for idx, (sym_id, img) in enumerate(rendered):
        col, row = idx % cols, idx // cols
        cx = margin + col*cell_w + cell_w//2
        sym_area_w, sym_area_h = cell_w - int(4*px), cell_h - label_h - int(4*px)
        scale = min(sym_area_w/max(img.width,1), sym_area_h/max(img.height,1), 1.0)
        nw, nh = max(1,int(img.width*scale)), max(1,int(img.height*scale))
        resized = img.resize((nw, nh), Image.LANCZOS)
        paste_x = cx - nw//2
        paste_y = margin + row*cell_h + (cell_h - label_h - nh)//2
        canvas.paste(resized, (paste_x, paste_y), resized)
        try:
            bbox = draw.textbbox((0,0), sym_id, font=font)
            tw = bbox[2] - bbox[0]
        except Exception:
            tw = len(sym_id)*int(3*px)
        draw.text((cx - tw//2, margin + row*cell_h + cell_h - label_h), sym_id, fill=(0,0,128), font=font)
        x0c, y0c = margin + col*cell_w, margin + row*cell_h
        draw.rectangle([x0c, y0c, x0c+cell_w-1, y0c+cell_h-1], outline=(200,200,200))

    canvas.convert("RGB").save(out_path)
    print(f"\nPreview: {out_path}  ({len(rendered)} símbolos)")


if __name__ == "__main__":
    main()
