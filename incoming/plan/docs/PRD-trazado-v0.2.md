# PRD: Editor de trazado sobre plano multidisciplina

> Documento de entrada tal como lo entregó el dueño (v0.2, borrador). No se edita: la revisión y las decisiones tomadas están en `REVIEW-PRD-trazado.md`.

**Versión:** 0.2 · **Estado:** borrador

---

## 1. Producto

**Nombre:** Editor de trazado sobre plano multidisciplina

**Descripción:** herramienta tipo Paint para dibujar sobre planos (PDF vectorial, imagen o SVG). El usuario elige en una barra el tipo de elemento que dibuja y coloca elementos puntuales. Cada elemento se guarda con tipo, tag y geometría. A partir de esos datos la herramienta genera listados de longitudes, cantidades, recorridos y cómputos, y un dibujo 2D normalizado (bandejas, portales, cámaras, trincheras) exportable a SVG y DXF.

**Valor central:** el dibujo deja de ser una imagen y pasa a ser una fuente de datos estructurados. El usuario no necesita saber CAD: dibuja trazos simples y el sistema produce el plano de salida.

**Usuarios objetivo:**

- Proyectistas e instaladores de electricidad, sanitaria, gas, climatización y telecomunicaciones.
- Responsables de cómputo y presupuesto de obra.

---

## 2. Problema

- Los listados de cables, cañerías, ductos o redes se arman a mano: se mide sobre el plano y se cargan planillas.
- Cualquier cambio de recorrido obliga a rehacer cómputos, listados y planos.
- La relación entre elementos de la red (qué tramo pertenece a qué línea, qué nodo conecta qué) se pierde o queda implícita.
- Un trazo a mano alzada no declara qué es. Sin intención explícita, la interpretación automática falla.
- Pasar de un croquis a un plano normalizado en DXF es trabajo manual repetitivo.

---

## 3. Principios de diseño

1. Simple como Paint: pocos botones grandes y aprendizaje en minutos.
2. El usuario declara la intención al dibujar; el sistema no adivina.
3. El modelo de datos es la única fuente de verdad. Listados, SVG y DXF se generan desde él y no pueden divergir.
4. Tags únicos y legibles por disciplina y tipo.
5. Modelo genérico con perfiles de disciplina: el núcleo no conoce electricidad ni sanitaria.
6. Primero el flujo básico útil; cálculos, normas y símbolos avanzados después.

---

## 4. Alcance

### Dentro de la versión 1

- Carga de plano base (PDF, imagen, SVG).
- Calibración de escala.
- Dibujo de tramos y colocación de nodos según el perfil activo.
- Tags con correlativo automático y atributos por perfil.
- Definición de líneas como recorrido ordenado.
- Tablas en tiempo real.
- Representación 2D con símbolos básicos por disciplina.
- Exportación a Excel, CSV, PDF y SVG.
- Importación de listados desde Excel o CSV.

### Dentro de la fase 2

- Exportación a DXF con capas, bloques y textos.
- Biblioteca de símbolos completa para la disciplina de prueba.

### Fuera de la versión 1

- Tramos verticales y alturas.
- Capas avanzadas en la interfaz.
- Cálculos hidráulicos, eléctricos o térmicos.
- Validación normativa automática.
- Edición multiusuario en tiempo real.
- Edición bidireccional desde DXF (el DXF es solo salida en v1 y v2).

---

## 5. Conceptos del núcleo

| Concepto | Descripción | Ejemplos |
|---|---|---|
| **Tramo** | Elemento lineal que conecta dos nodos | Cable, caño, bandeja, cañería, ducto, cable de datos |
| **Nodo** | Elemento puntual donde se conectan tramos | Cámara, caja de pase, tablero, válvula, difusor, roseta |
| **Línea** | Secuencia ordenada de tramos y nodos que forma un recorrido completo | Circuito, ramal, línea de extracción, línea de gas, enlace de datos |
| **Contenedor** | Tramo que aloja otros elementos | Bandeja, trinchera, caño multiconductor, ducto de shaft, zanja |

---

## 6. Perfiles de disciplina

Cada disciplina se define en un archivo de configuración. Agregar una disciplina no requiere cambios en el código. Un perfil describe también la **biblioteca de símbolos** con la que se representa cada elemento en 2D (ver sección 8).

### Esquema

```json
{
  "id": "string, identificador único",
  "nombre": "string",
  "tramos": [
    {
      "id": "string",
      "etiqueta": "string",
      "prefijo_tag": "string",
      "atributos": ["string"],
      "simbolo_2d": "id de símbolo en la biblioteca",
      "capa_dxf": "string"
    }
  ],
  "nodos": [
    {
      "id": "string",
      "etiqueta": "string",
      "prefijo_tag": "string",
      "atributos": ["string"],
      "simbolo_2d": "id de símbolo en la biblioteca",
      "capa_dxf": "string"
    }
  ],
  "calculos": ["ids de módulos de cálculo"],
  "normas": ["ids de reglas normativas"],
  "atajos_teclado": { "tecla": "id_elemento" },
  "unidades_salida": "m o mm"
}
```

### Ejemplo: electrica_BT (Instalación eléctrica en baja tensión)

- **Tramos:**
  - Cable (`CA`): sección, material, cantidad de conductores, tensión.
  - Caño / canalización (`CN`): diámetro, material, tipo de instalación.
  - Bandeja (`BN`): ancho, alto, material.
  - Cruce bajo calzada (`CR`): diámetro, profundidad.
- **Nodos:** cámara subterránea (`CM`), caja de pase (`CP`), tablero (`TB`).
- **Cálculos:** longitud, cantidad, llenado de canalización, caída de tensión.
- **Normas:** AEA 90364-7-771.
- **Capas DXF de ejemplo:** `ELEC-CABLE`, `ELEC-CANAL`, `ELEC-BANDEJA`, `ELEC-CAMARA`, `ELEC-TAG`.

### Ejemplo: sanitaria_cloacas (Cloacas)

- **Tramos:** cañería cloacal (`CC`): diámetro, material, pendiente.
- **Nodos:** cámara de inspección (`CI`), boca de registro (`BR`).
- **Cálculos:** longitud, pendiente, caudal, diámetro mínimo.

### Ejemplo: gas_natural (Gas natural)

- **Tramos:** cañería de gas (`GA`): diámetro, material, presión.
- **Nodos:** válvula de corte (`VC`), regulador (`RG`).
- **Cálculos:** longitud, pérdida de carga, caudal.

### Ejemplo: hvac_ductos (Climatización)

- **Tramos:** ducto (`DU`): ancho, alto, material, caudal.
- **Nodos:** difusor (`DF`), plenum (`PL`).
- **Cálculos:** longitud, superficie, pérdida de presión, caudal.

---

## 7. Modelo de datos

| Entidad | Campos | Notas |
|---|---|---|
| **Línea** | tag, disciplina, tipo, recorrido, longitud total, atributos | El recorrido es una lista ordenada de tags; el orden define longitudes acumuladas e inicio y fin |
| **Tramo** | tag, tipo, longitud calculada, nodo inicio, nodo fin, contenedor, atributos, geometría | La geometría se guarda en coordenadas reales (metros), no en píxeles |
| **Contenedor** | tag, tipo, tramo, longitud, elementos alojados | |
| **Nodo** | tag, tipo, ubicación, tramos conectados, atributos | |
| **Plano** | id, archivo base, escala, referencia de cota, disciplina activa | |

**Reglas de consistencia:**

- Un cambio en longitud o tipo de un tramo recalcula las líneas que lo usan.
- Eliminar un nodo avisa de los tramos huérfanos.
- Tags únicos por disciplina y tipo.
- Un tramo debe tener nodo de inicio y de fin antes de contarse en listados o exportarse.

---

## 8. Representación 2D y exportación

### 8.1 Flujo

1. El usuario dibuja tramos y coloca nodos. Cada uno queda en el modelo con su tipo y tag.
2. El generador 2D lee el modelo y, para cada elemento, toma el símbolo definido en la biblioteca del perfil activo.
3. Un tramo se convierte en primitivas gráficas (por ejemplo, dos líneas paralelas para una bandeja con su ancho normalizado). Un nodo se convierte en un símbolo con su tag.
4. Con esas primitivas se generan dos salidas desde la misma fuente:
   - **SVG:** vista para revisar, editar y compartir. Usa una capa por tipo de elemento.
   - **DXF:** archivo para programas CAD. Usa capas, bloques reutilizables y textos reales.

### 8.2 Biblioteca de símbolos

- Cada símbolo tiene: id, disciplina, dimensiones de referencia, primitivas gráficas, punto de inserción y punto de conexión.
- Los símbolos se definen en un archivo propio y se referencian desde el perfil. No se codifican en la aplicación.
- Un símbolo nuevo se agrega como archivo, sin cambios en el núcleo.
- La biblioteca de cada disciplina debe contemplar la simbología de la empresa o la norma de dibujo que se use.

### 8.3 Reglas de exportación

- **Unidades:** el DXF se escribe en metros o milímetros reales, según `unidades_salida` del perfil. No se usan píxeles.
- **Escala:** el plano de salida se genera a escala real. La escala de impresión se resuelve en la hoja, no en el modelo.
- **Capas:** una capa por tipo de elemento, definida en el perfil.
- **Bloques:** los símbolos se insertan como bloques DXF reutilizables, con atributos para el tag.
- **Textos:** tags y valores como texto real, editable en el programa CAD.

### 8.4 Principio de generación

El DXF se genera desde el modelo con una librería de escritura DXF (por ejemplo, `ezdxf` en Python). No se convierte desde el SVG. La conversión SVG → DXF pierde capas, bloques, textos y escalas, y produciría dos fuentes que podrían divergir.

---

## 9. Requisitos funcionales

| ID | Requisito | Descripción | Prioridad |
|---|---|---|---|
| RF-01 | Cargar plano base | Importar PDF, imagen o SVG como fondo | Alta |
| RF-02 | Calibrar escala | Marcar dos puntos sobre una cota conocida e ingresar la distancia real | Alta |
| RF-03 | Seleccionar disciplina activa | El perfil activo define los botones disponibles | Alta |
| RF-04 | Dibujar tramos | Polilíneas del tipo elegido, con snap ortogonal opcional | Alta |
| RF-05 | Colocar nodos | Elementos puntuales con ícono normalizado | Alta |
| RF-06 | Asignar tag | Popup opcional con tag propuesto y atributos del perfil; se puede saltar con Enter | Alta |
| RF-07 | Definir líneas | Recorrido ordenado por selección en secuencia o por origen y destino | Alta |
| RF-08 | Tablas en tiempo real | Listados de líneas, tramos, contenedores y nodos que se actualizan al editar | Alta |
| RF-09 | Editar y borrar | Seleccionar, mover, borrar; deshacer y rehacer | Alta |
| RF-10 | Resaltar línea | Al seleccionar una línea se resalta su recorrido completo | Media |
| RF-11 | Importar listados | Cargar líneas y atributos desde Excel o CSV | Media |
| RF-12 | Copiar y pegar | Duplicar tramos o nodos repetidos, con tags nuevos | Media |
| RF-13 | Capas | Agrupar elementos y mostrar u ocultar capas en la interfaz | Baja |
| RF-14 | Historial por tag | Registrar quién modificó qué y cuándo | Baja |
| RF-15 | Exportar datos | Tablas a Excel y CSV; datos a JSON | Alta |
| RF-16 | Generar representación 2D | Convertir tramos y nodos en primitivas gráficas según la biblioteca de símbolos del perfil | Alta |
| RF-17 | Exportar SVG | Plano 2D con una capa por tipo de elemento, a escala real | Alta |
| RF-18 | Exportar PDF | Plano 2D en hoja con escala y rótulo configurables | Media |
| RF-19 | Exportar DXF | Archivo con capas, bloques y textos, en unidades reales | Alta (fase 2) |
| RF-20 | Biblioteca de símbolos | Cargar y editar símbolos desde archivos, sin cambios en el núcleo | Alta |
| RF-21 | Rótulo y cajetín | Insertar cajetín con datos de proyecto en la hoja de salida | Media |

---

## 10. Requisitos no funcionales

| ID | Categoría | Requisito |
|---|---|---|
| RNF-01 | Usabilidad | Un usuario nuevo dibuja su primer tramo y tag en menos de 5 minutos con el tutorial |
| RNF-02 | Precisión | La longitud calculada coincide con la escala calibrada con error menor al 1 % en un tramo de prueba |
| RNF-03 | Rendimiento | Dibujo fluido, sin retardo perceptible, con planos de hasta 500 tramos |
| RNF-04 | Fiabilidad | Guardado automático cada 30 segundos y recuperación tras cierre inesperado |
| RNF-05 | Portabilidad | Perfiles, símbolos y datos exportables en formato abierto (JSON, CSV) |
| RNF-06 | Extensibilidad | Agregar una disciplina o un símbolo mediante archivos, sin cambios en el núcleo |
| RNF-07 | Compatibilidad | El DXF generado se abre sin errores en AutoCAD y en un visor DXF libre |
| RNF-08 | Consistencia | Listados, SVG y DXF salen del mismo modelo; un cambio en el modelo se refleja en las tres salidas |

---

## 11. Stack tecnológico

> **Estado: pendiente de definir por el usuario.** No se asume ninguna tecnología. Completar cada campo con el stack que se maneja.

(Tabla de campos vacía en el original: frontend, backend, persistencia, autenticación, generación 2D, exportación, plano, infraestructura, testing y observabilidad.)

---

## 12. Arquitectura

**Capas:**

1. **Interfaz:** canvas, barra de herramientas, panel de atributos, tablas, vista previa 2D.
2. **Núcleo genérico:** tramos, nodos, líneas, contenedores, tags, geometría, historial.
3. **Perfiles de disciplina:** configuración declarativa, incluida la referencia a símbolos.
4. **Biblioteca de símbolos:** primitivas 2D por disciplina, en archivos independientes.
5. **Generador 2D:** convierte el modelo en primitivas gráficas según perfil y biblioteca.
6. **Módulos de cálculo:** longitud, llenado, caudal, caída de presión, pendiente, etc.
7. **Reglas normativas:** verificaciones asociadas a perfil y norma.
8. **Adaptadores de salida:** Excel, CSV, PDF, SVG, DXF, JSON. Cada uno lee el modelo; ninguno depende de otro.

**Principio:** el núcleo no depende de ninguna disciplina ni de ningún formato de salida. Todas las salidas nacen del mismo modelo.

---

## 13. Flujo de usuario

1. Cargar plano base.
2. Calibrar escala.
3. Seleccionar disciplina activa.
4. Elegir tipo de elemento en la barra y dibujar o colocar.
5. Completar tag y atributos (opcional saltar).
6. Definir líneas como recorridos ordenados.
7. Revisar tablas y vista previa 2D en tiempo real.
8. Exportar: listados, SVG, PDF o DXF.

---

## 14. Métricas de éxito

| Métrica | Objetivo |
|---|---|
| Tiempo hasta primer listado válido | Menor a 30 minutos en un plano real de 1 piso |
| Tiempo hasta primer DXF válido | Menor a 45 minutos en el mismo plano, incluyendo revisión |
| Diferencia contra listado hecho a mano | Menor al 2 % en longitudes totales |
| Tasa de tags duplicados o huérfanos | Menor al 1 % de los elementos |
| Diferencias entre SVG y DXF del mismo modelo | Cero, medido en cantidad y posición de elementos |
| Disciplinas operativas con perfil validado | Al menos 2 en la fase 2 |

---

## 15. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Escala mal calibrada | Longitudes erróneas en listados y en el DXF | Calibración obligatoria con verificación; escala visible |
| Plano escaneado de baja calidad | Fondo difícil de leer | Recomendar PDF vectorial o DWG exportado; ajuste de contraste |
| Tags inconsistentes | Listados desordenados | Correlativo automático y validación de duplicados |
| Cambios de nivel no capturados | Longitudes subestimadas | Tramo vertical con cota, en versión posterior |
| Perfiles o símbolos mal definidos | Atributos faltantes o dibujo incorrecto | Validación de esquema al cargar; vista previa de cada símbolo |
| Simbología distinta a la de la empresa | Plano rechazado por el cliente | Biblioteca editable por la empresa; validación con un plano de referencia |
| DXF que no abre bien en el programa destino | Retrabajo | Pruebas de apertura en AutoCAD y visor libre (RNF-07) |
| Pérdida de datos | Retrabajo | Guardado automático y sincronización en la versión final |

---

## 16. Preguntas abiertas

- ¿Quién carga los atributos técnicos: el dibujo, una lista importada o ambos?
- ¿El recorrido se define dibujando o asignando desde una tabla?
- ¿Las salidas tienen formato fijo (plantilla de empresa) o libre?
- ¿La simbología sigue alguna norma de dibujo en particular, o es propia de cada empresa?
- ¿Qué versión de AutoCAD u otro programa CAD se usa en el destino? Impacta en la versión de DXF a generar.
- ¿Hace falta trabajo multiusuario desde el inicio?
- ¿Qué disciplinas entran primero y en qué orden?
- ¿Uso individual u organizacional? Impacta en autenticación y permisos.

---

## 17. Fases

| Fase | Nombre | Alcance | Criterio de salida |
|---|---|---|---|
| 1 | Núcleo y prototipo | Calibrar escala, tramos y nodos genéricos, tags, goma, deshacer, tablas básicas, un perfil de prueba, símbolos 2D básicos, exportación SVG | Flujo validado con un plano real y SVG revisado por el usuario |
| 2 | Datos, símbolos y DXF | Modelo completo, líneas como recorrido ordenado, importación Excel/CSV, alertas, biblioteca de símbolos de la disciplina de prueba, exportación DXF con capas y bloques | DXF abierto sin errores en el programa destino; listados confiables en al menos 2 disciplinas |
| 3 | Optimización | Snap avanzado, copiar y pegar, asignación por origen y destino, capas, historial, plantillas de planta, cajetín | Reducción medida del tiempo de carga |
| 4 | Cálculo y normas | Módulos de cálculo, reglas normativas verificables, exportación a software de cálculo | Verificación integrada con el proyecto |
