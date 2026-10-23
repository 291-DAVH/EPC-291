# 05 · Sección y caída de tensión

## Qué resuelve

Elige la sección definitiva del cable, verificando caída de tensión y sección mínima, y acumula la caída desde la barra del tablero.

## Entradas

In (paso 03), Iz (paso 04), Ib, longitud, tipo de circuito, resistencia del conductor a temperatura de servicio.

## Pasos

1. **Tipo de circuito:** seccional (alimentador o tablero hijo), motor, iluminación o tomacorrientes. Define el límite y la sección mínima.
2. **Sección mínima** (Tabla 771.13.I): 2,5 mm² para seccionales, tomacorrientes y usos específicos (motores); 1,5 mm² para iluminación terminal. El motor toma la mínima del tipo.
3. **Recorrer la serie de secciones** de menor a mayor (1,5 a 300 mm²), y para cada una:
   - descartar si es menor que la mínima;
   - descartar si Iz corregida < In;
   - calcular la caída de tensión:
     ΔU = √3 · I · L · (R · cos φ + X · sen φ) para trifásico, o la misma expresión con factor 2 en lugar de √3 para monofásico, con R a temperatura de servicio (R = R20 · (1 + α · (θ − 20))), X = 0,08 Ω/km y cos φ / sen φ del factor de potencia;
   - expresar la caída en % de la tensión de referencia (U de línea si es trifásico, U_fase si es monofásico);
   - aceptar si ΔU del circuito ≤ límite del tipo **y** ΔU acumulada desde la barra ≤ 5 %.
4. **Límites por tipo:** seccional 1 %, iluminación 3 %, tomacorrientes 3 %, motor en régimen 5 %.
5. **Caída acumulada:** cada circuito hereda la caída de su padre; se registra el total en el JSON.
6. **Si ninguna sección cumple:** se usa la mayor de la serie y se avisa "usar paralelo".

## Criterio de aceptación

- S ≥ mínima del tipo;
- Iz corregida ≥ In;
- ΔU ≤ límite del tipo;
- ΔU acumulada ≤ 5 %.

## Módulos

`aea_pipeline.calculate`, `voltage_drop.caida_tension`, `aea_conductors.section_min_circuit`, `aea_voltage_drop.limite_caida_pct`.
