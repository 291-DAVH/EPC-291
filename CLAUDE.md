# EPC-291 — guía para sesiones de Claude

- **Qué es:** plataforma EPC de ingeniería automatizada (engine Python + backend FastAPI + web/consola React + plugins de Claude). Visión y estado: `README.md`, `CHANGELOG.md`, `docs/architecture/decisions/` (ADR).
- **Capa Claude:** plugins, skills y agentes versionados viven en `claude/` (registro: `claude/plugins/registry.json`, regenerar con `python tools/build/epc_build.py registry`). `.claude/` es configuración local ignorada por git.
- **Ramas y release:** `docs/BRANCHING.md`. `main` estable y con tag; `dev` integración; ramas `feature|fix|chore/*` se fusionan con `--no-ff` tras `python tools/ci/run_gate.py` en verde. Nunca se sube a GitHub sin que el dueño lo pida.
- **Quién depende de quién:** `docs/architecture/DEPENDENCIAS.md` (generado del código con `python tools/build/impact_map.py`): qué usa cada motor, quién lo usa y qué se afecta si lo cambias. Consultarlo antes de tocar un motor.
- **Reglas fijas:** una sola fuente de la verdad por dato (ADR-0012); normas/PDF con copyright y `local/` nunca se versionan; el usuario MASTER de desarrollo vive solo en `local/` y nunca llega a `main`; el usuario final no ve formatos internos (JSON, YAML, Python, Markdown); `.svg` no es entregable.
- **Idioma:** se explica al usuario en español; el contenido del producto va en inglés (con i18n es/en en la interfaz).
