"""CAL-001 · lighting — Cálculo luminotécnico de interiores (flujo luminoso, malla, punto a punto, emergencia).

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    1. Número de luminarias por el método del flujo luminoso.
    2. Selección de malla regular nx × ny con relación de separaciones acotada.
    3. Niveles de iluminancia punto a punto (min / medio / max) y uniformidad,
       con luminaria de emisión Lambertiana y SOLO componente directa.
    4. Iluminación de emergencia antipánico (E_min y relación E_max/E_min).
    5. Iluminancia horizontal en un punto y a lo largo del eje de una ruta de escape
       (reutiliza el punto a punto) y criterio de conformidad flujo / punto a punto.
    6. UGR: NO se calcula (requiere fotometría); `verificar_ugr` devuelve 'NO VERIFICABLE'
       si faltan datos.

FÓRMULAS
    Método del flujo:     N = E·A / (Φ·UF·MF)        [N se redondea hacia arriba]
        E  [lx]  iluminancia media de mantenimiento requerida
        A  [m²]  superficie del plano de trabajo
        Φ  [lm]  flujo luminoso de una luminaria
        UF [-]   factor de utilización (dato de fotometría del fabricante o supuesto)
        MF [-]   factor de mantenimiento
    Malla: nx·ny ≥ N_min, separaciones sx = ancho/nx, sy = largo/ny,
        relación = max(sx, sy)/min(sx, sy) ≤ relacion_max (por defecto 1,5).
        Se elige la malla de menor N y, a igualdad, menor relación.
        Las luminarias se ubican en el centro de cada celda: ((i+½)·sx, (j+½)·sy).
    Emisión Lambertiana (I(θ) = I0·cosθ, con I0 = Φ/π [cd]):
        E_horizontal = I(θ)·cosθ / d² = (Φ/π)·h² / d⁴,   d² = dx² + dy² + h²
        Bajo la luminaria (dx = dy = 0):  E = Φ / (π·h²)
        Luminarias independientes: se suman las contribuciones (solo directa).
    Uniformidad: U0 = E_min / E_medio ;  relación de emergencia = E_max / E_min.

HIPÓTESIS
    - Luminaria puntual (dimensiones despreciables frente a la altura h).
    - Emisión Lambertiana; plano de cálculo horizontal.
    - Solo componente directa: se desprecia la inter-reflexión en paredes,
      techo y piso (resultado conservador en E_min).
    - Sala rectangular, luminarias a una misma altura.
    - El flujo que se pasa a las funciones punto a punto es el flujo EFECTIVO
      (p. ej. Φ·MF); el módulo no aplica MF por su cuenta en esas funciones.
    - Banda perimetral: se excluye de la evaluación una franja de ancho
      `banda` [m] junto a las paredes (configurable; 0 = sala completa).
    - La evaluación usa una grilla de puntos con paso `paso` [m].

UNIDADES (SI)
    longitudes [m], superficies [m²], flujo [lm], iluminancia [lx], intensidad [cd].

LIMITACIONES
    - No hay inter-reflexión ni curvas fotométricas reales: para verificación
      final usar el archivo fotométrico del fabricante (EULUMDAT/IES).
    - Ninguna tabla de niveles de iluminación está incluida: E requerida, U0
      requerida, UF y MF son datos de entrada.
    - La búsqueda de malla es combinatoria simple; no considera obstáculos,
      estructura, ni disposición real de luminarias.
    - Con luminarias a baja altura relativa a la separación, la hipótesis
      puntual pierde validez.

CRITERIO DE CONFORMIDAD [VERIFICAR] (H-023; ver calc-library.md CAL-001)
    El método del flujo es el de dimensionamiento; el punto a punto directo (solo directa,
    conservador) verifica uniformidad y emergencia. Conforme si E_flujo ≥ E exigida y
    E_medio_punto_a_punto ≥ 0,9·E exigida (ver `conformidad_iluminancia`). UGR y eje de ruta
    sin fotometría real: NO VERIFICABLE, salvo la verificación de ruta con las hipótesis
    del módulo (`iluminancia_eje_ruta`).

NORMA DE REFERENCIA (por designación, sin citar cláusulas)
    - EN 12464-1 / ISO 8995-1: iluminación de lugares de trabajo (niveles y
      uniformidad requeridos; los valores deben tomarse de la norma). [VERIFICAR]
    - EN 1838 / ISO 30061: iluminación de emergencia; los criterios de área
      antipánico (E_min ≥ 0,5 lx y E_max/E_min ≤ 40) provienen de memoria
      y se dejan como parámetros configurables. [VERIFICAR]
    - Método del flujo luminoso: formulación de ingeniería habitual.
"""

import math

__version__ = "0.1.0"

#: Criterios de emergencia antipánico por defecto. [VERIFICAR] contra la norma vigente.
EMERGENCIA_E_MIN_LX = 0.5      # [VERIFICAR]
EMERGENCIA_RELACION_MAX = 40.0  # [VERIFICAR]
#: Factor del criterio de conformidad del punto a punto directo respecto de E exigida. [VERIFICAR]
FACTOR_CONFORMIDAD_DIRECTO = 0.9
NO_VERIFICABLE = "NO VERIFICABLE"
#: Relación máxima entre separaciones de la malla (criterio de proyecto).
RELACION_SEPARACIONES_MAX = 1.5
_TOL = 1e-9


def _pos(valor, nombre):
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {valor!r})")
    if valor <= 0:
        raise ValueError(f"{nombre} debe ser > 0 (recibido: {valor})")


def _frac(valor, nombre):
    _pos(valor, nombre)
    if valor > 1:
        raise ValueError(f"{nombre} debe estar en (0, 1] (recibido: {valor})")


def flujo_n_luminarias(e_lx, area_m2, phi_lm, uf, mf):
    """Número (real) de luminarias por método del flujo: N = E·A/(Φ·UF·MF)."""
    _pos(e_lx, "e_lx")
    _pos(area_m2, "area_m2")
    _pos(phi_lm, "phi_lm")
    _frac(uf, "uf")
    _frac(mf, "mf")
    return e_lx * area_m2 / (phi_lm * uf * mf)


def n_luminarias_minimo(e_lx, area_m2, phi_lm, uf, mf):
    """Número entero mínimo de luminarias (techo de N, con tolerancia 1e-9
    para evitar que el error de coma flotante añada una luminaria espuria)."""
    n = flujo_n_luminarias(e_lx, area_m2, phi_lm, uf, mf)
    return int(math.ceil(n - _TOL))


def illuminance_mean_flux(n, area_m2, phi_lm, uf, mf):
    """E medio [lx] con n luminarias: E = N·Φ·UF·MF/A."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError(f"n debe ser entero ≥ 1 (recibido: {n!r})")
    _pos(area_m2, "area_m2")
    _pos(phi_lm, "phi_lm")
    _frac(uf, "uf")
    _frac(mf, "mf")
    return n * phi_lm * uf * mf / area_m2


def seleccionar_malla(n_min, ancho_m, largo_m, relacion_max=RELACION_SEPARACIONES_MAX, n_max_lado=60):
    """Malla regular (nx, ny) con nx·ny ≥ n_min y relación de separaciones ≤ relacion_max.

    Criterio: menor nx·ny; a igualdad, menor relación; a igualdad, menor nx.
    nx se cuenta a lo largo de `ancho_m` (eje x) y ny a lo largo de `largo_m` (eje y).
    Lanza ValueError si no existe malla que cumpla.
    """
    if not isinstance(n_min, int) or isinstance(n_min, bool) or n_min < 1:
        raise ValueError(f"n_min debe ser entero ≥ 1 (recibido: {n_min!r})")
    _pos(ancho_m, "ancho_m")
    _pos(largo_m, "largo_m")
    _pos(relacion_max, "relacion_max")
    if relacion_max < 1:
        raise ValueError("relacion_max debe ser ≥ 1")
    mejor = None
    for nx in range(1, n_max_lado + 1):
        for ny in range(1, n_max_lado + 1):
            n = nx * ny
            if n < n_min:
                continue
            sx, sy = ancho_m / nx, largo_m / ny
            rel = max(sx, sy) / min(sx, sy)
            if rel > relacion_max + _TOL:
                continue
            clave = (n, round(rel, 9), nx)
            if mejor is None or clave < mejor[0]:
                mejor = (clave, nx, ny)
    if mejor is None:
        raise ValueError(
            f"No existe malla con N ≥ {n_min} y relación de separaciones ≤ {relacion_max} "
            f"para {ancho_m} m × {largo_m} m (lado máx. {n_max_lado})")
    return mejor[1], mejor[2]


def points_grid(ancho_m, largo_m, nx, ny):
    """Posiciones (x, y) [m] de luminarias en el centro de cada celda nx × ny."""
    _pos(ancho_m, "ancho_m")
    _pos(largo_m, "largo_m")
    for v, nm in ((nx, "nx"), (ny, "ny")):
        if not isinstance(v, int) or isinstance(v, bool) or v < 1:
            raise ValueError(f"{nm} debe ser entero ≥ 1 (recibido: {v!r})")
    return [((i + 0.5) * ancho_m / nx, (j + 0.5) * largo_m / ny) for i in range(nx) for j in range(ny)]


def illuminance_lambertian(phi_lm, h_m, dx_m, dy_m):
    """E [lx] sobre plano horizontal por una luminaria Lambertiana (solo directa):
    E = (Φ/π)·h²/d⁴, con d² = dx² + dy² + h²."""
    _pos(phi_lm, "phi_lm")
    _pos(h_m, "h_m")
    d2 = dx_m * dx_m + dy_m * dy_m + h_m * h_m
    return (phi_lm / math.pi) * (h_m * h_m) / (d2 * d2)


def evaluar_malla(ancho_m, largo_m, luminarias, phi_lm, h_m, banda_m=0.0, paso_m=0.5):
    """Evalúa E en una grilla de puntos sobre la sala, excluyendo una banda perimetral.

    Parámetros
        luminarias : lista de (x, y) [m]
        phi_lm     : flujo EFECTIVO por luminaria (p. ej. Φ·MF) [lm]
        h_m        : altura de montaje sobre el plano de cálculo [m]
        banda_m    : ancho de la banda perimetral excluida [m] (≥ 0)
        paso_m     : paso de la grilla de evaluación [m]
    Devuelve dict: e_min, e_medio, e_max [lx], u0 = e_min/e_medio,
        relacion_max_min = e_max/e_min, n_puntos.
    """
    _pos(ancho_m, "ancho_m")
    _pos(largo_m, "largo_m")
    _pos(phi_lm, "phi_lm")
    _pos(h_m, "h_m")
    _pos(paso_m, "paso_m")
    if banda_m < 0:
        raise ValueError("banda_m debe ser ≥ 0")
    if 2 * banda_m >= ancho_m or 2 * banda_m >= largo_m:
        raise ValueError("La banda perimetral excluida consume toda la sala (2·banda ≥ lado)")
    if not luminarias:
        raise ValueError("Se requiere al menos una luminaria")
    n_x = int(math.floor((ancho_m - 2 * banda_m) / paso_m + _TOL)) + 1
    n_y = int(math.floor((largo_m - 2 * banda_m) / paso_m + _TOL)) + 1
    suma = 0.0
    e_min = math.inf
    e_max = -math.inf
    for i in range(n_x):
        x = banda_m + i * paso_m
        for j in range(n_y):
            y = banda_m + j * paso_m
            e = sum(illuminance_lambertian(phi_lm, h_m, x - lx, y - ly) for lx, ly in luminarias)
            suma += e
            e_min = min(e_min, e)
            e_max = max(e_max, e)
    n_pts = n_x * n_y
    e_medio = suma / n_pts
    return {"e_min": e_min, "e_medio": e_medio, "e_max": e_max,
            "u0": e_min / e_medio, "relacion_max_min": e_max / e_min, "n_puntos": n_pts}


def size_normal(e_lx, ancho_m, largo_m, h_montaje_m, phi_lm, uf, mf,
                       plano_trabajo_m=0.85, relacion_max=RELACION_SEPARACIONES_MAX,
                       banda_m=0.5, paso_m=0.5):
    """Flujo de trabajo completo: N mínimo → malla → verificación punto a punto.

    plano_trabajo_m: altura del plano de trabajo (dato de proyecto; 0,85 m es
    un valor usual de oficina/industria, pero se pasa como parámetro).
    Devuelve dict con n_min, nx, ny, n, e_medio_flujo, e_min, e_medio_directo,
    e_max, u0_directo.
    """
    if plano_trabajo_m < 0 or plano_trabajo_m >= h_montaje_m:
        raise ValueError("plano_trabajo_m debe estar en [0, h_montaje_m)")
    area = ancho_m * largo_m
    n_min = n_luminarias_minimo(e_lx, area, phi_lm, uf, mf)
    nx, ny = seleccionar_malla(n_min, ancho_m, largo_m, relacion_max)
    n = nx * ny
    lums = points_grid(ancho_m, largo_m, nx, ny)
    ev = evaluar_malla(ancho_m, largo_m, lums, phi_lm * mf, h_montaje_m - plano_trabajo_m, banda_m, paso_m)
    return {"n_min": n_min, "nx": nx, "ny": ny, "n": n,
            "e_medio_flujo": illuminance_mean_flux(n, area, phi_lm, uf, mf),
            "e_min": ev["e_min"], "e_medio_directo": ev["e_medio"], "e_max": ev["e_max"],
            "u0_directo": ev["u0"]}


def size_emergency(ancho_m, largo_m, h_m, phi_lm, e_min_req_lx=EMERGENCIA_E_MIN_LX,
                           relacion_max=EMERGENCIA_RELACION_MAX, banda_m=0.5, paso_m=0.5,
                           n_max=400, relacion_separaciones_max=RELACION_SEPARACIONES_MAX,
                           mf=1.0):
    """Menor número de luminarias de emergencia (malla regular) que cumpla
    E_min ≥ e_min_req_lx y E_max/E_min ≤ relacion_max, evaluado AL NIVEL DEL PISO
    (h_m = altura de montaje), solo componente directa.

    mf: factor de mantenimiento/depreciación aplicado a phi_lm (1,0 = flujo ya efectivo).
    Lanza ValueError si ningún N ≤ n_max cumple.
    """
    _pos(ancho_m, "ancho_m")
    _pos(largo_m, "largo_m")
    _pos(h_m, "h_m")
    _pos(phi_lm, "phi_lm")
    _pos(e_min_req_lx, "e_min_req_lx")
    _pos(relacion_max, "relacion_max")
    _frac(mf, "mf")
    if not isinstance(n_max, int) or n_max < 1:
        raise ValueError("n_max debe ser entero ≥ 1")
    for n in range(1, n_max + 1):
        for nx in range(1, n + 1):
            if n % nx:
                continue
            ny = n // nx
            sx, sy = ancho_m / nx, largo_m / ny
            if max(sx, sy) / min(sx, sy) > relacion_separaciones_max + _TOL:
                continue
            ev = evaluar_malla(ancho_m, largo_m, points_grid(ancho_m, largo_m, nx, ny),
                               phi_lm * mf, h_m, banda_m, paso_m)
            if ev["e_min"] >= e_min_req_lx and ev["relacion_max_min"] <= relacion_max:
                return {"n": n, "nx": nx, "ny": ny, "e_min": ev["e_min"],
                        "e_max": ev["e_max"], "relacion_max_min": ev["relacion_max_min"]}
    raise ValueError(f"Ningún N ≤ {n_max} cumple E_min ≥ {e_min_req_lx} lx y "
                     f"E_max/E_min ≤ {relacion_max} (revisar flujo, altura o criterios)")


def illuminance_in_point(luminarias, phi_lm, h_m, x_m, y_m):
    """E [lx] horizontal en el punto (x, y) por todas las luminarias (Lambertianas, solo directa).

    luminarias: lista de (x, y) [m]; phi_lm: flujo EFECTIVO por luminaria; h_m: altura de
    montaje sobre el plano del punto (piso para rutas de escape).
    """
    if not luminarias:
        raise ValueError("Se requiere al menos una luminaria")
    return sum(illuminance_lambertian(phi_lm, h_m, x_m - lx, y_m - ly) for lx, ly in luminarias)


def iluminancia_eje_ruta(luminarias, phi_lm, h_m, inicio_xy, fin_xy, paso_m=0.5, e_min_req_lx=None):
    """Iluminancia horizontal a lo largo del eje de una ruta de escape (segmento inicio→fin).

    Reutiliza el punto a punto. Devuelve dict: e_min, e_medio, e_max [lx], n_puntos y, si se
    pasa e_min_req_lx (dato del proyecto/norma, [VERIFICAR]), 'cumple' (e_min ≥ e_min_req).
    Solo componente directa, sin fotometría real: es una verificación conservadora.
    """
    _pos(phi_lm, "phi_lm")
    _pos(h_m, "h_m")
    _pos(paso_m, "paso_m")
    (x0, y0), (x1, y1) = inicio_xy, fin_xy
    largo = math.hypot(x1 - x0, y1 - y0)
    if largo <= 0:
        raise ValueError("El eje de la ruta tiene longitud cero")
    n = int(math.floor(largo / paso_m + _TOL)) + 1
    pts = [(x0 + (x1 - x0) * k * paso_m / largo, y0 + (y1 - y0) * k * paso_m / largo) for k in range(n)]
    if largo - (n - 1) * paso_m > _TOL:   # incluir el extremo final
        pts.append((x1, y1))
    es = [illuminance_in_point(luminarias, phi_lm, h_m, x, y) for x, y in pts]
    out = {"e_min": min(es), "e_medio": sum(es) / len(es), "e_max": max(es), "n_puntos": len(es)}
    if e_min_req_lx is not None:
        _pos(e_min_req_lx, "e_min_req_lx")
        out["cumple"] = out["e_min"] >= e_min_req_lx
    return out


def conformidad_iluminancia(e_req_lx, e_medio_flujo_lx, e_medio_directo_lx,
                            factor_directo=FACTOR_CONFORMIDAD_DIRECTO):
    """Criterio de conformidad [VERIFICAR]: el método del flujo dimensiona; el punto a punto
    directo es una verificación conservadora.

    Conforme si e_medio_flujo ≥ E exigida Y e_medio_directo ≥ factor_directo·E exigida (0,9).
    Devuelve dict {conforme, flujo_ok, directo_ok, e_directo_min_aceptable_lx}.
    """
    _pos(e_req_lx, "e_req_lx")
    _pos(e_medio_flujo_lx, "e_medio_flujo_lx")
    _pos(e_medio_directo_lx, "e_medio_directo_lx")
    _frac(factor_directo, "factor_directo")
    flujo_ok = e_medio_flujo_lx >= e_req_lx - _TOL
    lim = factor_directo * e_req_lx
    directo_ok = e_medio_directo_lx >= lim - _TOL
    return {"conforme": flujo_ok and directo_ok, "flujo_ok": flujo_ok, "directo_ok": directo_ok,
            "e_directo_min_aceptable_lx": lim}


def verificar_ugr(ugr_calculado=None, ugr_max=None):
    """UGR NO se calcula en este módulo (requiere fotometría: luminancias de las luminarias,
    posición del observador). Si no se aportan un UGR calculado externamente (software
    fotométrico) y el límite, devuelve {'resultado': 'NO VERIFICABLE'}; si se aportan,
    compara ugr_calculado ≤ ugr_max.
    """
    if ugr_calculado is None or ugr_max is None:
        return {"resultado": NO_VERIFICABLE, "cumple": None,
                "motivo": "UGR requiere fotometría (EULUMDAT/IES) y un cálculo externo; "
                          "este módulo no lo calcula."}
    for v, nm in ((ugr_calculado, "ugr_calculado"), (ugr_max, "ugr_max")):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
            raise ValueError(f"{nm} debe ser un número finito ≥ 0 (recibido: {v!r})")
    ok = ugr_calculado <= ugr_max
    return {"resultado": "CUMPLE" if ok else "NO CUMPLE", "cumple": ok,
            "ugr_calculado": ugr_calculado, "ugr_max": ugr_max}


if __name__ == "__main__":
    print("== CAL-001 lighting — ejemplo (datos ilustrativos, no de un proyecto) ==")
    r = size_normal(e_lx=300, ancho_m=40, largo_m=40, h_montaje_m=8.0,
                           phi_lm=20000, uf=0.60, mf=0.80)
    print(f"N mínimo por flujo        : {r['n_min']}")
    print(f"Malla elegida             : {r['nx']} × {r['ny']} = {r['n']} luminarias")
    print(f"E medio (método flujo)    : {r['e_medio_flujo']:.1f} lx")
    print(f"E punto a punto (directa) : min {r['e_min']:.1f} / medio {r['e_medio_directo']:.1f} / max {r['e_max']:.1f} lx")
    print(f"Uniformidad U0 (directa)  : {r['u0_directo']:.2f}")
    em = size_emergency(ancho_m=20, largo_m=20, h_m=4.0, phi_lm=300)
    print(f"Emergencia antipánico     : {em['n']} luminarias ({em['nx']}×{em['ny']}), "
          f"Emin {em['e_min']:.2f} lx, Emax/Emin {em['relacion_max_min']:.1f}")
