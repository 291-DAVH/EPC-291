#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ccpm.py - Calculadora de cronograma por Cadena Crítica (CCPM).

Python 3 estándar, sin dependencias externas.

USO
---
CLI (desde la raíz del proyecto):
    python3 -B 98_LIBRARY/calculations/ccpm.py 90-management/Planning/ccpm_input.json \
        --md ccpm_output.md --json ccpm_output.json
    (sin --md ni --json imprime el Markdown por salida estándar)
    --md-secciones [ARCHIVO]  tablas B, C y (si hay tareas con `paquete`) B2 «Plan de paquetes» de
                              schedule-ccpm.md listas para pegar
    --desde AAAA-MM-DD        replanificar desde esa fecha (tareas hechas no se reprograman)
    --lote NOMBRE             cadena de una entrega parcial (excluye tareas de otro `lote`)

Como biblioteca:
    import ccpm
    resultado = ccpm.calcular_ccpm(datos_dict)      # dict -> dict
    resultado = ccpm.calcular_desde_archivo("entrada.json")
    texto_md  = ccpm.generar_markdown(resultado)
    estado    = ccpm.estado_buffer(avance_cadena=0.5, consumo_buffer=0.2)

ENTRADA (JSON / dict)
---------------------
    inicio                    fecha ISO (AAAA-MM-DD). Obligatorio. Si no es día hábil
                              el proyecto arranca el primer día hábil posterior.
    feriados                  [fechas ISO] opcional.
    dias_laborables           opcional; por defecto lunes a viernes. Lista de enteros
                              (0 = lunes ... 6 = domingo) o de nombres en español.
    fecha_limite_contractual  fecha ISO opcional.
    horas_por_dia             opcional, defecto 8: horas hábiles de trabajo por día hábil. Convierte
                              las horas en días hábiles (ceil(horas / horas_por_dia)).
    plazo_horas               opcional: plazo contractual expresado en horas hábiles. Su significado
                              lo fija `tipo_plazo`.
    tipo_plazo                "transcurrido" (defecto): las horas corren en el calendario; el límite es
                              el día hábil ceil(plazo_horas / horas_por_dia) desde el inicio (si no se da
                              `fecha_limite_contractual`, se deriva de ahí).
                              "esfuerzo": son horas de trabajo de ingeniería; no fijan una fecha, se
                              comparan con el esfuerzo de las tareas internas (días x horas_por_dia) y
                              se informa el déficit. Con ambos conceptos conviene dar los dos datos.
    metodo_buffer             "50pct" (defecto) o "rss".
    factor_buffer             opcional, defecto 0.5 (solo método 50pct).
    hitos                     opcional: [{nombre, fecha, tarea}]  (tarea = id asociado).
    tareas                    lista de {id, nombre, recurso, dur_segura, dur_agresiva,
                              predecesores, fecha_no_antes_de, tipo_recurso}.
        dur_segura            días hábiles (estimación con holgura), entero >= 1.
        dur_segura_h          alternativa a dur_segura, en horas hábiles (se convierte con horas_por_dia).
        dur_agresiva_h        alternativa a dur_agresiva, en horas hábiles.
        dur_agresiva          opcional; por defecto ceil(70 % de la segura: recorte del 30 %), mínimo 1.
        tipo_recurso          "interno" (defecto) o "externo" (p. ej. cliente).
        fecha_no_antes_de     opcional (dependencia externa).
        estado                "pendiente" (defecto), "hecha", "bloqueada" o "excluida".
                              hecha     = ya terminada: no se reprograma (con `fin_real` los
                                          sucesores no arrancan antes del día hábil siguiente).
                              bloqueada = se calcula con su duración pero se informa con aviso y ni
                                          ella ni sus sucesoras se cuentan como cumplibles.
                              excluida  = fuera de la entrega parcial/alcance: no entra en la cadena; las
                                          dependencias hacia ella se ignoran (con aviso).
        inicio_real, fin_real fechas reales (ISO) de una tarea hecha; `fin_real` implica "hecha".
        lote                  opcional (nombre heredado): entrega parcial a la que pertenece la tarea;
                              con --lote NOMBRE se excluyen las tareas de otra entrega parcial
                              (las tareas sin `lote` son comunes y se incluyen).
        entregable            opcional (ENT-nnn), solo para las tablas de SCHEDULE_CCPM.
        paquete               opcional (PQ-nn): paquete de revisión al que pertenece la tarea
                              (deliverables.md, 4.1). Con él la salida incluye el «Plan de
                              paquetes» (orden por dependencias, fechas de entrega al usuario y de
                              revisión). No cambia el cálculo de la cadena ni de los buffers.
        fase_paquete          opcional, solo con `paquete`: "elaborar" (tarea de Claude), "revisar"
                              (revisión del usuario: tarea propia, con duración y recurso distintos
                              de los de Claude, para que la cadena muestre el cuello de botella real)
                              o "procesar" (Claude procesa comentarios). Un paquete posterior debe
                              depender de la tarea "revisar" (o "procesar") del paquete anterior: si
                              depende de una tarea "elaborar", se advierte.
    base                      opcional, para el seguimiento: {fin_cadena, buffer_proyecto_dias,
                              cadena: [ids de la cadena crítica base]}. Con tareas hechas y `base`
                              se informan avance de la cadena, retraso proyectado y consumo del buffer.

CONVENCIONES DE TIEMPO
----------------------
Los días hábiles del proyecto se numeran 1, 2, 3... desde el primer día hábil >= inicio.
Internamente se usan índices base 0 con intervalos semiabiertos [inicio, fin): una tarea
de d días que arranca en el índice s ocupa los días hábiles s+1 ... s+d (numeración de
usuario). La fecha de fin de una tarea es la fecha del último día hábil que ocupa. El
calendario (fines de semana y feriados) solo interviene al convertir índices a fechas.

ALGORITMO
---------
1. Duraciones agresivas (dur_agresiva, 70 % de la segura por defecto: recorte del 30 %).
2. Programación hacia adelante ("parallel schedule generation"): día a día, entre las
   tareas listas (precedencias cumplidas y fecha_no_antes_de alcanzada) se arrancan por
   prioridad las que tengan su recurso libre. Prioridad dentro de un recurso: mayor ruta
   restante hacia el final (suma de duraciones agresivas por precedencia, incluida la
   propia tarea); empate por id (orden "natural": T2 < T10). Los recursos externos (o
   tareas sin recurso) no se restringen; sí participan en la red.
3. Cadena crítica: se parte de la tarea que termina última (empate: id menor) y se
   retrocede eligiendo el predecesor que determinó el inicio: aquel cuyo fin coincide con
   el inicio, ya sea por precedencia o por recurso (tarea anterior del mismo recurso).
   Si hay empate se prefiere precedencia sobre recurso, luego mayor duración agresiva,
   luego id; los demás candidatos se informan como "alternativas". Si ninguno explica el
   inicio, el eslabón es el primero (inicio del proyecto o fecha_no_antes_de).
4. Buffers (método configurable):
   - 50pct: ceil(factor * suma de duraciones agresivas de la ruta), mínimo 1.
   - rss:   ceil(raíz(suma((dur_segura - dur_agresiva)^2))), mínimo 1.
   Buffer de proyecto: tras el fin de la cadena. Buffers de alimentación: una ruta no
   crítica por cada punto de unión (precedencia o recurso) a la cadena (y, de forma
   recursiva, a otras rutas de alimentación); la ruta se determina retrocediendo con el
   mismo criterio que la cadena, sobre tareas aún no asignadas. El buffer se inserta justo
   antes de la tarea de unión y la ruta se reprograma lo más tarde posible (hacia atrás),
   conservando el orden de uso de cada recurso. Si la ruta no tiene holgura para el
   buffer, se retrasa la tarea de unión (y lo que la sigue) lo necesario y se advierte.
5. Comparación con la fecha límite contractual (déficit en días hábiles, buffer que cabe).
6. estado_buffer(): semáforo VERDE / AMARILLO / ROJO (umbrales por defecto A VALIDAR).

LIMITACIONES CONOCIDAS
----------------------
- La nivelación de recursos es una heurística de prioridad (no óptima); distintas reglas
  de prioridad pueden dar cadenas críticas diferentes.
- Cada recurso interno es de capacidad 1 y las tareas no se interrumpen ni se dividen.
- Solo vínculos fin-inicio sin demora.
- Cuando un buffer de alimentación obliga a retrasar la unión, la cadena se mantiene
  como la identificada en la programación sin buffers (con un desfase informado).
- Las tareas fuera de la cadena que no se unen a ella no reciben buffer (se advierte).
- Los hitos se comparan contra la fecha de fin de su tarea (sin buffer), salvo la última
  tarea de la cadena, que se compara contra el fin de proyecto con buffer.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import re
import sys
import unicodedata
from bisect import bisect_left
from collections import defaultdict, deque
from datetime import date, timedelta

VERSION = "1.4"

RECORTE_AGRESIVO_PCT = 30   # duración agresiva por defecto = segura menos este porcentaje (regla del proyecto)

#: Umbrales por defecto del semáforo de buffer. Son valores de partida A VALIDAR por
#: el usuario/organización con datos reales (no son una norma).
PARAMS_SEMAFORO_DEFECTO = {
    "verde_pendiente": 0.33,
    "verde_ordenada": 0.10,
    "rojo_pendiente": 0.67,
    "rojo_ordenada": 0.33,
}

_DIAS_NOMBRE = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3,
                "viernes": 4, "sabado": 5, "domingo": 6}
_DIAS_ABREV = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
_CLAVES_ENTRADA = {"inicio", "feriados", "dias_laborables", "fecha_limite_contractual",
                   "horas_por_dia", "plazo_horas", "tipo_plazo",
                   "hitos", "tareas", "metodo_buffer", "factor_buffer", "base"}
#: Estados admitidos de una tarea (H-033, H-040).
ESTADOS_TAREA = ("pendiente", "hecha", "bloqueada", "excluida")
#: Fases de una tarea dentro de un paquete de revisión (campo `fase_paquete`).
FASES_PAQUETE = ("elaborar", "revisar", "procesar")
_MAX_ITER = 200


# ---------------------------------------------------------------------------
# Utilidades generales
# ---------------------------------------------------------------------------

def _ceil(x):
    """Techo con tolerancia a ruido de punto flotante."""
    return int(math.ceil(round(x, 9)))


def _clave_natural(s):
    partes = re.split(r"(\d+)", s)
    return tuple(int(p) if i % 2 else p for i, p in enumerate(partes))


def _parse_fecha(valor, campo):
    if not isinstance(valor, str):
        raise ValueError(f"{campo}: se esperaba una fecha ISO (AAAA-MM-DD), se recibió {valor!r}")
    try:
        return date.fromisoformat(valor.strip())
    except ValueError:
        raise ValueError(f"{campo}: fecha ISO inválida {valor!r} (formato AAAA-MM-DD)") from None


def _numero_positivo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
        raise ValueError(f"{campo}: se esperaba un número > 0, se recibió {valor!r}")
    return float(valor)


def _horas_a_dias(horas, campo, hpd):
    """Convierte horas hábiles en días hábiles enteros (redondeo hacia arriba, mínimo 1)."""
    return max(1, _ceil(_numero_positivo(horas, campo) / hpd))


def _entero_positivo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{campo}: se esperaba un entero >= 1 (días hábiles), se recibió {valor!r}")
    if isinstance(valor, float):
        if not valor.is_integer():
            raise ValueError(f"{campo}: debe ser un número entero de días hábiles, se recibió {valor!r}")
        valor = int(valor)
    if valor < 1:
        raise ValueError(f"{campo}: debe ser >= 1, se recibió {valor!r}")
    return valor


def _sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _fmt(x):
    """Número con coma decimal, sin ceros sobrantes."""
    if isinstance(x, float):
        s = f"{x:.2f}".rstrip("0").rstrip(".")
        return s.replace(".", ",")
    return str(x)


def _fecha_md(iso):
    if iso is None:
        return "-"
    d = date.fromisoformat(iso)
    return f"{iso} {_DIAS_ABREV[d.weekday()]}"


def _esc(texto):
    return str(texto).replace("|", "\\|").replace("\n", " ")


# ---------------------------------------------------------------------------
# Calendario
# ---------------------------------------------------------------------------

class Calendario:
    """Calendario de días hábiles con índices base 0 (0 = primer día hábil >= inicio)."""

    def __init__(self, inicio, feriados=(), dias_laborables=(0, 1, 2, 3, 4)):
        self.dias_laborables = frozenset(dias_laborables)
        if not self.dias_laborables:
            raise ValueError("dias_laborables: debe haber al menos un día laborable")
        self.feriados = frozenset(feriados)
        self.inicio_solicitado = inicio
        self.base = self._proximo_habil(inicio)
        self._fechas = [self.base]

    def es_habil(self, d):
        return d.weekday() in self.dias_laborables and d not in self.feriados

    def _proximo_habil(self, d):
        for _ in range(100000):
            if self.es_habil(d):
                return d
            d += timedelta(days=1)
        raise ValueError("El calendario no tiene días hábiles (revisar feriados/dias_laborables)")

    def _extender_hasta_indice(self, i):
        while len(self._fechas) <= i:
            self._fechas.append(self._proximo_habil(self._fechas[-1] + timedelta(days=1)))

    def _extender_hasta_fecha(self, d):
        while self._fechas[-1] < d:
            self._fechas.append(self._proximo_habil(self._fechas[-1] + timedelta(days=1)))

    def fecha(self, i):
        """Fecha del día hábil de índice i (base 0)."""
        if i < 0:
            raise ValueError(f"índice de día hábil negativo: {i}")
        self._extender_hasta_indice(i)
        return self._fechas[i]

    def indice_techo(self, d):
        """Índice del primer día hábil con fecha >= d (0 si d es anterior al inicio)."""
        if d <= self.base:
            return 0
        self._extender_hasta_fecha(d)
        return bisect_left(self._fechas, d)

    def contar_hasta(self, d):
        """Cantidad de días hábiles en [base, d] (0 si d < base)."""
        if d < self.base:
            return 0
        i = self.indice_techo(d)
        return i + 1 if self._fechas[i] == d else i

    def dias_habiles_entre(self, d1, d2):
        """Días hábiles con signo: los contenidos en (d1, d2] si d2 >= d1; negativo si no."""
        if d2 >= d1:
            return self._contar_intervalo(d1, d2)
        return -self._contar_intervalo(d2, d1)

    def _contar_intervalo(self, a, b):
        n, d = 0, a
        while d < b:
            d += timedelta(days=1)
            if self.es_habil(d):
                n += 1
        return n


# ---------------------------------------------------------------------------
# Validación y normalización de la entrada
# ---------------------------------------------------------------------------

def _parse_dias_laborables(valor):
    if valor is None:
        return (0, 1, 2, 3, 4)
    if not isinstance(valor, (list, tuple)) or not valor:
        raise ValueError("dias_laborables: debe ser una lista no vacía (0=lunes..6=domingo o nombres)")
    out = set()
    for v in valor:
        if isinstance(v, bool):
            raise ValueError(f"dias_laborables: valor inválido {v!r}")
        if isinstance(v, int):
            if not 0 <= v <= 6:
                raise ValueError(f"dias_laborables: {v} fuera de rango 0..6 (0 = lunes)")
            out.add(v)
        elif isinstance(v, str):
            k = _sin_acentos(v.strip().lower())
            if k not in _DIAS_NOMBRE:
                raise ValueError(f"dias_laborables: nombre de día desconocido {v!r}")
            out.add(_DIAS_NOMBRE[k])
        else:
            raise ValueError(f"dias_laborables: valor inválido {v!r}")
    return tuple(sorted(out))


def _detectar_ciclo(ids, preds):
    """Devuelve una lista de ids que forma un ciclo, o None si la red es acíclica."""
    grado = {i: len(preds[i]) for i in ids}
    succ = defaultdict(list)
    for i in ids:
        for p in preds[i]:
            succ[p].append(i)
    cola = deque(i for i in ids if grado[i] == 0)
    vistos = 0
    while cola:
        u = cola.popleft()
        vistos += 1
        for v in succ[u]:
            grado[v] -= 1
            if grado[v] == 0:
                cola.append(v)
    if vistos == len(ids):
        return None
    resto = {i for i in ids if grado[i] > 0}
    cur = sorted(resto, key=_clave_natural)[0]
    orden, pos = [], {}
    while cur not in pos:
        pos[cur] = len(orden)
        orden.append(cur)
        cur = sorted((p for p in preds[cur] if p in resto), key=_clave_natural)[0]
    ciclo = orden[pos[cur]:]
    ciclo.reverse()  # sentido predecesor -> sucesor
    return ciclo + [ciclo[0]]


def _validar(datos, desde=None, lote=None):
    if not isinstance(datos, dict):
        raise ValueError("La entrada debe ser un objeto JSON (dict)")
    adv = []
    desconocidas = sorted(set(datos) - _CLAVES_ENTRADA)
    if desconocidas:
        adv.append("Claves de entrada no reconocidas (ignoradas): " + ", ".join(map(str, desconocidas)))

    if "inicio" not in datos:
        raise ValueError("Falta el campo obligatorio 'inicio' (fecha ISO)")
    inicio = _parse_fecha(datos["inicio"], "inicio")
    if desde is not None:
        if isinstance(desde, date):
            desde = desde.isoformat()
        desde = _parse_fecha(desde, "desde")

    feriados_raw = datos.get("feriados") or []
    if not isinstance(feriados_raw, (list, tuple)):
        raise ValueError("feriados: debe ser una lista de fechas ISO")
    feriados = [_parse_fecha(f, f"feriados[{k}]") for k, f in enumerate(feriados_raw)]
    # Con 'desde' el calendario arranca en esa fecha (replanificar desde hoy).
    ref_inicio = desde if desde is not None else inicio
    cal = Calendario(ref_inicio, feriados, _parse_dias_laborables(datos.get("dias_laborables")))
    if desde is not None:
        adv.append(f"Replanificación desde {desde.isoformat()}: las tareas hechas no se reprograman; "
                   "las pendientes arrancan desde esa fecha.")
    if cal.base != ref_inicio:
        adv.append(f"La fecha de inicio {ref_inicio.isoformat()} no es día hábil: el proyecto "
                   f"arranca el {cal.base.isoformat()}.")

    hpd = 8.0
    if datos.get("horas_por_dia") is not None:
        hpd = _numero_positivo(datos["horas_por_dia"], "horas_por_dia")
        if hpd > 24:
            raise ValueError(f"horas_por_dia: debe ser <= 24, se recibió {datos['horas_por_dia']!r}")
    tipo_plazo = str(datos.get("tipo_plazo", "transcurrido")).strip().lower()
    if tipo_plazo not in ("transcurrido", "esfuerzo"):
        raise ValueError(f"tipo_plazo: debe ser 'transcurrido' o 'esfuerzo', se recibió {tipo_plazo!r}")
    plazo_horas = None
    if datos.get("plazo_horas") is not None:
        plazo_horas = _numero_positivo(datos["plazo_horas"], "plazo_horas")

    limite = None
    if datos.get("fecha_limite_contractual") is not None:
        limite = _parse_fecha(datos["fecha_limite_contractual"], "fecha_limite_contractual")
    if plazo_horas is not None and tipo_plazo == "transcurrido":
        n_dias = max(1, _ceil(plazo_horas / hpd))
        derivado = cal.fecha(n_dias - 1)
        if limite is None:
            limite = derivado
            adv.append(f"Fecha límite derivada de plazo_horas ({plazo_horas:g} h hábiles transcurridas / "
                       f"{hpd:g} h por día = {n_dias} día(s) hábil(es)): {derivado.isoformat()}.")
        elif limite != derivado:
            adv.append(f"fecha_limite_contractual ({limite.isoformat()}) no coincide con plazo_horas "
                       f"({plazo_horas:g} h = {n_dias} día(s) hábil(es), {derivado.isoformat()}): se usa la fecha dada.")

    metodo = str(datos.get("metodo_buffer", "50pct")).strip().lower()
    if metodo not in ("50pct", "rss"):
        raise ValueError(f"metodo_buffer: debe ser '50pct' o 'rss', se recibió {metodo!r}")
    factor = datos.get("factor_buffer", 0.5)
    if isinstance(factor, bool) or not isinstance(factor, (int, float)) or not 0 < factor <= 1:
        raise ValueError(f"factor_buffer: debe ser un número en (0, 1], se recibió {factor!r}")

    tareas_raw = datos.get("tareas")
    if not isinstance(tareas_raw, list) or not tareas_raw:
        raise ValueError("tareas: debe ser una lista no vacía")

    todas, orden_todas = {}, []
    for k, t in enumerate(tareas_raw):
        if not isinstance(t, dict):
            raise ValueError(f"tareas[{k}]: debe ser un objeto")
        if t.get("id") is None or str(t["id"]).strip() == "":
            raise ValueError(f"tareas[{k}]: falta el campo 'id'")
        tid = str(t["id"]).strip()
        if tid in todas:
            raise ValueError(f"Id de tarea duplicado: {tid!r}")
        if t.get("dur_segura") is not None and t.get("dur_segura_h") is not None:
            raise ValueError(f"Tarea {tid!r}: use 'dur_segura' (días) o 'dur_segura_h' (horas), no ambas")
        if t.get("dur_agresiva") is not None and t.get("dur_agresiva_h") is not None:
            raise ValueError(f"Tarea {tid!r}: use 'dur_agresiva' (días) o 'dur_agresiva_h' (horas), no ambas")
        if "dur_segura" not in t and t.get("dur_segura_h") is None:
            raise ValueError(f"Tarea {tid!r}: falta 'dur_segura'")
        if t.get("dur_segura_h") is not None:
            seg = _horas_a_dias(t["dur_segura_h"], f"Tarea {tid!r}: dur_segura_h", hpd)
        else:
            seg = _entero_positivo(t["dur_segura"], f"Tarea {tid!r}: dur_segura")
        if t.get("dur_agresiva_h") is not None:
            agr = _horas_a_dias(t["dur_agresiva_h"], f"Tarea {tid!r}: dur_agresiva_h", hpd)
            if agr > seg:
                raise ValueError(f"Tarea {tid!r}: dur_agresiva ({agr}) no puede superar a dur_segura ({seg})")
        elif t.get("dur_agresiva") is None:
            agr = max(1, -(-seg * (100 - RECORTE_AGRESIVO_PCT) // 100))   # ceil(70 % de la segura)
        else:
            agr = _entero_positivo(t["dur_agresiva"], f"Tarea {tid!r}: dur_agresiva")
            if agr > seg:
                raise ValueError(f"Tarea {tid!r}: dur_agresiva ({agr}) no puede superar a dur_segura ({seg})")
        tipo = str(t.get("tipo_recurso", "interno")).strip().lower()
        if tipo not in ("interno", "externo"):
            raise ValueError(f"Tarea {tid!r}: tipo_recurso debe ser 'interno' o 'externo', se recibió {tipo!r}")
        recurso = str(t.get("recurso") or "").strip()
        preds_raw = t.get("predecesores") or []
        if not isinstance(preds_raw, (list, tuple)):
            raise ValueError(f"Tarea {tid!r}: predecesores debe ser una lista de ids")
        preds_l = []
        for p in preds_raw:
            p = str(p).strip()
            if p not in preds_l:
                preds_l.append(p)
        nb = t.get("fecha_no_antes_de")
        nb = _parse_fecha(nb, f"Tarea {tid!r}: fecha_no_antes_de") if nb is not None else None
        # Estado (H-033, H-040)
        ir, fr = t.get("inicio_real"), t.get("fin_real")
        ir = _parse_fecha(ir, f"Tarea {tid!r}: inicio_real") if ir is not None else None
        fr = _parse_fecha(fr, f"Tarea {tid!r}: fin_real") if fr is not None else None
        if ir and fr and fr < ir:
            raise ValueError(f"Tarea {tid!r}: fin_real ({fr}) es anterior a inicio_real ({ir})")
        est = t.get("estado")
        if est is None:
            est = "hecha" if fr is not None else "pendiente"
        else:
            est = _sin_acentos(str(est).strip().lower())
            if est not in ESTADOS_TAREA:
                raise ValueError(f"Tarea {tid!r}: estado debe ser uno de {', '.join(ESTADOS_TAREA)}, "
                                 f"se recibió {t.get('estado')!r}")
            if est != "hecha" and fr is not None:
                raise ValueError(f"Tarea {tid!r}: tiene fin_real pero estado {est!r}; "
                                 "una tarea con fin real es 'hecha'")
        lt = t.get("lote")
        lt = str(lt).strip() if lt not in (None, "") else None
        pq = t.get("paquete")
        pq = str(pq).strip() if pq not in (None, "") else None
        fase = t.get("fase_paquete")
        if fase in (None, ""):
            fase = None
        else:
            fase = _sin_acentos(str(fase).strip().lower())
            if fase not in FASES_PAQUETE:
                raise ValueError(f"Tarea {tid!r}: fase_paquete debe ser una de {', '.join(FASES_PAQUETE)}, "
                                 f"se recibió {t.get('fase_paquete')!r}")
            if pq is None:
                raise ValueError(f"Tarea {tid!r}: 'fase_paquete' requiere 'paquete'")
        motivo = None
        if lote is not None and lt is not None and lt != str(lote).strip() and est != "hecha":
            est, motivo = "excluida", f"fuera de la entrega parcial {str(lote).strip()!r} (lote {lt!r})"
        elif est == "excluida":
            motivo = "excluida de la entrega parcial/alcance"
        todas[tid] = {
            "id": tid, "nombre": str(t.get("nombre") or tid), "recurso": recurso, "tipo": tipo,
            "seg": seg, "agr": agr, "preds_lista": preds_l, "no_antes": nb,
            "restringido": tipo == "interno" and recurso != "",
            "min_idx": cal.indice_techo(nb) if nb else 0,
            "estado": est, "inicio_real": ir, "fin_real": fr, "lote": lt, "motivo": motivo,
            "entregable": str(t.get("entregable") or "").strip(),
            "paquete": pq, "fase": fase,
        }
        orden_todas.append(tid)
    plazo_info = None
    if plazo_horas is not None:
        activas = [todas[i] for i in orden_todas if todas[i]["estado"] not in ("excluida", "hecha")
                   and todas[i]["tipo"] == "interno"]
        esf_seg = sum(t["seg"] for t in activas) * hpd
        esf_agr = sum(t["agr"] for t in activas) * hpd
        plazo_info = {"tipo": tipo_plazo, "plazo_horas": plazo_horas, "horas_por_dia": hpd,
                      "dias_habiles_equivalentes": max(1, _ceil(plazo_horas / hpd)),
                      "esfuerzo_seguro_horas": esf_seg, "esfuerzo_agresivo_horas": esf_agr,
                      "deficit_esfuerzo_horas": None}
        if tipo_plazo == "esfuerzo":
            deficit = esf_agr - plazo_horas
            plazo_info["deficit_esfuerzo_horas"] = max(0.0, deficit)
            if deficit > 0:
                adv.append(f"Esfuerzo agresivo de las tareas internas ({esf_agr:g} h) supera el plazo de "
                           f"{plazo_horas:g} h de esfuerzo: déficit de {deficit:g} h.")
            elif esf_seg > plazo_horas:
                adv.append(f"Esfuerzo seguro ({esf_seg:g} h) supera el plazo de {plazo_horas:g} h; "
                           "solo cabe con las duraciones agresivas.")
    if lote is not None and not any(todas[i]["lote"] == str(lote).strip() for i in orden_todas):
        adv.append(f"Ninguna tarea declara lote {str(lote).strip()!r}: se calculó con todas las tareas.")

    for tid in orden_todas:
        for p in todas[tid]["preds_lista"]:
            if p not in todas:
                raise ValueError(f"La tarea {tid!r} referencia un predecesor inexistente: {p!r}")
            if p == tid:
                raise ValueError(f"Ciclo en la red de precedencias: {tid} -> {tid}")
    ciclo = _detectar_ciclo(orden_todas, {i: set(todas[i]["preds_lista"]) for i in orden_todas})
    if ciclo:
        raise ValueError("Ciclo en la red de precedencias: " + " -> ".join(ciclo))

    adv.extend(_avisos_paquetes(todas, orden_todas))

    # Tareas activas (entran en el cálculo): pendientes y bloqueadas.
    hechas = [i for i in orden_todas if todas[i]["estado"] == "hecha"]
    excluidas = [i for i in orden_todas if todas[i]["estado"] == "excluida"]
    bloqueadas = [i for i in orden_todas if todas[i]["estado"] == "bloqueada"]
    orden = [i for i in orden_todas if todas[i]["estado"] in ("pendiente", "bloqueada")]
    if not orden:
        raise ValueError("No quedan tareas pendientes ni bloqueadas para planificar "
                         "(todas están hechas o excluidas)")
    tareas = {i: todas[i] for i in orden}
    for tid in orden:
        tk = tareas[tid]
        tk["preds_lista_original"] = list(tk["preds_lista"])
        nuevos = []
        for p in tk["preds_lista"]:
            ep = todas[p]["estado"]
            if ep == "hecha":
                fr = todas[p]["fin_real"]
                if fr is not None:
                    tk["min_idx"] = max(tk["min_idx"], cal.contar_hasta(fr))
            elif ep == "excluida":
                adv.append(f"La tarea {tid!r} depende de {p!r}, excluida del cálculo: se ignora esa "
                           "dependencia (verificar que el predecesor esté cubierto por otro medio).")
            else:
                nuevos.append(p)
        tk["preds_lista"] = nuevos
    preds = {i: set(tareas[i]["preds_lista"]) for i in orden}
    succ = {i: [] for i in orden}
    for i in orden:
        for p in tareas[i]["preds_lista"]:
            succ[p].append(i)

    # Tareas afectadas por bloqueo: bloqueadas y todas sus sucesoras.
    afectadas, cola_b = set(), deque(bloqueadas)
    while cola_b:
        u = cola_b.popleft()
        if u in afectadas:
            continue
        afectadas.add(u)
        cola_b.extend(succ[u])
    if bloqueadas:
        adv.append("Tareas BLOQUEADAS (se calculan con su duración pero NO se cuentan como cumplibles; "
                   "las que dependen de ellas tampoco): " + ", ".join(bloqueadas)
                   + ". Resolver el bloqueo o replanificar la entrega sin ellas.")

    hitos = []
    for k, h in enumerate(datos.get("hitos") or []):
        if not isinstance(h, dict):
            raise ValueError(f"hitos[{k}]: debe ser un objeto")
        nombre = str(h.get("nombre") or f"Hito {k + 1}")
        if "fecha" not in h:
            raise ValueError(f"Hito {nombre!r}: falta 'fecha'")
        tarea = h.get("tarea")
        if tarea is not None:
            tarea = str(tarea).strip()
            if tarea not in todas:
                raise ValueError(f"El hito {nombre!r} referencia una tarea inexistente: {tarea!r}")
            if todas[tarea]["estado"] in ("hecha", "excluida"):
                adv.append(f"El hito {nombre!r} referencia la tarea {tarea!r} ({todas[tarea]['estado']}): "
                           "se compara con el fin de proyecto.")
                tarea = None
        hitos.append({"nombre": nombre, "fecha": _parse_fecha(h["fecha"], f"Hito {nombre!r}: fecha"),
                      "tarea": tarea})

    # Ruta restante (suma de duraciones agresivas hacia el final, incluida la propia tarea).
    ruta = {}
    grado = {i: len(succ[i]) for i in orden}
    cola = deque(i for i in orden if grado[i] == 0)
    while cola:
        u = cola.popleft()
        ruta[u] = tareas[u]["agr"] + max((ruta[s] for s in succ[u]), default=0)
        for p in preds[u]:
            grado[p] -= 1
            if grado[p] == 0:
                cola.append(p)

    if len(orden) > 1:
        aisladas = [i for i in orden if not preds[i] and not succ[i]]
        if aisladas:
            adv.append("Tareas sin predecesor ni sucesor (aisladas de la red): " + ", ".join(aisladas)
                       + ". Verificar que no falte una dependencia.")
    sin_recurso = [i for i in orden if tareas[i]["tipo"] == "interno" and not tareas[i]["recurso"]]
    if sin_recurso:
        adv.append("Tareas internas sin 'recurso' (no se restringen por recurso único): "
                   + ", ".join(sin_recurso))

    base = datos.get("base")
    if base is not None and not isinstance(base, dict):
        raise ValueError("base: debe ser un objeto {fin_cadena, buffer_proyecto_dias, cadena}")

    return {"inicio": inicio, "desde": desde, "lote": (str(lote).strip() if lote is not None else None),
            "cal": cal, "tareas": tareas, "orden": orden, "todas": todas, "orden_todas": orden_todas,
            "hechas": hechas, "excluidas": excluidas, "bloqueadas": bloqueadas, "afectadas": afectadas,
            "preds": preds, "succ": succ, "ruta": ruta, "clave": {i: _clave_natural(i) for i in orden},
            "hitos": hitos, "limite": limite, "plazo_info": plazo_info, "metodo": metodo, "factor": float(factor),
            "base": base, "advertencias": adv}


# ---------------------------------------------------------------------------
# Paquetes de revisión (campo `paquete`; deliverables.md, 4.1)
# ---------------------------------------------------------------------------

def _avisos_paquetes(todas, orden_todas):
    """Advertencias sobre la secuencia de revisión de los paquetes (no cambian el cálculo).

    Solo se emiten si alguna tarea declara `paquete`:
    - un paquete posterior que depende de una tarea de otro paquete que no es su revisión
      ("revisar") ni su procesamiento de comentarios ("procesar"): el paquete no debe empezar
      antes de que el anterior esté REVISADO;
    - un paquete sin tarea "revisar" cuando el proyecto usa fases;
    - una tarea "revisar" con el mismo recurso que una tarea "elaborar" del mismo paquete: la
      revisión es del usuario, un recurso distinto de Claude.
    """
    act = [i for i in orden_todas if todas[i]["paquete"] and todas[i]["estado"] != "excluida"]
    if not act:
        return []
    adv = []
    usa_fases = any(todas[i]["fase"] for i in act)
    por_pq = defaultdict(list)
    for i in act:
        por_pq[todas[i]["paquete"]].append(i)
    pqs_con_fase = {pq for pq, ids in por_pq.items() if any(todas[i]["fase"] for i in ids)}
    if usa_fases:
        for pq in sorted(por_pq, key=_clave_natural):
            ids = por_pq[pq]
            if not any(todas[i]["fase"] == "revisar" for i in ids):
                adv.append(f"El paquete {pq!r} no tiene ninguna tarea con fase_paquete 'revisar': la revisión "
                           "del usuario debe modelarse como tarea propia, con su duración y su recurso.")
            rev_rec = {todas[i]["recurso"] for i in ids if todas[i]["fase"] == "revisar" and todas[i]["recurso"]}
            ela_rec = {todas[i]["recurso"] for i in ids if todas[i]["fase"] == "elaborar" and todas[i]["recurso"]}
            comunes = sorted(rev_rec & ela_rec)
            if comunes:
                adv.append(f"En el paquete {pq!r} la revisión y la elaboración comparten el recurso "
                           f"{', '.join(map(repr, comunes))}: la revisión es una tarea del usuario, un recurso "
                           "distinto del que elabora (si no, el cuello de botella real no se ve).")
    for i in act:
        ti = todas[i]
        for q in ti["preds_lista"]:
            tq = todas.get(q)
            if tq is None or tq["estado"] == "excluida" or not tq["paquete"] or tq["paquete"] == ti["paquete"]:
                continue
            if tq["paquete"] in pqs_con_fase and tq["fase"] not in ("revisar", "procesar"):
                adv.append(f"La tarea {i!r} (paquete {ti['paquete']!r}) depende de {q!r} del paquete "
                           f"{tq['paquete']!r}, que no es su revisión ni su procesamiento de comentarios: el "
                           f"paquete {ti['paquete']!r} no debe empezar hasta que {tq['paquete']!r} esté REVISADO.")
    return adv


def _plan_paquetes(m, p, cal):
    """Plan de paquetes: orden por dependencias, fechas y cuello de botella de la revisión.

    Devuelve (plan, advertencias); plan es None si ninguna tarea declara `paquete`.
    """
    todas, ps, pe = m["todas"], p["plan_s"], p["plan_e"]
    miembros = defaultdict(list)
    for i in m["orden_todas"]:
        t = todas[i]
        if t["paquete"] and t["estado"] != "excluida":
            miembros[t["paquete"]].append(i)
    if not miembros:
        return None, []
    adv = []
    info = {}
    for pq, ids in miembros.items():
        ini, fin, idx = [], [], []
        entrega, rev_ini, rev_fin = [], [], []
        dias_rev = dias_ela = 0
        for i in ids:
            t = todas[i]
            if t["estado"] == "hecha":
                d_i, d_f, k = t["inicio_real"], t["fin_real"], None
            else:
                d_i, d_f, k = cal.fecha(ps[i]), cal.fecha(pe[i] - 1), ps[i]
                idx.append(k)
            if d_i:
                ini.append(d_i)
            if d_f:
                fin.append(d_f)
            if t["fase"] == "elaborar":
                dias_ela += t["agr"]
                if d_f:
                    entrega.append(d_f)
            elif t["fase"] == "revisar":
                dias_rev += t["agr"]
                if d_i:
                    rev_ini.append(d_i)
                if d_f:
                    rev_fin.append(d_f)
        dep = set()
        for i in ids:
            for q in todas[i].get("preds_lista_original", todas[i]["preds_lista"]):
                tq = todas.get(q)
                if tq and tq["estado"] != "excluida" and tq["paquete"] and tq["paquete"] != pq:
                    dep.add(tq["paquete"])
        if all(todas[i]["estado"] == "hecha" for i in ids):
            estado = "hecho"
        elif any(i in m["afectadas"] for i in ids):
            estado = "bloqueado"
        else:
            estado = "pendiente"
        en_cad = [i for i in p["ids_cadena"] if i in ids]
        info[pq] = {
            "id": pq,
            "tareas": sorted(ids, key=lambda i: (ps[i] if todas[i]["estado"] != "hecha" else -1, m["clave"].get(i, _clave_natural(i)))),
            "depende_de": sorted(dep, key=_clave_natural),
            "inicio": _iso(min(ini)) if ini else None,
            "fin": _iso(max(fin)) if fin else None,
            "entrega_al_usuario": _iso(max(entrega)) if entrega else None,
            "inicio_revision": _iso(min(rev_ini)) if rev_ini else None,
            "fin_revision": _iso(max(rev_fin)) if rev_fin else None,
            "dias_elaboracion": dias_ela, "dias_revision_usuario": dias_rev,
            "estado": estado, "tareas_en_cadena_critica": en_cad,
            "_k": min(idx) if idx else -1,
        }
    # Orden topológico (Kahn) con prioridad por inicio y luego por id natural.
    grado = {pq: len([d for d in info[pq]["depende_de"] if d in info]) for pq in info}
    suc = defaultdict(list)
    for pq in info:
        for d in info[pq]["depende_de"]:
            if d in info:
                suc[d].append(pq)
    hp = [(info[pq]["_k"], _clave_natural(pq), pq) for pq in info if grado[pq] == 0]
    heapq.heapify(hp)
    orden = []
    while hp:
        _, _, u = heapq.heappop(hp)
        orden.append(u)
        for v in suc[u]:
            grado[v] -= 1
            if grado[v] == 0:
                heapq.heappush(hp, (info[v]["_k"], _clave_natural(v), v))
    if len(orden) < len(info):
        resto = sorted((pq for pq in info if pq not in orden), key=lambda q: (info[q]["_k"], _clave_natural(q)))
        adv.append("Dependencias circulares entre paquetes (cada uno espera a otro): " + ", ".join(resto)
                   + ". Revisar las predecesoras de sus tareas.")
        orden += resto
    paquetes = []
    for n, pq in enumerate(orden, 1):
        d = info[pq]
        d.pop("_k")
        d["orden"] = n
        paquetes.append(d)
    cad = p["ids_cadena"]
    dias_cad = sum(todas[i]["agr"] for i in cad)
    rev_cad = [i for i in cad if todas[i]["fase"] == "revisar"]
    dias_rev_cad = sum(todas[i]["agr"] for i in rev_cad)
    cuello = {"tareas_cadena": len(cad), "tareas_revision_en_cadena": len(rev_cad),
              "dias_cadena": dias_cad, "dias_revision_en_cadena": dias_rev_cad,
              "porcentaje_revision_en_cadena": round(dias_rev_cad / dias_cad, 4) if dias_cad else 0.0}
    if rev_cad and dias_cad and dias_rev_cad / dias_cad >= 0.5:
        adv.append(f"Cuello de botella: la revisión del usuario ocupa {dias_rev_cad} de los {dias_cad} día(s) "
                   "hábil(es) de la cadena crítica (" + ", ".join(rev_cad) + "). El ritmo del proyecto lo "
                   "fija la revisión; acortar la elaboración no adelanta la fecha.")
    return {"paquetes": paquetes, "cuello_de_botella": cuello}, adv


# ---------------------------------------------------------------------------
# Programación hacia adelante con restricción de recurso
# ---------------------------------------------------------------------------

def _adelante(m, min_start, extra):
    """Devuelve (inicio, fin, res_prev); fin exclusivo. res_prev[t] = tarea previa del recurso."""
    T, preds, ruta, clave = m["tareas"], m["preds"], m["ruta"], m["clave"]
    start, end, res_free, res_last, res_prev = {}, {}, {}, {}, {}
    pend = set(T)
    horizonte = sum(t["agr"] for t in T.values()) + max(min_start.values(), default=0) + 10
    t = 0
    while pend:
        if t > horizonte:  # pragma: no cover (red acíclica: no debería ocurrir)
            raise RuntimeError("La programación no converge (revisar la red)")
        listas = []
        for tid in pend:
            if min_start[tid] > t:
                continue
            if all(p in end and end[p] <= t for p in (preds[tid] | extra.get(tid, set()))):
                listas.append(tid)
        listas.sort(key=lambda i: (-ruta[i], clave[i]))
        for tid in listas:
            tk = T[tid]
            if tk["restringido"]:
                r = tk["recurso"]
                if res_free.get(r, 0) > t:
                    continue
                res_prev[tid] = res_last.get(r)
                res_last[r] = tid
                res_free[r] = t + tk["agr"]
            start[tid] = t
            end[tid] = t + tk["agr"]
            pend.discard(tid)
        t += 1
    return start, end, res_prev


def _determinantes(tid, m, start, end, res_prev):
    """Candidatos que determinaron el inicio de tid, en orden de preferencia."""
    s = start[tid]
    T, clave = m["tareas"], m["clave"]
    prec = [p for p in m["preds"][tid] if end[p] == s]
    prec.sort(key=lambda p: (-T[p]["agr"], clave[p]))
    rp = res_prev.get(tid)
    rec_ok = rp is not None and end[rp] == s
    out = []
    for p in prec:
        out.append((p, "precedencia y recurso" if (rec_ok and p == rp) else "precedencia"))
    if rec_ok and rp not in prec:
        out.append((rp, "recurso"))
    return out


def _cadena_critica(m, start, end, res_prev, min_start):
    T, clave = m["tareas"], m["clave"]
    cur = sorted(T, key=lambda i: (-end[i], clave[i]))[0]
    eslabones = []
    while True:
        dets = _determinantes(cur, m, start, end, res_prev)
        if dets:
            pred, vinculo = dets[0]
            alternativas = [{"id": p, "vinculo": v} for p, v in dets[1:]]
        else:
            pred, alternativas = None, []
            vinculo = "inicio del proyecto" if start[cur] == 0 else "fecha_no_antes_de"
        eslabones.append({"id": cur, "vinculo": vinculo, "predecesor": pred, "alternativas": alternativas})
        if pred is None:
            break
        cur = pred
    eslabones.reverse()
    return eslabones


# ---------------------------------------------------------------------------
# Buffers
# ---------------------------------------------------------------------------

def _tamano_buffer(ids, m):
    """Devuelve (tamaño en días, detalle del cálculo) para una ruta de tareas."""
    T = m["tareas"]
    if m["metodo"] == "50pct":
        suma = sum(T[i]["agr"] for i in ids)
        bruto = m["factor"] * suma
        det = {"metodo": "50pct", "factor": m["factor"], "suma_dur_agresivas": suma,
               "valor_calculado": round(bruto, 4)}
    else:
        ss = sum((T[i]["seg"] - T[i]["agr"]) ** 2 for i in ids)
        bruto = math.sqrt(ss)
        det = {"metodo": "rss", "suma_cuadrados": ss, "valor_calculado": round(bruto, 4)}
    tam = max(1, _ceil(bruto))
    det["tamano_dias"] = tam
    return tam, det


def _rutas_alimentacion(m, start, end, res_prev, cadena_ids):
    asignadas = set(cadena_ids)
    rutas = []
    cola = deque(cadena_ids)
    clave, T = m["clave"], m["tareas"]
    while cola:
        tj = cola.popleft()
        cands = sorted(m["preds"][tj], key=lambda p: (-end[p], clave[p]))
        cands = [(p, "precedencia") for p in cands]
        rp = res_prev.get(tj)
        if rp is not None and end[rp] == start[tj] and rp not in m["preds"][tj]:
            cands.append((rp, "recurso"))
        for p, via in cands:
            if p in asignadas:
                continue
            camino = [p]
            asignadas.add(p)
            cur = p
            while True:
                dets = [(q, v) for q, v in _determinantes(cur, m, start, end, res_prev)
                        if q not in asignadas]
                if not dets:
                    break
                q = dets[0][0]
                camino.append(q)
                asignadas.add(q)
                cur = q
            camino.reverse()
            tam, det = _tamano_buffer(camino, m)
            rutas.append({"id": f"FB-{len(rutas) + 1}", "tareas": camino, "ultima": p,
                          "se_une_a": tj, "via": via, "tam": tam, "detalle": det})
            cola.extend(camino)
    return rutas, asignadas


def _alap(m, start, end, rutas):
    """Reprograma lo más tarde posible las tareas de rutas de alimentación.

    Devuelve (LS, LE, buf, faltas, sin_raiz). 'faltas' = {tarea de unión: días a retrasarla}
    para dar cabida al buffer; 'sin_raiz' = tareas con falta de holgura que no se pudo
    resolver retrasando una unión (quedan en su fecha temprana).
    """
    T, clave = m["tareas"], m["clave"]
    buf = {(r["ultima"], r["se_une_a"]): r["tam"] for r in rutas}
    movibles = {x for r in rutas for x in r["tareas"]}
    LS, LE = dict(start), dict(end)
    por_rec = defaultdict(list)
    for tid, tk in T.items():
        if tk["restringido"]:
            por_rec[tk["recurso"]].append(tid)
    res_next = {}
    for lst in por_rec.values():
        lst.sort(key=lambda i: (start[i], clave[i]))
        res_next.update(zip(lst, lst[1:]))
    raiz, faltas, sin_raiz = {}, {}, []
    for x in sorted(movibles, key=lambda i: (-end[i], clave[i])):
        ys = set(m["succ"][x])
        if x in res_next:
            ys.add(res_next[x])
        cands = []
        for y in ys:
            buffered = (x, y) in buf
            b = LS[y] - buf.get((x, y), 0)
            if y in movibles:
                r = raiz.get(y)
            else:
                r = y if buffered else None
            cands.append((b, 0 if r is not None else 1, clave[y], r))
        b, _, _, r = min(cands, key=lambda c: c[:3])
        raiz[x] = r
        LE[x] = b
        LS[x] = b - T[x]["agr"]
        if LS[x] < start[x]:
            falta = start[x] - LS[x]
            if r is not None:
                faltas[r] = max(faltas.get(r, 0), falta)
            else:
                sin_raiz.append(x)
            LS[x], LE[x] = start[x], end[x]
    return LS, LE, buf, faltas, sin_raiz


def _planificar(m):
    T, cal = m["tareas"], m["cal"]
    adv = []
    min0 = {i: T[i]["min_idx"] for i in T}
    s0, e0, rp0 = _adelante(m, min0, {})
    cadena = _cadena_critica(m, s0, e0, rp0, min0)
    ids_cadena = [e["id"] for e in cadena]
    set_cadena = set(ids_cadena)
    tam_pb, det_pb = _tamano_buffer(ids_cadena, m)
    extra = {}
    for e in cadena:
        if e["predecesor"] is not None and "recurso" in e["vinculo"]:
            extra.setdefault(e["id"], set()).add(e["predecesor"])

    min_start = dict(min0)
    retrasos = defaultdict(int)
    convergio = False
    for _ in range(_MAX_ITER):
        start, end, res_prev = _adelante(m, min_start, extra)
        rutas, asignadas = _rutas_alimentacion(m, start, end, res_prev, ids_cadena)
        LS, LE, buf, faltas, sin_raiz = _alap(m, start, end, rutas)
        if not faltas:
            convergio = True
            break
        for r, s in faltas.items():
            min_start[r] = max(min_start[r], start[r] + s)
            retrasos[r] += s
    if not convergio:
        adv.append("No se logró acomodar todos los buffers de alimentación en "
                   f"{_MAX_ITER} iteraciones; revisar el cronograma con cuidado.")
    for r, s in sorted(retrasos.items(), key=lambda kv: m["clave"][kv[0]]):
        adv.append(f"La tarea {r!r} se retrasó {s} día(s) hábil(es) para dar cabida a un buffer de "
                   "alimentación: la ruta de alimentación no tenía holgura suficiente "
                   "(la cadena crítica se alarga por ese desfase).")
    if sin_raiz:
        adv.append("Sin holgura suficiente para el buffer de alimentación de la(s) tarea(s) "
                   + ", ".join(sorted(sin_raiz, key=lambda i: m["clave"][i]))
                   + ": el buffer se muestra superpuesto con la ruta.")

    movibles = {x for r in rutas for x in r["tareas"]}
    plan_s = {i: (LS[i] if i in movibles else start[i]) for i in T}
    plan_e = {i: (LE[i] if i in movibles else end[i]) for i in T}
    return {"cadena": cadena, "ids_cadena": ids_cadena, "set_cadena": set_cadena,
            "pb": tam_pb, "det_pb": det_pb, "rutas": rutas, "asignadas": asignadas,
            "start": start, "end": end, "plan_s": plan_s, "plan_e": plan_e,
            "retrasos": dict(retrasos), "adv": adv}


# ---------------------------------------------------------------------------
# Cálculo principal y salidas
# ---------------------------------------------------------------------------

def _iso(d):
    return d.isoformat()


def calcular_ccpm(datos, desde=None, lote=None):
    """Calcula el cronograma CCPM a partir de un dict. Devuelve un dict serializable a JSON.

    desde : fecha ISO (o date) para «replanificar desde hoy»: el calendario arranca ese día, las
            tareas hechas no se reprograman y las pendientes se programan desde esa fecha.
    lote  : nombre de la entrega parcial; las tareas con otro `lote` quedan excluidas.

    Lanza ValueError con mensaje claro ante datos inválidos (ciclos, ids inexistentes,
    fechas mal formadas, duraciones inválidas, etc.).
    """
    m = _validar(datos, desde, lote)
    p = _planificar(m)
    cal, T = m["cal"], m["tareas"]
    adv = list(m["advertencias"]) + p["adv"]
    clave = m["clave"]

    cadena, ids_cadena = p["cadena"], p["ids_cadena"]
    ps, pe = p["plan_s"], p["plan_e"]
    fin_cadena_idx = pe[ids_cadena[-1]]           # exclusivo = días hábiles desde el inicio
    pb = p["pb"]
    fin_proy_idx = fin_cadena_idx + pb
    fecha_fin_cadena = cal.fecha(fin_cadena_idx - 1)
    fecha_fin_proy = cal.fecha(fin_proy_idx - 1)

    rol, ruta_de = {}, {}
    for i in ids_cadena:
        rol[i] = "cadena_critica"
    for r in p["rutas"]:
        for i in r["tareas"]:
            rol[i] = "alimentacion"
            ruta_de[i] = r["id"]
    for i in m["orden"]:
        rol.setdefault(i, "fuera_de_cadena")

    tareas_out = []
    for i in sorted(m["orden"], key=lambda i: (ps[i], clave[i])):
        t = T[i]
        tareas_out.append({
            "id": i, "nombre": t["nombre"], "recurso": t["recurso"], "tipo_recurso": t["tipo"],
            "predecesores": list(t["preds_lista"]),
            "dur_segura": t["seg"], "dur_agresiva": t["agr"],
            "fecha_no_antes_de": _iso(t["no_antes"]) if t["no_antes"] else None,
            "inicio": _iso(cal.fecha(ps[i])), "fin": _iso(cal.fecha(pe[i] - 1)),
            "inicio_dia": ps[i] + 1, "fin_dia": pe[i],
            "inicio_temprano": _iso(cal.fecha(p["start"][i])),
            "fin_temprano": _iso(cal.fecha(p["end"][i] - 1)),
            "rol": rol[i], "buffer_alimentacion": ruta_de.get(i),
            "estado": t["estado"], "cumplible": i not in m["afectadas"],
            "paquete": t["paquete"], "fase_paquete": t["fase"],
        })

    cadena_out = []
    for k, e in enumerate(cadena, 1):
        i = e["id"]
        cadena_out.append({
            "orden": k, "id": i, "nombre": T[i]["nombre"], "tipo_recurso": T[i]["tipo"],
            "dur_agresiva": T[i]["agr"], "dur_segura": T[i]["seg"],
            "inicio": _iso(cal.fecha(ps[i])), "fin": _iso(cal.fecha(pe[i] - 1)),
            "inicio_dia": ps[i] + 1, "fin_dia": pe[i],
            "vinculo_con_anterior": e["vinculo"], "predecesor": e["predecesor"],
            "alternativas": e["alternativas"],
            "desfase_por_buffer_alimentacion": p["retrasos"].get(i, 0),
        })
    suma_cadena = sum(T[i]["agr"] for i in ids_cadena)

    if any(T[i]["tipo"] == "externo" for i in ids_cadena):
        adv.append("La cadena crítica incluye tareas de recurso externo ("
                   + ", ".join(i for i in ids_cadena if T[i]["tipo"] == "externo")
                   + "): su cumplimiento depende de terceros; gestionarlas con prioridad.")
    no_unidas = [i for i in m["orden"] if i not in p["asignadas"] and (m["preds"][i] or m["succ"][i])]
    if no_unidas:
        adv.append("Tareas que no pertenecen a la cadena ni a una ruta de alimentación (no se unen a "
                   "la cadena crítica; sin buffer): " + ", ".join(no_unidas) + ".")
    tarde = [i for i in m["orden"] if pe[i] > fin_cadena_idx]
    if tarde:
        adv.append("Tareas que terminan después del fin de la cadena crítica: " + ", ".join(tarde)
                   + ". Revisar la red.")

    fb_out = []
    for r in p["rutas"]:
        js = ps[r["se_une_a"]]
        ini = max(0, js - r["tam"])
        fb_out.append({
            "id": r["id"], "tipo": "alimentacion", "tareas_protegidas": list(r["tareas"]),
            "se_une_a": r["se_une_a"], "tipo_vinculo_union": r["via"], "tamano_dias": r["tam"],
            "inicio": _iso(cal.fecha(ini)), "fin": _iso(cal.fecha(js - 1)),
            "inicio_dia": ini + 1, "fin_dia": js, "calculo": r["detalle"],
        })
    buffer_proyecto = {
        "id": "BP", "tipo": "proyecto", "tareas_protegidas": list(ids_cadena), "tamano_dias": pb,
        "inicio": _iso(cal.fecha(fin_cadena_idx)), "fin": _iso(fecha_fin_proy),
        "inicio_dia": fin_cadena_idx + 1, "fin_dia": fin_proy_idx, "calculo": p["det_pb"],
    }

    # Hitos
    ultima_cadena = ids_cadena[-1]
    hitos_out = []
    for h in m["hitos"]:
        if h["tarea"] is None or h["tarea"] == ultima_cadena:
            ref, comp = fecha_fin_proy, "fin de proyecto (con buffer)"
        else:
            ref, comp = cal.fecha(pe[h["tarea"]] - 1), "fin de la tarea (sin buffer)"
        marg = cal.dias_habiles_entre(ref, h["fecha"])
        hitos_out.append({
            "nombre": h["nombre"], "fecha": _iso(h["fecha"]), "tarea": h["tarea"],
            "comparado_con": comp, "fecha_comparada": _iso(ref),
            "holgura_dias_habiles": marg, "estado": "CUMPLE" if marg >= 0 else "NO CUMPLE",
        })

    # Bloqueos (H-040): el fin del proyecto no es cumplible si la última tarea de la cadena
    # es una tarea bloqueada o depende de una.
    fin_cumplible = ultima_cadena not in m["afectadas"]
    for h in hitos_out:
        if h["tarea"] is None or h["tarea"] == ultima_cadena:
            afect = not fin_cumplible
        else:
            afect = h["tarea"] in m["afectadas"]
        h["cumplible"] = not afect
        if afect:
            h["estado"] = "NO CUMPLIBLE (bloqueo)"

    # Fecha límite contractual
    limite_out = None
    if m["limite"] is not None:
        L = m["limite"]
        disponibles = cal.contar_hasta(L)
        if fin_proy_idx <= disponibles:
            limite_out = {
                "fecha_limite": _iso(L), "fin_con_buffer": _iso(fecha_fin_proy), "cumple": fin_cumplible,
                "cumple_por_fechas": True, "cumplible": fin_cumplible,
                "holgura_dias_habiles": disponibles - fin_proy_idx, "deficit_dias_habiles": 0,
                "buffer_que_cabe_dias": pb, "buffer_propuesto_dias": pb,
                "alerta": None,
            }
        else:
            deficit = fin_proy_idx - disponibles
            cabe = max(0, disponibles - fin_cadena_idx)
            if disponibles < fin_cadena_idx:
                alerta = (f"ALERTA: la cadena crítica sola (sin buffer) termina el {_iso(fecha_fin_cadena)}, "
                          f"{fin_cadena_idx - disponibles} día(s) hábil(es) después del límite contractual "
                          f"{_iso(L)}; no cabe ningún buffer. Hay que reducir alcance, agregar recursos "
                          "o renegociar la fecha.")
            else:
                alerta = (f"ALERTA: el fin con buffer ({_iso(fecha_fin_proy)}) supera el límite contractual "
                          f"{_iso(L)} en {deficit} día(s) hábil(es). Solo caben {cabe} día(s) de buffer de "
                          f"proyecto de los {pb} calculados ({round(100 * cabe / pb)} %).")
            limite_out = {
                "fecha_limite": _iso(L), "fin_con_buffer": _iso(fecha_fin_proy), "cumple": False,
                "cumple_por_fechas": False, "cumplible": fin_cumplible,
                "holgura_dias_habiles": -deficit, "deficit_dias_habiles": deficit,
                "buffer_que_cabe_dias": cabe, "buffer_propuesto_dias": pb, "alerta": alerta,
            }
            adv.append(alerta)
        if not fin_cumplible:
            limite_out["alerta_bloqueo"] = ("El fin de proyecto depende de tareas bloqueadas ("
                                            + ", ".join(m["bloqueadas"]) + "): no se cuenta como cumplible "
                                            "hasta resolver el bloqueo.")

    seguimiento = _seguimiento(m, p, cal, fecha_fin_cadena, pb, limite_out, adv)
    plan_paquetes, adv_pq = _plan_paquetes(m, p, cal)
    adv.extend(adv_pq)
    cal_info = {
        "dias_laborables": [_DIAS_ABREV[d] for d in sorted(cal.dias_laborables)],
        "feriados": sorted(_iso(f) for f in cal.feriados),
    }
    return {
        "version": VERSION,
        "resumen": {
            "inicio_solicitado": _iso(m["inicio"]), "inicio_efectivo": _iso(cal.base),
            "fin_cadena": _iso(fecha_fin_cadena), "dias_habiles_hasta_fin_cadena": fin_cadena_idx,
            "suma_dur_agresivas_cadena": suma_cadena,
            "buffer_proyecto_dias": pb, "metodo_buffer": m["metodo"],
            "fin_proyecto": _iso(fecha_fin_proy), "dias_habiles_hasta_fin_proyecto": fin_proy_idx,
            "cantidad_tareas": len(m["orden"]),
            "desde": _iso(m["desde"]) if m["desde"] else None, "lote": m["lote"],
            "tareas_hechas": list(m["hechas"]), "tareas_excluidas": list(m["excluidas"]),
            "tareas_bloqueadas": list(m["bloqueadas"]),
            "tareas_afectadas_por_bloqueo": [i for i in m["orden"] if i in m["afectadas"]],
            "fin_proyecto_cumplible": fin_cumplible,
            "cantidad_paquetes": len(plan_paquetes["paquetes"]) if plan_paquetes else 0,
        },
        "tareas_fuera_de_calculo": [
            {"id": i, "nombre": m["todas"][i]["nombre"], "estado": m["todas"][i]["estado"],
             "inicio_real": _iso(m["todas"][i]["inicio_real"]) if m["todas"][i]["inicio_real"] else None,
             "fin_real": _iso(m["todas"][i]["fin_real"]) if m["todas"][i]["fin_real"] else None,
             "motivo": m["todas"][i]["motivo"]}
            for i in m["orden_todas"] if m["todas"][i]["estado"] in ("hecha", "excluida")],
        "seguimiento": seguimiento,
        "plan_paquetes": plan_paquetes,
        "entrada_tareas": [
            {"id": i, "entregable": m["todas"][i]["entregable"], "nombre": m["todas"][i]["nombre"],
             "paquete": m["todas"][i]["paquete"],
             "recurso": m["todas"][i]["recurso"], "dur_segura": m["todas"][i]["seg"],
             "dur_agresiva": m["todas"][i]["agr"],
             "predecesores": list(m["todas"][i].get("preds_lista_original", m["todas"][i]["preds_lista"])),
             "estado": m["todas"][i]["estado"]} for i in m["orden_todas"]],
        "calendario": cal_info,
        "tareas": tareas_out,
        "cadena_critica": {"eslabones": cadena_out, "suma_dur_agresivas": suma_cadena,
                           "fin": _iso(fecha_fin_cadena)},
        "buffers": {"proyecto": buffer_proyecto, "alimentacion": fb_out},
        "hitos": hitos_out,
        "fecha_limite": limite_out,
        "plazo_horas": m["plazo_info"],
        "semaforo": {
            "parametros": dict(PARAMS_SEMAFORO_DEFECTO),
            "nota": "Umbrales por defecto A VALIDAR con datos reales de la organización.",
        },
        "advertencias": adv,
    }


def calcular_desde_archivo(ruta, desde=None, lote=None):
    """Lee un JSON de entrada y devuelve el resultado de calcular_ccpm."""
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido en {ruta}: {e}") from None
    return calcular_ccpm(datos, desde=desde, lote=lote)


# ---------------------------------------------------------------------------
# Avance, consumo de buffer y seguimiento (H-039, H-055, H-056)
# ---------------------------------------------------------------------------

#: Pesos por hito de un entregable. VALORES DE PARTIDA [VERIFICAR]: la oficina debe ajustarlos.
PESOS_HITO_DEFECTO = {"generado": 0.40, "revisado": 0.20, "auditado": 0.20, "emitido": 0.20}


def _validar_pesos(pesos):
    p = dict(PESOS_HITO_DEFECTO if pesos is None else pesos)
    if not p or any(isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0 for v in p.values()):
        raise ValueError("pesos: deben ser números >= 0")
    if abs(sum(p.values()) - 1.0) > 1e-9:
        raise ValueError(f"pesos: deben sumar 1 (suman {sum(p.values())})")
    return p


def avance_entregable(hitos_cumplidos, pesos=None):
    """Avance [0, 1] de un entregable = suma de los pesos de los hitos cumplidos.

    hitos_cumplidos: iterable de nombres de hito (p. ej. ["generado", "revisado"]).
    """
    p = _validar_pesos(pesos)
    hs = set(hitos_cumplidos or [])
    desconocidos = hs - set(p)
    if desconocidos:
        raise ValueError("Hitos desconocidos: " + ", ".join(sorted(map(str, desconocidos))))
    return round(sum(p[h] for h in hs), 10)


def avance_global(entregables, pesos=None):
    """Avance global [0, 1] = promedio ponderado de los avances de los entregables aplicables.

    entregables: lista de {"id", "hitos": [...cumplidos], "aplica": True (opcional),
    "peso": 1 (opcional)}. Por defecto todos los entregables pesan lo mismo (promedio simple).
    Los que tienen aplica=False (no aplican / excluidos del alcance) no cuentan.
    Es la ÚNICA definición de «avance global» (SCHEDULE_CCPM, sección D).
    """
    if not isinstance(entregables, (list, tuple)):
        raise ValueError("entregables: debe ser una lista")
    aplicables = [e for e in entregables if e.get("aplica", True)]
    if not aplicables:
        raise ValueError("No hay entregables aplicables para calcular el avance global")
    ws = []
    for e in aplicables:
        w = e.get("peso", 1)
        if isinstance(w, bool) or not isinstance(w, (int, float)) or w <= 0:
            raise ValueError(f"Entregable {e.get('id')!r}: peso debe ser > 0, se recibió {w!r}")
        ws.append(w)
    avs = [avance_entregable(e.get("hitos", []), pesos) for e in aplicables]
    return round(sum(w * a for w, a in zip(ws, avs)) / sum(ws), 10)


def consumo_buffer(retraso_dias_habiles, buffer_dias, cadena_cabe=True, avance_cadena=None, params=None):
    """Consumo del buffer de proyecto = retraso proyectado [d hábiles] / duración del buffer.

    retraso_dias_habiles : retraso proyectado del fin de la cadena respecto de la línea base
                           (negativo o 0 = sin retraso).
    buffer_dias          : duración del buffer de proyecto vigente (la que CABE, si hay límite).
    cadena_cabe          : False si la cadena con su buffer no cabe en el plazo contractual.
    avance_cadena        : [0, 1] opcional; con él la zona usa las rectas de `estado_buffer`; sin él
                           se usa la regla de tercios fija (<= 1/3 VERDE, >= 2/3 ROJO).
    Si el buffer es 0 o la cadena no cabe, el consumo no está definido: se reporta el retraso
    proyectado en días hábiles frente al límite y la zona es ROJO (si hay retraso o no cabe).
    """
    for nombre, v in (("retraso_dias_habiles", retraso_dias_habiles), ("buffer_dias", buffer_dias)):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(f"{nombre} debe ser numérico, se recibió {v!r}")
    if buffer_dias < 0:
        raise ValueError("buffer_dias no puede ser negativo")
    retraso = max(0, retraso_dias_habiles)
    out = {"retraso_dias_habiles": retraso_dias_habiles, "buffer_dias": buffer_dias,
           "cadena_cabe": bool(cadena_cabe), "consumo": None, "consumo_pct": None}
    if buffer_dias == 0 or not cadena_cabe:
        out["zona"] = "ROJO" if (retraso > 0 or not cadena_cabe) else "VERDE"
        out["texto"] = (f"Consumo indefinido (buffer {_fmt(buffer_dias)} d / cadena "
                        f"{'cabe' if cadena_cabe else 'no cabe'}): retraso proyectado "
                        f"{_fmt(retraso_dias_habiles)} día(s) hábil(es) frente al límite; zona {out['zona']}.")
        return out
    c = retraso / buffer_dias
    out["consumo"], out["consumo_pct"] = round(c, 4), round(100 * c, 1)
    if c >= 1:
        zona = "ROJO"
    elif avance_cadena is not None:
        zona = estado_buffer(avance_cadena, c, params)
    else:
        zona = "VERDE" if c <= 1 / 3 + 1e-9 else ("ROJO" if c >= 2 / 3 - 1e-9 else "AMARILLO")
    out["zona"] = zona
    out["texto"] = (f"Consumo {_fmt(out['consumo_pct'])} % ({_fmt(retraso)} d / {_fmt(buffer_dias)} d); zona {zona}.")
    return out


def _seguimiento(m, p, cal, fecha_fin_cadena, pb, limite_out, adv):
    """Bloque de seguimiento (solo si hay tareas hechas o `base` en la entrada)."""
    base = m["base"]
    if not m["hechas"] and not base:
        return None
    seg = {"avance_cadena": None, "retraso_proyectado_dias_habiles": None, "consumo": None,
           "nota": "Avance de la cadena = suma de dur. agresivas de las tareas hechas de la cadena "
                   "base / suma de la cadena base. Requiere `base.cadena` y `base.fin_cadena`."}
    base = base or {}
    avance = None
    if base.get("cadena"):
        ids = [str(i) for i in base["cadena"]]
        faltan = [i for i in ids if i not in m["todas"]]
        if faltan:
            adv.append("base.cadena referencia tareas inexistentes (ignoradas): " + ", ".join(faltan))
        ids = [i for i in ids if i in m["todas"]]
        tot = sum(m["todas"][i]["agr"] for i in ids)
        hec = sum(m["todas"][i]["agr"] for i in ids if m["todas"][i]["estado"] == "hecha")
        if tot:
            avance = round(hec / tot, 4)
            seg["avance_cadena"] = avance
    if base.get("fin_cadena"):
        fb = _parse_fecha(base["fin_cadena"], "base.fin_cadena")
        retraso = cal.dias_habiles_entre(fb, fecha_fin_cadena)
        seg["retraso_proyectado_dias_habiles"] = retraso
        buf = base.get("buffer_proyecto_dias", pb)
        cabe = True if limite_out is None else bool(limite_out["cumple_por_fechas"])
        if limite_out is not None and not cabe:
            buf = limite_out["buffer_que_cabe_dias"]
        seg["consumo"] = consumo_buffer(retraso, buf, cabe, avance)
    return seg


# ---------------------------------------------------------------------------
# Gestión de buffers (semáforo)
# ---------------------------------------------------------------------------

def estado_buffer(avance_cadena, consumo_buffer, params=None):
    """Estado del buffer según avance de la cadena y consumo del buffer (ambos en [0, 1]).

    VERDE    si consumo <= verde_pendiente * avance + verde_ordenada
    ROJO     si consumo >= rojo_pendiente  * avance + rojo_ordenada
    AMARILLO en cualquier otro caso.

    params (dict, opcional) puede redefinir cualquiera de: verde_pendiente, verde_ordenada,
    rojo_pendiente, rojo_ordenada. Por defecto 0,33 / 0,10 / 0,67 / 0,33, valores de partida
    A VALIDAR (PARAMS_SEMAFORO_DEFECTO).
    """
    for nombre, v in (("avance_cadena", avance_cadena), ("consumo_buffer", consumo_buffer)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 1:
            raise ValueError(f"{nombre} debe estar entre 0 y 1, se recibió {v!r}")
    p = dict(PARAMS_SEMAFORO_DEFECTO)
    if params:
        desconocidos = set(params) - set(p)
        if desconocidos:
            raise ValueError("Parámetros de semáforo desconocidos: " + ", ".join(sorted(desconocidos)))
        p.update(params)
    for x in (0.0, 1.0):
        if p["verde_pendiente"] * x + p["verde_ordenada"] >= p["rojo_pendiente"] * x + p["rojo_ordenada"]:
            raise ValueError("Umbrales incoherentes: la recta verde debe quedar por debajo de la roja "
                             "en avance 0 y en avance 1")
    eps = 1e-9
    if consumo_buffer <= p["verde_pendiente"] * avance_cadena + p["verde_ordenada"] + eps:
        return "VERDE"
    if consumo_buffer >= p["rojo_pendiente"] * avance_cadena + p["rojo_ordenada"] - eps:
        return "ROJO"
    return "AMARILLO"


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

_ROL_TXT = {"cadena_critica": "Cadena crítica", "alimentacion": "Alimentación",
            "fuera_de_cadena": "Fuera de cadena"}


def _calculo_txt(det):
    if det["metodo"] == "50pct":
        return (f"{_fmt(det['factor'] * 100.0)} % x {det['suma_dur_agresivas']} = "
                f"{_fmt(det['valor_calculado'])} -> {det['tamano_dias']}")
    return (f"RSS: raíz({det['suma_cuadrados']}) = {_fmt(det['valor_calculado'])} -> "
            f"{det['tamano_dias']}")


def _md_plan_paquetes(res, titulo):
    """Líneas Markdown del «Plan de paquetes» (vacías si ninguna tarea declara `paquete`)."""
    pl = res.get("plan_paquetes")
    if not pl:
        return []
    L = [titulo, "",
         "Orden de ejecución por dependencias entre paquetes de revisión (`deliverables.md`, 4.1): un "
         "paquete no empieza hasta que los paquetes de los que depende estén REVISADOS. «Entrega al "
         "usuario» es el fin de la última tarea de elaboración; «Revisado» es el fin de la revisión del "
         "usuario. Fechas con duraciones agresivas.", "",
         "| Orden | Paquete | Tareas | Depende de | Inicio | Entrega al usuario | Revisión del usuario | "
         "Revisado | Días de revisión | Estado |",
         "|---:|---|---|---|---|---|---|---|---:|---|"]
    for q in pl["paquetes"]:
        rev = (f"{_fecha_md(q['inicio_revision'])} a {_fecha_md(q['fin_revision'])}"
               if q["inicio_revision"] else "-")
        L.append(f"| {q['orden']} | {_esc(q['id'])} | {_esc(', '.join(q['tareas']))} | "
                 f"{_esc(', '.join(q['depende_de']) or '-')} | {_fecha_md(q['inicio'])} | "
                 f"{_fecha_md(q['entrega_al_usuario'])} | {rev} | {_fecha_md(q['fin_revision'])} | "
                 f"{q['dias_revision_usuario']} | {q['estado']} |")
    cb = pl["cuello_de_botella"]
    L += ["", f"Cuello de botella: {cb['tareas_revision_en_cadena']} de {cb['tareas_cadena']} tarea(s) de la "
              f"cadena crítica son revisión del usuario ({cb['dias_revision_en_cadena']} de "
              f"{cb['dias_cadena']} día(s) hábil(es); {_fmt(round(100 * cb['porcentaje_revision_en_cadena'], 1))} %).", ""]
    return L


def generar_markdown(res):
    """Genera el informe en Markdown (español) a partir del resultado de calcular_ccpm."""
    r = res["resumen"]
    L = ["# Cronograma por Cadena Crítica (CCPM)", ""]
    L += ["## Resumen", "", "| Concepto | Valor |", "|---|---|",
          f"| Inicio solicitado | {_fecha_md(r['inicio_solicitado'])} |",
          f"| Inicio efectivo (primer día hábil) | {_fecha_md(r['inicio_efectivo'])} |",
          f"| Fin de la cadena crítica | {_fecha_md(r['fin_cadena'])} (día hábil {r['dias_habiles_hasta_fin_cadena']}) |",
          f"| Buffer de proyecto | {r['buffer_proyecto_dias']} día(s) hábil(es), método {r['metodo_buffer']} |",
          f"| **Fin de proyecto (cadena + buffer)** | **{_fecha_md(r['fin_proyecto'])}** (día hábil {r['dias_habiles_hasta_fin_proyecto']}) |",
          f"| Días laborables | {', '.join(res['calendario']['dias_laborables'])} |",
          f"| Feriados | {', '.join(res['calendario']['feriados']) or 'ninguno'} |",
          f"| Tareas | {r['cantidad_tareas']} |", ""]

    L += ["## Cronograma por tarea", "",
          "Fechas con duraciones agresivas. Las tareas de rutas de alimentación están reprogramadas "
          "lo más tarde posible sin consumir su buffer (fechas tempranas en el JSON).", "",
          "| Id | Tarea | Recurso | Tipo | Predecesores | Dur. segura | Dur. agresiva | Inicio | Fin | Rol |",
          "|---|---|---|---|---|---:|---:|---|---|---|"]
    for t in res["tareas"]:
        rol = _ROL_TXT[t["rol"]] + (f" ({t['buffer_alimentacion']})" if t["buffer_alimentacion"] else "")
        L.append(f"| {_esc(t['id'])} | {_esc(t['nombre'])} | {_esc(t['recurso'] or '-')} | {t['tipo_recurso']} | "
                 f"{_esc(', '.join(t['predecesores']) or '-')} | {t['dur_segura']} | {t['dur_agresiva']} | "
                 f"{_fecha_md(t['inicio'])} | {_fecha_md(t['fin'])} | {rol} |")
    L.append("")

    fuera = res.get("tareas_fuera_de_calculo") or []
    if fuera or r["tareas_bloqueadas"] or r["desde"] or r["lote"]:
        L += ["## Estado de las tareas", ""]
        if r["desde"]:
            L.append(f"Replanificado desde {_fecha_md(r['desde'])}: las tareas hechas no se reprograman.")
        if r["lote"]:
            L.append(f"Cadena de la entrega parcial {_esc(r['lote'])}: las tareas de otras entregas parciales están excluidas.")
        if r["tareas_bloqueadas"]:
            L.append("**BLOQUEADAS (no cumplibles):** " + ", ".join(r["tareas_bloqueadas"])
                     + ". Afectadas por el bloqueo: " + (", ".join(r["tareas_afectadas_por_bloqueo"]) or "-") + ".")
        L.append("")
        if fuera:
            L += ["| Id | Tarea | Estado | Inicio real | Fin real | Motivo |", "|---|---|---|---|---|---|"]
            for f in fuera:
                L.append(f"| {_esc(f['id'])} | {_esc(f['nombre'])} | {f['estado']} | "
                         f"{_fecha_md(f['inicio_real'])} | {_fecha_md(f['fin_real'])} | {_esc(f['motivo'] or '-')} |")
            L.append("")

    cc = res["cadena_critica"]
    L += ["## Cadena crítica", "",
          f"Suma de duraciones agresivas: {cc['suma_dur_agresivas']} día(s) hábil(es). "
          f"Fin de cadena: {_fecha_md(cc['fin'])}.", "",
          "| Orden | Id | Tarea | Inicio | Fin | Dur. agresiva | Vínculo con el anterior | Notas |",
          "|---:|---|---|---|---|---:|---|---|"]
    for e in cc["eslabones"]:
        notas = []
        if e["predecesor"]:
            notas.append(f"depende de {e['predecesor']}")
        if e["alternativas"]:
            notas.append("empate con " + ", ".join(f"{a['id']} ({a['vinculo']})" for a in e["alternativas"]))
        if e["desfase_por_buffer_alimentacion"]:
            notas.append(f"desfasada {e['desfase_por_buffer_alimentacion']} día(s) por buffer de alimentación")
        if e["tipo_recurso"] == "externo":
            notas.append("recurso externo")
        L.append(f"| {e['orden']} | {_esc(e['id'])} | {_esc(e['nombre'])} | {_fecha_md(e['inicio'])} | "
                 f"{_fecha_md(e['fin'])} | {e['dur_agresiva']} | {e['vinculo_con_anterior']} | "
                 f"{_esc('; '.join(notas) or '-')} |")
    L.append("")

    L += _md_plan_paquetes(res, "## Plan de paquetes")

    L += ["## Buffers", "",
          "| Buffer | Tipo | Protege | Se inserta antes de | Tamaño (días hábiles) | Inicio | Fin | Cálculo |",
          "|---|---|---|---|---:|---|---|---|"]
    bp = res["buffers"]["proyecto"]
    L.append(f"| {bp['id']} | Proyecto | {_esc(', '.join(bp['tareas_protegidas']))} | fin del proyecto | "
             f"{bp['tamano_dias']} | {_fecha_md(bp['inicio'])} | {_fecha_md(bp['fin'])} | {_calculo_txt(bp['calculo'])} |")
    for b in res["buffers"]["alimentacion"]:
        L.append(f"| {b['id']} | Alimentación | {_esc(', '.join(b['tareas_protegidas']))} | {_esc(b['se_une_a'])} "
                 f"({b['tipo_vinculo_union']}) | {b['tamano_dias']} | {_fecha_md(b['inicio'])} | "
                 f"{_fecha_md(b['fin'])} | {_calculo_txt(b['calculo'])} |")
    if not res["buffers"]["alimentacion"]:
        L += ["", "No hay rutas de alimentación (no se detectaron rutas no críticas que se unan a la cadena)."]
    L.append("")

    L += ["## Hitos", ""]
    if res["hitos"]:
        L += ["| Hito | Fecha | Tarea | Comparado con | Fecha comparada | Holgura (días hábiles) | Estado |",
              "|---|---|---|---|---|---:|---|"]
        for h in res["hitos"]:
            L.append(f"| {_esc(h['nombre'])} | {_fecha_md(h['fecha'])} | {_esc(h['tarea'] or '-')} | "
                     f"{h['comparado_con']} | {_fecha_md(h['fecha_comparada'])} | {h['holgura_dias_habiles']} | "
                     f"{h['estado']} |")
    else:
        L.append("Sin hitos definidos.")
    L.append("")

    pi = res.get("plazo_horas")
    if pi:
        L += ["## Plazo en horas hábiles", "", "| Concepto | Valor |", "|---|---|",
              f"| Tipo de plazo | {pi['tipo']} |",
              f"| Plazo | {_fmt(pi['plazo_horas'])} h hábiles ({_fmt(pi['dias_habiles_equivalentes'])} día(s) hábil(es) a {_fmt(pi['horas_por_dia'])} h por día) |",
              f"| Esfuerzo de tareas internas (agresivo / seguro) | {_fmt(pi['esfuerzo_agresivo_horas'])} h / {_fmt(pi['esfuerzo_seguro_horas'])} h |"]
        if pi["tipo"] == "esfuerzo":
            L.append(f"| Déficit de esfuerzo | {_fmt(pi['deficit_esfuerzo_horas'])} h |")
        L.append("")

    L += ["## Comparación con la fecha límite contractual", ""]
    fl = res["fecha_limite"]
    if fl is None:
        L.append("No se definió fecha límite contractual.")
    else:
        L += ["| Concepto | Valor |", "|---|---|",
              f"| Fecha límite contractual | {_fecha_md(fl['fecha_limite'])} |",
              f"| Fin con buffer | {_fecha_md(fl['fin_con_buffer'])} |",
              f"| Resultado | {'CUMPLE' if fl['cumple'] else ('NO CUMPLIBLE (bloqueo)' if not fl['cumplible'] and fl['cumple_por_fechas'] else 'NO CUMPLE')} |"]
        if fl["cumple_por_fechas"]:
            L.append(f"| Holgura | {fl['holgura_dias_habiles']} día(s) hábil(es) |")
        else:
            L += [f"| Déficit | {fl['deficit_dias_habiles']} día(s) hábil(es) |",
                  f"| Buffer de proyecto que sí cabe | {fl['buffer_que_cabe_dias']} de {fl['buffer_propuesto_dias']} día(s) |"]
            L += ["", f"> {fl['alerta']}"]
        if fl.get("alerta_bloqueo"):
            L += ["", f"> {fl['alerta_bloqueo']}"]
    L.append("")

    sg = res.get("seguimiento")
    if sg:
        L += ["## Seguimiento (sección D)", "", "| Concepto | Valor |", "|---|---|",
              f"| Avance de la cadena | {('%s %%' % _fmt(round(100 * sg['avance_cadena'], 1))) if sg['avance_cadena'] is not None else 'no calculado (falta base.cadena)'} |",
              f"| Retraso proyectado (días hábiles) | {sg['retraso_proyectado_dias_habiles'] if sg['retraso_proyectado_dias_habiles'] is not None else 'no calculado (falta base.fin_cadena)'} |",
              f"| Consumo del buffer | {sg['consumo']['texto'] if sg['consumo'] else '-'} |", ""]

    p = res["semaforo"]["parametros"]
    L += ["## Gestión de buffers (zonas de seguimiento)", "",
          "Estado = VERDE si consumo <= "
          f"{_fmt(p['verde_pendiente'])} x avance + {_fmt(p['verde_ordenada'])}; ROJO si consumo >= "
          f"{_fmt(p['rojo_pendiente'])} x avance + {_fmt(p['rojo_ordenada'])}; AMARILLO en medio. "
          "**Umbrales por defecto, a validar** con datos reales. Función: `estado_buffer(avance, consumo, params)`.", "",
          "| Avance de la cadena | Consumo máximo en VERDE | Consumo mínimo en ROJO |", "|---:|---:|---:|"]
    for av in (0.0, 0.25, 0.5, 0.75, 1.0):
        L.append(f"| {int(av * 100)} % | {_fmt(round(p['verde_pendiente'] * av + p['verde_ordenada'], 4))} | "
                 f"{_fmt(round(p['rojo_pendiente'] * av + p['rojo_ordenada'], 4))} |")
    L.append("")

    L += ["## Advertencias", ""]
    if res["advertencias"]:
        L += [f"- {a}" for a in res["advertencias"]]
    else:
        L.append("Sin advertencias.")
    L.append("")
    return "\n".join(L)


def generar_md_secciones(res):
    """Tablas de las secciones B y C de schedule-ccpm.md, con el formato exacto de sus columnas,
    listas para pegar."""
    r = res["resumen"]
    L = ["## B. Tareas (resumen de la entrada)", "",
         "| ID | Entregable / actividad | Recurso | Dur. segura | Dur. agresiva | Predecesores | Estado |",
         "|---|---|---|---|---|---|---|"]
    for t in res["entrada_tareas"]:
        act = (t["entregable"] + " - " if t["entregable"] else "") + t["nombre"]
        L.append(f"| {_esc(t['id'])} | {_esc(act)} | {_esc(t['recurso'] or '-')} | {t['dur_segura']} | "
                 f"{t['dur_agresiva']} | {_esc(', '.join(t['predecesores']) or '-')} | {t['estado']} |")
    L += ["", "## C. Resultado del cálculo (pegar la salida de `ccpm.py`)", "",
          "| Concepto | Valor |", "|---|---|",
          f"| Fin de la cadena crítica | {r['fin_cadena']} (día hábil {r['dias_habiles_hasta_fin_cadena']}) |",
          f"| Buffer de proyecto (días) | {r['buffer_proyecto_dias']} |",
          f"| Fecha de fin del proyecto (con buffer) | {r['fin_proyecto']} (día hábil {r['dias_habiles_hasta_fin_proyecto']}) |"]
    fl = res["fecha_limite"]
    if fl is None:
        marg = "sin fecha límite contractual definida"
    elif fl["cumple_por_fechas"]:
        marg = f"margen de {fl['holgura_dias_habiles']} día(s) hábil(es) (límite {fl['fecha_limite']})"
    else:
        marg = (f"DÉFICIT de {fl['deficit_dias_habiles']} día(s) hábil(es) (límite {fl['fecha_limite']}; "
                f"cabe buffer de {fl['buffer_que_cabe_dias']} de {fl['buffer_propuesto_dias']} d)")
    if r["tareas_bloqueadas"]:
        marg += "; NO CUMPLIBLE: depende de tareas bloqueadas (" + ", ".join(r["tareas_bloqueadas"]) + ")" \
            if not r["fin_proyecto_cumplible"] else "; hay tareas bloqueadas (" + ", ".join(r["tareas_bloqueadas"]) + ")"
    L.append(f"| Margen o déficit frente al límite contractual (días) | {_esc(marg)} |")
    cad = " > ".join(e["id"] for e in res["cadena_critica"]["eslabones"])
    L.append(f"| Cadena crítica (tareas) | {_esc(cad)} |")
    fb = "; ".join(f"{b['id']} ({', '.join(b['tareas_protegidas'])} -> {b['se_une_a']}): {b['tamano_dias']} d"
                   for b in res["buffers"]["alimentacion"]) or "ninguno"
    L.append(f"| Buffers de alimentación | {_esc(fb)} |")
    L.append("")
    L += _md_plan_paquetes(res, "## B2. Plan de paquetes")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Calculadora de cronograma por Cadena Crítica (CCPM).",
        epilog="Ejemplo (desde la raíz del proyecto): python3 -B 98_LIBRARY/calculations/ccpm.py "
               "90-management/Planning/ccpm_input.json --md ccpm_output.md --json ccpm_output.json")
    ap.add_argument("entrada", help="archivo JSON de entrada")
    ap.add_argument("--md", help="ruta de salida Markdown")
    ap.add_argument("--json", dest="json_out", help="ruta de salida JSON")
    ap.add_argument("--md-secciones", dest="md_secciones", nargs="?", const="-", default=None,
                    metavar="ARCHIVO",
                    help="emite las tablas B y C de schedule-ccpm.md listas para pegar "
                         "(a ARCHIVO, o a la salida estándar si se omite)")
    ap.add_argument("--desde", metavar="AAAA-MM-DD",
                    help="replanificar desde esta fecha: las tareas hechas no se reprograman")
    ap.add_argument("--lote", metavar="NOMBRE",
                    help="cadena de una entrega parcial: excluye las tareas cuyo campo 'lote' sea otro")
    args = ap.parse_args(argv)
    try:
        res = calcular_desde_archivo(args.entrada, desde=args.desde, lote=args.lote)
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo {args.entrada}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    md = generar_markdown(res)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
            f.write("\n")
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(md)
    if args.md_secciones is not None:
        sec = generar_md_secciones(res)
        if args.md_secciones == "-":
            sys.stdout.write(sec)
        else:
            with open(args.md_secciones, "w", encoding="utf-8") as f:
                f.write(sec)
    elif not args.md and not args.json_out:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
