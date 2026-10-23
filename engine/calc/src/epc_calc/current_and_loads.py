"""CAL-003 · current_and_loads — Corriente de diseño, balance de cargas, reserva y reparto en fases.

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    1. Corriente de diseño de una carga monofásica o trifásica y potencia aparente.
    2. Balance de cargas con factores de utilización y de simultaneidad (P, Q, S, fp, I).
    3. Reserva disponible frente a un interruptor.
    4. Reparto aproximado de circuitos monofásicos entre fases (algoritmo voraz).

FÓRMULAS
    Monofásica:  I = P / (V · cosφ · η)            Trifásica: I = P / (√3 · V · cosφ · η)
        P [W] potencia de la carga (en el eje si es motor, junto con η); V [V] tensión
        fase-neutro (mono) o de línea (tri); η rendimiento (1,0 si P ya es eléctrica).
    Aparente:    S = V·I (mono) ;  S = √3·V·I (tri) ;  S = P/cosφ
    Balance:     P_dem = fs · Σ (fu_i · P_i)
                 Q_dem = fs · Σ (fu_i · P_i · tanφ_i)      (carga inductiva)
                 S_dem = √(P_dem² + Q_dem²) ;  fp_global = P_dem / S_dem
                 I_dem = S_dem / (√3·V)  (trifásica equilibrada)
        fu_i factor de utilización de cada carga ; fs factor de simultaneidad global.
        Se suman P y Q (no las S), porque las S de cargas con distinto fp no se suman aritméticamente.
    Reserva:     reserva = (I_n − I_b) ; reserva% = 100·(I_n − I_b)/I_n ; uso% = 100·I_b/I_n
    Reparto:     voraz tipo LPT: se ordenan los circuitos por corriente decreciente y cada
                 uno se asigna a la fase con menor corriente acumulada (empate: menor índice).
                 Desbalance% = 100·(I_max − I_media)/I_media.

HIPÓTESIS
    - Sistema trifásico equilibrado de tensión nominal constante.
    - Las corrientes de fases se suman aritméticamente en el reparto (válido si los
      circuitos tienen fp similar; es una aproximación).
    - fu y fs son datos del proyecto; el módulo no incluye tablas de factores.

UNIDADES
    P [W], Q [var], S [VA], V [V], I [A], ángulos vía cosφ (adimensional).

LIMITACIONES
    - El reparto voraz no garantiza el óptimo global (problema de partición NP-difícil);
      es una buena aproximación para pocos circuitos. No considera la corriente de neutro,
      armónicos de tercer orden ni cargas desequilibradas con distinto ángulo.
    - Los factores de utilización y simultaneidad no se tabulan aquí.
    - La reserva se define respecto a la corriente asignada del interruptor, no respecto a
      la regulación térmica ni a la capacidad del conductor.

NORMA DE REFERENCIA (por designación)
    - IEC 60364-1 / IEC 60364-5-52 (corriente de empleo I_B, I_n ≥ I_B); la determinación de
      factores de simultaneidad y utilización corresponde a la guía de proyecto. [VERIFICAR]
"""

import math

__version__ = "0.1.0"

_RAIZ3 = math.sqrt(3.0)


def _pos(valor, nombre):
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {valor!r})")
    if valor <= 0:
        raise ValueError(f"{nombre} debe ser > 0 (recibido: {valor})")


def _nonneg(valor, nombre):
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {valor!r})")
    if valor < 0:
        raise ValueError(f"{nombre} debe ser ≥ 0 (recibido: {valor})")


def _frac(valor, nombre):
    _pos(valor, nombre)
    if valor > 1:
        raise ValueError(f"{nombre} debe estar en (0, 1] (recibido: {valor})")


def corriente_monofasica(p_w, v_v, fp=1.0, eta=1.0):
    """I [A] = P / (V·cosφ·η)."""
    _nonneg(p_w, "p_w")
    _pos(v_v, "v_v")
    _frac(fp, "fp")
    _frac(eta, "eta")
    return p_w / (v_v * fp * eta)


def corriente_trifasica(p_w, v_linea_v, fp=1.0, eta=1.0):
    """I [A] = P / (√3·V·cosφ·η)."""
    _nonneg(p_w, "p_w")
    _pos(v_linea_v, "v_linea_v")
    _frac(fp, "fp")
    _frac(eta, "eta")
    return p_w / (_RAIZ3 * v_linea_v * fp * eta)


def potencia_aparente_desde_p(p_w, fp):
    """S [VA] = P / cosφ."""
    _nonneg(p_w, "p_w")
    _frac(fp, "fp")
    return p_w / fp


def power_apparent_single_phase(v_v, i_a):
    """S [VA] = V·I."""
    _pos(v_v, "v_v")
    _nonneg(i_a, "i_a")
    return v_v * i_a


def power_apparent_three_phase(v_linea_v, i_a):
    """S [VA] = √3·V·I."""
    _pos(v_linea_v, "v_linea_v")
    _nonneg(i_a, "i_a")
    return _RAIZ3 * v_linea_v * i_a


def balance_cargas(cargas, fs=1.0, v_linea_v=None):
    """Balance de potencia con factores de utilización y simultaneidad.

    cargas: lista de dicts con claves
        "nombre" (opcional), "p_w" (potencia eléctrica absorbida), "fp" (cosφ, def. 1,0),
        "fu" (factor de utilización, def. 1,0).
    fs: factor de simultaneidad global (0 < fs ≤ 1).
    v_linea_v: si se indica, se calcula también I_dem trifásica equilibrada.
    Devuelve dict: p_w, q_var, s_va, fp, p_instalada_w, i_a (o None).
    """
    if not cargas:
        raise ValueError("La lista de cargas está vacía")
    _frac(fs, "fs")
    p_inst = 0.0
    p_sum = 0.0
    q_sum = 0.0
    for k, c in enumerate(cargas):
        if not isinstance(c, dict) or "p_w" not in c:
            raise ValueError(f"La carga #{k} debe ser un dict con la clave 'p_w'")
        nombre = c.get("nombre", f"#{k}")
        p = c["p_w"]
        fp = c.get("fp", 1.0)
        fu = c.get("fu", 1.0)
        try:
            _nonneg(p, "p_w")
            _frac(fp, "fp")
            _frac(fu, "fu")
        except ValueError as e:
            raise ValueError(f"Carga '{nombre}': {e}") from None
        tan_phi = math.sqrt(1.0 - fp * fp) / fp
        p_inst += p
        p_sum += fu * p
        q_sum += fu * p * tan_phi
    p_dem = fs * p_sum
    q_dem = fs * q_sum
    s_dem = math.hypot(p_dem, q_dem)
    fp_glob = p_dem / s_dem if s_dem > 0 else 1.0
    i_dem = None
    if v_linea_v is not None:
        _pos(v_linea_v, "v_linea_v")
        i_dem = s_dem / (_RAIZ3 * v_linea_v)
    return {"p_instalada_w": p_inst, "p_w": p_dem, "q_var": q_dem, "s_va": s_dem,
            "fp": fp_glob, "i_a": i_dem}


def reserve_breaker(i_diseno_a, i_interruptor_a, reserva_min_pct=None):
    """Reserva frente a un interruptor de corriente asignada I_n.

    Devuelve dict: reserva_a, reserva_pct (sobre I_n), uso_pct, cumple (None si no se da mínimo).
    Si I_b > I_n, la reserva es negativa y cumple = False.
    """
    _nonneg(i_diseno_a, "i_diseno_a")
    _pos(i_interruptor_a, "i_interruptor_a")
    res_a = i_interruptor_a - i_diseno_a
    res_pct = 100.0 * res_a / i_interruptor_a
    cumple = None
    if reserva_min_pct is not None:
        _nonneg(reserva_min_pct, "reserva_min_pct")
        cumple = res_pct >= reserva_min_pct
    return {"reserva_a": res_a, "reserva_pct": res_pct,
            "uso_pct": 100.0 * i_diseno_a / i_interruptor_a, "cumple": cumple}


def split_phases(circuitos, n_fases=3):
    """Asigna circuitos monofásicos a fases minimizando el desbalance (voraz LPT).

    circuitos: lista de tuplas (nombre, corriente_A).
    Devuelve dict: asignacion (lista de listas de nombres por fase, orden de asignación),
        corrientes (A por fase), desbalance_pct = 100·(I_max − I_media)/I_media.
    """
    if not isinstance(n_fases, int) or isinstance(n_fases, bool) or n_fases < 1:
        raise ValueError(f"n_fases debe ser entero ≥ 1 (recibido: {n_fases!r})")
    if not circuitos:
        raise ValueError("La lista de circuitos está vacía")
    items = []
    for k, c in enumerate(circuitos):
        try:
            nombre, i = c
        except (TypeError, ValueError):
            raise ValueError(f"El circuito #{k} debe ser una tupla (nombre, corriente_A)") from None
        _nonneg(i, f"corriente del circuito '{nombre}'")
        items.append((nombre, i))
    orden = sorted(items, key=lambda t: -t[1])  # sorted es estable: empates conservan el orden de entrada
    corr = [0.0] * n_fases
    asig = [[] for _ in range(n_fases)]
    for nombre, i in orden:
        f = min(range(n_fases), key=lambda k: (corr[k], k))
        corr[f] += i
        asig[f].append(nombre)
    media = sum(corr) / n_fases
    desb = 100.0 * (max(corr) - media) / media if media > 0 else 0.0
    return {"asignacion": asig, "corrientes": corr, "desbalance_pct": desb}


if __name__ == "__main__":
    print("== CAL-003 current_and_loads — ejemplo (valores ilustrativos) ==")
    print(f"Trifásica 10 kW, 400 V, cosφ 0,8: I = {corriente_trifasica(10000, 400, 0.8):.2f} A")
    print(f"Monofásica 2,3 kW, 230 V, cosφ 0,8, η 0,5: I = {corriente_monofasica(2300, 230, 0.8, 0.5):.2f} A")
    b = balance_cargas([{"nombre": "A", "p_w": 10000, "fp": 0.8, "fu": 1.0},
                        {"nombre": "B", "p_w": 20000, "fp": 1.0, "fu": 0.5}], fs=0.8, v_linea_v=400)
    print(f"Balance: P = {b['p_w']/1000:.1f} kW, Q = {b['q_var']/1000:.1f} kvar, S = {b['s_va']/1000:.2f} kVA, "
          f"fp = {b['fp']:.3f}, I = {b['i_a']:.2f} A")
    r = reserve_breaker(b["i_a"], 32, reserva_min_pct=20)
    print(f"Interruptor 32 A: reserva {r['reserva_a']:.1f} A ({r['reserva_pct']:.0f} %), uso {r['uso_pct']:.0f} %, cumple 20 %: {r['cumple']}")
    rep = split_phases([("C1", 10), ("C2", 8), ("C3", 7), ("C4", 5), ("C5", 4), ("C6", 2)])
    for k, (n, i) in enumerate(zip(rep["asignacion"], rep["corrientes"]), 1):
        print(f"  L{k}: {n} -> {i:.1f} A")
    print(f"  Desbalance = {rep['desbalance_pct']:.1f} %")
