<div align="center">

<img src="assets/logo.png" alt="aea90364-standard" width="320"/>

# aea90364-standard

</div>

Motor de cálculo de instalaciones de baja tensión según **AEA 90364-7** (771, 770, 701, 722) y **AEA 90909-1**. Se empaqueta como plugin de Claude.

> Estado: borrador. Los cálculos están pendientes de validación del usuario contra el ejemplar oficial de la norma.

## Qué hace

Dado el Excel de un tablero, el motor dimensiona cada circuito: corriente de proyecto, protección, sección del cable, caída de tensión y poder de corte. Entrega un JSON para `sld-generator` y, para el alimentador principal, la Memoria de Cálculo y la Síntesis de Proyecto en Markdown. No genera PDF.

## Cómo se calcula

El cálculo completo, paso a paso, está en la carpeta [`docs/`](docs/00-dimensionado-bt.md):

- [**Dimensionado de cables de baja tensión (BT)**](docs/00-dimensionado-bt.md): visión general y criterio de aceptación.
- [01 · Datos de entrada](docs/01-datos-de-entrada.md): cómo completar el Excel del tablero y de los circuitos.
- [02 · Demanda y corriente de proyecto](docs/02-demanda-y-corriente-de-proyecto.md): cálculo de Ib desde potencia, tensión y factor de potencia.
- [03 · Protección por sobrecarga](docs/03-proteccion-sobrecarga.md): elección de In y coordinación con el cable.
- [04 · Capacidad de conducción](docs/04-capacidad-de-conduccion.md): Iz según aislación, material, método de instalación, agrupamiento y temperatura.
- [05 · Sección y caída de tensión](docs/05-seccion-y-caida-de-tension.md): sección mínima, caída por circuito y acumulada.
- [06 · Cortocircuito y poder de corte](docs/06-cortocircuito-y-poder-de-corte.md): icu y disparo magnético.
- [07 · Verificaciones complementarias](docs/07-verificaciones-complementarias.md): térmica en cortocircuito, contactos indirectos, PE, tableros, armónicos y locales especiales.
- [08 · Salidas](docs/08-salidas.md): JSON, Memoria de Cálculo y Síntesis de Proyecto.
- [09 · Tablas normativas](docs/09-tablas-normativas.md): tablas de la norma incorporadas, su verificación y lo que falta.
- [10 · Reglas de ingeniería](docs/10-reglas-de-ingenieria.md): alturas de tomacorrientes e interruptores, reservas, llenado, circuitos, baños, puesta a tierra, conductores de protección, colores, protección contra choques y sobrecorrientes, en JSON por subgrupo.
- [11 · Pendientes](docs/11-pendientes.md): lo que falta o hay que confirmar, con prioridad y estado.

## Uso

```
python library/calculations/aea_pipeline.py src/input_motor_AEA_V2.xlsx
```

Opciones principales: `-o` (JSON de salida), `--alimentador TAG`, `--margen-iz`, `--eta-motores`, `--temp-c`, `--k-magnetico`. Detalle en [08 · Salidas](docs/08-salidas.md).

Para completar el Excel, use la plantilla `src/input_motor_AEA_V2.xlsx`, explicada en [01 · Datos de entrada](docs/01-datos-de-entrada.md). El original `src/input_for_sld_V1.xlsx` no se modifica.

## Skills

| Skill | Función |
|---|---|
| `feeder-sizing` | Dimensionado paso a paso del alimentador, con formulario de entrada y criterios de caída de 1 %, 3 % y 5 % |
| `electrical-dimensioning` | Flujo completo de dimensionado de la instalación |
| `calculation-memo` | JSON de todos los circuitos y MC del alimentador principal |
| `memo-summary` | SP del alimentador principal |

## Estructura

- `docs/`: descripción paso a paso del cálculo.
- `library/calculations/`: código fuente, datos normativos (`aea_tables.json`), reglas de ingeniería (`rules/`) y pruebas.
- `skills/`: skills de trabajo.
- `plugin/elec-calc-generator/`: carpeta del plugin.
- `plugin/aea90364-standard.plugin`: paquete para instalar.
- `assets/`: normas AEA en PDF (referencia) y logo.
- `src/`: Excel de entrada y salidas generadas.

## Pruebas

```
cd library/calculations
python -m unittest discover -s . -p "test_*.py"
```

## Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md) y el [Changelog](CHANGELOG.md).
