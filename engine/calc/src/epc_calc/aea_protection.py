"""aea_protection — Protección contra contactos indirectos y coordinación de dispositivos (AEA 90364-4-41, 4-43, 7-771.18).

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Verificación de la desconexión automática por esquema (TN, TT, IT) y corriente
    convencional de funcionamiento (I2) de los dispositivos de protección.

FÓRMULAS
    I2 = k2 · In            (k2: 1,45 MCB IEC 60898; 1,30 MCCB IEC 60947-2; 1,60 fusible gG)
    In,max = min(Iz, 1,45·Iz/k2)       (coordinación con I2 ≤ 1,45·Iz)
    TN:  Zs · Ia ≤ U0
    TT:  Ra · Ia ≤ UL ;  Ra,max = UL/Ia ;  If = U0/(Ra + Rb)
    IT (segunda falla, masas interconectadas):  2 · Ia · Zs ≤ U   (sin neutro)
                                                2 · Ia · Zs' ≤ U0 (con neutro distribuido)

UNIDADES
    I [A], Z, R [Ω], U [V].

LIMITACIONES
    - k2 son valores usuales de normas de producto; el fabricante prevalece.
    - No calcula Zs desde la instalación (ver `short_circuit.py`, `aea_earthing.py`).

NORMA DE REFERENCIA
    AEA 90364-4-41 (§41.3), 90364-4-43, 90364-7-771.18 y IT 90909-1.  [VERIFICAR]
"""
__version__ = "0.1.0"

K2_CONVENCIONAL = {"mcb": 1.45, "mccb": 1.30, "fusible_gg": 1.60}


def i2_convencional(in_a, tipo="mcb"):
    """Corriente convencional de funcionamiento I2 = k2·In [A]."""
    if tipo not in K2_CONVENCIONAL:
        raise ValueError(f"tipo {tipo} desconocido: {sorted(K2_CONVENCIONAL)}")
    if in_a <= 0:
        raise ValueError("In debe ser positiva")
    return K2_CONVENCIONAL[tipo] * in_a


def in_max_por_iz(iz_a, tipo="mcb"):
    """In máxima que cumple In ≤ Iz e I2 ≤ 1,45·Iz [A]."""
    return min(iz_a, 1.45 * iz_a / K2_CONVENCIONAL[tipo])


def verifica_tn(zs_ohm, ia_a, u0_v=230.0):
    """TN: Zs·Ia ≤ U0. Devuelve dict con producto, límite, margen y cumple."""
    prod = zs_ohm * ia_a
    return {"zs_ia_v": prod, "limite_v": u0_v, "cumple": prod <= u0_v}


def ra_maxima_tt(ia_a, ul_v=50.0):
    """TT: resistencia de puesta a tierra máxima Ra = UL/Ia [Ω]."""
    return ul_v / ia_a


def verifica_tt(ra_ohm, ia_a, ul_v=50.0):
    """TT: Ra·Ia ≤ UL."""
    prod = ra_ohm * ia_a
    return {"ra_ia_v": prod, "limite_v": ul_v, "ra_max_ohm": ul_v / ia_a, "cumple": prod <= ul_v}


def corriente_falla_tt(u0_v, ra_ohm, rb_ohm):
    """TT: corriente de primera falla If = U0/(Ra + Rb) [A]."""
    return u0_v / (ra_ohm + rb_ohm)


def verifica_it_segunda_falla(zs_ohm, ia_a, u_v=400.0, u0_v=230.0, neutro_distribuido=False):
    """IT, segunda falla: 2·Ia·Zs ≤ U (sin neutro) o ≤ U0 (con neutro distribuido)."""
    prod = 2.0 * ia_a * zs_ohm
    limite = u0_v if neutro_distribuido else u_v
    return {"dos_ia_zs_v": prod, "limite_v": limite, "cumple": prod <= limite}
