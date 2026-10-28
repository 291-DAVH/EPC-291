"""Parámetros normativos de la protección de conductores y de las curvas de disparo, en un solo lugar (antes escritos en línea en tres módulos).

Hoy hay una sola jurisdicción (AEA 90364 / IEC 60364-4-43 / IEC 60898-1 / IEC 60947-2); cuando exista una segunda, este módulo pasa a ser una política por norma.
Los valores son los mismos que tenían los módulos: moverlos a `aea_tables.json` (cuya revisión registra aprobaciones por hash) queda como decisión aparte.
"""

# IEC 60364-4-43: la corriente convencional de funcionamiento del dispositivo no supera 1,45 · Iz.
K_MAX_I2_IZ = 1.45

# Corriente convencional de funcionamiento I2 = k2 · In (disparo seguro), por tipo de dispositivo.
K2_CONVENCIONAL = {"mcb": 1.45, "mccb": 1.30, "fusible_gg": 1.60}

# Corriente convencional de no funcionamiento k1 · In (IEC 60898-1 para MCB, IEC 60947-2 para MCCB).
K1_NO_DISPARO = {"mcb": 1.13, "mccb": 1.05}
