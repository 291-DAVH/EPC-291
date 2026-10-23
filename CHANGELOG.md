# Changelog

All notable changes. Format: Keep a Changelog; versions follow `docs/BRANCHING.md` (releases are tagged on `main`).

## [Unreleased]

## [0.2.0] - 2026-10-23
Second release: management, engineering workspace, SLD data entry, deliverable package and the fixes found by running Docker and a clean CI environment.

### Fixed
- **The `knowledge` backend module was never committed:** the `**/knowledge/` ignore rule (meant for study material) also matched `backend/src/epc/modules/knowledge`, so a clean checkout (and v0.1.0 as published) could not import the backend. The module is re-included, the empty `build/` folders of the project skeleton are kept, and a new gate check (`ignored-sources`) fails when a source file is hidden by an ignore rule. Found by running the CI steps in a clean Linux container.
- **Docker:** creating a project failed inside the image (the non-root user cannot rewrite `claude/plugins/registry.json`); a read-only installation now uses the committed registry. Both images build and the compose stack (PostgreSQL 16, Alembic migration, backend, nginx front) runs; project creation and SLD generation with PDF were verified in the container, and the Alembic upgrade/downgrade/upgrade round trip on PostgreSQL passes.

### Changed
- `tools/dev/seed_demo.py` no longer deletes existing demo data: without `--reset` it does nothing; with `--reset` the current folder is moved to `local/projects-demo.bak-<timestamp>` (last two kept) before regenerating, so manual changes are not lost.
- Pre-commit hook: also blocks `.env` files (only `.env.example`) and added lines that look like private keys or GitHub/AWS tokens.
- Historical documents and `tools/migrate` carry a note mapping the old `platform/` paths to the current layout.

### Added
- **Deliverables: PDF and package.** A drawing delivered as DXF now offers its PDF too (same-name file next to it, only formats with `deliver: true` in the policy; SVG is never offered): buttons `.dxf` / `.pdf` per row and `?format=` on the download. New **Download package** button: a ZIP of everything delivered (folder structure kept, `INDICE.csv` with code, revision and SHA-256), named `<project>_Paquete_Rev00.zip`; with several transmittals, one ZIP per issue (`<project>_IFA_TR-001_Rev00.zip`). The revision shown is the one the client sees (`Rev 00`); the internal revision stays in the transmittal. Engine: `epc_drawing.export.pdf` renders a DXF to PDF (ezdxf + matplotlib, white background, page = drawing size); the SLD generation now also produces a PDF per sheet (`drawings/pdf`).
- **SLD data entry:** backend module `sld` and sub-tab *Datos del unifilar* in Engineering (admin/engineer): board, titleblock and circuit table (parent/child, topology, phase, device, cable type) with validation, "load the plugin example", save, and *Generate diagram* which runs the sld generator unchanged in the background and publishes SVG, DXF and calculation JSON into the engineering folders (visible in Files). Titleblock data typed in the form reaches the drawing; no logos are copied. The backend now depends on `epc-drawing`.
- **Design criteria:** sub-tab *Criterios de diseño* inside Engineering (admin/engineer). Catalog of 15 base criteria for AR electrical (`engine/jurisdictions/AR/electrical/design-criteria.json`, not validated against the standards), per-project overrides with origin (client / standard / project), note and change history, reset to base value, and a design criteria report generated in the project language. API under `/api/projects/{id}/engineering/criteria`. The demo seed no longer writes a static criteria document. Calculation and drawing plugins do not read the criteria yet.

## [0.1.0] - 2026-10-23
First release. It gathers the foundation (plugins, rules engine, portal) and the restructuring into backend, frontend, database, infra and management modules.

### Added
- `planning/` area: vision, roadmap, 3 PRDs, 11 epics, 22 stories, sprints, risk register, release notes and templates; `tools/planning/board.py` generates `planning/BOARD.md`.
- `docs/explanation/what-is-epc.md`, `docs/architecture/` (target architecture, structure, migration phases) and ADR-0001 to ADR-0006.
- ADR-0008: CAD stays 2D with ezdxf and shapely; FreeCAD and 3D out of scope. The Rust desktop edition (ADR-0007, EP-012) is **deferred**.
- Planning for the **desktop edition** (Rust/Tauri, cross-platform): ADR-0007 (proposed), EP-012, US-0023 to US-0027, roadmap milestone M5, risk R-009. UI reused from `frontend/`; Python engine kept as a bundled sidecar.
- **Engineering tab:** backend module `engineering` (overview, sandboxed SVG preview, text/table view of CSV, XLSX, Markdown) under the admin-only surface; web **Ingeniería** tab between Plan and Deliverables, visible only to the admin/engineer role (SVG previews with zoom, lists as tables); demo seed generates single-line and multi-line SVG diagrams plus load and cable lists. `.svg` remains internal, never a deliverable.
- **Cleanup:** `platform/` retired. `platform/tools` -> `tools/` (build, dev, hooks, migrate; `check_skill_conflicts.py` into `tools/ci`), `platform/methodologies` -> `management/methodologies`, `platform/core/workflow` -> `management/workflow`, requirements and the virtual environment to the repository root (`.venv`, `.env.demo`, `.env.admin`), build output to `dist/`. A single `.claude/` at the root. Empty `apps/` placeholders and the obsolete `pyproject.toml` removed; the git hook path is now `tools/hooks`.
- **Phase 8, management module:** backend modules `wbs` (EDT with weighted progress roll-up), `schedule` (dates, finish-to-start dependencies, critical path, slack, conflicts, late activities) and `backlog` (internal; BL-nnn items with type, priority, status, estimate, WBS link). JSON schemas `wbs`, `schedule`, `backlog` in `shared/schemas`; empty files in the project skeleton; demo seed generates a consistent plan for the 20 simulated projects (WBS progress equals project progress). Web: read-only **Plan** tab (Gantt with critical path and today marker, WBS tree). Console: **Planning** page (backlog add/move, Gantt, WBS). Customers can read WBS and schedule (`/api/app/...`); writes and the backlog are admin-only. US-0017 done.

### Changed
- **Migration phase 7:** `database/` (Alembic, baseline migration `0001`, SQLite-based migration tests, README on what lives in the database vs project files) and `infra/` (backend and frontend Dockerfiles, nginx, compose with PostgreSQL 16 and an automatic `upgrade head`, `.dockerignore` that keeps `local/` out of images). CI workflow with the gate, a PostgreSQL migration round-trip and image builds; PR template. The gate gained `database` and `infra` checks (20 in total). ADR-0006 accepted.
- **Migration phase 6:** `platform/apps/web` became the `frontend/` npm workspace: `@epc/ui` (API client, i18n, components, theme, shell, shared new-project form), `@epc/web` (customer app, features `portfolio`, `project`, `new-project`) and `@epc/console` (admin app on its own port, features `overview`, `plugins`, `skills`, `rules`, `checker`, `project-files`). Admin pages are no longer part of the customer bundle. New check `tools/ci/check_frontend_boundaries.py`; the gate type-checks and builds both apps.
- **Migration phase 5:** `platform/apps/api` replaced by `backend/` (modular monolith, package `epc`): `core` (config, errors, fsutil) and bounded contexts under `modules/` with `api -> service -> repository -> models` layers and a `public.py` facade each; domain errors mapped to HTTP in `epc.main`. Boundaries enforced by import-linter contracts generated with `tools/ci/gen_importlinter.py` and an AST architecture test; the gate runs both plus the backend tests.
- **Migration phase 2:** private folders moved under a single git-ignored `local/` (`dev-knowledge`, `legacy`, `projects-demo`, `projects`); `platform/schemas` and `platform/i18n` moved to `shared/`; the project skeleton moved to `management/templates/project-skeleton`; code, hook, ignore rules and docs updated.
- **Migration phase 4:** `engine/` created with five Python packages, each with its own `pyproject.toml`, `src/`, `tests/` and README: `epc_calc` (from aea-calc), `epc_rules` (from `platform/core/rules`), `epc_standards` (from standard-ingest), `epc_drawing` (iec-symbols, iram-titleblock, sld, mld) and `epc_documents` (doc-quality, pm2-docs); `platform/jurisdictions` -> `engine/jurisdictions`. Flat scripts became importable packages (sibling imports rewritten, hyphenated modules renamed, subprocess calls use `python -m`), the SLD no longer needs plugin lookup, and plugins became packaging only. A built plugin carries the engine packages it wraps under `lib/` and the plugin hash covers them. Environment-dependent tests are now skipped explicitly; skills use `python -m` commands.
- **Migration phase 3:** `claude/` created. `platform/hub` -> `claude/plugins`, `platform/skills` -> `claude/skills`, `platform/agents` -> `claude/agents`; `claude/marketplace` template plus `epc_build.py marketplace`; plugins are assembled in Claude Code's official layout (with an install line and `dependencies`); agents referenced by plugins are validated and packaged.
- The gate now builds the marketplace and runs `claude plugin validate --strict` on it and on every plugin (12 checks).
- `tools/ci/run_gate.py`: the 10-check test battery run after every phase.
- Repository organization: README, README.es, CHANGELOG, CONTRIBUTING, `.editorconfig`, `.gitattributes`, `.gitignore` and `.env.example` moved from `platform/` to the repository root; all documentation moved from `platform/docs/` to `docs/` (new `docs/README.md` index).
- A single `.gitignore` for the whole repository.

### Foundation (initial work, before the restructuring)
#### Added
- Plugin hub (`platform/hub`): aea-calc 1.6.0, iec-symbols 0.4.16, iram-titleblock 0.5.1, sld 0.1.1, mld 0.1.0 (pending), standard-ingest, intake-analysis, pm2-docs, doc-quality, spec-writer, procurement, equipment-catalog; 14 skills in `platform/skills`.
- Rules engine (`platform/core/rules`) and standards ingestion pipeline (extract, validate, promote).
- FastAPI service (end-user and admin surfaces) and React web app.
- Project template with workspace / deliverables separation; demo seeding of 20 simulated projects.
- Branching policy and pre-commit safety hook.

#### Changed
- Plugins resolve each other from the hub; `vendor/*.plugin` copies removed.
- `sld` 0.1.1 supports `iec-symbols` >= 0.4.14 file naming; `cairosvg` is optional.
- Study and copyrighted material moved to `dev-knowledge/` (outside git).
- See [docs/MIGRATION_LOG.md](docs/MIGRATION_LOG.md) and [docs/MIGRATION_INVENTORY.md](docs/MIGRATION_INVENTORY.md).
