# Backlog de ingeniería eléctrica (circuitos, cables, canalizaciones y proyecto)

Ideas y pendientes del flujo de cálculo de cables y canalizaciones, de los circuitos del tablero y de los datos del proyecto. Se anotaron el 2026-10-28, a partir del diseño automático (recorrido, circuitos y dimensionado), la tabla de circuitos y el formulario del tablero.
Estado: `[ ]` pendiente, `[~]` hecho en parte (se dice qué falta), `[x]` hecho.

## Cierran cosas que quedaron a medias
1. [x] **Acometidas con cable propio** (2026-10-28). Un tablero define una o varias acometidas (hasta 6), cada una con nombre, fuente, fase, largo, corriente (vacía = la suma de la cabecera del tablero), instalación, aislación y conductor; se dimensionan como un circuito y salen en la memoria. Queda: que el unifilar dibuje todas las acometidas (hoy solo la primera, en las cifras del rótulo) y repartir la corriente entre ellas cuando alimentan juntas.
2. [ ] **La fase final del proyecto debe mandar.** Hoy se guarda y se muestra, pero el flujo de gestión (puertas de emisión, `management/workflow`) deduce la fase solo por las emisiones hechas: que deje de ofrecer pasos más allá de la fase final.
3. [x] **Circuitos que cruzan niveles** (2026-10-28). El circuito se dibuja en cada hoja que toca con el mismo TAG: en la del tablero va del tablero al pleno, y en las de arriba o abajo del pleno a sus cargas. El largo se encadena por los plenos (la altura se cuenta una vez) y el tablero lo usa. Queda: los niveles que el cable atraviesa sin hoja propia no suman su altura, y el diseño automático y el dimensionado de canalizaciones siguen trabajando sobre una hoja.
4. [ ] **Recorrido incompleto en el diseño automático.** La propuesta de canalizaciones puede no llegar a todas las luminarias de un circuito (el cálculo lo avisa después): cerrar esos tramos o decir cuáles faltan antes de aceptar el recorrido.

## Calidad del cálculo
5. [ ] **Vista de "por qué esta sección".** En cada circuito, qué la determinó: In, Iz, caída de tensión o sección mínima.
6. [ ] **Agrupamiento tomado del plano.** El motor ya baja la Iz por agrupamiento (circuitos juntos); hoy se carga a mano. Contar los circuitos que comparten tramo en la bandeja o el conduit.
7. [ ] **Valores típicos a confirmar.** Diámetros de cable por sección y medidas comerciales de conduits y bandejas (`engine/plan/src/epc_plan/params.json`, bloque `sizing`): llevarlos al catálogo del proyecto para fijarlos con el proveedor.

## Uso diario
8. [ ] **Edición en bloque de circuitos.** Cambiar conductor, aislación e instalación de varios circuitos a la vez (por ejemplo, todas las luminarias de un nivel).
9. [ ] **Recalcular solo al editar.** Hoy se calcula al aceptar un circuito o con "Calcular"; que corra solo, con una espera breve después del último cambio.
10. [ ] **Plantillas de circuitos por familia** (iluminación, tomas, climatización, motores) con cable y protección típicos del proyecto.

## Entregables y pruebas
11. [ ] **Memoria en Word, logos en el rótulo de la memoria y mapa de lux a DXF** (ya estaban en el backlog de iluminación).
12. [ ] **Casos de prueba con planos reales** (PDF de CAD con mucho rayado, como el que superó el límite de trazos) para ajustar el reconocimiento de muros.
