# Revisión del PRD «Editor de trazado sobre plano» frente a EPC-291

Documento revisado: `PRD-trazado-v0.2.md`. Se contrasta con ADR-0008 (CAD 2D primero), ADR-0012 (una sola fuente), ADR-0016 (la organización es dueña de su ingeniería), ADR-0019 y ADR-0020 (trazado sobre el plano), con `SPEC.md` de este módulo y con lo que el motor ya hace.

## Veredicto

El PRD es coherente con la dirección ya decidida y mejora el ADR-0020 en tres puntos: perfiles de disciplina como archivos, biblioteca de símbolos separada y la regla de que el DXF sale del modelo y no del SVG. Hay **cuatro choques con reglas fijas** y **cinco huecos de diseño** que conviene cerrar antes de escribir código.

## Lo que ya existe y se reutiliza

| El PRD pide | Ya está en la plataforma |
|---|---|
| Stack (sección 11, vacío) | Motor Python + backend FastAPI + web React: el stack queda decidido por el repositorio; solo falta elegir la librería del canvas (SVG con zoom, o canvas bajo MIT) |
| DXF con capas, bloques y textos (RF-19) | `ezdxf` ya genera los DXF del motor (`epc_drawing`: capas, bloques, sello); se agrega un generador para el trazado, no una tecnología nueva |
| Biblioteca de símbolos (RF-20) | `epc_drawing/symbols/library` (unifilar, multifilar, BT y MT) con catálogo; los símbolos de planta (cámara, caja de pase, bandeja) son un conjunto nuevo en el mismo formato |
| Rótulo y cajetín (RF-21) | `epc_drawing/titleblock` (láminas IRAM A0–A4, rótulo personalizado) |
| Importar Excel/CSV (RF-11) | `openpyxl` ya se usa; los cables vienen además de los tableros de la plataforma |
| Tablas en tiempo real, tags, historial | Patrones del backend (registros con historia, `core/ids`) y del frontend |
| Cálculos de fase 4 (llenado, caída, pendiente) | Ya existen en `epc_calc` (ampacidad, caída de tensión, ruta real del cable `aea_route`); el trazado debe **alimentarlos**, no reimplementarlos |

## Choques con reglas fijas (hay que resolverlos)

1. **SVG como entregable (RF-17, fase 1, métrica 5).** La regla del proyecto y el ADR-0020 dicen que el SVG nunca es entregable: es solo vista de trabajo. Propuesta: el SVG es la **vista en pantalla**; los entregables son **DXF y PDF**. Consecuencia: **el DXF pasa a la fase 1** (hoy está en la 2) y el criterio de salida de la fase 1 se mide con DXF/PDF, no con SVG.
2. **Tags de cables y circuitos (principio 4, entidad Línea).** El cable de un circuito ya tiene su tag en el tablero (ADR-0012: una sola fuente). Si el trazado vuelve a definir «Línea CA-001», habrá dos fuentes. Propuesta: la Línea **referencia** el tag del circuito de la plataforma; el trazado solo crea tags de lo que no existe (cámaras, bandejas, tramos de cañería).
3. **Un solo plano con disciplina activa (entidad Plano).** El ADR-0020 prevé varios planos por proyecto (uno por nivel), cada uno con escala y nivel, y montantes que los unen. El PRD deja «tramos verticales y alturas» fuera de la v1 y el plano sin nivel. Propuesta: el plano lleva **nivel** desde la v1 y las montantes entran como nodo con cota; sin eso, ni las cloacas (pendiente) ni la ruta real del cable quedan bien.
4. **Datos de la organización (pregunta 8).** No es una pregunta abierta: ADR-0016 y ADR-0013 ya fijan que cada organización es dueña de sus proyectos y de sus planos, con permisos por tipo de cuenta. El trazado cuelga del proyecto y del permiso de escritura de ingeniería; no tiene su propia autenticación.

## Huecos de diseño

1. **«Línea» como secuencia ordenada no alcanza para redes.** Cloacas, gas, incendio y ductos son **árboles** (ramales, derivaciones), no recorridos. Propuesta: el modelo base es un **grafo** (nodos y tramos); la «línea» es un recorrido elegido sobre el grafo (cable) o el árbol completo de una red (cañerías). El orden de las longitudes acumuladas sale del camino, no de una lista guardada.
2. **Cota de nodos para la pendiente.** Las cloacas necesitan cota de fondo en cada cámara aunque no haya «tramos verticales»: es un atributo del nodo y la pendiente se calcula entre nodos.
3. **Contenedor: declarado o derivado.** Qué cables van por qué bandeja ¿lo dibuja el usuario o sale de que el recorrido del cable coincide con el tramo de la bandeja? Propuesta: **derivado** del recorrido (el ADR-0020 ya lo dice: la cantidad de circuitos por tramo se deduce), con corrección manual excepcional.
4. **Sistema de coordenadas del plano.** Falta definir el origen y el manejo de PDF de varias hojas, rotación y plano en unidades de papel. Propuesta: coordenadas en metros reales respecto del primer punto de calibración, una escala por hoja y por plano, y guardar la transformación del fondo.
5. **Verificación del DXF (RNF-07).** No hay AutoCAD en el entorno de pruebas. Propuesta: `ezdxf` con `audit()` en el gate más apertura en un visor libre; la prueba en AutoCAD queda como verificación manual del dueño, anotada como «no verificada localmente».

## Respuestas propuestas a las preguntas abiertas

| Pregunta | Propuesta |
|---|---|
| ¿Quién carga los atributos? | Ambos: lo que ya existe (cables del tablero) viene de la plataforma; lo propio del trazado (diámetros, material) se completa en el popup o por importación |
| ¿El recorrido se dibuja o se asigna? | Se dibuja la **geometría**; el cable se **asigna** a un recorrido por origen y destino (adelantar a la fase 2 lo que el PRD deja a la 3) |
| ¿Formato fijo o libre? | Fijo, con la plantilla de la organización (rótulo de `titleblock`) |
| Simbología | Por defecto la de la biblioteca de la plataforma; la empresa agrega o reemplaza símbolos como archivos |
| Versión de DXF | Definirla con el dueño; `ezdxf` escribe R2010 por defecto, compatible con casi todo |
| Multiusuario | No en la v1 (guardado por versión del proyecto) |
| Disciplinas | Eléctrica BT primero (ya tiene cálculo y ruta real), luego incendio y cloacas |
| Individual u organizacional | Las dos: un profesional independiente es una organización de una persona (ADR-0016) |

## Cambios propuestos al plan de fases

| Fase | Propuesta |
|---|---|
| 1 | Plano con nivel y escala; nodos y tramos como grafo; perfil eléctrico BT; símbolos de planta; tablas; **DXF y PDF** (la vista SVG solo en pantalla); guardado automático |
| 2 | Cables del tablero asignados a recorridos (origen y destino); contenedores derivados; importación Excel/CSV; bandejas y llenado; segundo perfil (cloacas con cotas) |
| 3 | Copiar y pegar, snap avanzado, capas, historial, plantillas de planta |
| 4 | Redes de incendio y cloacas con su cálculo; reglas normativas verificables; detección de choques |

## Antes de construir: decisiones que necesita del dueño

1. Aceptar que el SVG no es entregable y que el DXF entra en la fase 1.
2. Confirmar que la Línea referencia los circuitos de la plataforma (una sola fuente).
3. Confirmar el modelo en grafo y la cota en los nodos.
4. Elegir la librería del canvas (SVG con zoom frente a canvas).
5. Indicar el programa CAD destino y su versión.

Sin esas cinco respuestas, el trabajo de la fase 1 puede empezar por lo que no depende de ellas: el modelo de datos, el perfil eléctrico, el generador de DXF desde el modelo y su prueba con `ezdxf`.
