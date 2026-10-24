# ADR-0012: One source of truth per datum

Status: Accepted. Date: 2026-10-24.

## Context
Copies drift. The norm review (ADR-0011) made it concrete: the drawing engine kept its own list of base design criteria next to the catalog the reviewer corrects, and the repository held a second, unused library of multi-line symbols and several copies of the same files.

## Decision
- Every datum (a norm value, a design criterion, a symbol, an example, a label list, a logo) lives in **one** file; anything that needs it reads that file. Where a packaged artifact must carry the data (a plugin used outside the repository), the build **generates** the copy from the source (`engine_data` in the plugin manifest) and the copy changes the plugin's hash; it is never edited by hand.
- The gate check `single-source` fails when two versioned files have the same content. Exempt: test fixtures (pinned expected outputs) and the pairs listed in the check with their reason.
- Derived data is marked as such and rebuilt, not edited: `dist/`, `registry.json`, the plugin locks, `_indice.json` counts.

## Where each datum lives
| Datum | Source | Read by |
|---|---|---|
| Rules of the AEA engine | `engine/calc/src/epc_calc/rules/*.json` | calculation engine, norm review |
| Calculation tables and constants | `engine/calc/src/epc_calc/aea_tables.json` | calculation engine, norm review |
| Base design criteria | `engine/jurisdictions/AR/electrical/design-criteria.json` | design pipeline, project criteria screen, norm review, built plugin (generated copy) |
| Review state of the norms | `engine/jurisdictions/AR/review.json` + `review-log.jsonl` | norm review |
| Project criteria overrides | `<project>/workspace/00-setup/design-criteria.json` | design pipeline |
| Report types / register definitions | `management/methodologies/<id>/reports.json`, `registers.json` | reporting, registers |
| Project registers and plan | `<project>/workspace/05-management/` | registers, reporting, management |
| Multi-line / single-line symbols | `engine/drawing/src/epc_drawing/symbols/library/<kind>/` | SLD and MLD generators |

## Consequences
- (+) A correction is made once and everything follows; the review of a norm cannot leave a stale copy behind.
- (-) Known remaining duplication to resolve (tracked, not hidden): the rules also exist in the rules-engine format (`epc_rules`) that `epc_standards` generates from the calculation rules into private drafts; the project phases and the emission names are listed in more than one backend module and in the frontend dictionary.
