# 03 · Protección por sobrecarga (In)

## Qué resuelve

Elige el calibre del dispositivo de protección In, de la serie normalizada.

## Entradas

Ib del circuito (paso 02) y, si es motor, el margen de arranque.

## Pasos

1. Para motores (topologías `dol`, `dol_ol`, `star_delta`, `softstarter`, `vfd`, `dol_rcd`) se multiplica Ib por **1,25** antes de elegir In.
2. Se toma la **primera In de la serie** que sea mayor o igual que ese valor. Serie: 6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250 y 1600 A.
3. Si Ib supera la serie, se avisa y se usa la In máxima.
4. Por la In elegida se decide el dispositivo: con `auto`, MCB hasta 63 A y MCCB por encima.
5. La condición de sobrecarga queda: **Ib ≤ In ≤ Iz** (paso 04) y **I2 ≤ 1,45 · Iz**, donde I2 = k2 · In.

## Criterio de aceptación

In ≥ Ib y, al verificar Iz, In ≤ Iz e I2 ≤ 1,45 · Iz.

## Módulos

`aea_pipeline.calculate` (elección de In), `aea_pipeline._dispositivo`, `aea_protection.i2_convencional`, `aea_protection.in_max_por_iz`.

> Nota: el motor elige In y verifica Iz en el dimensionado. La verificación de I2 con k2 de cada producto está disponible en `aea_protection`, pero el valor de k2 depende del fabricante.
