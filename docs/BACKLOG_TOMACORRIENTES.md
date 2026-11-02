# Backlog de tomacorrientes

Lo que hay y lo que falta del motor `epc_receptacles` y de su integración en la plataforma (ADR-0031, hecho el 2026-11-02).
Estado: `[ ]` pendiente, `[~]` hecho en parte (se dice qué falta), `[x]` hecho.

## Hecho
- [x] Motor `epc_receptacles`: cantidad por uso del ambiente (por área, por perímetro o fija), reparto a lo largo de las paredes lejos de las esquinas, verificación de la altura de montaje (AEA 90364-7-771 y 770, ambientes con agua), carga y circuitos mínimos; cada estimación dice por qué y con qué confianza.
- [x] Catálogo de tomacorrientes en tres niveles (fábrica, empresa, proyecto), con su editor en Datos y en Ingeniería → Catálogos del proyecto.
- [x] Panel «Tomacorrientes» en el editor de planos: uso del ambiente, tomacorriente, cantidad, altura y sección de la norma; calcula, verifica lo dibujado y pone los nodos `TG`/`TE` en el plano (reemplaza los que puso un cálculo anterior y conserva el circuito del más cercano).
- [x] El diseño automático de circuitos usa la potencia de cada tomacorriente colocado.
- [x] Los valores típicos (cantidad por uso, alturas, tomacorrientes por circuito) están en la página global de normas, para confirmarlos una sola vez.
- [x] Estudio guardado con la hoja, memoria en Markdown entre los documentos del proyecto, PDF al emitir y botón en Memorias.

## Pendiente
### De tu lado
- [ ] **Confirmar en la página de normas los valores típicos** de «Tomacorrientes · valores típicos»: solo el depósito (un tomacorriente cada 9 m de perímetro, mínimo 2) viene de una cláusula; el resto es práctica habitual con confianza 0,4.
- [ ] **Reemplazar los tomacorrientes de fábrica** por los del proyecto (potencia, corriente, IP).

### Motor
- [ ] Cantidades por cláusula de la norma para viviendas (770) y locales (771) cuando se carguen y aprueben las reglas.
- [ ] Posición según puertas, muebles y puestos de trabajo (hoy se reparte parejo por las paredes); ambientes que no son rectángulos (hoy se usa el rectángulo envolvente).
- [ ] Reglas especiales ya cargadas en las reglas de AEA que aún no se verifican: aulas con tomacorrientes junto al pizarrón, jardines infantiles a 1,7 m, tomas accesibles a niños (2x10+T con pantalla), circuitos ATE en rojo, carga de vehículos eléctricos.
- [ ] Tomacorrientes de uso especial: un circuito por cada uno, con su destino.

### Plataforma
- [ ] Mapa del plano en el informe (la memoria de iluminación lo trae; esta aún no).
- [ ] Exportar a DXF queda **en espera** con todo lo de optimizar el DXF.
- [ ] La pantalla de normas con la unidad nueva no se probó en el navegador (sí por API y pruebas).
