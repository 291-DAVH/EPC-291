# 02 · Demanda y corriente de proyecto (Ib)

## Qué resuelve

Calcula la corriente que realmente circula por el circuito en servicio normal, Ib.

## Entradas

Carga y unidad, tensión de línea U, factor de potencia (`FP` o `FP_DEFAULT`), rendimiento (`RENDIMIENTO`, solo para motores o HP), fases (`FASE`).

## Pasos

1. **Si la carga está en amperes**, Ib es ese valor, sin conversión.
2. **Potencia activa (W, kW, MW, HP):**
   - trifásico: Ib = P / (√3 · U · cos φ);
   - monofásico: Ib = P / (U_fase · cos φ), con U_fase = U / √3 si la tensión dada es de línea.
   - Para HP se usa la potencia mecánica dividida por el rendimiento.
3. **Potencia aparente (VA, kVA, MVA):** Ib = S / (√3 · U) en trifásico, o S / U_fase en monofásico; no interviene el factor de potencia.
4. **Circuito padre sin carga:** Ib es la suma de las Ib de sus hijos.
5. **Motores (opcional, `--eta-motores`):** si se activa, la potencia de eje se divide por el rendimiento antes de calcular Ib.

## Criterio de aceptación

Ib positiva y finita en todos los circuitos con carga; los padres tienen hijos.

## Módulos

`aea_pipeline.corriente_proyecto`, `aea_pipeline.convert_load`, `current_and_loads.corriente_trifasica` y `corriente_monofasica`, `aea_demand`.
