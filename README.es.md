<div align="center">

<img src="assets/logo.png" alt="EPC-291" width="360"/>

# EPC-291

**Ingeniería EPC automatizada, armada con plugins.**
Cálculos, planos, documentos y reglas basadas en normas para proyectos de ingeniería, con una aplicación web para clientes y una consola técnica para ingenieros.

[![Versión](https://img.shields.io/badge/versi%C3%B3n-0.3.0-1f6feb?style=for-the-badge)](CHANGELOG.md)
[![Batería](https://img.shields.io/badge/bater%C3%ADa%20de%20pruebas-21%20controles-2ea44f?style=for-the-badge)](tools/ci/run_gate.py)
[![Python](https://img.shields.io/badge/python-3.12-3776ab?style=for-the-badge)](backend/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?style=for-the-badge)](backend/)
[![React](https://img.shields.io/badge/web-React%20%2B%20TypeScript-0ea5e9?style=for-the-badge)](frontend/)
[![PostgreSQL](https://img.shields.io/badge/base%20de%20datos-PostgreSQL-336791?style=for-the-badge)](database/)
[![Plugins](https://img.shields.io/badge/plugins-13-f0abfc?style=for-the-badge)](claude/plugins/registry.json)
[![Argentina](https://img.shields.io/badge/jurisdicci%C3%B3n-AR-64748b?style=for-the-badge)](engine/jurisdictions/)

[Contribuir](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Arquitectura](docs/architecture/README.md) · [Tablero de planificación](planning/BOARD.md) · [Documentación](docs/README.md)

English: [README.md](README.md)

</div>

---

## ✨ Qué es

Una plataforma EPC (Ingeniería, Compras y Construcción) armada como Lego: plugins pequeños que Claude Code ejecuta hoy, sobre un único motor de ingeniería que también servirá a una aplicación web y a una de escritorio.

- **Motor de ingeniería** — paquetes Python puros de cálculo, dibujo, documentos, reglas y normas, sin depender de la web ni de Claude.
- **Capa de Claude** — plugins (solo empaquetado), skills y agentes que envuelven el motor. Los plugins gobiernan sus skills.
- **Producto** — backend FastAPI modular, aplicación React para clientes y una consola aparte para administradores.
- **Gestión** — los proyectos siguen PM² por defecto (PMI u otra a elección), con EDT, cronograma con ruta crítica y backlog interno.

El cliente ve solo proyectos, entregables, datos de entrada, requisitos, informes y el plan del proyecto. Plugins, skills, reglas y archivos internos existen únicamente para el rol administrador.

## 🧭 Qué incluye

| Área | Carpeta | Contenido | Estado |
|---|---|---|---|
| Motor de ingeniería | `engine/` | calc, rules, standards, drawing, documents + paquetes por país | ✅ |
| Capa de Claude | `claude/` | 13 plugins, 15 skills, agentes, marketplace | ✅ |
| Backend | `backend/` | 11 módulos con límites verificados (import-linter) | ✅ |
| Frontend | `frontend/` | `web` (cliente), `console` (admin), `packages/ui` | ✅ |
| Base de datos | `database/` | Base de Alembic: organizaciones, usuarios, proyectos, entregables, registro | ✅ |
| Infraestructura | `infra/` | Docker, compose con PostgreSQL, flujo de CI | ✅ |
| Gestión de proyectos | `management/` | esqueleto de proyecto, metodologías | ✅ |
| Planificación del software | `planning/` | visión, PRD, backlog, sprints, tablero (no se distribuye) | ✅ |
| Autenticación, organizaciones, facturación | — | planificado (US-0018) | 🚧 |
| Versión de escritorio (Rust/Tauri) | `desktop/` | pospuesta (ADR-0007) | ⏸️ |
| Media tensión, HVAC, incendio, civil | — | después de baja tensión | 🚧 |

Argentina es la primera jurisdicción (AEA 90364, IRAM); otros países se suman como paquetes por país con su propio `rules.json` por norma.

## 🚀 Uso rápido (Windows)

```bash
# Clonar y activar el hook de seguridad
git clone https://github.com/291-DAVH/EPC-291.git
cd EPC-291
git config core.hooksPath tools/hooks

# Python environment (desde la raíz del repositorio)
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt -r database/requirements.txt import-linter
.venv\Scripts\python -m pip install -e engine/calc -e engine/rules -e engine/standards -e engine/drawing -e engine/documents -e "backend[dev]"

# Batería de pruebas (21 controles, antes de integrar cualquier cambio)
.venv\Scripts\python tools\ci\run_gate.py
```

Correr la aplicación con 20 proyectos simulados (dos terminales):

```bash
# 1) datos de demo y API (copia .env.example a .env.demo y pon EPC_PROJECTS=<repo>/local/projects-demo)
.venv\Scripts\python tools\dev\seed_demo.py          # primera vez; después hace falta --reset (guarda una copia de tus cambios manuales)
.venv\Scripts\python -m uvicorn epc.main:app --app-dir backend\src --port 8000 --env-file .env.demo

# 2) aplicación web (clientes) en :5173, consola (admin) en :5174
cd frontend && npm install && npm run dev:web        # npm run dev:console para la consola
```

`EPC_ROLE=admin` habilita la API técnica y la consola. Stack completo con PostgreSQL: ver [infra/README.md](infra/README.md).

## 🗂️ Estructura

```
EPC-291/
├─ assets/        logo
├─ engine/        calc/ rules/ standards/ drawing/ documents/ jurisdictions/   (Python puro)
├─ claude/        plugins/ skills/ agents/ marketplace/                        (capa de Claude Code)
├─ backend/       src/epc/{core, modules/*}   tests/   .importlinter           (FastAPI)
├─ frontend/      web/ console/ packages/ui                                    (workspace React)
├─ database/      migrations/ (Alembic)   tests/
├─ infra/         docker/ compose/        (+ .github/workflows/ci.yml)
├─ management/    templates/project-skeleton: workspace (editable) + deliverables (para el cliente)
├─ shared/        schemas/ (JSON Schema)   i18n/
├─ planning/      planificación del software durante el desarrollo
├─ docs/          arquitectura, ADR, explicaciones, política de ramas
├─ tools/         ci/ (batería de pruebas), build/ (registro de plugins, empaquetado), dev/ (semilla de demo), hooks/, planning/
├─ .claude/       configuración de Claude Code para desarrollar este repositorio
└─ local/         IGNORADA POR GIT: dev-knowledge, legacy, proyectos demo y reales
```

## 🔌 Plugins

| Plugin | Versión | Tipo | Requiere |
|---|---|---|---|
| `aea-calc` | 1.6.1 | cálculo | — |
| `iec-symbols` | 0.4.17 | conocimiento | — |
| `iram-titleblock` | 0.5.2 | generador | — |
| `sld` | 0.1.2 | generador | aea-calc, iec-symbols, iram-titleblock |
| `mld` | 0.2.0 | generador | aea-calc, sld, iram-titleblock, iec-symbols |
| `board-design` | 0.1.0 | flujo | aea-calc, sld, mld, iec-symbols, iram-titleblock |
| `standard-ingest` | 0.1.0 | flujo | — |
| `intake-analysis` | 0.1.0 | flujo | — |
| `pm2-docs` | 0.1.0 | flujo | doc-quality |
| `doc-quality` | 0.1.0 | flujo | — |
| `spec-writer` | 0.1.0 | flujo | doc-quality |
| `procurement` | 0.1.0 | conector | equipment-catalog |
| `equipment-catalog` | 0.1.0 | conocimiento | — |

La fuente de verdad es `claude/plugins/registry.json` (generado).

## 🛠️ Cómo se trabaja

1. `main` es estable, `dev` integra, el trabajo va en `feature/*`, `fix/*` y `chore/*`, y se une con `--no-ff` ([docs/BRANCHING.md](docs/BRANCHING.md)).
2. La batería de pruebas debe estar en verde antes de integrar.
3. Los plugins gobiernan las skills: una skill duplicada se resuelve con la copia del plugin y avisa (error en builds de producción).
4. El `.svg` es solo interno; el `.dxf` se edita en el workspace y se entrega una copia sellada.
5. Los PDF con derechos de autor y todo lo de `local/dev-knowledge/` nunca entran al repositorio (reglas de ignore y hook de pre-commit).
6. El contenido del producto está en inglés; Claude le explica al usuario en español.

## 📚 Documentación

| Documento | Contenido |
|---|---|
| [docs/explanation/what-is-epc.md](docs/explanation/what-is-epc.md) | Qué es un EPC y por qué la estructura es así |
| [docs/architecture/](docs/architecture/README.md) | Arquitectura objetivo, ADR, fases de migración |
| [planning/README.md](planning/README.md) | Visión, PRD, backlog, sprints, [tablero](planning/BOARD.md) |
| [docs/USER_DATA_MODEL.md](docs/USER_DATA_MODEL.md) | Qué ve el cliente y cómo los datos de entrada se vuelven requisitos |
| [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) | Python, herramientas del sistema y grafo de plugins |
| [CHANGELOG.md](CHANGELOG.md) · [CONTRIBUTING.md](CONTRIBUTING.md) | Cambios y cómo contribuir |

## 🤝 Contribuir

Lee [CONTRIBUTING.md](CONTRIBUTING.md), abre una rama desde `dev`, corre la batería de pruebas y envía un Pull Request con la [plantilla](.github/pull_request_template.md).

## 📜 Estado y licencia

Versión 0.3.0. Las tablas de cálculo y las reglas de normas están pendientes de validación contra los documentos oficiales (`engine/calc/docs/11-pendientes.md`). Todavía no se eligió una licencia: todos los derechos reservados hasta que el titular decida.

<div align="center">

<sub>Hecho con ⚡ para ingenieros que diseñan instalaciones.</sub>

</div>
