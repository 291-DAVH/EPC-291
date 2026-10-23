# Changelog

All notable changes. Format: Keep a Changelog; versions follow `docs/BRANCHING.md` (releases are tagged on `main`).

## [Unreleased] (dev)
### Added
- `planning/` area: vision, roadmap, 3 PRDs, 11 epics, 22 stories, sprints, risk register, release notes and templates; `tools/planning/board.py` generates `planning/BOARD.md`.
- `docs/explanation/what-is-epc.md`, `docs/architecture/` (target architecture, structure, migration phases) and ADR-0001 to ADR-0006.

### Changed
- **Migration phase 5:** `platform/apps/api` replaced by `backend/` (modular monolith, package `epc`): `core` (config, errors, fsutil) and bounded contexts under `modules/` with `api -> service -> repository -> models` layers and a `public.py` facade each; domain errors mapped to HTTP in `epc.main`. Boundaries enforced by import-linter contracts generated with `tools/ci/gen_importlinter.py` and an AST architecture test; the gate runs both plus the backend tests.
- **Migration phase 2:** private folders moved under a single git-ignored `local/` (`dev-knowledge`, `legacy`, `projects-demo`, `projects`); `platform/schemas` and `platform/i18n` moved to `shared/`; the project skeleton moved to `management/templates/project-skeleton`; code, hook, ignore rules and docs updated.
- **Migration phase 4:** `engine/` created with five Python packages, each with its own `pyproject.toml`, `src/`, `tests/` and README: `epc_calc` (from aea-calc), `epc_rules` (from `platform/core/rules`), `epc_standards` (from standard-ingest), `epc_drawing` (iec-symbols, iram-titleblock, sld, mld) and `epc_documents` (doc-quality, pm2-docs); `platform/jurisdictions` -> `engine/jurisdictions`. Flat scripts became importable packages (sibling imports rewritten, hyphenated modules renamed, subprocess calls use `python -m`), the SLD no longer needs plugin lookup, and plugins became packaging only. A built plugin carries the engine packages it wraps under `lib/` and the plugin hash covers them. Environment-dependent tests are now skipped explicitly; skills use `python -m` commands.
- **Migration phase 3:** `claude/` created. `platform/hub` -> `claude/plugins`, `platform/skills` -> `claude/skills`, `platform/agents` -> `claude/agents`; `claude/marketplace` template plus `epc_build.py marketplace`; plugins are assembled in Claude Code's official layout (with an install line and `dependencies`); agents referenced by plugins are validated and packaged.
- The gate now builds the marketplace and runs `claude plugin validate --strict` on it and on every plugin (12 checks).
- `tools/ci/run_gate.py`: the 10-check test battery run after every phase.
- Repository organization: README, README.es, CHANGELOG, CONTRIBUTING, `.editorconfig`, `.gitattributes`, `.gitignore` and `.env.example` moved from `platform/` to the repository root; all documentation moved from `platform/docs/` to `docs/` (new `docs/README.md` index).
- A single `.gitignore` for the whole repository.

## [0.1.0] - 2026-10-23 (draft)
### Added
- Plugin hub (`platform/hub`): aea-calc 1.6.0, iec-symbols 0.4.16, iram-titleblock 0.5.1, sld 0.1.1, mld 0.1.0 (pending), standard-ingest, intake-analysis, pm2-docs, doc-quality, spec-writer, procurement, equipment-catalog; 14 skills in `platform/skills`.
- Rules engine (`platform/core/rules`) and standards ingestion pipeline (extract, validate, promote).
- FastAPI service (end-user and admin surfaces) and React web app.
- Project template with workspace / deliverables separation; demo seeding of 20 simulated projects.
- Branching policy and pre-commit safety hook.

### Changed
- Plugins resolve each other from the hub; `vendor/*.plugin` copies removed.
- `sld` 0.1.1 supports `iec-symbols` >= 0.4.14 file naming; `cairosvg` is optional.
- Study and copyrighted material moved to `dev-knowledge/` (outside git).
- See [docs/MIGRATION_LOG.md](docs/MIGRATION_LOG.md) and [docs/MIGRATION_INVENTORY.md](docs/MIGRATION_INVENTORY.md).
