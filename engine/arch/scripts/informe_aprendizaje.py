"""Estudia todas las muestras de `samples/` con el motor y deja UN solo informe, `out/aprendizaje.html`: qué tienen en común los planos (estilo de dibujo, grosor de muro, proporciones
de puertas y ventanas, ortogonalidad), cada muestra con su original y su resultado, la biblioteca de símbolos y lo que todavía falla.

Uso: python scripts/informe_aprendizaje.py
El informe queda en `out/` (fuera de git): incluye miniaturas de las muestras.
"""
import base64
import io
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from epc_arch import ArchError, Options, pdf_to_png, recognize   # noqa: E402
from epc_arch.geometry import angle_gap, seg_angle, seg_length   # noqa: E402
from epc_arch.sources.raster import close_gaps, otsu, wall_size   # noqa: E402

MUESTRAS = RAIZ / "samples"
SALIDA = RAIZ / "out"
EXT = (".pdf", ".dxf", ".png", ".jpg", ".jpeg", ".webp", ".avif", ".bmp", ".tif", ".tiff")


def _bytes(p: Path) -> bytes:
    datos = p.read_bytes()
    if p.suffix.lower() in (".webp", ".avif"):
        b = io.BytesIO()
        Image.open(io.BytesIO(datos)).convert("RGB").save(b, "PNG")
        return b.getvalue()
    return datos


def _imagen(p: Path) -> Image.Image:
    if p.suffix.lower() == ".pdf":
        return Image.open(io.BytesIO(pdf_to_png(p.read_bytes(), 0, 1200))).convert("RGB")
    return Image.open(p).convert("RGB")


def _miniatura(im: Image.Image) -> str:
    im = im.copy()
    im.thumbnail((520, 520))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=68)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def _estilo(p: Path, im: Image.Image) -> str:
    """Cómo dibuja los muros la muestra, visto en el dibujo mismo."""
    if p.suffix.lower() in (".pdf", ".dxf"):
        return "vectorial"
    g = np.asarray(im.convert("L"))
    level = otsu(g)
    ink = g <= level
    if ink.mean() > 0.5:
        return "plano azul (invertido)"
    if ((g > 50) & (g < 205)).mean() > 0.6:
        return "render o foto"
    sat = np.asarray(im.convert("HSV"))[..., 1]
    color = (sat > 60).mean() > 0.15
    return ("trazo grueso" if wall_size(close_gaps(ink)) else "doble línea fina") + (" con color" if color else "")


def _grosores(walls, T):
    """Clases de grosor de los muros: el exterior suele ser más grueso que el interior."""
    if not walls or not T:
        return []
    clases = Counter(round(w.thickness / T * 4) / 4 for w in walls)
    return sorted(clases.items())


def estudiar():
    filas = []
    for n, p in enumerate(sorted(q for q in MUESTRAS.rglob("*") if q.is_file() and q.suffix.lower() in EXT), 1):
        im = _imagen(p)
        fila = {"n": n, "muestra": p.relative_to(MUESTRAS).as_posix(), "img": _miniatura(im), "estilo": _estilo(p, im)}
        try:
            r = recognize(_bytes(p), p.name, Options(background=False))
        except ArchError as e:
            fila["error"] = str(e)
            filas.append(fila)
            continue
        a = r.architecture
        T = a.wall_thickness
        lado = max(a.size)
        largos = [seg_length(w.a, w.b) for w in a.walls]
        if a.walls:
            dom = Counter(round(seg_angle(w.a, w.b)) % 90 for w in a.walls).most_common(1)[0][0]
            orto = sum(l for w, l in zip(a.walls, largos) if min(angle_gap(seg_angle(w.a, w.b), dom), angle_gap(seg_angle(w.a, w.b), dom + 90)) <= 2) / (sum(largos) or 1)
        else:
            orto = None
        fila.update({
            "svg": r.svg.replace("<svg ", '<svg style="width:100%;height:auto;max-height:520px" ', 1),
            "conteo": a.counts(), "T": T, "T_rel": (T / lado * 100) if T else None, "orto": orto,
            "largo_rel": sum(largos) / lado if largos else 0.0, "grosores": _grosores(a.walls, T),
            "puertas_T": [o.width / T for o in a.openings if o.kind == "door" and T],
            "ventanas_T": [o.width / T for o in a.openings if o.kind == "window" and T],
            "avisos": a.warnings,
        })
        filas.append(fila)
    return filas


def _med(xs, fmt="{:.1f}"):
    xs = [x for x in xs if x is not None]
    return fmt.format(st.median(xs)) if xs else "—"


def _rango(xs):
    xs = sorted(x for x in xs if x is not None)
    if len(xs) < 4:
        return "—"
    q = lambda f: xs[min(len(xs) - 1, int(f * len(xs)))]          # noqa: E731
    return f"{q(0.25):.1f} – {q(0.75):.1f}"


def _juicio(f) -> str:
    """Una palabra honesta sobre la muestra, por lo que el motor encontró."""
    if "error" in f:
        return "no se lee"
    c = f["conteo"]
    if c["walls"] == 0:
        return "sin muros"
    if c["walls"] > 150:
        return "ruido"
    if f["orto"] is not None and f["orto"] < 0.8:
        return "girado o curvo"
    if c["doors"] + c["windows"] == 0:
        return "muros sin aberturas"
    return "bien"


CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1f2933;--muted:#6b7280;--line:#e3e6ea;--acc:#b45309;--ok:#15803d;--warn:#b91c1c;--blue:#2563eb}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#111418;--card:#1a1e24;--ink:#e6e8eb;--muted:#9aa3ae;--line:#2a3038}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px 16px 64px}h1{font-size:28px;margin:0 0 4px}h2{font-size:20px;margin:40px 0 12px;padding-top:8px;border-top:1px solid var(--line)}
p.sub{color:var(--muted);margin:0 0 20px}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}.kpi b{display:block;font-size:24px}.kpi span{color:var(--muted);font-size:13px}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:14px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:var(--muted);font-weight:600}
ul.learn li{margin:6px 0}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;margin:14px 0}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:10px}.pair img{width:100%;height:auto;max-height:520px;object-fit:contain;background:#fff;border-radius:6px}
.pair .svgbox{background:#fff;border-radius:6px;overflow:hidden}.meta{color:var(--muted);font-size:13px;margin-top:6px}
.tag{display:inline-block;font-size:12px;padding:1px 8px;border-radius:99px;border:1px solid var(--line);margin-left:6px}
.tag.bien{color:var(--ok)}.tag.ruido,.tag.no,.tag.sin{color:var(--warn)}.lib img{width:100%;background:#fff;border-radius:8px}
@media (max-width:700px){.pair{grid-template-columns:1fr}}
"""


def informe(filas) -> str:
    ok = [f for f in filas if "error" not in f]
    estilos = Counter(f["estilo"] for f in filas)
    juicios = Counter(_juicio(f) for f in filas)
    puertas = [x for f in ok for x in f["puertas_T"]]
    ventanas = [x for f in ok for x in f["ventanas_T"]]
    ratios = []
    for f in ok:
        gs = [g for g, k in f["grosores"] if k >= 2]
        if len(gs) >= 2:
            ratios.append(max(gs) / min(gs))
    total = Counter()
    for f in ok:
        total.update(f["conteo"])
    h = [f"<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Aprendizaje de planos</title><style>{CSS}</style></head><body><main>"]
    h.append("<h1>Lo aprendido de las muestras</h1>")
    h.append(f"<p class='sub'>{len(filas)} muestras estudiadas con el motor <code>epc_arch</code>: qué tienen en común, cómo se reconocen los muros, puertas y ventanas, y dónde falla todavía.</p>")
    h.append("<div class='kpis'>")
    for v, t in ((len(filas), "muestras"), (juicios.get("bien", 0), "se leen bien"), (total["walls"], "muros encontrados"), (total["doors"], "puertas"), (total["windows"], "ventanas"),
                 (_med([f["T_rel"] for f in ok], "{:.2f} %"), "grosor de muro típico (del lado mayor)")):
        h.append(f"<div class='kpi'><b>{v}</b><span>{t}</span></div>")
    h.append("</div>")

    h.append("<h2>Puntos comunes</h2><ul class='learn'>")
    h.append(f"<li><b>Los muros corren en dos direcciones.</b> En la mediana, el {_med([f['orto'] * 100 for f in ok if f['orto'] is not None], '{:.0f}')} % del largo de muro está a 0° o 90° del eje principal del plano. Por eso el motor alinea, une y cierra los muros sobre dos ejes.</li>")
    h.append(f"<li><b>El muro es lo más grueso del dibujo.</b> Su grosor ronda el {_med([f['T_rel'] for f in ok], '{:.2f}')} % del lado mayor (cuartiles {_rango([f['T_rel'] for f in ok])} %). Texto, cotas, muebles y tramas son más finos: se separan abriendo la tinta con un cuadrado apenas menor que el muro.</li>")
    h.append(f"<li><b>Hay dos grosores.</b> Donde se distinguen, el muro exterior es {_med(ratios)} veces el interior (cuartiles {_rango(ratios)}). Cada muro conserva el suyo.</li>")
    h.append("<li><b>Un muro es un tramo continuo</b> que solo cortan puertas y ventanas. Las hojas de puerta y los muebles pegados al muro no lo parten.</li>")
    h.append(f"<li><b>Puertas:</b> arco fino de un cuarto de círculo con la hoja; el cuarto de círculo que barre está vacío. Ancho típico {_med(puertas)} grosores de muro (cuartiles {_rango(puertas)}). La mayoría están en esquinas o uniones en T, entre el extremo de un muro y la cara del que lo cruza.</li>")
    h.append(f"<li><b>Ventanas:</b> hueco en el muro con 2 o 3 líneas finas paralelas. Ancho típico {_med(ventanas)} grosores (cuartiles {_rango(ventanas)}). Casi siempre en muros exteriores.</li>")
    h.append("</ul>")

    h.append("<h2>Cómo están dibujadas</h2><table><tr><th>Estilo de dibujo</th><th>Muestras</th><th>Cómo se leen</th></tr>")
    como = {"trazo grueso": "Muros desde la mancha gruesa: el mejor caso en imágenes.", "trazo grueso con color": "Mancha gruesa, pero los rellenos de color pueden confundirse con muro.",
            "doble línea fina": "Pares de líneas paralelas a un grosor de muro; más sensible a cotas y muebles.", "doble línea fina con color": "Pares de líneas; el color complica.",
            "vectorial": "Trazo por trazo, exacto: la mejor fuente.", "plano azul (invertido)": "Se invierte y se lee como trazo.", "render o foto": "No se lee: hace falta un dibujo en líneas."}
    for e, k in estilos.most_common():
        h.append(f"<tr><td>{e}</td><td>{k}</td><td>{como.get(e, '')}</td></tr>")
    h.append("</table>")

    h.append("<h2>Resultado por muestra</h2><table><tr><th>#</th><th>Muestra</th><th>Estilo</th><th>Muros</th><th>Puertas</th><th>Ventanas</th><th>Juicio</th></tr>")
    for f in filas:
        c = f.get("conteo", {})
        h.append(f"<tr><td>{f['n']:02d}</td><td>{f['muestra']}</td><td>{f['estilo']}</td><td>{c.get('walls', '—')}</td><td>{c.get('doors', '—')}</td><td>{c.get('windows', '—')}</td><td>{_juicio(f)}</td></tr>")
    h.append("</table>")

    h.append("<h2>Lado a lado</h2><p class='sub'>Izquierda: la muestra. Derecha: lo que reconoce el motor, dibujado limpio.</p>")
    for f in filas:
        j = _juicio(f)
        h.append(f"<div class='card'><b>{f['n']:02d} · {f['muestra']}</b><span class='tag {j.split()[0]}'>{j}</span>")
        if "error" in f:
            h.append(f"<div class='pair'><img src='{f['img']}' alt=''><div class='meta'>{f['error']}</div></div></div>")
            continue
        c = f["conteo"]
        h.append(f"<div class='pair'><img src='{f['img']}' alt=''><div class='svgbox'>{f['svg']}</div></div>")
        h.append(f"<div class='meta'>{f['estilo']} · {c['walls']} muros · {c['doors']} puertas · {c['windows']} ventanas · {c['openings']} huecos · grosor {f['T']:.1f}</div></div>" if f["T"] else "</div>")

    lib = RAIZ / "biblioteca" / "hoja-contacto.svg"
    if lib.exists():
        h.append("<h2>Biblioteca de símbolos</h2><p class='sub'>25 símbolos de planta en <code>biblioteca/svg/</code> (1 unidad = 1 cm), para cuando se reconozcan muebles.</p>")
        h.append("<div class='card lib'><img alt='' src='data:image/svg+xml;base64," + base64.b64encode(lib.read_bytes()).decode() + "'></div>")

    h.append("<h2>Lo que todavía falla</h2><ul class='learn'>")
    for j, k in juicios.most_common():
        if j != "bien":
            h.append(f"<li><b>{j}</b>: {k} muestras — " + ", ".join(f"{f['n']:02d}" for f in filas if _juicio(f) == j) + ".</li>")
    h.append("<li>Las puertas son lo más débil: se encuentran donde el muro deja un hueco claro y el arco está limpio; con marcas encima o arcos cortados por muebles se pierden.</li>")
    h.append("<li>Los planos a color con rellenos oscuros, los girados y las láminas con interfaz de programa necesitan otro tratamiento.</li></ul>")
    h.append("</main></body></html>")
    return "".join(h)


def main() -> int:
    filas = estudiar()
    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "aprendizaje.html").write_text(informe(filas), encoding="utf-8")
    datos = [{k: v for k, v in f.items() if k not in ("img", "svg")} for f in filas]
    (SALIDA / "aprendizaje.json").write_text(json.dumps(datos, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    print(f"{len(filas)} muestras -> {SALIDA / 'aprendizaje.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
