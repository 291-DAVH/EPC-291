"""Validadores numéricos compartidos por los módulos de cálculo (antes copiados en cada uno).

El cuerpo y los mensajes de error son los mismos que tenían las copias; cada módulo los importa con su nombre local de siempre (`_num`, `_pos`, `_nonneg`, `_frac`).
"""
import math


def num(v, nombre, minimo=0.0, estricto=False):
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {v!r})")
    if (estricto and v <= minimo) or (not estricto and v < minimo):
        raise ValueError(f"{nombre} debe ser {'>' if estricto else '≥'} {minimo} (recibido: {v})")


def pos(valor, nombre):
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {valor!r})")
    if valor <= 0:
        raise ValueError(f"{nombre} debe ser > 0 (recibido: {valor})")


def nonneg(valor, nombre):
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito (recibido: {valor!r})")
    if valor < 0:
        raise ValueError(f"{nombre} debe ser ≥ 0 (recibido: {valor})")


def frac(valor, nombre):
    pos(valor, nombre)
    if valor > 1:
        raise ValueError(f"{nombre} debe estar en (0, 1] (recibido: {valor})")
