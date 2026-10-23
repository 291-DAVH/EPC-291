# Plataforma EPC (resumen en español)

Framework de ingeniería EPC automatizada, armado con plugins (como Lego). Hoy corre dentro de Claude Code; el mismo motor pasará a web (Python + React) y a escritorio.

- `hub/` contiene todos los plugins; `skills/` todas las skills. Los plugins gobiernan: si una skill está duplicada, vale la del plugin y se te avisa antes de producción.
- `../dev-knowledge/` guarda normas, informes de terceros y material de estudio: nunca se versiona ni se sube.
- `../projects/<cliente>/<proyecto>/` separa `workspace/` (editable, interno) de `deliverables/` (lo que recibe el cliente).
- `.svg` nunca se entrega; `.dxf` se edita en el workspace y se entrega una copia sellada.
- Gestión de proyecto: PM² por defecto; el usuario puede elegir PMI u otra metodología.
- Plan completo: `docs/plan/PLAN_FRAMEWORK_EPC.md`. Registro de la migración: `docs/MIGRATION_LOG.md`.
