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
| [0013](ADR-0013-account-types-and-permissions.md) | Account types, a permission matrix and an audit log | Accepted |
| [0014](ADR-0014-sign-in-alias-and-providers.md) | Sign-in with an alias and with external providers | Accepted |
| [0015](ADR-0015-development-master-account.md) | A MASTER account for development only | Accepted |
| [0016](ADR-0016-organizations-own-their-engineering.md) | Organizations do their own engineering; their data is their own | Accepted |
| [0017](ADR-0017-company-registration.md) | A company registers with its own form, an e-mailed code and validation by the team | Accepted |
| [0018](ADR-0018-ai-usage-metering-and-limits.md) | Use of Claude is metered per organization and limited by a monthly allowance | Accepted (design) |
| [0019](ADR-0019-engineering-roadmap.md) | What the engineering area grows into | Accepted (direction) |
| [0020](ADR-0020-plan-canvas.md) | Drawing the routes over the architectural plan | Accepted (direction) |
| [0021](ADR-0021-plan-drawing-editor.md) | Plan-drawing editor: levels, scale, graph, circuits and DXF | Accepted |
| [0022](ADR-0022-engine-split-generated-plugins.md) | Drawing engine split into independent packages; plugins generated from the code | Accepted |
| [0023](ADR-0023-drawing-services-and-standard-solutions.md) | Drawings as services; DXF layer catalog; standard solutions | Accepted (direction) |
| [0024](ADR-0024-coordination-between-disciplines.md) | Coordination between disciplines | Accepted |
| [0025](ADR-0025-architecture-recognition.md) | Architecture recognition as an isolated engine | Accepted |
| [0026](ADR-0026-automatic-circuit-design.md) | Automatic design of circuits and runs | Accepted |
| [0027](ADR-0027-one-engine-per-norm.md) | One engine per norm | Accepted |
| [0028](ADR-0028-norm-selector.md) | Norm selector: generic calculation engines, norms as complete packages, one registry | Proposed |
| [0029](ADR-0029-lighting-engine.md) | Lighting engine | Accepted |
| [0030](ADR-0030-lighting-in-the-platform.md) | Lighting in the platform: backend module and plan-editor integration | Proposed |
