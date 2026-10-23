# 06 · Cortocircuito, poder de corte y disparo magnético

## Qué resuelve

Verifica que el dispositivo soporte la corriente de cortocircuito en su punto de instalación y que dispare magnéticamente ante una falla al final del cable.

## Entradas

Icc en barras (`ICC_KA`), tensión, sección, longitud y resistencia del cable.

## Pasos

1. **Poder de corte (icu).** Se toma la primera icu de la serie (6, 10, 15, 20, 25, 36, 50, 70 y 100 kA) que sea mayor o igual que la Icc de las barras. Si la Icc supera 100 kA se avisa.
2. **Icc mínima al final del cable** (cortocircuito fase-neutro o fase-fase en el extremo):
   - impedancia de la fuente por fase: Z_f = c_max · U_fase / Icc_barras, con c_max = 1,05;
   - impedancia acumulada: Z = |(Z_f + R) + jX|, con R y X del cable y de sus padres;
   - Icc mín trifásica (bifásica entre fases) = c_min · U / (2 · Z); fase-neutro = c_min · U_fase / (2 · Z), con c_min = 0,95;
   - se compara con el disparo magnético: Icc mín ≥ **10 · In** (factor `K_MAGNETICO_C`).
3. Si no se cumple, el motor avisa: conviene una curva de disparo distinta o un cable más corto o de mayor sección.
4. **Dispositivos RCCB** no se verifican por disparo magnético.

## Criterio de aceptación

- icu ≥ Icc de barras;
- Icc mín ≥ 10 · In (salvo RCCB).

## Módulos

`aea_pipeline.current_sc_min`, `aea_pipeline.calculate`, `short_circuit.impedance_cable`, `aea_icc_factors`, `aea_icc_decay` (para la Icc calculada con IT 90909-1).

> Nota: el cálculo de la Icc de barras a partir de la red se hace fuera del motor (IT 90909-1); el motor recibe la Icc como dato en TABLERO.
