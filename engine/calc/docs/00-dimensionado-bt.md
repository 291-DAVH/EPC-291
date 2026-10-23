# Dimensionado de cables de baja tensión (BT)

**Norma:** AEA 90364-7 (771 para viviendas y locales, 770 para viviendas, 701 baños, 722 vehículos eléctricos) y AEA 90909-1 para cortocircuito.

## Qué resuelve

Dado un tablero con sus circuitos, el motor determina para cada uno:

1. La corriente de proyecto **Ib**.
2. El dispositivo de protección **In**.
3. La **sección del cable** que cumple capacidad, caída de tensión y sección mínima.
4. El **poder de corte** del dispositivo (icu) frente a la corriente de cortocircuito de las barras.
5. La verificación de **disparo magnético** en el extremo del cable.

Además entrega el JSON de cálculo para `sld-generator` y, para el alimentador principal, la Memoria de Cálculo y la Síntesis de Proyecto.

## Secuencia del cálculo

| Paso | Qué se calcula | Documento |
|---|---|---|
| 1 | Lectura de datos del tablero y de los circuitos | [01 · Datos de entrada](01-datos-de-entrada.md) |
| 2 | Corriente de proyecto Ib de cada circuito | [02 · Demanda y corriente de proyecto](02-demanda-y-corriente-de-proyecto.md) |
| 3 | Dispositivo de protección In | [03 · Protección por sobrecarga (In)](03-proteccion-sobrecarga.md) |
| 4 | Capacidad de conducción Iz | [04 · Capacidad de conducción](04-capacidad-de-conduccion.md) |
| 5 | Sección, caída de tensión y sección mínima | [05 · Sección y caída de tensión](05-seccion-y-caida-de-tension.md) |
| 6 | Cortocircuito, poder de corte y disparo magnético | [06 · Cortocircuito y poder de corte](06-cortocircuito-y-poder-de-corte.md) |
| 7 | Verificaciones complementarias (térmica, contactos indirectos, tableros, locales especiales) | [07 · Verificaciones complementarias](07-verificaciones-complementarias.md) |
| 8 | Salidas: JSON, MC y SP | [08 · Salidas](08-salidas.md) |

Las tablas normativas que alimentan los pasos 4 y 5 están descritas en [09 · Tablas normativas](09-tablas-normativas.md).

## Criterio general

Un circuito queda dimensionado cuando su sección cumple, a la vez, que:

- Iz (corregida por método, temperatura y agrupamiento) es mayor o igual que In, y In es mayor o igual que Ib;
- la caída de tensión acumulada desde la barra no supera el límite del tipo de circuito;
- la sección es igual o mayor que la mínima del tipo de circuito.

El cálculo toma la **primera sección** de la serie normalizada que cumple todo lo anterior.

> Estado: borrador pendiente de validación del usuario contra el ejemplar oficial de AEA 90364-7.
