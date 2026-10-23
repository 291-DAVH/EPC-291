# 04 · Capacidad de conducción (Iz)

## Qué resuelve

Determina la corriente máxima que el cable puede llevar en su forma de instalación. Es el criterio que obliga a no usar un cable demasiado fino.

## Entradas

Material, aislación, clase del conductor, método de instalación, número de ternas, circuitos agrupados, temperatura ambiente (o del terreno y resistividad térmica), y opcionalmente Iz del fabricante (`IZ_A`).

## Pasos

1. **Elegir la tabla** según el método de instalación. Los códigos se muestran en la hoja LISTAS:
   - B1 (caño embutido o cablecanal, PVC): tabla 771.16.I.
   - B2, C, E, F, G (caño, bandeja, aire): tabla 771.16.III.
   - D1 (caño enterrado): tabla 771.16.V.
   - D2 (directamente enterrado): tabla 771.16.VI.
2. **Tomar Iz base** para la sección candidata, según número de cargados (2 monofásico, 3 trifásico), material y aislación. Si se informó `IZ_A`, ese valor reemplaza la tabla.
3. **Factor de clase:** 0,95 para clase 5 (flexible); 1,00 para clase 2.
4. **Factor de temperatura** (solo instalaciones al aire, tabla 771.16.II.a): según la temperatura ambiente, con base 40 °C para PVC y XLPE. Para XLPE la temperatura de servicio es 90 °C; para PVC, 70 °C.
5. **Factor de agrupamiento:** número de circuitos en la misma canalización (tablas 771.16.II.b, IV, VII.c y VII.d).
6. **Factores de terreno** (solo enterrados, tablas 771.16.VII.a y VII.b): temperatura del suelo y resistividad térmica.
7. **Multiplicar por el número de ternas** en paralelo.
8. **Iz corregida** = N · Iz0 · f_clase · f_temp · f_agrup · f_suelo.
9. La sección candidata sirve si Iz corregida es mayor o igual que In (multiplicado por el margen, 1,0 por defecto).

## Criterio de aceptación

Iz corregida ≥ In.

## Limitaciones

- B1 con XLPE no tiene tabla en 771.16.I; el motor avisa y pide usar B2 o C.
- Aluminio solo desde 16 mm².
- Para D2 se usa la columna `c4_3x` (3 cargados); la correspondencia de columnas 2x/3x está pendiente de confirmar.

## Módulos

`aea_ampacity.iz`, `aea_ampacity.factores`, `aea_tables.iz_tabla`, `aea_tables.factor_*`, `aea_tables.iz_corregida`.
