# migrate

One-off scripts used on 2026-10-23 to restructure the original folders into this repository. They are kept for traceability only: they contain absolute paths of the old machine layout (`E:\plugins\prueba\...`) and are not meant to be run again.

- `migrate_legacy.py`: moved the master PDFs to `dev-knowledge/`, copied plugins/skills/rules into `platform/`, archived the originals in `_legacy/`.
- `generate_project_files.py`: generated READMEs, `DEPENDENCIES.md` and config files from `hub/registry.json`. It is path-relative and can be re-run.
