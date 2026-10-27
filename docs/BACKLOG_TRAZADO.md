# Backlog del área de trazado (editor de planos)

Ideas aprobadas por el responsable para implementar. Todas son de interfaz: no tocan el motor de cálculo.
Estado: `[ ]` pendiente, `[~]` hecho en parte (se dice qué falta), `[x]` hecho. Las ideas de coordinación entre disciplinas están en `docs/architecture/decisions/ADR-0024-coordination-between-disciplines.md`.

## Prioridad alta (orden sugerido)
1. [ ] Imán (snap) a nodos, puntos medios y grilla opcional; Mayús bloquea a ortogonal.
2. [ ] Línea continua: el siguiente tramo arranca en el último nodo; Esc o doble clic corta.
3. [ ] Barra de coordenadas abajo: X, Y en metros, escala y zoom.
4. [ ] Colorear por circuito o tipo de bandeja, con leyenda, y rótulos de longitud en cada tramo.
5. [ ] Selección rectangular por arrastre (además de Mayús+clic).
6. [ ] Menú contextual (clic derecho): propiedades, borrar, asignar circuito y tipo.

## Dibujar más rápido
- [x] Insertar nodo sobre una línea (parte el tramo en dos, conserva el circuito).
- [x] Copiar y pegar, con repetición en matriz.
- [x] Entrada por longitud o coordenadas mientras se dibuja ("5,2" + Enter).

## Navegación
- [x] Minimapa.
- [x] Zoom a la selección y al circuito en foco.
- [x] Panear con barra espaciadora o botón central.
- [x] Capas visibles (fondo, rótulos, cotas, tipos de tramo) y opacidad del fondo.

## Ver lo calculado
- [x] Resaltar el recorrido del circuito de tablero a carga.
- [x] Avisos clicables que centran el lienzo en el elemento.
- [x] Cota rápida (medir sin crear).

## Menos errores
- [x] Alinear y distribuir nodos.
- [x] Detección de nodos solapados/duplicados y tramos sin salida.
- [x] Confirmar antes de borrar muchos elementos.

## Edición y precisión
- [x] Guías de alineación al mover nodos.
- [x] Estirar tramos al mover un nodo (modo "solo nodo" para desconectar).
- [x] Girar, espejar y escalar un grupo.
- [x] Bloquear elementos (candado), incluido el plano de fondo.
- [x] Medir ángulos y áreas.

## Plano de fondo
- [x] Calibración por dos puntos: alinear y rotar el fondo.
- [x] Imán a vértices y líneas del DXF importado.
- [x] Recortar o enmascarar parte del plano.

## Inteligencia sobre el trazado
- [x] Autoruta sugerida por las bandejas existentes (aceptar con un clic).
- [x] Ocupación de canalización: barra verde/amarilla/roja frente al máximo de la norma.
- [x] Detección de cruces y distancias mínimas (fuerza vs. señal).
- [x] Vista previa de cambios desde la última generación.

## Equipo y seguimiento
- [x] Comentarios fijados en el plano (chincheta, marcar resuelto).
- [x] Historial de versiones con comparación visual y restaurar.
- [x] Indicador de guardado y recuperación ante cierre accidental.

## Salida
- [~] Vista previa de impresión (hoja y rótulo) antes de generar. — Hoja simple con un rótulo básico; no es la lámina IRAM.
- [x] Exportar imagen del lienzo a PNG/PDF.
- [x] Plantillas de trazado reutilizables entre proyectos.

## Según la especialidad
- [~] Modos por disciplina: la botonera y la paleta se adaptan (eléctrica, cloacas, etc.). — La paleta sale del perfil; la herramienta Ruta solo aparece en eléctrica.
- [~] Pendiente automática en cloacas con aviso si queda fuera de norma. — El motor ya calcula las cotas y avisa; ahora se ven sobre los nodos. Los valores de la norma siguen pendientes de confirmar.
- [~] Biblioteca de símbolos del catálogo, con rotación. — Hecho: giro del símbolo (también en el DXF). Falta: elegir el símbolo con una vista previa.

## Información en pantalla
- [x] Tabla de selección (cantidad, longitud total, circuitos).
- [x] Vista de circuito: aislar uno y atenuar el resto.
- [x] Tooltips con datos al pasar el ratón.
- [x] Rótulos que no se pisan (reubicación automática).

## Velocidad y comodidad
- [x] Repetir la última acción.
- [x] Atajos configurables y pantalla de ayuda de atajos.
- [x] Favoritos fijos arriba en la paleta.
- [x] Copiar un tramo a varios niveles o plantas repetidas.

## Varios niveles
- [x] Ver el nivel de arriba y el de abajo atenuados.
- [~] Conectar nodos entre niveles (sube/baja) y ruta entre niveles por plenos. — Hecho: el enlace `nivel:nodo` de un conducto vertical y su comprobación (existe, cae en el mismo lugar, apunta de vuelta). Falta: medir un circuito que cruza niveles.

## Calidad y confianza
- [x] Lista de comprobaciones antes de generar (escala, circuitos sin ruta, nodos huérfanos, tramos sin tipo).
- [x] Modo revisión solo lectura con marca visible.
- [x] Pruebas automáticas del editor con navegador (dibujar, deshacer, calibrar).

## Aspecto de escritorio y táctil
- [x] Atajos visibles en la botonera y paleta de comandos (Ctrl+K).
- [x] Vista previa "fantasma" del elemento bajo el cursor.
- [~] Pellizco para zoom, dos dedos para panear, asas grandes de arrastre. — Hecho en el código; falta probarlo en una pantalla táctil real.
