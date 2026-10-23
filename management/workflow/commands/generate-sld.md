# Generar SLD — `$ARGUMENTS`

Genera un diagrama unifilar (Single Line Diagram) en SVG. Argumento: `LV` (baja tensión) o `MV` (media tensión). Si no se indica, se infiere de los parámetros del proyecto.

## Antes de generar (puerta de preparación)

Verificar en `deliverables.md` que están `REVIEWED`:
- Cálculo de balance de cargas (potencias por circuito).
- Cálculo de cortocircuito (Icc disponible).
- Cálculo de conductores y protecciones (sección, tipo de protección, curva, poder de corte).

Si alguno no está `REVIEWED`: no generar. Informar cuál paquete falta.

## Paso 1 — Cargar el plugin

Leer:
- `.claude/library/plugins/sld-lv/README.md` (o `sld-mv/README.md` para MT).
- `.claude/library/plugins/sld-lv/_catalog.json` — catálogo de símbolos con ids, puertos de conexión y variables de rótulo.

El `.claudeignore` excluye los `.svg` individuales para no llenar el contexto; el catálogo JSON es la fuente de referencia suficiente.

## Paso 2 — Recopilar los datos del diagrama

De los cálculos `REVIEWED`:

| Dato | Fuente |
|---|---|
| Tensión de servicio, frecuencia, régimen de neutro | `project-information.md` — PAR-001, PAR-002, PAR-003 |
| Potencia instalada y demanda por circuito | Memoria de balance de cargas |
| Icc en cada barra | Memoria de cortocircuito |
| Sección, tipo y longitud de cada conductor | Memoria de conductores |
| Tipo de protección, calibre, curva, poder de corte | Memoria de protecciones |
| Equipos principales (transformador, generador, UPS, ATS) | `engineering-standards.md`, datasheets |

## Paso 3 — Seleccionar símbolos del catálogo

Para cada elemento del diagrama, buscar en `_catalog.json` el símbolo por etiqueta (`tags`) o nombre (`name_es`). Ejemplos frecuentes:

| Elemento | id en catálogo (LV) |
|---|---|
| Interruptor termomagnético | `lv_mcb`, `lv_mccb` |
| Diferencial | `lv_rcd`, `lv_rcbo` |
| Interruptor de caja moldeada | `lv_mccb_basic` |
| Variador de frecuencia | `lv_vfd` |
| Transformador | `lv_transformer` |
| Barra colectora | `lv_busbar` |
| Medidor de energía | `lv_energy_meter_kwh` |
| ATS | `lv_ats` |
| Generador | `lv_generator` |

## Paso 4 — Construir el SVG

Convenciones IRAM que rigen (del README):
- **Unidad**: 1 unidad SVG = 1 mm.
- **Retícula**: puertos en múltiplos de 2,5 mm.
- **Grosores**: símbolos y conductores 0,25 mm; barras 0,5 mm; bordes de rellenos 0,18 mm.
- **Texto**: h = 2,5 mm (tipo de equipo, datos, polos); fuente osifont / ISOCPEUR / DejaVu Sans.
- **Colores**: azul `#0000ff` conductores y aparamenta; rojo `#ff0000` cables externos; verde `#139b48` PE; gris `#dcdcdc` contorno de celda.
- **Referencia `<use>`**:
  ```xml
  <use href="#lv_mcb" x="{X + vb.x}" y="{Y + vb.y}" width="{vb.w}" height="{vb.h}"/>
  ```
  donde `(X, Y)` es el puerto superior del símbolo y `vb` es el viewBox del catálogo.

Sustituir las variables de rótulo (`{tag}`, `{calibre}`, `{curva}`, etc.) con los datos recopilados en el Paso 2. Eliminar el `<text>` si no hay dato disponible (no dejar `{placeholder}` sin reemplazar).

## Paso 5 — Verificar y guardar

Verificar:
- Cada conductor llega a un puerto válido (coordenada coincide con el puerto del catálogo).
- No quedan `{placeholder}` sin reemplazar.
- Las barras tienen el Icc y la tensión anotados.
- El título del diagrama incluye: código del documento, revisión, proyecto, fecha.

Guardar en `02-engineering/XX_ELECTRICAL/` (o la carpeta de la disciplina correspondiente) con el nombre:
```
[SIGLA]-E-DG-[nnn]_Rev[00.0.IC].svg
```

Proponer la fila correspondiente en `drawing-status.md` con estado `CAD_INPUT` y anotar en `deliverables.md`.

## Paso 6 — Exportación DXF (siempre disponible)

Cuando el usuario pide `skill export dxf`, `generate dxf`, `exportar dxf` o `generar DXF`, o cuando el estado del paquete llega a `ENTREGABLE_AL_CLIENTE`:

```
python -B .claude/library/core/skill_learn.py create-electrical-line-diagram export dxf <ruta_salida.dxf>
```

- Si hay plantilla en `knowledge/dxf/`: se usa como base del layout DXF.
- Si no hay plantilla: se genera un DXF mínimo con el contenido del SVG convertido a polylines/MTEXT.
- Capas: `SIMBOLOS` (azul), `CABLES_EXTERNOS` (rojo), `PE` (verde), `TEXTOS` (negro), `MARCO` (negro).
- Unidades: mm (igual que el SVG IRAM).

## Paso 7 — Trigger automático: estado ENTREGABLE_AL_CLIENTE

Cuando el estado del paquete activo pasa a `ENTREGABLE_AL_CLIENTE` (vía `send-to-review.py`, `release-documents.py` o manualmente), **sin esperar confirmación del usuario**, generar automáticamente los tres formatos:

| Formato | Acción |
|---|---|
| SVG | Ya existe en `02-engineering/`; verificar que es el vigente. |
| PDF | `cairosvg [archivo].svg -o [archivo].pdf` |
| DXF | `python -B .claude/library/core/skill_learn.py create-electrical-line-diagram export dxf [archivo].dxf` |

Registrar los tres archivos en `attached_outputs` y en la hoja de revisión del paquete.
Si falla un formato, registrar el error pero no bloquear los demás.

## Paso 8 — Siguiente paso

El SVG es un **insumo de dibujo** (`_DIN_`): el usuario lo revisa, abre AutoCAD/Revit y dibuja el plano definitivo. Informar al usuario con:
```
SLD generado: [ruta_svg]
Exportar a DXF: skill export dxf  (disponible en cualquier momento)
Estado ENTREGABLE_AL_CLIENTE → genera SVG + PDF + DXF automáticamente.
Próximo paso: revisar el SVG, transferir a CAD y actualizar drawing-status.md → DRAWN.
```
