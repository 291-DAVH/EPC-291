# Repertorio aprendido de las muestras

Fuente: 33 archivos de `samples/` (27 imágenes y 5 PDF), estudiados el 2026-11-02. Los originales no se versionan; aquí solo queda lo aprendido. El estado por hash está en `samples/registro.json`.

## 1. Qué hay en las muestras

| Tipo | Cantidad | Qué son |
|---|---|---|
| Plantas 2D en blanco y negro (muros como banda negra) | ~10 | Estilo "plantilla": muros gruesos, puertas con arco, muebles en trazo fino |
| Plantas CAD con acotado (muros doble línea, sombreado) | ~8 | Con cotas, ejes, textos, rótulo; mucho ruido para un lector de imagen |
| Plantas renderizadas / a color | ~5 | Acuarela, piso de madera, azul "blueprint", vista 3D isométrica |
| Capturas de pantalla / collages | ~4 | Interfaz de software, láminas con varias vistas, plano pequeño dentro de una lámina |
| PDF vectoriales de CAD | 4 | Láminas con planta + cortes + fachadas, instalaciones sanitarias, planta de casa (Farnsworth) |
| PDF que en realidad es imagen | 1 | `1776680613386.pdf`: plano de distribución sin vectores |

## 2. Resultado del motor `epc_arch` sobre las 33 muestras

El motor corrió sin errores en las 33 (también leyó WebP y AVIF, previa conversión a PNG).

- **Puertas:** 0 en las 28 imágenes. Es el límite documentado del lector de imagen (no lee arcos). Solo el PDF vectorial `1786358143480.pdf` dio 7 puertas y 10 ventanas.
- **Ventanas:** aparecen en la mayoría de las imágenes, pero con poca confianza (una sola línea).
- **Sobredetección de muros:** `667595ed…webp` (1098 muros), `do-architectural…png` (1043), `diseno-fondo…avif` (838), `75f00798….jpg` (801) y `plano-diseno-moderno….avif` (754). Son láminas con texto, cotas, tramas o vista 3D: el lector de imagen toma cada trazo recto como candidato. Los planos limpios dan entre 7 y 120 muros, que es lo razonable.
- **Espesor de muro (T):** en imagen sale en píxeles (1 a 11); en PDF vectorial, en unidades normalizadas a 3000 de lado (6 a 35).
- **Rendimiento:** la imagen más pesada tardó 1,3 s; los PDF entre 0,2 y 1,3 s. Con estas muestras el tiempo no es el problema; la precisión sí.

## 3. Patrones que se repiten (lo que hay que reconocer)

**Muros**
- Banda negra maciza (la mayoría de plantillas): lo detecta bien la estrategia de trazo grueso.
- Doble línea con sombreado diagonal o puntos (CAD): hay que leerla como par de líneas paralelas.
- Muro de color (naranja en el PDF de UA8, gris oscuro en renders): hoy se pierde en escala de grises.

**Aberturas**
- Puerta: arco de cuarto de círculo más hoja recta, radio 0,7 a 1,0 m.
- Puerta doble: dos arcos enfrentados (terraza, acceso).
- Ventana: 2 o 3 trazos finos paralelos entre las caras del muro; en renders, rectángulo azul o vidrio.
- Hueco sin hoja: corte del muro sin arco.

**Contexto que confunde**
- Texto de ambientes ("BEDROOM", "COCINA"), cotas con extensiones, ejes numerados, norte, rótulos, cuadro de cuadros, árboles y personas en cortes.

## 4. Biblioteca de símbolos (`biblioteca/svg/`)

25 símbolos de planta, 1 unidad = 1 cm, trazo solo, cabecera hacia arriba. Reproducen lo que más se repite en las muestras:

- **Dormitorio:** cama individual, matrimonial y king, placard, escritorio con silla.
- **Estar:** sofá de 3 y de 2 cuerpos, sillón, mueble de TV.
- **Comedor:** mesa rectangular de 6 y de 4 plazas, mesa redonda de 4, silla.
- **Baño:** inodoro, lavabo, bañera, ducha.
- **Cocina:** cocina de 4 hornallas, heladera, mesada con fregadero.
- **Circulación y aberturas:** escalera recta, puerta batiente, ventana.
- **Exterior:** árbol, auto (garaje).

Ver `catalogo.json` (medidas y descripciones) y `hoja-contacto.svg` (vista de todos juntos). Regenerar con `python scripts/generar_biblioteca.py`.

**Importante:** los símbolos son dibujos propios, hechos a mano a partir de lo observado; no los extrajo el motor automáticamente. Las medidas son las de uso corriente en vivienda y se pueden ajustar.

## 5. Qué falta para reconocer muebles automáticamente

El motor hoy reconoce muros y aberturas, no muebles. Para hacerlo:

1. **PDF/DXF vectoriales:** agrupar trazos cortos cercanos que no son muro (clusters), tomar su caja y compararla con la biblioteca por medidas y forma. Aquí la biblioteca sirve de plantilla.
2. **Imágenes:** hace falta además leer arcos y curvas (hoy solo líneas rectas horizontales y verticales). Sin eso, solo se puede detectar por caja y proporción.
3. **Filtro de ruido previo:** descartar texto, cotas, ejes y rótulos antes de buscar muros; es lo que más reduce los falsos muros en las láminas.
4. **Color:** conservar color o canal de saturación para leer muros de color (naranja, gris oscuro) que en escala de grises se confunden con el fondo.
5. **Datos reales de escala:** 3 de los 5 PDF traen escala en el rótulo (1:50, 1:100). Leerla permitiría dar medidas en metros.

## 6. Archivos que conviene pedirte la próxima vez

- DXF originales (ninguna muestra fue DXF todavía): son la fuente más limpia para aprender muebles como bloques con nombre.
- Más PDF vectoriales de planta sola (sin cortes ni fachadas en la misma hoja).
- Un mismo plano en DXF, PDF e imagen, para comparar el resultado de los tres lectores.

## 7. Segunda pasada: lo que se reaprendió (2026-11-02)

46 muestras (las 33 originales, 8 referencias de estilo y 5 correcciones marcadas). Se revisaron una por una, original y resultado lado a lado.

**Leyenda del usuario:** naranja = puertas (arco + hoja), amarillo = ventanas, trazo grueso continuo negro o gris = muros. Un muro es un solo tramo que solo cortan puertas y ventanas.

**Muros (imágenes)**
- Se leen de la mancha gruesa: la tinta se "abre" con un cuadrado apenas más chico que el muro, así desaparecen texto, cotas, muebles y tramas, y cada muro queda como una sola banda.
- El grosor del muro se mide por dónde se acaba esa mancha al abrir con cuadrados cada vez más grandes.
- Una hoja de puerta o un mueble pegado al muro alarga algunas filas: las filas se unen aunque un extremo se corra, y el largo del muro es la mediana.
- Cada muro conserva su grosor (el exterior es más grueso que el interior).
- Un muro cortado por una ventana o puerta sigue siendo parte del edificio (no se descarta como trazo suelto).
- Si el plano dibuja los muros como doble línea fina, se vuelve al método de pares de líneas.

**Puertas y ventanas**
- La mayoría de puertas y ventanas están entre el **extremo de un muro y la cara del muro que lo cruza** (esquinas y T), no entre dos tramos en línea. Ahora se buscan ahí también.
- Una puerta es un arco **fino** con el cuarto de círculo **vacío** por dentro, de 2,5 a 12 grosores de muro.
- Un hueco en el extremo de un muro solo se acepta si tiene puerta o ventana; un hueco vacío ahí suele ser un muro que termina en la habitación.

**Sigue fallando**
- Planos a color con rellenos (Colonial): el relleno se toma por muro.
- Láminas con interfaz de programa, girados (no ortogonales) o renders.
- Puertas en planos cuyas marcas naranjas tapan el arco (las imágenes de corrección sirven para muros y ventanas, no para medir puertas).

## 8. Tercera pasada: puntos comunes medidos (62 muestras)

El informe completo, con cada muestra y su resultado, es `out/aprendizaje.html` (se regenera con `python scripts/informe_aprendizaje.py`).

- **Estilos de dibujo:** 42 de trazo grueso, 6 de doble línea fina, 5 planos azules, 5 vectoriales, 2 con color, 2 renders.
- **Dos direcciones:** en la mediana, el 100 % del largo de muro está a 0° o 90° del eje del plano.
- **Grosor de muro:** ~0,8 % del lado mayor de la imagen; es lo más grueso del dibujo después de rótulos y rellenos.
- **Puertas:** ~5 grosores de muro de ancho. **Ventanas:** ~6 grosores, y solo en muros que dan al exterior.
- **Muros finos (4–5 px):** el grosor se mide en la imagen completa; una copia reducida los borra.
- **Rótulos y rellenos:** mucho más gruesos que un muro (más de 2,5 veces); se descartan.

## 9. Lo que enseñan los libros (samples/pdf, 4 libros)

- *Los fundamentos del diseño aplicados a la arquitectura* (Ochaeta): **la línea define por su grosor lo que significa**, y **la forma aparece cuando la línea cierra un espacio**. La escala se dibuja **gráfica y numérica** (1:100 = 1 cm del papel es 1 m). Ambientes ligados por puertas o vestíbulos (matriz de relaciones).
- *Fundamentos básicos de la arquitectura* (Ostaiza, Cedeño): muros de mampostería de **0,10 y 0,15 m**; los vanos son puertas, ventanas y accesos; el objeto arquitectónico es muros, losas, columnas, vanos y pisos.
- *El proyecto arquitectónico* (Boix, Montelpare): la presentación final no es un "pasado en limpio": **pulir los dibujos, darles coherencia y mejorar la expresión gráfica** es parte del proyecto.
- *El diseño arquitectónico: un acertijo epistemológico* (Hierro, Baltierra): ensayos teóricos sobre la práctica proyectual; sin reglas gráficas aplicables.

**Aplicado al motor**
1. **Jerarquía de líneas:** el muro cortado es lo más pesado (relleno oscuro). La hoja de la puerta lleva una línea media y el arco y el vidrio, líneas finas.
2. **Ambientes:** los muros, con puertas y ventanas cerradas, encierran ambientes. Cada uno se dibuja con un tono suave y su área en m² (o su número si no hay escala). Los huecos de hasta 2,5 grosores entre muros se cierran.
3. **Escala escrita:** en los PDF se lee "ESCALA 1:50" o "1/100" del texto de la hoja, y todo pasa a metros. Así, en `1786358143480.pdf` el muro mide 0,25 m.
4. **Encuadre:** el dibujo se recorta al edificio, con margen y un pie con el conteo y la escala gráfica.

## 10. Segunda tanda de libros (24 en samples/pdf)

**El más útil: *Dibujo técnico arquitectónico: estándares básicos* (Sierra Mejía).** Normas aplicadas al motor:
- **Grosor de línea por escala (mm impresos):**

  | Escala | Muro cortado | Ventana y muro bajo | Vidrio | Puertas y muebles |
  |---|---|---|---|---|
  | 1:100 | 0,4–0,5 | 0,15 | 0,05 | 0,10 |
  | 1:50 | 0,6–0,7 | 0,3–0,35 | 0,05 | 0,10 |

  En el dibujo se expresan como fracción del grosor del muro.
- **Puertas:** en planta se dibujan abiertas, con la hoja a escuadra de su posición cerrada y el giro en línea punteada. Anchos: 0,70 (baños, despensas), 0,80 (alcobas, baños), 0,90 (alcobas, PMR), 1,00 o más (accesos). Con escala conocida, la hoja se busca entre 0,60 y 1,20 m.
- **Ventanas:** en planta se dibujan cerradas, con el marco paralelo al muro y el vidrio en la línea más fina.
- **Textos:** nombres de espacios de 2–2,5 mm, títulos de 3–3,5 mm, una sola fuente legible. Debajo de la planta va "PLANTA … Escala 1:100".
- **Capas:** a-muros, a-puertas, a-ventanas… (ISO 13567).
- **Escalas habituales:** 1:50 y 1:100 para plantas.

***Manual de técnicas constructivas* (Cantú, López, Narpe):** los muros de ladrillo miden 10, 15, 20, 30 y 45 cm (media asta, un asta, asta y media). Hay dos clases de grosor, con el exterior de 1,5 a 3 veces el interior.

**Minimalismo (varios libros):** "menos es más", reducir a lo esencial y sin adornos sobrantes, con colores neutros. El dibujo sigue esa línea: tinta oscura, papel blanco, tintes de piso suaves.

**Historia y teoría** (Vitruvio, Velarde, Dander, Ramírez, Pingarrón, de la Rosa, Haramoto, Tovar), **sostenibilidad** (UNAM, Aburrá, Briones, Heredia) y **colonial**: dan contexto, pero no reglas gráficas aplicables al reconocimiento.

**Ambientes:** ahora también se cierran en los huecos que el motor encontró y no clasificó. 42 de 60 planos leídos tienen ambientes.

## 11. Puertas y láminas con varias vistas (2026-11-02)

- **Láminas con varias vistas** (planta, cortes y fachadas en la misma hoja): cada vista es un grupo de muros aparte. Se queda la vista con ambientes y puertas; las demás se dejan fuera con un aviso. En `1786358143480.pdf` se quedó la planta y se dejaron fuera 4 vistas.
- **Puertas en gris claro:** muchos planos CAD dibujan el giro en gris claro. Para buscar el arco cuenta cualquier marca en el papel, no solo la tinta oscura. Así aparecen las puertas del CAD `46ea…`.
- **Dos lecturas de una imagen:** por trazo grueso y por líneas. Se queda la que cierra más ambientes (un plano bien leído encierra habitaciones), salvo que tenga mucho más del doble de muros: las tramas también cierran celdas pequeñas.
- **Todavía mal:** los planos de muros de doble línea fina sobre papel cuadriculado (`ref1`) y los que tienen ejes cruzando la planta (`planta-baja`).

## 12. Muros de doble línea fina (2026-11-02)

- Un muro dibujado como **dos líneas finas paralelas** (a veces con relleno claro) se convierte en banda: se rellena el espacio entre las dos caras (cierre morfológico de 3 y 5 px) y se lee como trazo grueso.
- Una imagen se lee de hasta cuatro maneras: trazo grueso, por líneas y doble línea cerrada con 3 y 5 px. Gana la que cierra más ambientes. Si la primera lectura cerró algo, se descartan las que tienen más del doble de sus muros, porque son tramas.
- **Resultados:**

  | Plano | Antes | Ahora |
  |---|---|---|
  | `ref1` (doble línea sobre cuadrícula) | 7 muros | 54 muros, con ambientes |
  | `ref4` (plano azul a mano) | 251 muros | 117 muros |
  | `ref5` (acuarela) | — | sale limpio |

- **Sigue mal:** los muros azules huecos con relleno claro (`4da535…`), los ejes estructurales que cruzan toda la planta (`planta-baja`) y el grosor sobrestimado en `ref1` (16,7 px).

## 13. Ejes estructurales y muros de color (2026-11-02)

- **Ejes:** son líneas finas y largas (más del 45 % de la hoja) que cruzan al menos otras tres de su tipo en el tramo medio. Un muro, en cambio, se une a otros en sus extremos o en T. Se borran de la imagen antes de leer, salvo donde algo más grueso los atraviesa, para no cortar los muros. En `planta-baja` se encontraron 10 ejes y el contorno de la casa volvió a cerrar; en los otros planos, ninguno.
- **Grosor en `ref1` (16,7 px):** no está mal. Equivale a unos 15 cm en una casa de 5 m, porque al cerrar la doble línea se mide de cara a cara del muro.
- **Muros con relleno de color** (azul claro entre dos líneas): probé tomar el color saturado como muro y lo descarté. En `4da535…` subió de 45 a 116 muros, porque el texto y la cota del mismo color también se vuelven muro.

## 14. Puertas buscadas donde giran (2026-11-02)

- Antes la puerta se buscaba solo en huecos ya encontrados, y si el hueco estaba mal medido se perdía. Ahora se busca **desde cada extremo de muro**, con todos los radios posibles de puerta (2,5 a 12 grosores) y a los dos lados.
- **La bisagra puede estar en la jamba opuesta** (la esquina del otro muro), con la hoja cerrando hacia el extremo; se prueban las dos jambas.
- **Condiciones para aceptar una puerta:**
  - el arco está dibujado casi completo (80 % o más);
  - el cuarto de círculo que barre está vacío;
  - el arco es una línea fina;
  - la hoja abierta está dibujada;
  - el paso de la puerta no es muro.
- **Umbral:** muchos planos dibujan una línea fina en el umbral. El paso se comprueba contra los muros reconocidos, no contra la tinta.
- **Resultado en la revisión a ojo:** `01-online` tiene 5 puertas, todas reales. En `46ea…` (CAD) aparecen 5 puertas reales y en `2d-site`, 3 reales, ya sin el círculo falso del baño.
- **Siguen faltando:**
  - puertas dobles;
  - puertas tapadas por marcas;
  - puertas cuyo arco no llega a 80 %.

## 15. Puertas: más encontradas, menos falsas (2026-11-02)

- El arco se acepta desde el 70 % dibujado, no solo desde el 80 %. Así aparecen las puertas con el arco cortado por muebles y cada hoja de una puerta doble, que se lee como dos puertas.
- **Anchos parecidos:** las puertas de un plano tienen pocos anchos estándar (0,70 a 1,00 m). Con 3 o más puertas, se descartan las que miden menos de 0,6 o más de 1,5 veces la mediana. Con menos de 3, se usa un ancho típico de 5 grosores de muro y un margen de 0,5 a 2,2 veces. Esto quita los círculos grandes falsos de muebles, autos y canteros.
- **Probado y descartado:** rechazar los giros que abren hacia afuera sin un muro más allá. Hacía perder puertas reales, porque el rayo sale por otros huecos.
- **Revisión a ojo:**

  | Plano | Puertas |
  |---|---|
  | `01-online` | 5 reales |
  | `2d-site` | 4 reales (antes 3), con una hoja de la puerta doble de la terraza |
  | `46ea…` | 6, con una falsa fuera del muro derecho |
  | `9c766…` | 12, la mayoría reales y algunas falsas en el garaje |

## 16. Puertas falsas (2026-11-02)

- Un arco de puerta real llega siempre a sus dos extremos: la jamba y la punta de la hoja abierta. Cuando el arco no está completo (menos del 90 %), se exige que el primer y el último quinto estén dibujados en un 85 % o más. Las curvas de autos, canteros y muebles terminan en cualquier parte y se descartan.
- El arco mínimo sube a 75 %. Se prefiere un plano limpio a encontrar cada puerta.
- **Probado y descartado:** exigir que la bisagra de la jamba opuesta toque un muro. Quitaba puertas reales y dejaba las falsas.
- **Revisión:**

  | Plano | Resultado |
  |---|---|
  | `01-online` | 5 reales |
  | `46ea…` | 5 reales (antes 6, con 1 falsa) |
  | `2d-site` | 3 reales |
  | `9c766…` | 6: se fueron las falsas del garaje; quedan 2 dudosas en ventanas del muro izquierdo |
  | `corr09` | 1 falsa grande |

  Se perdieron algunas puertas reales con arco parcial: la hoja de la terraza de `2d-site` y una de `ref5`.

## 17. Planos de color (2026-11-02)

- En un plano con pisos coloreados, el umbral automático toma los rellenos como tinta y todo el plano se vuelve una mancha. Por eso se agregan lecturas alternativas, y gana la que cierra más ambientes:
  - **tinta neutra:** quita los píxeles con color saturado; los muros suelen ser gris o negro;
  - **tinta oscura:** gris ≤ 110 y ≤ 160, solo si son más oscuros que el umbral. Sirve para rellenos pastel casi sin saturación.
- **`Colonial…`:** pasó de una mancha a mostrar el contorno del garaje y del centro de la casa. Todavía faltan los muros de la izquierda (terraza, cocina, baño).
- **Muros azules huecos (`4da535…`):** sin cambio.
- **Velocidad:** la búsqueda de puertas comprobaba el paso contra todos los muros para cada radio (60 s por imagen). Ahora se calcula vectorizada y solo donde el arco ya pasó: unos 4 s por imagen.
- **Error corregido:** la caché de la tinta engrosada se identificaba por la dirección de memoria. Python la reutiliza, así que una imagen podía usar la tinta de otra y los resultados cambiaban según el orden.

## 18. Muros por su forma, no por su color (2026-11-02, idea del usuario)

- **Muro:** un rectángulo largo y angosto, casi siempre del mismo ancho, sea relleno, contorno con trama o contorno vacío.
  - Se toma **cualquier marca sobre el papel** (gris ≤ 235, de cualquier color) y se cierran contornos y tramas (huecos de 3 y 5 px) hasta formar la banda.
  - **Forma:** se queda solo la banda con las **dos caras rectas y continuas**, con el 90 % o más de la cara marcada. Esas bandas dan el ancho de muro del plano; también se aceptan las del mismo ancho (±25 %) con caras cortadas por ventanas o marcos (60 % o más).
  - Un renglón de texto, una línea discontinua o un mueble tienen las caras rotas (50–80 %) y son más angostos. Se descartan.
- **Puertas:** se buscan en la tinta normal y en cualquier marca, porque muchos CAD dibujan el giro en gris muy claro.
- **Elegir lectura:** se mide el área cerrada por la raíz del número de ambientes. Una lectura que solo encuentra el contorno exterior cierra una sola caja y no debe ganar.
- **Plano real Ford Laguna 5 (PL-004):**

  | Etapa | Muros | Puertas |
  |---|---|---|
  | Antes | Solo los rojos de arriba, más texto | 0 |
  | Ahora | 19, con el contorno completo, incluidos los grises de la izquierda y de abajo | 5: las dos hojas de la puerta doble de abajo, la simple de la izquierda, una hoja de la doble de arriba y una falsa |

  - Faltan los muros a 45° de las esquinas.
  - Sobran la línea de eje D–D y el borde de los gabinetes.
- **Efecto en otras muestras:**
  - `9c766…`: mejor contorno y 5 puertas.
  - `2d-site`: contorno más completo, pero bajó de 3 puertas a 1.

## 19. Ejes claros y muros a 45° (2026-11-02)

- **Ejes en línea clara de trazo y punto** (como el D–D magenta): se unen sus trazos entre todas las marcas y se buscan líneas finas largas (25 % o más de la hoja) que se cruzan con otra en su tramo medio. Se borran de las lecturas por forma. Un muro se une en sus extremos o en T; un eje atraviesa.
- **Muros a 45°:** la imagen se gira 45°, los muros diagonales quedan horizontales o verticales, se leen con la misma regla de forma (caras rectas y ancho del muro del plano) y se devuelven a su lugar.
- **Ford PL-004:** ahora sale el edificio completo, con el muro diagonal superior izquierdo y 5 puertas (simple izquierda, las dos hojas de la doble inferior, una de la doble superior y una dudosa abajo a la derecha). La línea de eje desapareció.
- **Falta en Ford:**
  - el muro diagonal inferior derecho, que es más corto;
  - el borde de los gabinetes de celdas, que todavía crea dos franjas falsas (A5 y A6).

## 20. Planta de prueba con verdad conocida (2026-11-02)

`scripts/planta_prueba.py` dibuja una vivienda propia de 14 × 10 m con dormitorio, baño, depósito, pasillo, cocina, estar-comedor y estacionamiento con portón. La genera de tres formas: SVG de presentación (A3, 1:100, capas A-MUROS-30/15/12, A-PUERTAS, A-VENTANAS, A-MOBILIARIO, A-TEXTOS, A-COTAS, A-ROTULO), DXF en cm con las mismas capas, y PNG. Guarda la verdad en `out/planta_prueba/verdad.json`.

- **Verdad:** 11 muros de 30, 15 y 12 cm; 6 puertas; 8 ventanas; 3 huecos (dos vanos y el portón); 7 ambientes.

| Lectura | Puertas | Ventanas | Huecos | Espesores | Ambientes |
|---|---|---|---|---|---|
| DXF | 6/6, anchos exactos (60, 70, 80, 80, 80, 100) | 8/8 | 3/3 | 30, 15 y 12 cm | 6/7 (falta el depósito) |
| PNG | 4/6, todas reales | 7/8 | — | 46, 24 y 19 px (= 30, 15 y 12 cm) | 8, sin m² (no hay escala en la imagen) |

En el PNG faltan las puertas del dormitorio y del depósito.

**Correcciones que salieron de esta prueba:**
- en una capa de muros se aceptan todos los espesores, no solo el principal;
- la bisagra se busca en la cara del muro del que cuelga la puerta, con su propio grosor, no con el del muro exterior;
- los radios de puerta se prueban más finos (120 pasos), porque el arco tiene ±2 px de tolerancia;
- la puerta más chica es 1,8 grosores del muro principal (antes 2,5): con muros de 30 cm, 2,5 dejaba afuera las puertas de 60–70 cm;
- un tramo corto junto a una puerta se mide por su propio grosor.

## 21. Seis plantas de prueba con estilos distintos (2026-11-02)

`scripts/planta_prueba.py` genera p1–p6 en `out/planta_prueba/<id>/`, cada una en SVG A3 1:100, DXF y PNG, con su verdad:

| Planta | Estilo de muro |
|---|---|
| p1 vivienda | Relleno oscuro |
| p2 departamento | Trama a 45° |
| p3 oficinas | Solo contorno (CAD) |
| p4 casa en L | Color terracota |
| p5 local con garaje doble | Gris claro con trama cruzada y contorno rojo |
| p6 la vivienda p1 | Plano azul |

**Puertas detectadas (verdad / DXF / PNG):**

| Planta | Verdad | DXF | PNG |
|---|---|---|---|
| p1 | 6 | 6 | 4 |
| p2 | 4 | 4 | 4 |
| p3 | 9 | 9 | 9 |
| p4 | 4 | 4 | 4 |
| p5 | 4 | 4 | 4 |
| p6 | 6 | 6 | 4 |

- **Ventanas:** el DXF las acierta todas; el PNG, casi todas, salvo p3 (0 de 8).
- **Espesores 30 / 15 / 12 cm:** salen en todas las plantas.

**Aprendido:**
- Un muro dibujado solo con su contorno necesita cerrar huecos del ancho del muro, hasta 45 px para 30 cm a 1,5 px/cm. Se agregaron cierres de 9, 16 y 24 px.
- Ese cierre tapa también las ventanas del muro (p3 queda sin ventanas): falta leer las ventanas antes de cerrar.

## 22. Proyectos de autoría propia (desde 2026-11-02)

Cada sesión de estudio termina con un proyecto propio en `out/proyectos/NN/`, generado por `scripts/proyecto_autor.py`, cada uno más complejo que el anterior. Ya no se regeneran `out_NN`, `index.html` ni `aprendizaje.html`.

**Plantilla de lámina** (indicada por el usuario):
- columna derecha con notas, leyenda y cuadro de superficies, y el rótulo vertical abajo a la derecha;
- plantas arriba, de izquierda a derecha y de nivel bajo a alto, con ejes comunes;
- corte y fachada debajo de su planta, compartiendo los ejes;
- axonometría abajo a la izquierda;
- título y escala debajo de cada vista, alineados a su borde izquierdo.

**Proyecto 01: casa de dos niveles con terraza.** Lámina A1 (A-101) a escala 1:100. Contiene planta baja, planta alta, azotea, corte A-A, fachada sur y axonometría sudeste. Tiene ejes A–D y 1–4, muros de 30/15/12 cm, escalera de 14 alzadas, terraza con baranda, sala de máquinas y cuadro de superficies (163 m² cubiertos).

**Motor sobre sus plantas:**

| Planta | DXF puertas | DXF ventanas | PNG puertas | PNG ventanas |
|---|---|---|---|---|
| PB | 3/3 | 8/8 | 3/3 | 7/8 |
| PA | 4/4 | 5/5 | 3/4 | 4/5 |
| Azotea | 1/1 | — | 1/1 | — |

**Lección del dibujo:** un corte que atraviesa una ventana no borra el muro: queda el antepecho (hasta 0,90 m) y el dintel (desde 2,30 m), con el vidrio entre ambos. Sobre una puerta queda el dintel (desde 2,20 m).

## 23. Proyecto 02: etiquetas, cotas y tablas (2026-11-02)

`scripts/proyecto_02.py` genera dos láminas A1 de una vivienda de dos niveles (12 × 10 m) con cochera, estudio, 3 dormitorios, 2 baños y terraza:
- **A-201 (arquitectura):** plantas con tres cadenas de cotas (vanos, ejes y total), corte A-A, fachada sur y axonometría.
- **A-202 (carpinterías y acabados):** plantas con los códigos de acabado de cada local, tablas de puertas, de ventanas y de materiales.

**Reglas aplicadas:**
- No hay texto genérico: cada puerta (círculo), ventana (hexágono), muro (rectángulo con su tipo M-xx) y local (número, nombre y área; en A-202 también los rombos de acabado) lleva su etiqueta. El texto sale de los parámetros del modelo.
- Las directrices van siempre a 45° con un quiebre horizontal de 2 mm. Un ubicador prueba largos y direcciones hasta encontrar un lugar libre: sin cruzar otras directrices ni pisar etiquetas, muros, escaleras o líneas de cota. Las etiquetas de puerta se colocan primero, en su giro; los locales chicos usan una etiqueta compacta. El programa informa si queda algo sin etiquetar: hoy, nada.
- Las cotas se dibujan a 16–29 mm del edificio, con líneas de referencia cortas en la cadena de vanos. Así queda una banda libre junto a los muros para etiquetas exteriores, como las de las ventanas chicas de baño.
- Las tablas se calculan del modelo (las cantidades se cuentan) y se filtran a lo que aparece en la lámina. Tienen el ancho de la columna derecha, títulos de 3 mm en negrita y datos de 2 mm.

**Motor:** al elegir entre lecturas de una imagen, ahora también cuentan las puertas halladas. Una lectura que cierra ambientes tapando huecos anchos, sin ninguna puerta, no es una buena lectura. Con ese cambio, la planta alta del proyecto 02 como imagen pasó de 0/5 a 5/5 puertas, sin empeorar las demás pruebas.
