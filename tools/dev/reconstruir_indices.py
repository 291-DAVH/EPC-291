"""reconstruir_indices.py — Reconstruye _catalog.json y _library.svg de un plugin.

Uso: python3 reconstruir_indices.py <directorio_plugin> [--bump minor|patch]

1. Lee todos los SVG del plugin y extrae id, viewBox, puertos y label_slots.
2. Fusiona con _catalog.json existente (preserva campos manuales).
3. Actualiza _library.svg con un <symbol> por símbolo (sin ports ni slots).
4. Incrementa la versión (patch por defecto).
"""
import argparse, json, os, sys
import xml.etree.ElementTree as ET
from datetime import date

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def parse_viewbox(vb):
    parts = list(map(float, vb.strip().split()))
    return {"x": parts[0], "y": parts[1], "w": parts[2], "h": parts[3]} if len(parts) == 4 else None


def extract_ports(root):
    ports = []
    g = root.find(f".//{{{SVG_NS}}}g[@id='ports']")
    if g is None:
        return ports
    for c in g.findall(f"{{{SVG_NS}}}circle"):
        ports.append({"id": c.get("id","").replace("port_",""),
                      "x": float(c.get("cx",0)), "y": float(c.get("cy",0)),
                      "dir": c.get("data-dir","")})
    return ports


def extract_slots(root):
    slots = []
    g = root.find(f".//{{{SVG_NS}}}g[@id='label_slots']")
    if g is None:
        return slots
    for t in g.findall(f".//{{{SVG_NS}}}text"):
        key = t.get("data-key","")
        if key:
            slots.append({"key": key, "placeholder": t.get("data-placeholder",f"{{{key}}}"),
                          "example": t.get("data-example",""), "x": float(t.get("x",0)),
                          "y": float(t.get("y",0)), "anchor": t.get("text-anchor","start"),
                          "size": float(t.get("font-size",3.47))})
    return slots


def symbol_body(root):
    main_g = next((g for g in root.findall(f"{{{SVG_NS}}}g")
                   if g.get("id","") and g.get("id") not in ("ports","label_slots")), None)
    if main_g is None:
        return ""
    return "\n".join(ET.tostring(c, encoding="unicode") for c in main_g
                     if c.get("id","") not in ("ports","label_slots"))


def bump_version(v, kind):
    parts = (v.split(".") + ["0","0","0"])[:3]
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if kind == "minor":
        minor += 1; patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directorio")
    parser.add_argument("--bump", choices=["minor","patch"], default="patch")
    args = parser.parse_args()
    d = args.directorio

    catalog_path = os.path.join(d, "_catalog.json")
    existing = {}
    header = {}
    if os.path.exists(catalog_path):
        with open(catalog_path, encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict) and "symbols" in raw:
            header = {k: v for k,v in raw.items() if k != "symbols"}
            for s in raw["symbols"]: existing[s["id"]] = s
        elif isinstance(raw, list):
            for s in raw: existing[s["id"]] = s

    header["version"] = bump_version(header.get("version","2.0.0"), args.bump)
    header["generated"] = date.today().isoformat()

    svg_files = sorted(f for f in os.listdir(d) if f.endswith(".svg") and not f.startswith("_"))
    new_symbols, symbol_defs = [], []

    for fname in svg_files:
        path = os.path.join(d, fname)
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as e:
            print(f"  [error] {fname}: {e}"); continue

        sym_id = os.path.splitext(fname)[0]
        vb_str = root.get("viewBox","")
        vb = parse_viewbox(vb_str) if vb_str else None
        ports, slots = extract_ports(root), extract_slots(root)
        base = existing.get(sym_id, {})

        sym = {"id": sym_id, "file": fname,
               "name_es": base.get("name_es", sym_id.replace("_"," ")),
               "name_en": base.get("name_en",""),
               "description": base.get("description",""),
               "tags": base.get("tags",[]),
               "origin": base.get("origin","drawn"),
               "source": base.get("source",""),
               "notes": base.get("notes", None),
               "iec_60617": base.get("iec_60617",[])}
        if vb:
            sym["viewBox"] = vb
            sym["size"] = {"w": round(vb["w"],2), "h": round(vb["h"],2)}
        if ports: sym["ports"] = ports
        if slots: sym["label_slots"] = slots
        for k in ("diagram_type","sld_equivalent","mld_equivalent","poles",
                  "terminal_marks","conventions","fixed_texts"):
            if k in base: sym[k] = base[k]

        new_symbols.append(sym)
        body = symbol_body(root)
        if vb_str:
            symbol_defs.append(f'  <symbol id="{sym_id}" viewBox="{vb_str}" overflow="visible">\n{body}\n  </symbol>')
        print(f"  ok {sym_id}  ({len(ports)}p {len(slots)}s)")

    catalog_out = dict(header)
    catalog_out["symbols"] = new_symbols
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog_out, f, ensure_ascii=False, indent=2)
    print(f"\nok _catalog.json: {len(new_symbols)} símbolos v{header['version']}")

    library_path = os.path.join(d, "_library.svg")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             f'<svg xmlns="{SVG_NS}" xmlns:xlink="http://www.w3.org/1999/xlink">',
             "  <defs>"] + symbol_defs + ["  </defs>", "</svg>"]
    with open(library_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"ok _library.svg: {len(symbol_defs)} símbolos")


if __name__ == "__main__":
    main()
