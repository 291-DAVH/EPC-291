"""aea_rules — Reglas de ingeniería de las normas AEA (alturas, reservas, llenado, distancias, circuitos).

ESTADO: BORRADOR — pendiente de validación por el usuario.

OBJETIVO
    Consultar las reglas de `rules/*.json`: una por requisito, con valor, tipo (obligatorio,
    recomendado, prohibido), a qué inmuebles aplica y su referencia (norma, edición,
    cláusula, página; sin texto de la norma). Sirve de base para verificar proyectos (alturas de
    tomacorrientes, reserva de bandejas, llenado de caños, etc.).

FÓRMULAS
    No hay cálculo: es una base de datos de reglas. Ejemplos de uso de los valores:
    ocupación ≤ 35 % de la sección interna ; reserva de bandejas ≥ 20 % ; altura de tomacorrientes ≥ 0,15 m.

UNIDADES
    Cada regla declara la unidad en el nombre del parámetro (_m, _mm, _pct, _a, _cm, _va).

LIMITACIONES
    - Los valores numéricos de `parametros` son una lectura de la norma; la fuente es la cláusula y página indicadas.
    - Cubre 771, 770, 701 y 722 y, por OCR, capítulos 41, 43, 51, 52 y 54 de las Partes 4 y 5; cada regla
      de esas partes indica en `fuente.verificacion` si se comprobó por OCR o sobre la imagen.
    - No incluye los capítulos 42 y 44, el 434, ni valores del factor c (están en AEA 90909-0, ausente).

NORMA DE REFERENCIA
    AEA 90364-7-771 (Ed. 2006), 7-770, 7-701 (Ed. 2012), 7-722 (Ed. 2018); AEA 90364-4 y -5 (Ed. 2006).  [VERIFICAR]
"""
import json
import os

__version__ = "0.1.0"
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")
TIPOS = ("obligatorio", "recomendado", "prohibido")
_CACHE = {}


def limpiar_cache_reglas():
    """Descarta los datos en memoria: se vuelven a leer del archivo (después de corregir un valor normativo)."""
    _CACHE.clear()


def _leer(nombre):
    if nombre not in _CACHE:
        with open(os.path.join(CARPETA, nombre), encoding="utf-8") as f:
            _CACHE[nombre] = json.load(f)
    return _CACHE[nombre]


def indice():
    """Índice de grupos con su archivo y cantidad de reglas."""
    return _leer("_indice.json")


def grupos():
    """Nombres de los grupos de reglas."""
    return sorted(indice()["grupos"])


def reglas(grupo=None):
    """Lista de reglas de un grupo, o de todos si `grupo` es None."""
    nombres = [grupo] if grupo else grupos()
    salida = []
    for g in nombres:
        if g not in indice()["grupos"]:
            raise ValueError(f"grupo {g!r} inexistente: {grupos()}")
        salida += _leer(indice()["grupos"][g]["archivo"])["reglas"]
    return salida


def regla(id_):
    """Regla por id ('grupo.nombre')."""
    for r in reglas(id_.split(".")[0]):
        if r["id"] == id_:
            return r
    raise ValueError(f"regla {id_!r} inexistente")


def valor(id_, parametro):
    """Valor de un parámetro de una regla, p. ej. valor('bandejas.reserva_20pct', 'reserva_min_pct') = 20."""
    p = regla(id_)["parametros"]
    if parametro not in p:
        raise ValueError(f"{id_} no tiene el parámetro {parametro!r}: {sorted(p)}")
    return p[parametro]


def buscar(texto=None, grupo=None, aplica_a=None, tipo=None, norma=None):
    """Filtra reglas por texto (tema, regla, id), grupo, tipo de inmueble, tipo de regla y norma (p. ej. '771')."""
    t = texto.lower() if texto else None
    salida = []
    for r in reglas(grupo):
        if t and t not in (r["id"] + " " + r["tema"] + " " + r["regla"]).lower():
            continue
        if aplica_a and aplica_a not in r["aplica_a"]:
            continue
        if tipo and r["tipo"] != tipo:
            continue
        if norma and norma not in r["fuente"]["norma"]:
            continue
        salida.append(r)
    return salida
