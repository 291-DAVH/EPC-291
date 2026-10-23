"""CAL-005 · cable_thermal — Verificación térmica de un cable ante cortocircuito (adiabática).

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Determinar la sección mínima que soporta térmicamente una corriente de cortocircuito
    durante un tiempo dado y comprobar la condición I²·t ≤ k²·S².

FÓRMULAS
    S_min = I · √t / k                    [mm²]
    Condición:  I² · t ≤ k² · S²          (energía específica pasante ≤ capacidad del cable)
    Tiempo máximo admisible:   t_max = k² · S² / I²
    Corriente máxima admisible para un tiempo t:   I_max = k · S / √t
        I [A] (valor eficaz de la corriente de cortocircuito), t [s], S [mm²],
        k [A·s^½/mm²] (depende del material del conductor y del aislamiento).

CONSTANTES k (conductor/aislamiento), para temperatura inicial y final usuales del aislamiento
    Cu/PVC = 115 ; Cu/XLPE = 143 ; Al/PVC = 76 ; Al/XLPE = 94      [VERIFICAR]
    Provienen de memoria de IEC 60364-4-43; condiciones (temperaturas, sección máxima
    de validez, aislaciones adicionales) no incluidas. El usuario puede pasar su propio k.

HIPÓTESIS
    - Proceso adiabático (todo el calor queda en el conductor): válido para t pequeño
      (típicamente hasta unos 5 s). [VERIFICAR]
    - Para t muy corto (< 0,1 s) la corriente no es constante: debe usarse la integral de
      Joule (I²t) del dispositivo de protección (dato del fabricante) en lugar de I²·t.
    - k constante; no se considera la temperatura previa de operación del cable más allá
      de lo implícito en k.

UNIDADES
    I [A], t [s], S [mm²], k [A·s^½/mm²].

LIMITACIONES
    - No se incluyen tablas de secciones comerciales: `seccion_comercial_superior` recibe la
      lista de secciones disponibles como parámetro.
    - No verifica esfuerzos electrodinámicos ni límites de terminales/empalmes/pantallas.
    - Los valores de k para otras aislaciones (EPR, mineral, etc.) deben ingresarse a mano.

NORMA DE REFERENCIA (por designación)
    - IEC 60364-4-43 (protección contra sobrecorrientes; ecuación adiabática y valores de k).
      [VERIFICAR] — sin citar cláusulas.
    - IEC 60949 (cálculo de corrientes de cortocircuito admisibles térmicamente). [VERIFICAR]
"""

import math

__version__ = "0.1.0"

#: k [A·s^½/mm²] por (material, aislación). [VERIFICAR] contra IEC 60364-4-43.
K_ADIABATICO = {
    ("Cu", "PVC"): 115.0,   # [VERIFICAR]
    ("Cu", "XLPE"): 143.0,  # [VERIFICAR]
    ("Al", "PVC"): 76.0,    # [VERIFICAR]
    ("Al", "XLPE"): 94.0,   # [VERIFICAR]
}
#: Tiempo a partir del cual el supuesto adiabático deja de ser aceptable (s). [VERIFICAR]
T_ADIABATICO_MAX_S = 5.0
#: Tiempo por debajo del cual debe usarse la integral de Joule del dispositivo (s). [VERIFICAR]
T_CORTO_S = 0.1


def _pos(valor, nombre):
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {valor!r})")
    if valor <= 0:
        raise ValueError(f"{nombre} debe ser > 0 (recibido: {valor})")


def k_material(material, aislacion):
    """k de la tabla interna. material: 'Cu'|'Al'; aislacion: 'PVC'|'XLPE'. [VERIFICAR]"""
    try:
        return K_ADIABATICO[(material, aislacion)]
    except KeyError:
        raise ValueError(f"Combinación ({material!r}, {aislacion!r}) sin k predefinido; "
                         f"disponibles: {sorted(K_ADIABATICO)}. Ingresar k explícito.") from None


def _advertencias_tiempo(t_s):
    adv = []
    if t_s > T_ADIABATICO_MAX_S:
        adv.append(f"t = {t_s} s > {T_ADIABATICO_MAX_S} s: el supuesto adiabático puede no ser válido [VERIFICAR].")
    if t_s < T_CORTO_S:
        adv.append(f"t = {t_s} s < {T_CORTO_S} s: usar la integral de Joule (I²t) del dispositivo de protección.")
    return adv


def seccion_minima_mm2(i_cc_a, t_s, k):
    """S_min [mm²] = I·√t/k."""
    _pos(i_cc_a, "i_cc_a")
    _pos(t_s, "t_s")
    _pos(k, "k")
    return i_cc_a * math.sqrt(t_s) / k


def verificar_i2t(i_cc_a, t_s, k, seccion_mm2):
    """Comprueba I²·t ≤ k²·S². Devuelve dict: i2t, k2s2, cumple, margen (k²S²/I²t), t_max_s,
    i_max_a (para el t dado), s_min_mm2, advertencias."""
    _pos(i_cc_a, "i_cc_a")
    _pos(t_s, "t_s")
    _pos(k, "k")
    _pos(seccion_mm2, "seccion_mm2")
    i2t = i_cc_a ** 2 * t_s
    k2s2 = (k * seccion_mm2) ** 2
    return {"i2t": i2t, "k2s2": k2s2, "cumple": i2t <= k2s2, "margen": k2s2 / i2t,
            "t_max_s": k2s2 / i_cc_a ** 2, "i_max_a": k * seccion_mm2 / math.sqrt(t_s),
            "s_min_mm2": seccion_minima_mm2(i_cc_a, t_s, k), "advertencias": _advertencias_tiempo(t_s)}


def tiempo_maximo_s(i_cc_a, k, seccion_mm2):
    """t_max [s] = k²S²/I²."""
    _pos(i_cc_a, "i_cc_a")
    _pos(k, "k")
    _pos(seccion_mm2, "seccion_mm2")
    return (k * seccion_mm2) ** 2 / i_cc_a ** 2


def seccion_comercial_superior(s_min_mm2, secciones_disponibles_mm2):
    """Menor sección de la lista (dato del usuario/norma) que sea ≥ S_min. ValueError si ninguna."""
    _pos(s_min_mm2, "s_min_mm2")
    if not secciones_disponibles_mm2:
        raise ValueError("La lista de secciones disponibles está vacía")
    for s in secciones_disponibles_mm2:
        _pos(s, "sección disponible")
    candidatas = [s for s in secciones_disponibles_mm2 if s >= s_min_mm2]
    if not candidatas:
        raise ValueError(f"Ninguna sección disponible ≥ {s_min_mm2:.2f} mm²")
    return min(candidatas)


if __name__ == "__main__":
    print("== CAL-005 cable_thermal — ejemplo (valores ilustrativos) ==")
    k = k_material("Cu", "XLPE")
    s_min = seccion_minima_mm2(10000, 0.5, k)
    print(f"Ik = 10 kA, t = 0,5 s, k = {k:g}: S_min = {s_min:.2f} mm²")
    s = seccion_comercial_superior(s_min, [35, 50, 70, 95])
    v = verificar_i2t(10000, 0.5, k, s)
    print(f"Sección adoptada {s} mm²: I²t = {v['i2t']:.3g} A²s ≤ k²S² = {v['k2s2']:.4g} A²s -> cumple: {v['cumple']} "
          f"(margen {v['margen']:.3f}; t_max = {v['t_max_s']:.3f} s)")
