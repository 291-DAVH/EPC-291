# Changelog

## 0.1.0 - 2026-10-23
- Restructured the legacy folders into one platform: `hub/` (10 plugins), `skills/` (12 skills), `core/workflow`, `methodologies/pm2`, `jurisdictions/AR`, `agents/`.
- Plugins resolve each other from the hub; `vendor/*.plugin` copies removed.
- `sld` 0.1.1: compatible with `iec-symbols` >= 0.4.14 file naming; `cairosvg` optional.
- Study and copyrighted material moved to `dev-knowledge/` (outside git).
- See `docs/MIGRATION_LOG.md` and `docs/MIGRATION_INVENTORY.md`.
