"""CAL-009 · conductor_selection — Sección mínima de conductor por conducción y por caída de tensión.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Dada la corriente de proyecto Ib, la longitud y una TABLA de capacidades/resistencias
    pasada como parámetro (JSON o dict), devolver la sección mínima por (a) capacidad de
    conducción y (b) caída de tensión (reutiliza CAL-002 `voltage_drop.py`), y la protección
    (menor In de la serie pasada como parámetro con Ib ≤ In ≤ Iz).

REGLA DE DATOS (calc-library.md, regla 5)
    El módulo NO embebe ninguna tabla normativa ni serie de interruptores: la tabla de
    capacidades (Iz, R, X por sección), los factores de agrupamiento y temperatura, la serie
    de In y el límite de caída de tensión son PARÁMETROS que el ingeniero toma de la norma
    vigente (ficha de extracto de la norma (`calc-library.md`, regla 9)). Si falta la tabla, el resultado
    es 'NO VERIFICABLE'.

FORMATO DE LA TABLA (JSON)
    {
      "_encabezado": "texto libre; si contiene 'FICTICIO' se advierte que no es válida",
      "fuente": {"id_nrm": "NRM-nnn", "edicion": "...", "tabla": "...", "pagina": "..."},
      "conductores": [
        {"seccion_mm2": 2.5, "i_adm_a": 27.0, "r_ohm_km": 7.41, "x_ohm_km": 0.10}, ...
      ]
    }
    i_adm_a = capacidad de conducción para el método de instalación y material elegidos;
    r_ohm_km / x_ohm_km a la temperatura de servicio (x_ohm_km opcional: 0 con advertencia).

PROCEDIMIENTO
    1. In = menor valor de la serie con In ≥ Ib (si se pasa serie). Sin serie: protección
       'NO VERIFICABLE' y la conducción se verifica contra Ib.
    2. Iz = i_adm · f_agrupamiento · f_temperatura.
    3. Conducción: menor sección con Iz ≥ In (o ≥ Ib sin serie)  [Ib ≤ In ≤ Iz].
    4. Caída de tensión con Ib (CAL-002): menor sección con ΔU% ≤ límite.
    5. Sección mínima = la mayor de ambas; se verifica de nuevo conducción y caída.

LIMITACIONES
    - No verifica I2 ≤ 1,45·Iz (depende del dispositivo de protección), ni cortocircuito
      (CAL-005), ni agrupamientos múltiples distintos de un único factor.
    - Un solo conductor por fase; sin neutro; sin corrección de R por temperatura.
    - El resultado es tan válido como la tabla recibida (revisar su ficha de extracto).

NORMA DE REFERENCIA (por designación)
    - IEC 60364-5-52 (capacidades, factores), IEC 60364-4-43 (Ib ≤ In ≤ Iz) y reglamentación
      local. [VERIFICAR]

USO (desde la raíz del plugin)
    python3 -B library/calculations/conductor_selection.py table.json --ib 24 --longitud 100 \
        --fases 3 --un 400 --fp 0.9 --drop-max 3 --fa 0.8 --ft 0.9 --serie-in 10,16,20,25,32
"""

import argparse
import json
import math
import os
import sys

from epc_aea90364 import voltage_drop  # noqa: E402  (CAL-002)

__version__ = "0.1.0"

NO_VERIFICABLE = "NO VERIFICABLE"


def _num(v, nombre, estricto=True):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {v!r})")
    if (estricto and v <= 0) or (not estricto and v < 0):
        raise ValueError(f"{nombre} debe ser {'>' if estricto else '≥'} 0 (recibido: {v})")


def _factor(v, nombre):
    _num(v, nombre)
    if v > 1:
        raise ValueError(f"{nombre} debe estar en (0, 1] (recibido: {v})")


def cargar_tabla(origen):
    """Lee y valida una tabla (ruta a JSON o dict). Devuelve el dict normalizado, con las
    secciones ordenadas de menor a mayor. Lanza ValueError si es inválida."""
    if isinstance(origen, (str, os.PathLike)):
        try:
            with open(origen, "r", encoding="utf-8") as f:
                origen = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido en la tabla: {e}") from None
    if not isinstance(origen, dict) or not isinstance(origen.get("conductores"), list) or not origen["conductores"]:
        raise ValueError("La tabla debe ser un objeto con la lista no vacía 'conductores'")
    filas, advertencias = [], []
    for k, c in enumerate(origen["conductores"]):
        if not isinstance(c, dict):
            raise ValueError(f"conductores[{k}] debe ser un objeto")
        for campo in ("seccion_mm2", "i_adm_a", "r_ohm_km"):
            if campo not in c:
                raise ValueError(f"conductores[{k}]: falta '{campo}'")
            _num(c[campo], f"conductores[{k}].{campo}")
        x = c.get("x_ohm_km")
        if x is None:
            x = 0.0
        _num(x, f"conductores[{k}].x_ohm_km", estricto=False)
        filas.append({"seccion_mm2": float(c["seccion_mm2"]), "i_adm_a": float(c["i_adm_a"]),
                      "r_ohm_km": float(c["r_ohm_km"]), "x_ohm_km": float(x)})
    if any(c.get("x_ohm_km") is None for c in origen["conductores"]):
        advertencias.append("Algunas filas no traen x_ohm_km: se tomó 0 (la caída puede quedar subestimada).")
    filas.sort(key=lambda f: f["seccion_mm2"])
    secs = [f["seccion_mm2"] for f in filas]
    if len(set(secs)) != len(secs):
        raise ValueError("La tabla tiene secciones repetidas")
    enc = str(origen.get("_encabezado", ""))
    if "FICTICI" in enc.upper():
        advertencias.append("TABLA FICTICIA (" + enc + "): el resultado NO es válido para el proyecto.")
    return {"encabezado": enc, "fuente": origen.get("fuente") or {}, "conductores": filas,
            "advertencias": advertencias}


def _serie(serie_in):
    if serie_in is None:
        return None
    if not isinstance(serie_in, (list, tuple)) or not serie_in:
        raise ValueError("serie_in debe ser una lista no vacía de corrientes asignadas [A]")
    for v in serie_in:
        _num(v, "serie_in[]")
    return sorted(set(float(v) for v in serie_in))


def seleccionar_conductor(ib_a, longitud_m, tabla, fases, un_v, fp, caida_max_pct,
                          f_agrupamiento=1.0, f_temperatura=1.0, serie_in=None):
    """Selecciona la sección mínima (ver docstring del módulo).

    tabla: dict/ruta (ver cargar_tabla) o None. Si es None -> resultado 'NO VERIFICABLE'.
    Devuelve dict con: resultado ('OK' | 'NO CUMPLE' | 'NO VERIFICABLE'), motivo, seccion_mm2,
    seccion_conduccion_mm2, seccion_caida_mm2, in_a, iz_a, delta_u_pct, proteccion
    ('OK' | 'NO VERIFICABLE' | 'NO CUMPLE'), advertencias, estado_validacion.
    """
    base = {"modulo": "CAL-009", "version": __version__,
            "estado_validacion": "[VERIFICAR] — BORRADOR; válido solo con tabla de norma validada"}
    if tabla is None:
        return dict(base, resultado=NO_VERIFICABLE, proteccion=NO_VERIFICABLE,
                    motivo="Falta la tabla de capacidades/resistencias (norma sin extracto): "
                           "no se puede dimensionar. Cargar el extracto de la norma.",
                    advertencias=[])
    _num(ib_a, "ib_a")
    _num(longitud_m, "longitud_m", estricto=False)
    _num(un_v, "un_v")
    _num(caida_max_pct, "caida_max_pct")
    _factor(f_agrupamiento, "f_agrupamiento")
    _factor(f_temperatura, "f_temperatura")
    t = cargar_tabla(tabla) if not (isinstance(tabla, dict) and "advertencias" in tabla and "fuente" in tabla
                                    and "encabezado" in tabla) else tabla
    serie = _serie(serie_in)
    adv = list(t["advertencias"])
    f = f_agrupamiento * f_temperatura

    in_a, proteccion = None, NO_VERIFICABLE
    if serie is not None:
        candidatos = [v for v in serie if v >= ib_a - 1e-9]
        if not candidatos:
            return dict(base, resultado="NO CUMPLE", proteccion="NO CUMPLE", fuente=t["fuente"],
                        motivo=f"Ninguna In de la serie es ≥ Ib = {ib_a} A.", advertencias=adv)
        in_a, proteccion = candidatos[0], "OK"
    else:
        adv.append("Sin serie de In: la protección queda NO VERIFICABLE y la conducción se "
                   "verifica contra Ib.")
    i_ref = in_a if in_a is not None else ib_a

    def iz(c):
        return c["i_adm_a"] * f

    def du(c):
        return voltage_drop.caida_tension(fases, ib_a, longitud_m, c["r_ohm_km"], c["x_ohm_km"],
                                           fp, un_v)["delta_u_pct"]

    cond = next((c for c in t["conductores"] if iz(c) >= i_ref - 1e-9), None)
    caida = next((c for c in t["conductores"] if du(c) <= caida_max_pct + 1e-9), None)
    res = dict(base, fuente=t["fuente"], in_a=in_a, proteccion=proteccion, ib_a=ib_a,
               f_total=f, advertencias=adv,
               seccion_conduccion_mm2=cond["seccion_mm2"] if cond else None,
               seccion_caida_mm2=caida["seccion_mm2"] if caida else None)
    faltan = []
    if cond is None:
        faltan.append(f"conducción (ninguna sección de la tabla tiene Iz ≥ {i_ref} A con f = {f:.3g})")
    if caida is None:
        faltan.append(f"caída de tensión (ninguna sección de la tabla logra ΔU ≤ {caida_max_pct} %)")
    if faltan:
        return dict(res, resultado="NO CUMPLE", seccion_mm2=None,
                    motivo="No cumple por " + " y ".join(faltan) + ".")
    final = max(cond, caida, key=lambda c: c["seccion_mm2"])
    iz_f, du_f = iz(final), du(final)
    ok = iz_f >= i_ref - 1e-9 and du_f <= caida_max_pct + 1e-9
    gobierna = "conducción" if cond["seccion_mm2"] >= caida["seccion_mm2"] else "caída de tensión"
    return dict(res, resultado="OK" if ok else "NO CUMPLE", seccion_mm2=final["seccion_mm2"],
                iz_a=iz_f, delta_u_pct=du_f, criterio_gobernante=gobierna,
                motivo=f"Gobierna {gobierna}.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="CAL-009: selección de sección de conductor "
                                 "(la tabla se pasa por JSON; nunca está embebida).")
    ap.add_argument("tabla", help="JSON con la tabla de conductores (extracto de norma)")
    ap.add_argument("--ib", type=float, required=True, help="corriente de proyecto Ib [A]")
    ap.add_argument("--longitud", type=float, required=True, help="longitud [m]")
    ap.add_argument("--fases", type=int, choices=(1, 3), required=True)
    ap.add_argument("--un", type=float, required=True, help="tensión nominal [V]")
    ap.add_argument("--fp", type=float, default=0.9, help="cosφ")
    ap.add_argument("--drop-max", type=float, required=True, help="límite de caída de tensión [%%]")
    ap.add_argument("--fa", type=float, default=1.0, help="factor de agrupamiento")
    ap.add_argument("--ft", type=float, default=1.0, help="factor de temperatura")
    ap.add_argument("--serie-in", help="serie de In separada por comas, p. ej. 10,16,20,25,32")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    a = ap.parse_args(argv)
    try:
        tabla = cargar_tabla(a.tabla) if os.path.exists(a.tabla) else None
        serie = [float(x) for x in a.serie_in.split(",")] if a.serie_in else None
        r = seleccionar_conductor(a.ib, a.longitud, tabla, a.fases, a.un, a.fp, a.drop_max,
                                  a.fa, a.ft, serie)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        for k, v in r.items():
            print(f"{k}: {v}")
    return 0 if r["resultado"] == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
