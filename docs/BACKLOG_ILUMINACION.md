# Backlog de iluminación

Lo que falta y lo que se puede mejorar del motor `epc_lighting` y de su integración en la plataforma (ADR-0029 y ADR-0030, fases 1 a 7 terminadas el 2026-10-28).
Estado: `[ ]` pendiente, `[~]` hecho en parte (se dice qué falta). Las ideas de mejora son propuestas: faltan aprobar.

## Pendientes (lo que quedó sin hacer o sin verificar)

### De tu lado (no los puede hacer el programa)
- [ ] **Revisar y aprobar los niveles del Decreto 351/79** en la pantalla de normas ("Niveles de iluminación"). Mientras estén pendientes no alimentan ninguna meta.
- [ ] **Confirmar con la norma vigente** los criterios de emergencia antipánico (0,5 lx y relación máx/mín 40) y el factor 0,9 del chequeo directo: están como valores típicos con confianza 0,5.
- [ ] **Reemplazar las luminarias de fábrica** por las del proyecto (flujo, potencia, curva): hoy son valores típicos marcados como ilustrativos.

### Motor
- [ ] Filas industriales de la Tabla 2 del Decreto 351/79 (hoy hay una fila marcada "sin cargar").
- [ ] Reglas de uniformidad y relaciones de luminancia del Decreto: se revisan pero no se usan para verificar.
- [ ] Otras normas de iluminación (IRAM-AADL J 20-06, EN 12464-1) como paquetes de norma, con el selector de norma (ADR-0028).
- [ ] Ambientes que no son rectángulos: se calcula sobre el rectángulo envolvente y se descartan las luminarias que caen fuera. Falta calcular sobre el contorno real y los ambientes girados.
- [ ] Inter-reflexiones en el punto a punto (hoy solo luz directa) y luminarias inclinadas o giradas.
- [ ] Cálculo propio de UGR (hoy solo se compara un valor calculado afuera).
- [ ] Áreas exteriores: ubicar los proyectores (hoy solo se calcula la cantidad), tabla de niveles exteriores típicos y aprovechamiento del haz (CBU) desde la curva isocandela.
- [ ] Emergencia: el motor ya revisa rutas de escape, pero la pantalla no deja dibujarlas ni cargar sus datos; tampoco hay campo para la iluminancia mínima propia del ambiente.
- [ ] Importar curvas de fabricante (archivos IES y LDT) y tablas de utilización del fabricante.

### Plataforma
- [ ] **Luminarias de emergencia como nodos del plano**: el perfil eléctrico no tiene un tipo para ellas (hoy se ven como marcas rojas y van a la memoria).
- [ ] El diseño automático toma la potencia en W como VA (factor de potencia 1): falta el factor de potencia o el consumo del driver.
- [ ] Al recalcular y volver a aplicar, las luminarias reemplazadas pierden el circuito que tenían asignado.
- [ ] La memoria de cálculo usa el formato general de informes: falta el rótulo y los logos del proyecto, como llevan los planos emitidos.
- [ ] La memoria no incluye el plano con las luminarias ni el mapa de iluminancia.
- [ ] Un solo estudio por hoja (sin historial de estudios anteriores).
- [ ] La revisión de las reglas de iluminación guarda su estado junto al de AEA 90364 (un solo archivo de revisión): moverlo al motor de iluminación cuando haya más normas.
- [ ] La pantalla de revisión de normas para reglas de iluminación no se probó en el navegador (sí por API y tipos).
- [ ] Las pruebas del motor que leen las reglas reales del Decreto suponen que todas están pendientes (`test_norm_data`): se romperán el día que apruebes una. Pasarlas a copias temporales.
- [ ] Las pruebas de emergencia tardan unos 6 s (búsqueda de hasta 400 luminarias): acelerar la búsqueda o limitarla.

## Mejoras propuestas

### Cálculo y verificación
- [ ] **Verificar el plano tal como está dibujado**: si mueves o borras luminarias a mano, recalcular la iluminancia con las posiciones reales y decir si sigue cumpliendo.
- [ ] **Comparar alternativas** por ambiente (cantidad, W/m², cumple o no) y proponer la de menor potencia instalada.
- [ ] Verificar la eficiencia energética contra un límite de W/m² y estimar el consumo anual y su costo.
- [ ] Elegir automáticamente la luminaria cuando el ambiente solo tiene actividad.

### Pantalla
- [ ] **Mostrar en el panel el error de guardado del estudio** y avisar cuando el backend es una versión anterior (hoy el error sale en otra parte y se confunde con "no hay botón").
- [ ] Copiar los parámetros de un ambiente a otros, y plantillas por tipo de ambiente (aula, oficina, pasillo).
- [ ] Proponer la actividad según el nombre del ambiente ("Aula", "Pasillo").
- [ ] Rotular cada luminaria con su etiqueta en el plano y poder arrastrarlas con el mapa visible.
- [ ] Mapa de iluminancia: curvas de nivel, valor al pasar el cursor, recuerdo del interruptor y exportación a imagen o DXF.
- [ ] Mostrar la meta y su fuente (norma y cláusula) en la tarjeta del ambiente, también para las actividades.

### Catálogo
- [ ] Duplicar, buscar y agrupar luminarias; importar desde una planilla.
- [ ] Marcar favoritas por proyecto.

### Entregables
- [ ] Memoria con plano, mapa y tablas por ambiente en una sola emisión.
- [ ] Versión en Word de la memoria, si el cliente la pide.
