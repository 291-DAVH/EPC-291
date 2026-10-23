"""CAL-023 · aea_export — Exportación del cálculo a JSON (único entregable; sin PDF).

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Todo el resultado del dimensionado se entrega como UN archivo JSON (`<proyecto>_calculo.json`)
    que consume `sld-generator`. Este módulo construye, valida, exporta y carga ese archivo.
    NO genera PDF, Word ni Markdown.

FORMATO (ver `example_calculo.json`)
    Objeto cuyas claves son los ID de circuito (p. ej. "C-01", "G-02-A", "L-01"); cada valor:
        "In"   : corriente nominal de la protección [A]            (número > 0)
        "Ib"   : corriente de proyecto del circuito [A]            (número > 0)
        "icu"  : poder de corte de la protección [kA]              (número > 0)
        "S"    : sección adoptada del conductor [mm²]              (número > 0)
        "dU"   : caída de tensión acumulada [%]                    (número ≥ 0)
        "disp" : dispositivo de protección/maniobra, texto libre   (p. ej. "MCB > KM (10 A)")
    Orden de claves en el archivo: el de inserción. Sin campos adicionales (el SLD no los admite).

VALIDACIÓN
    ERROR  : falta un campo, campo extra, tipo o rango inválido, `disp` vacío, ID vacío.
    AVISO  : In < Ib; In no aparece en `disp`; dU > 5 %; S fuera de la serie normalizada.

UNIDADES
    A, kA, mm², %.

NORMA DE REFERENCIA
    Contrato de datos con `sld-generator` (sin norma); los valores salen de los módulos `aea_*`.
"""
import json
import math
import os
import re
import sys

__version__ = "0.1.0"

FIELDS = ("In", "Ib", "icu", "S", "dU", "disp")
SERIE_S_MM2 = (0.5, 0.75, 1, 1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300, 400, 500, 630)
DU_AVISO_PCT = 5.0


def _es_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def circuito_json(i_n_a, i_b_a, icu_ka, s_mm2, du_pct, disp, decimales=2):
    """Arma el registro de un circuito (redondea Ib, S y dU)."""
    r = {"In": _limpio(i_n_a), "Ib": round(float(i_b_a), 1), "icu": _limpio(icu_ka),
         "S": _limpio(s_mm2), "dU": round(float(du_pct), decimales), "disp": str(disp)}
    return r


def _limpio(v):
    """Enteros como int (250, no 250.0)."""
    return int(v) if float(v) == int(v) else float(v)


def validate_calculation(datos):
    """Devuelve {'errores': [...], 'avisos': [...]} (listas de str)."""
    err, av = [], []
    if not isinstance(datos, dict) or not datos:
        return {"errores": ["el cálculo debe ser un objeto no vacío {id_circuito: {...}}"], "avisos": []}
    for cid, c in datos.items():
        if not isinstance(cid, str) or not cid.strip():
            err.append(f"ID de circuito inválido: {cid!r}")
            continue
        if not isinstance(c, dict):
            err.append(f"{cid}: debe ser un objeto")
            continue
        falta = [k for k in FIELDS if k not in c]
        extra = [k for k in c if k not in FIELDS]
        if falta:
            err.append(f"{cid}: faltan campos {falta}")
        if extra:
            err.append(f"{cid}: campos no admitidos {extra}")
        if falta:
            continue
        for k in ("In", "Ib", "icu", "S"):
            if not _es_num(c[k]) or c[k] <= 0:
                err.append(f"{cid}: {k} debe ser un número > 0 (recibido: {c[k]!r})")
        if not _es_num(c["dU"]) or c["dU"] < 0:
            err.append(f"{cid}: dU debe ser un número ≥ 0 (recibido: {c['dU']!r})")
        if not isinstance(c["disp"], str) or not c["disp"].strip():
            err.append(f"{cid}: disp debe ser un texto no vacío")
            continue
        if all(_es_num(c[k]) for k in ("In", "Ib", "S", "dU")):
            if c["In"] < c["Ib"]:
                av.append(f"{cid}: In ({c['In']}) < Ib ({c['Ib']})")
            if not re.search(r"(?<![\d.])" + re.escape(str(c["In"])) + r"(?![\d.])", c["disp"]):
                av.append(f"{cid}: In ({c['In']}) no aparece en disp «{c['disp']}»")
            if c["dU"] > DU_AVISO_PCT:
                av.append(f"{cid}: dU {c['dU']} % > {DU_AVISO_PCT} %")
            if c["S"] not in SERIE_S_MM2:
                av.append(f"{cid}: S {c['S']} mm² fuera de la serie normalizada")
    return {"errores": err, "avisos": av}


def export_calculation(datos, ruta):
    """Valida y escribe el JSON (UTF-8, sin BOM, sangría 1). Rechaza rutas .pdf/.docx/.md.
    Lanza ValueError si hay errores; devuelve los avisos."""
    if os.path.splitext(ruta)[1].lower() != ".json":
        raise ValueError("el cálculo se exporta solo como .json (sin PDF)")
    v = validate_calculation(datos)
    if v["errores"]:
        raise ValueError("cálculo inválido: " + "; ".join(v["errores"]))
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return v["avisos"]


def load_calculation(ruta):
    """Lee el JSON (acepta BOM) y lo devuelve validado; lanza ValueError si hay errores."""
    with open(ruta, encoding="utf-8-sig") as f:
        datos = json.load(f)
    v = validate_calculation(datos)
    if v["errores"]:
        raise ValueError("cálculo inválido: " + "; ".join(v["errores"]))
    return datos


def _main(argv):
    if len(argv) == 2 and argv[0] == "validar":
        with open(argv[1], encoding="utf-8-sig") as f:
            v = validate_calculation(json.load(f))
        for e in v["errores"]:
            print("ERROR:", e)
        for a in v["avisos"]:
            print("AVISO:", a)
        print("OK" if not v["errores"] else "CON ERRORES")
        return 1 if v["errores"] else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
