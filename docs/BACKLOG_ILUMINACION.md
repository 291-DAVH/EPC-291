# Backlog de iluminación

Lo que falta y lo que se puede mejorar del motor `epc_lighting` y de su integración en la plataforma (ADR-0029 y ADR-0030, fases 1 a 7 terminadas el 2026-10-28; mejoras del 2026-10-28 hechas aparte).
Estado: `[ ]` pendiente, `[~]` hecho en parte (se dice qué falta), `[x]` hecho.

## Pendientes (lo que quedó sin hacer o sin verificar)

### De tu lado (no los puede hacer el programa)
- [ ] **Revisar y aprobar los niveles del Decreto 351/79** en la pantalla de normas ("Niveles de iluminación"). Mientras estén pendientes no alimentan ninguna meta.
- [ ] **Confirmar con la norma vigente** los criterios de emergencia antipánico (0,5 lx y relación máx/mín 40) y el factor 0,9 del chequeo directo: están como valores típicos con confianza 0,5.
- [ ] **Reemplazar las luminarias de fábrica** por las del proyecto (flujo, potencia, factor de potencia, curva): hoy son valores típicos marcados como ilustrativos.
- [ ] **Cargar el límite de W/m² y la tarifa por kWh** en las opciones de cada hoja si quieres que la verificación de energía y el costo se calculen: el programa no trae ninguno.

### Motor
- [ ] Filas industriales de la Tabla 2 del Decreto 351/79 (hoy hay una fila marcada "sin cargar").
- [ ] Reglas de uniformidad y relaciones de luminancia del Decreto: se revisan pero no se usan para verificar.
- [ ] Otras normas de iluminación (IRAM-AADL J 20-06, EN 12464-1) como paquetes de norma, con el selector de norma (ADR-0028).
- [ ] Ambientes que no son rectángulos: se calcula sobre el rectángulo envolvente y se descartan las luminarias que caen fuera. Falta calcular sobre el contorno real y los ambientes girados.
- [ ] Inter-reflexiones en el punto a punto (hoy solo luz directa) y luminarias inclinadas o giradas.
- [ ] Cálculo propio de UGR (hoy solo se compara un valor calculado afuera).
- [ ] Áreas exteriores: ubicar los proyectores (hoy solo se calcula la cantidad), tabla de niveles exteriores típicos y aprovechamiento del haz (CBU) desde la curva isocandela.
- [ ] Emergencia: el motor ya revisa rutas de escape, pero la pantalla no deja dibujarlas ni cargar sus datos; tampoco hay campo para la iluminancia mínima propia del ambiente.
- [ ] Importar curvas de fabricante (archivos IES y LDT) y tablas de utilización del fabricante. (La planilla del catálogo ya se importa, sin curvas.)

### Plataforma
- [x] Luminarias de emergencia como nodos del plano (tipo `LE`, familia de circuito `IUE`).
- [x] El diseño automático usa la potencia aparente de cada luminaria (factor de potencia del catálogo; sin dato, los W).
- [x] Al recalcular y volver a aplicar, las luminarias nuevas toman el circuito de la que reemplazan.
- [x] La memoria de cálculo trae el rótulo del proyecto (emisora, cliente, quien dibujó, revisó y aprobó), la tabla de energía y el plano con luminarias y mapa.
- [~] El rótulo de la memoria es una tabla de datos: falta el recuadro con los logos que llevan los planos emitidos.
- [ ] Un solo estudio por hoja (sin historial de estudios anteriores).
- [ ] La revisión de las reglas de iluminación guarda su estado junto al de AEA 90364 (un solo archivo de revisión): moverlo al motor de iluminación cuando haya más normas.
- [ ] La pantalla de revisión de normas para reglas de iluminación no se probó en el navegador (sí por API y tipos).
- [x] Las pruebas del motor que leen las reglas reales del Decreto ya no dependen de que estén pendientes.
- [ ] Las pruebas de emergencia tardan unos 6 s (búsqueda de hasta 400 luminarias): acelerar la búsqueda o limitarla.
- [ ] Las luminarias del grupo `emergency` no se ofrecen al comparar ni al elegir sola; hoy el grupo solo lo trae la de fábrica (las del catálogo propio que sean de emergencia deben llevar ese grupo).

## Mejoras

### Cálculo y verificación
- [x] **Verificar el plano tal como está dibujado**: botón "Verificar el plano dibujado" (calcula con las luminarias que hay, donde estén).
- [x] **Comparar alternativas** por ambiente, con la mejor al principio y "Usar".
- [x] Verificar la eficiencia energética contra un límite de W/m² propio y estimar kWh/año y costo (con horas y tarifa propias).
- [x] Elegir automáticamente la luminaria cuando el ambiente solo tiene actividad (opción de la hoja).

### Pantalla
- [x] Mostrar en el panel el error de guardado del estudio y el de lectura (así se ve cuando el backend es una versión anterior).
- [x] Copiar los parámetros de un ambiente a otros, y plantillas por tipo de ambiente (se guardan con la hoja).
- [x] Proponer la actividad según el nombre del ambiente.
- [x] Rotular cada luminaria con su etiqueta en la vista previa.
- [x] Mapa de iluminancia: curvas de nivel con su valor, el interruptor se recuerda en la hoja y exportación a imagen (PNG).
- [ ] Exportar el mapa a DXF.
- [x] Mostrar la fuente de la meta (norma y cláusula, o la actividad) en la tarjeta de cada ambiente.
- [ ] Arrastrar las luminarias de la vista previa antes de aplicar (hoy se arrastran después, ya como nodos).

### Catálogo
- [x] Duplicar, buscar, agrupar e importar desde una planilla (pegar o archivo CSV).
- [x] Marcar favoritas (van primero) y cargar el factor de potencia de cada luminaria.

### Entregables
- [x] Memoria con plano, mapa y tablas por ambiente en una sola emisión.
- [ ] Versión en Word de la memoria, si el cliente la pide.
