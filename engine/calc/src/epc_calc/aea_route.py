"""aea_route — Recorrido real de un cable: tramos con instalaciones distintas y capacidad de conducción gobernante.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Un cable que sale de un tablero (o la acometida de otro tablero) rara vez tiene una sola instalación: puede ir en bandeja,
    caer a una cámara de pase, seguir directamente enterrado, pasar a un tramo en caño enterrado, cruzar una calzada y subir
    por bandeja a un piso. Cada tramo tiene su método de instalación (tablas 771.16), su temperatura (aire o suelo), su
    resistividad térmica del terreno y su agrupamiento. La capacidad de conducción del cable es la del tramo más desfavorable;
    la caída de tensión se calcula con la longitud total.

TRAMO (dict)
    kind        tray_perforated | tray_solid | conduit_air | chamber | buried_direct | buried_duct | road_crossing
    length_m    longitud del tramo [m]
    label       descripción libre ("Bandeja hasta cámara C-1")
    ambient_c   temperatura ambiente [°C] (tramos en aire; por defecto la del proyecto)
    soil_c      temperatura del suelo [°C] (tramos enterrados; por defecto la del proyecto)
    rho_kmw     resistividad térmica del terreno [K·m/W] (tramos enterrados; por defecto la del proyecto)
    circuits    cantidad de circuitos que comparten ese tramo, el propio incluido (agrupamiento, por defecto 1)
    depth_m     profundidad [m] (informativa; las tablas 771.16.V y VI son para 0,7 m)

FÓRMULAS
    Iz_tramo(S) = N · Iz0(método, S) · f_temp · f_agrup · f_suelo      (aea_ampacity.iz con los parámetros del tramo)
    Iz(S) = min sobre los tramos de Iz_tramo(S) ;  L = Σ L_tramo

LIMITACIONES
    - El tramo limitante gobierna aunque sea corto: la norma permite justificar tramos cortos con un análisis térmico, que no se
      hace acá [VERIFICAR].
    - Cámara de pase = cable en aire sobre soportes (método E/F). Cruce bajo calzada = caño enterrado (D1), con su profundidad.
    - La profundidad no modifica el cálculo: las tablas son para 0,7 m [VERIFICAR para mayores profundidades].
    - Unipolares en caño (B1) solo existe para PVC; con XLPE se usa B2 y se avisa.

NORMA DE REFERENCIA
    AEA 90364-7-771 §16 (771.16.I a VII) ; IEC 60364-5-52.  [VERIFICAR]
"""
from typing import Dict, List, Optional, Tuple

from epc_calc import aea_ampacity as AMP

__version__ = "0.1.0"

#: tipo de tramo -> (método con cable multipolar, método con unipolares)
KINDS: Dict[str, Tuple[str, str]] = {
    "tray_perforated": ("E", "F"),
    "tray_solid": ("C", "C"),
    "conduit_air": ("B2", "B1"),
    "chamber": ("E", "F"),
    "buried_direct": ("D2", "D2"),
    "buried_duct": ("D1", "D1"),
    "road_crossing": ("D1", "D1"),
}
BURIED = ("buried_direct", "buried_duct", "road_crossing")
MAX_SEGMENTS = 20
DEPTH_REFERENCE_M = 0.7


def validate(route: List[dict]) -> Dict[str, str]:
    """Errores del recorrido por campo (vacío si es válido). Un recorrido vacío es válido: se usa la instalación del circuito."""
    e: Dict[str, str] = {}
    if len(route) > MAX_SEGMENTS:
        e["route"] = f"up to {MAX_SEGMENTS} segments"
    for i, s in enumerate(route[:MAX_SEGMENTS], 1):
        k = f"segment {i}"
        if s.get("kind") not in KINDS:
            e[f"{k}.kind"] = "one of " + ", ".join(KINDS)
        if not isinstance(s.get("length_m"), (int, float)) or isinstance(s.get("length_m"), bool) or not 0 < s["length_m"] <= 5000:
            e[f"{k}.length_m"] = "between 0 and 5000 m"
        n = s.get("circuits", 1)
        if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 20:
            e[f"{k}.circuits"] = "between 1 and 20"
        for fld, lo, hi in (("ambient_c", 0, 80), ("soil_c", 0, 60), ("rho_kmw", 0.3, 5), ("depth_m", 0, 5)):
            v = s.get(fld)
            if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi):
                e[f"{k}.{fld}"] = f"between {lo} and {hi}"
    return e


def total_length(route: List[dict]) -> float:
    return round(sum(float(s["length_m"]) for s in route), 3)


def segment_params(base: dict, seg: dict, defaults: dict, multipolar: bool) -> dict:
    """Parámetros de aea_ampacity del tramo: los del circuito (material, aislación, clase, ternas) con el método, temperaturas y agrupamiento del tramo."""
    metodo = KINDS[seg["kind"]][0 if multipolar else 1]
    p = dict(base)
    p.update(metodo=metodo, agrup=int(seg.get("circuits") or 1),
             t_amb=float(seg.get("ambient_c") if seg.get("ambient_c") is not None else defaults.get("t_amb", base["t_amb"])),
             t_suelo=float(seg.get("soil_c") if seg.get("soil_c") is not None else defaults.get("t_suelo", base["t_suelo"])),
             rho=float(seg.get("rho_kmw") if seg.get("rho_kmw") is not None else defaults.get("rho", base["rho"])))
    return p


def _iz_tramo(p: dict, s: float, fases: int) -> Tuple[float, str, Optional[str]]:
    """(Iz, método usado, aviso). B1 con XLPE no tiene tabla: se usa B2 y se avisa."""
    try:
        return AMP.iz(p, s, fases), p["metodo"], None
    except ValueError:
        if p["metodo"] == "B1":
            q = dict(p, metodo="B2")
            return AMP.iz(q, s, fases), "B2", "unipolares en caño con esta aislación no tienen tabla (B1): se usó B2"
        raise


def iz_ruta(base: dict, route: List[dict], s: float, fases: int, defaults: dict, multipolar: bool = True) -> dict:
    """Capacidad de conducción de la sección `s` a lo largo del recorrido.

    Devuelve {"iz_a": Iz gobernante, "limitante": índice (0 = primer tramo), "tramos": [{...por tramo...}], "avisos": [...]}.
    ValueError si algún tramo no tiene tabla para esa sección."""
    tramos, avisos = [], []
    for i, seg in enumerate(route):
        p = segment_params(base, seg, defaults, multipolar)
        iz, metodo, aviso = _iz_tramo(p, s, fases)
        if aviso:
            avisos.append(f"tramo {i + 1}: {aviso}")
        f = AMP.factores(dict(p, metodo=metodo), fases == 3)
        tramos.append({"n": i + 1, "kind": seg["kind"], "label": seg.get("label", ""), "length_m": float(seg["length_m"]), "metodo": metodo,
                       "circuits": p["agrup"], "t_amb": p["t_amb"], "t_suelo": p["t_suelo"], "rho_kmw": p["rho"], "depth_m": seg.get("depth_m"),
                       "iz_a": round(iz, 1), "f_temp": round(f["f_temp"], 3), "f_agrup": round(f["f_agrup"], 3), "f_suelo": round(f["f_suelo"], 3)})
    lim = min(range(len(tramos)), key=lambda i: tramos[i]["iz_a"])
    for i, t in enumerate(tramos):
        t["limitante"] = i == lim
    return {"iz_a": tramos[lim]["iz_a"], "limitante": lim, "tramos": tramos, "avisos": avisos}


def route_warnings(route: List[dict]) -> List[str]:
    """Avisos de datos que el cálculo no corrige (profundidad distinta de la de las tablas)."""
    out = []
    for i, s in enumerate(route, 1):
        d = s.get("depth_m")
        if s.get("kind") in BURIED and d is not None and d > DEPTH_REFERENCE_M + 1e-9:
            out.append(f"tramo {i}: profundidad {d:g} m mayor que la de las tablas ({DEPTH_REFERENCE_M} m): verificar el factor [VERIFICAR]")
    return out
