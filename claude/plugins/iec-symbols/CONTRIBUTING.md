# Cómo contribuir

Gracias por colaborar con la biblioteca de símbolos IEC 60617.

## Estructura

| Carpeta | Contenido |
|---|---|
| `src/sld-lv-symbol/` | Unifilares de baja tensión (SVG + DXF) |
| `src/sld-mv-symbol/` | Unifilares de media tensión (SVG + DXF) |
| `src/mld-lv-symbol/` | Multifilares de baja tensión (SVG + DXF) |
| `src/mld-mv-symbol/` | Multifilares de media tensión (pendiente) |
| `src/ssd-mv-symbol/` | Biblioteca adicional de media tensión |
| `src/catalogo_simbolos.xlsx` | Catálogo Excel único (ordenado alfabéticamente por símbolo), generado con `tools/build_cat9.py`. Es el único `catalogo_simbolos.xlsx` del repo |
| `src/{sld-lv,sld-mv,mld-lv,mld-mv}-symbol/_catalog.json` | Un catálogo JSON por biblioteca (4 en total) |
| `plugin/` | Manifiesto del plugin y paquete `.plugin` |
| `assets/` | Documento de referencia IEC 60617 |
| `tools/` | Scripts de build (ver abajo) |

## Herramientas (`tools/`)

| Script | Uso |
|---|---|
| `svg2dxf_all.py <svg> <dxf>` | Genera el DXF de un símbolo a partir de su SVG |
| `build_pkg.py <plugin_dir> <catalogo_simbolos.xlsx> <salida.plugin>` | Empaqueta el plugin (usar rutas absolutas) |
| `build_cat9.py <project\|root> <salida.xlsx>` | Genera el catálogo Excel con escala uniforme (4 px/mm). Requiere `cairosvg` y `openpyxl` |

Ejemplos:

```
python tools/svg2dxf_all.py src/mld-lv-symbol/291_E_LV_MLD_IEC60617_acb_2p.svg src/mld-lv-symbol/291_E_LV_MLD_IEC60617_acb_2p.dxf
python tools/build_pkg.py /abs/path/plugin/iec60617-symbol-generator /abs/path/catalogo_simbolos.xlsx /abs/path/plugin/iec60617-symbol-generator.plugin
python tools/build_cat9.py project src/catalogo_simbolos.xlsx
```

## Reglas de edición

1. **Cada símbolo es un par SVG + DXF con el mismo nombre.** Si cambias uno, regenera el otro.
2. **Los SVG editados a mano no se modifican por script.** Si un SVG fue ajustado manualmente, sólo se regenera su DXF; el SVG queda tal cual.
3. **Cambios en SLD se reflejan en MLD.** Si modificas un símbolo unifilar, ajusta su equivalente multifilar en la misma PR.
4. **Grilla de 2,5 mm.** Proporciones en múltiplos de 2,5 mm; círculos de diámetro 10 mm; paso entre polos MLD de 10 mm.
5. **Textos centrados** dentro de la celda, círculo o caja que les corresponde.
6. **Un rótulo de tipo por símbolo.** No dupliques etiquetas superpuestas.
7. **Mismo tamaño por polo.** Las celdas de un mismo equipo deben tener igual medida en 1p, 2p, 3p y 4p.

## Flujo de trabajo

1. Crea una rama desde `main`: `git checkout -b feat/nombre-corto`.
2. Haz los cambios y verifica que los SVG sean XML válido.
3. Regenera los DXF de los archivos modificados.
4. Regenera los catálogos Excel si cambió alguna imagen.
5. Actualiza `CHANGELOG.md` con la nueva versión. La carpeta de manifiesto del plugin (`plugin/iec60617-symbol-generator/`) es de uso interno y no está versionada; sólo se versiona el paquete `plugin/iec60617-symbol-generator.plugin`.
6. Abre un Pull Request usando la plantilla de `.github/pull_request_template.md`.

## Mensajes de commit

Usa [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/):

- `feat(symbols): ...` nuevo símbolo o nueva funcionalidad
- `fix(mld): ...` corrección en multifilares
- `fix(sld): ...` corrección en unifilares
- `docs: ...` documentación
- `chore(release): x.y.z` cambio de versión

## Versionado

Se usa Versionado Semántico:

- **MAJOR**: cambio que rompe nombres de archivos o parámetros de los símbolos.
- **MINOR**: símbolo nuevo o parámetros nuevos.
- **PATCH**: corrección geométrica o de texto.

## Reportar problemas

Abre un issue con el nombre del símbolo, la versión del plugin y una captura del resultado esperado y del obtenido.
