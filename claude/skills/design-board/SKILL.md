---
name: "design-board"
description: "Diseña un tablero BT de punta a punta: los criterios de diseño del proyecto gobiernan el cálculo de los circuitos (caída de tensión, secciones, material, aislación) y ese cálculo alimenta el unifilar (SLD) y el multifilar (MLD) en láminas IRAM (SVG, DXF y PDF)."
---

# design-board

## Contexto de ejecución
- **Invocación:** explícita — cuando el usuario pide dimensionar un tablero y dibujar su unifilar o multifilar, o regenerarlos tras cambiar un criterio de diseño.
- **Orden fijo:** criterios de diseño → cálculo (`epc_calc.aea_pipeline`) → unifilar → multifilar. El cálculo es la única fuente de los números que se dibujan: no se calcula dentro de los generadores de dibujo ni se corrigen a mano los valores del dibujo.
- **Los criterios mandan.** Los límites de caída de tensión (seccionales 1 %, iluminación y tomas 3 %, motores 5 %), las secciones mínimas, el material (cobre o aluminio), la aislación (XLPE o PVC) y la sensibilidad del diferencial salen de los criterios del proyecto. Si el usuario pide cambiar uno (por ejemplo, "el cliente exige 2 % en motores"), se cambia el criterio con su origen y se regenera; no se edita el dibujo.
- **Valores base sin validar.** Los criterios base (`engine/jurisdictions/AR/electrical/design-criteria.json`) son propuestas no validadas contra las normas. Decirlo al usuario antes de emitir.

## Entradas
- **Datos del tablero y circuitos:** `workspace/02-engineering/electrical/PQ-01/src/sld-input.json` (los guarda la pestaña *Datos del unifilar*): tablero (nombre, tensión, sistema, Icc, fp, acometida), circuitos (TAG, descripción, carga y unidad `A|W|kW|MW|VA|kVA|MVA|HP`, destino, padre, topología, fase, longitud, fp, rendimiento, dispositivo, cable) y rótulo (empresa, cliente, proyectado/verificado/validado, escala, revisión).
- **Criterios:** valores base más los cambios del proyecto en `workspace/00-setup/design-criteria.json` (cada cambio con su origen: cliente, norma o decisión de proyecto).
- **Datos de la oficina:** empresa, clientes, personas y logos se cargan una sola vez en *Datos* y completan el rótulo.

## Procedimiento
1. Confirmar con el usuario los datos del tablero y que los criterios sean los que rigen (mostrar los que difieren del valor base).
2. Ejecutar desde la raíz del repositorio (o con `PYTHONPATH` del plugin):
   `python -m epc_drawing.board_design --project <carpeta del proyecto> --out <carpeta de trabajo> --name <TABLERO> --diagrams sld,mld`
   Con archivos sueltos: `--input board.json --criteria criteria.json`.
3. Leer `summary.json` de la carpeta `out/`: avisos del cálculo (sección que no cumple, Icc mínima, etc.) y circuitos que **no cumplen**. No entregar con circuitos que no cumplen sin decirlo.
4. Revisar `SLD_<TABLERO>*.svg` y `MLD_<TABLERO>*.svg` (hojas, columnas, rótulo) y los DXF en CAD.
5. Copiar a `drawings/svg`, `drawings/dxf`, `drawings/pdf` y `calc` del paquete de ingeniería (la aplicación web lo hace sola) y, para entregar, usar el paso *Emitir* (copia sellada del DXF + PDF + transmittal).

## Salidas
- `<TABLERO>_dimensionado.json`: contrato de `aea_export` (In, Ib, Icu, S, ΔU acumulada, dispositivo por circuito).
- `<TABLERO>_dimensionado_detalle.json`: tipo de circuito, límite aplicado, ΔU propia y acumulada, Iz, material, aislación, método, si cumple.
- `<TABLERO>_criterios.json`: criterios que se aplicaron (trazabilidad).
- `SLD_<TABLERO>[_Hn]` y `SLD_<TABLERO>_TABLA`: unifilar y tabla de cálculo (SVG y DXF). `MLD_<TABLERO>[_Hn]`: multifilar (SVG y DXF).
- El SVG es de trabajo y nunca se entrega; se entrega el DXF (copia sellada) y su PDF.

## Reglas
- No modificar `epc_drawing.sld` ni `epc_drawing.mld` para cambiar un número: los números vienen del cálculo.
- Multifilar: paso de 10 mm entre polos, símbolos MLD sin escalar, una barra por conductor (L1 L2 L3 N), cargas monofásicas repartidas entre fases, PE en verde discontinuo y cable externo en rojo. Si falta un símbolo de la biblioteca, avisar y no modificarla sin preguntar.
- Lo pendiente conocido: ver `engine/calc/docs/11-pendientes.md` y las limitaciones de `aea_pipeline` (sin selectividad ni verificación I²t, solo cobre/aluminio en las tablas 771.16).

## Runtime
The code is the `epc_calc` and `epc_drawing` packages (`engine/calc`, `engine/drawing`). In a repository checkout set `PYTHONPATH=engine/calc/src;engine/drawing/src` (`;` is the Windows separator) or run `pip install -e engine/calc -e engine/drawing`; in an installed plugin set `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/lib"`. Run modules with `python -m <module>`.
