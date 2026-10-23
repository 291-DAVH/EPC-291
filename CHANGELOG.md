# Changelog

All notable changes. Format: Keep a Changelog; versions follow `docs/BRANCHING.md` (releases are tagged on `main`).

## [Unreleased] (dev)
### Changed
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
