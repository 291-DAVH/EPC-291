# Backlog del área de trazado (editor de planos)

Ideas aprobadas por el responsable para implementar. Todas son de interfaz: no tocan el motor de cálculo.
Estado: `[ ]` pendiente, `[x]` hecho.

## Prioridad alta (orden sugerido)
1. [ ] Imán (snap) a nodos, puntos medios y grilla opcional; Mayús bloquea a ortogonal.
2. [ ] Línea continua: el siguiente tramo arranca en el último nodo; Esc o doble clic corta.
3. [ ] Barra de coordenadas abajo: X, Y en metros, escala y zoom.
4. [ ] Colorear por circuito o tipo de bandeja, con leyenda, y rótulos de longitud en cada tramo.
5. [ ] Selección rectangular por arrastre (además de Mayús+clic).
6. [ ] Menú contextual (clic derecho): propiedades, borrar, asignar circuito y tipo.

## Dibujar más rápido
- [ ] Insertar nodo sobre una línea (parte el tramo en dos, conserva el circuito).
- [ ] Copiar y pegar, con repetición en matriz.
- [ ] Entrada por longitud o coordenadas mientras se dibuja ("5,2" + Enter).

## Navegación
- [ ] Minimapa.
- [ ] Zoom a la selección y al circuito en foco.
- [ ] Panear con barra espaciadora o botón central.
- [ ] Capas visibles (fondo, rótulos, cotas, tipos de tramo) y opacidad del fondo.

## Ver lo calculado
- [ ] Resaltar el recorrido del circuito de tablero a carga.
- [ ] Avisos clicables que centran el lienzo en el elemento.
- [ ] Cota rápida (medir sin crear).

## Menos errores
- [ ] Alinear y distribuir nodos.
- [ ] Detección de nodos solapados/duplicados y tramos sin salida.
- [ ] Confirmar antes de borrar muchos elementos.

## Edición y precisión
- [ ] Guías de alineación al mover nodos.
- [ ] Estirar tramos al mover un nodo (modo "solo nodo" para desconectar).
- [ ] Girar, espejar y escalar un grupo.
- [ ] Bloquear elementos (candado), incluido el plano de fondo.
- [ ] Medir ángulos y áreas.

## Plano de fondo
- [ ] Calibración por dos puntos: alinear y rotar el fondo.
- [ ] Imán a vértices y líneas del DXF importado.
- [ ] Recortar o enmascarar parte del plano.

## Inteligencia sobre el trazado
- [ ] Autoruta sugerida por las bandejas existentes (aceptar con un clic).
- [ ] Ocupación de canalización: barra verde/amarilla/roja frente al máximo de la norma.
- [ ] Detección de cruces y distancias mínimas (fuerza vs. señal).
- [ ] Vista previa de cambios desde la última generación.

## Equipo y seguimiento
- [ ] Comentarios fijados en el plano (chincheta, marcar resuelto).
- [ ] Historial de versiones con comparación visual y restaurar.
- [ ] Indicador de guardado y recuperación ante cierre accidental.

## Salida
- [ ] Vista previa de impresión (hoja y rótulo) antes de generar.
- [ ] Exportar imagen del lienzo a PNG/PDF.
- [ ] Plantillas de trazado reutilizables entre proyectos.

## Según la especialidad
- [ ] Modos por disciplina: la botonera y la paleta se adaptan (eléctrica, cloacas, etc.).
- [ ] Pendiente automática en cloacas con aviso si queda fuera de norma.
- [ ] Biblioteca de símbolos del catálogo, con rotación.

## Información en pantalla
- [ ] Tabla de selección (cantidad, longitud total, circuitos).
- [ ] Vista de circuito: aislar uno y atenuar el resto.
- [ ] Tooltips con datos al pasar el ratón.
- [ ] Rótulos que no se pisan (reubicación automática).

## Velocidad y comodidad
- [ ] Repetir la última acción.
- [ ] Atajos configurables y pantalla de ayuda de atajos.
- [ ] Favoritos fijos arriba en la paleta.
- [ ] Copiar un tramo a varios niveles o plantas repetidas.

## Varios niveles
- [ ] Ver el nivel de arriba y el de abajo atenuados.
- [ ] Conectar nodos entre niveles (sube/baja) y ruta entre niveles por plenos.

## Calidad y confianza
- [ ] Lista de comprobaciones antes de generar (escala, circuitos sin ruta, nodos huérfanos, tramos sin tipo).
- [ ] Modo revisión solo lectura con marca visible.
- [ ] Pruebas automáticas del editor con navegador (dibujar, deshacer, calibrar).

## Aspecto de escritorio y táctil
- [ ] Atajos visibles en la botonera y paleta de comandos (Ctrl+K).
- [ ] Vista previa "fantasma" del elemento bajo el cursor.
- [ ] Pellizco para zoom, dos dedos para panear, asas grandes de arrastre.
