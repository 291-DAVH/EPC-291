"""Luminous intensity of a luminaire in a given direction (UPV point-by-point article, step B).

The table gives cd per klm of lamp flux; the real intensity is that value times
the lamp flux in klm. Angles beyond the last tabulated gamma emit nothing: the
engine does not extrapolate a distribution the manufacturer did not publish.
"""
import math
from bisect import bisect_right
from typing import Sequence, Tuple

from epc_lighting.model import Photometry


def _along_gamma(gammas: Sequence[float], values: Sequence[float], gamma: float) -> float:
    if gamma > gammas[-1] + 1e-9:
        return 0.0
    if gamma <= gammas[0] or len(gammas) == 1:
        return values[0]
    i = min(bisect_right(gammas, gamma) - 1, len(gammas) - 2)
    t = (gamma - gammas[i]) / (gammas[i + 1] - gammas[i])
    return values[i] + t * (values[i + 1] - values[i])


def _c_weights(c_deg: Sequence[float], c: float) -> Tuple[int, int, float]:
    """The two C planes around c (wrapping at 360) and the weight of the second."""
    n = len(c_deg)
    if n == 1:
        return 0, 0, 0.0
    c = c % 360.0
    idx = bisect_right(c_deg, c) - 1
    low = c_deg[idx] if idx >= 0 else c_deg[-1] - 360.0
    high = c_deg[idx + 1] if idx + 1 < n else c_deg[0] + 360.0
    return idx % n, (idx + 1) % n, (c - low) / (high - low)


def intensity_cd(phot: Photometry, gamma_deg: float, c_deg: float, lamp_flux_lm: float) -> float:
    """Intensity in candela towards (gamma, C) for a luminaire of the given lamp flux."""
    i0, i1, t = _c_weights(phot.c_deg, c_deg)
    a = _along_gamma(phot.gamma_deg, phot.values[i0], gamma_deg)
    b = _along_gamma(phot.gamma_deg, phot.values[i1], gamma_deg)
    return (a + t * (b - a)) * lamp_flux_lm / 1000.0


def emitted_fraction(phot: Photometry) -> float:
    """Share of the lamp flux the intensity table emits: 2*pi * integral of I(gamma) sin(gamma), per klm / 1000.

    A luminaire cannot emit more than its lamps produce, so a value above 1
    means the table or its unit is wrong; below 1 it is the light output ratio.
    The C planes are averaged with equal weight.
    """
    step = 1.0
    last = min(180.0, phot.gamma_deg[-1])
    n = int(math.ceil(last / step))
    per_plane = []
    for row in phot.values:
        total = 0.0
        for i in range(n):
            g0, g1 = i * last / n, (i + 1) * last / n
            mid = (g0 + g1) / 2
            total += _along_gamma(phot.gamma_deg, row, mid) * math.sin(math.radians(mid)) * math.radians(g1 - g0)
        per_plane.append(2 * math.pi * total / 1000.0)
    return sum(per_plane) / len(per_plane)
