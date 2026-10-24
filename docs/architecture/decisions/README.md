# Architecture decision records

Format: `ADR-NNNN-title.md` with Status, Context, Decision, Consequences. A decision is never edited after acceptance; a new ADR supersedes it.

| ADR | Title | Status |
|---|---|---|
| [0001](ADR-0001-modular-monolith-monorepo.md) | Monorepo with a modular monolith backend | Proposed |
| [0002](ADR-0002-three-kinds-of-management.md) | Three kinds of "management" with three homes | Proposed |
| [0003](ADR-0003-engine-and-claude-layer.md) | Engine as pure libraries, Claude layer as thin packaging | Proposed |
| [0004](ADR-0004-client-visibility.md) | The client sees only deliverables and data | Accepted (already implemented) |
| [0005](ADR-0005-private-material-and-local-folder.md) | Private material lives in an ignored `local/` folder | Proposed |
| [0006](ADR-0006-database-strategy.md) | PostgreSQL for platform state, files for engineering artifacts | Accepted |
| [0007](ADR-0007-desktop-edition-rust.md) | Desktop edition with Rust (Tauri), engine stays in Python | Deferred |
| [0008](ADR-0008-cad-strategy-2d-first.md) | CAD strategy: 2D first with ezdxf and shapely | Accepted |
| [0009](ADR-0009-identity-and-subscriptions.md) | Accounts, organizations (individual and corporate) and tenant isolation | Accepted |
| [0010](ADR-0010-registers-as-platform-data.md) | Management registers are platform data, defined by the methodology | Accepted |
| [0011](ADR-0011-norm-review.md) | Norm review by a dedicated reviewer role | Accepted |
| [0012](ADR-0012-single-source-of-truth.md) | One source of truth per datum | Accepted |
