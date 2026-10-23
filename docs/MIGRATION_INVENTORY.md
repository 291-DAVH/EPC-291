# Migration inventory (read-only analysis, nothing moved)

> **Historical record.** Paths written as `platform/...` or `\platform\...` describe the layout during the migration. Where things live now:
> `platform/hub` -> `claude/plugins` · `platform/skills` -> `claude/skills` · `platform/agents` -> `claude/agents` · `platform/core/rules` -> `engine/rules` ·
> `platform/core/workflow` -> `management/workflow` · `platform/methodologies` -> `management/methodologies` · `platform/jurisdictions` -> `engine/jurisdictions` ·
> `platform/schemas`, `platform/i18n` -> `shared/` · `platform/tools` -> `tools/` · `platform/apps/api` -> `backend/` · `platform/apps/web` -> `frontend/` ·
> `dev-knowledge`, `_legacy`, `projects*` -> `local/`. The `platform/` folder no longer exists (see `docs/architecture/target-structure.md`).

Scan date: 2026-10-23. Method: MD5 per file + `plugin.json` versions + dates. Every "keep" below is a proposal pending user confirmation.

## A. Plugins → `platform/hub/`

| Hub id | KEEP (single source) | Version | DISCARD after confirmation (duplicates / older) |
|---|---|---|---|
| `aea-calc` | `elec-calc-generator/plugin/elec-calc-generator/` (+ its `docs/`) | 1.6.0 | `elec-calc-generator/skills/` (7 files identical), `elec-calc-generator/library/calculations/` (70 files identical to `plugin/.../scripts`), `elec-calc-generator/docs/` (12 identical), root `aea90364-standard.plugin` (v1.5.0, older), `plugin/aea90364-standard.plugin` (build artifact, regenerate), `sld-generator/vendor/elec-calc-generator.plugin` (v0.1.0), Template `.claude/library/plugins/calculations/` (older, Oct 13-14, lacks all `aea_*` modules) |
| `iec-symbols` | `291_E_IEC60617_Symbols_Generator/plugin/iec60617-symbol-generator/` + `src/` library | 0.4.16 | `sld-generator/vendor/iec60617-symbol-generator.plugin` (v0.3.0, 15 MB), Template `library/plugins/{sld-lv,sld-mv,mld-lv,mld-mv}` (older), `mld-generator/assets/mld-lv,mld-mv` (78 files identical to Template copy, older) |
| `iram-titleblock` | `291_G_IRAM_Custom_TitleBlocks_Generator/plugin/iram-titleblock-plugin/` | 0.5.1 | `mld-generator/vendor/iram-titleblock-plugin.plugin` (v0.2.1), `sld-generator/vendor/iram-titleblock-plugin.plugin` (v0.3.0), Template `library/plugins/laminas-iram` (different layout, 5 files, older) |
| `sld` | `sld-generator/plugin/sld-generator/` + `src/` | 0.1.0 | `sld-generator/vendor/` (3 .plugin, 14.9 MB), Template skill `create-electrical-line-diagram` (older than `sld-generator` skill) |
| `mld` | `mld-generator/plugin/mld-generator/` + `.claude-plugin` | 0.1.0 (pending) | `mld-generator/vendor/` (2 .plugin, older), Template skill `convert-sld-to-mld` (17 of 18 files identical; the `mld-generator` copy is newer) |

### Template content with no standalone source (becomes new hub plugins — proposal)
| Source in `00-Template-Claude/.claude/` | Proposed hub id |
|---|---|
| skills `create-pm2-document`, `library/plugins/management` (PM² templates), rules M8/M10 | `pm2-docs` + `methodologies/pm2` |
| `library/plugins/calculations/` extras not in aea-calc: `document_verifier`, `input_converter`, `charter_exporter`, `ccpm`, canvas templates and their tests (19 files only in the Template) | `doc-quality` (verifiers/converters) and `pm2-docs` |
| skill `generar-pliego` (without its PDFs) | `spec-writer` |
| skill `get-cotizacion` | `procurement` |
| skills `memoria-calculos`, `sintesis-memoria` | already covered by `aea-calc` skills `calculation-memo` / `memo-summary` — confirm before dropping |
| skills `generate-laminas-iram`, `generate-electrical-symbol` | covered by `iram-titleblock` / `iec-symbols` — confirm |
| `library/plugins/standards`, `equipment` (5 / 4 files) | review: probably `jurisdictions/AR` and `equipment-catalog` |

### Not plugins
- `image-a-flag-svg/` (6 SVG logos: Ford client, EnergySapiens provider): sample tenant branding → `projects/_template` or tenant branding assets, not the hub.
- `sld-generator/test` and `test_a3` (outputs of A1 vs A3 runs, 4 files equal, 8 differ): candidate seeds for `platform/tests/golden/`.
- `00-Template-Claude/.project/_BACKUP_pre-optimizacion_2026-10-12.tgz` (0.8 MB): internal backup → `dev-knowledge/notes/` or delete.
- `__pycache__`, `.plugin` build artifacts: regenerate, do not keep.

## B. PDFs → `dev-knowledge/` (never versioned)

Total: 107 PDF files in 7 folders, 1,013 MB, but only 98 unique. The 9 AEA standards plus the 8 CIMET and 2 NFPA documents exist in up to 3 identical copies.

| Current location | Files / size | Unique? | Destination |
|---|---|---|---|
| `elec-calc-generator/assets/` | 9 / 342.6 MB (AEA 90364-2, -4, -4-42, -5, -7-701, -7-722, -7-770, -7-771; AEA 90909-1) | master copy | `dev-knowledge/standards/AR/<AEA-ID>/source/` |
| `elec-calc-generator/library/calculations/assets/` | 19 / 369.2 MB | 9 = copies of the above; 10 unique: 8 CIMET/OPTEL datasheets (cable manufacturer), NFPA 70B 2026, NFPA 70E 2027 | AEA copies: delete after confirming; CIMET → `dev-knowledge/third-party-reports/`; NFPA → `dev-knowledge/standards/US/` |
| Template `.claude/library/plugins/calculations/assets/` | 19 / 369.2 MB | identical to the line above (19 of 19) | delete after confirming |
| Template `.claude/library/plugins/management/assets/` | 11 / 60.6 MB (PM² guides) | unique | `dev-knowledge/standards/INTL/PM2/source/` (reference for the `pm2` methodology pack; CC BY 4.0 per the template, but kept out of git by rule) |
| Template `.claude/skills/generar-pliego/knowledge/pdf/` | 27 / 88.1 MB (Ford civil x3, fire fighting x5, fire detection x4, electrical x10, HVAC x3, thermomechanical x2) | unique, client-confidential | `dev-knowledge/reference-specs/FORD/` |
| `sld-generator/assets/` | 40 / 133.4 MB (`sld_1..40.pdf`) | unique | `dev-knowledge/training-material/drawings/` |
| `291_E_IEC60617_Symbols_Generator/assets/` | 1 / 10.1 MB (`IEC_60617_Simbologia.pdf`) | unique | `dev-knowledge/standards/INTL/IEC-60617/source/` |

Savings: about 430 MB of pure duplicates, plus about 15 MB of `vendor/*.plugin` copies.

## C. Findings that need your attention before migrating

1. **`291_E_IEC60617_Symbols_Generator` tracks a PDF in git** (`IEC_60617_Simbologia.pdf`, 10 MB) and has a GitHub remote (`davillenah/291_E_IEC60617_Symbols_Generator`). If it was pushed, it is already public or on the remote. Check whether that repo is private and, if needed, purge it from history (`git filter-repo`) before anything else. The other two repos have no PDF in their history. `elec-calc-generator` already ignores `*.pdf`.
2. **Ford pliegos are client-confidential documents** and the Template currently stores them inside a skill. They must leave the product tree (rule 9).
3. **Three separate git repos exist** (291_E, 291_G, elec-calc). Moving to a single `platform` repo changes the history strategy: either keep them as archived repos or import them with `git subtree`/`filter-repo`. Needs your decision.
4. **Country code for international standards:** the `rules.schema.json` pattern accepts only two letters. IEC, NFPA and PM² need either `INTL` or a separate folder. Proposed: `INTL` for IEC/ISO/PM² and `US` for NFPA; relax the schema pattern to `^([A-Z]{2}|INTL)$`.
5. **Version drift already happened:** the Template holds older copies of the calculation, symbol and IRAM plugins than the standalone folders. Only the standalone versions listed in section A would be kept.
