# migrate

One-off scripts used on 2026-10-23 to restructure the original folders into this repository. They are kept for traceability only: they contain absolute paths of the old machine layout (`E:\plugins\prueba\...`) and are not meant to be run again.

- `migrate_legacy.py`: moved the master PDFs to `local/dev-knowledge/`, copied plugins/skills/rules into `platform/`, archived the originals in `_legacy/`.
- `generate_project_files.py`: generated the first versions of the READMEs, `DEPENDENCIES.md` and config files from `hub/registry.json`. Those files were later moved to the repository root and `docs/` and are now maintained by hand: **do not re-run it** (it would recreate them under `platform/`).
