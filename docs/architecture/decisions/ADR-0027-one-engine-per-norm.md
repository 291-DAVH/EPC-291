# ADR-0027: One engine per norm

Status: accepted. Done: `engine/calc` is now `engine/aea90364` (package `epc_aea90364`); the design criteria and the review state moved into it; promoted standards go to the norm engine a jurisdiction names. Date: 2026-10-27

## Context
The data of the AEA 90364 norm was spread over four places: the calculation and its tables and rules inside `engine/calc`, the design criteria and the review state inside `engine/jurisdictions/AR`, the promoted `rules.json` planned for `engine/jurisdictions/<CC>/<domain>/<ID>/`, and the private PDFs in `local/dev-knowledge`. A norm is one thing (its calculation, its numbers, its rules, its criteria and its review go together), and the engine that calculates with it was called after what it does (`calc`), not after the norm it applies.

## Decisions
1. **One engine per norm family**, named after it: `engine/aea90364/`, package `epc_aea90364`. Everything of the norm is inside: the calculation, `aea_tables.json`, `rules/`, `data/` (standard solutions, `design-criteria.json`, `review.json`, `review-log.jsonl`), `standards/<STANDARD-ID>/rules.json` (promoted standards) and `norm_data.py`, which says where each piece is. Another norm (IEC 60364, NFPA 70) is another engine of the same shape.
2. **A jurisdiction only says which norm engine it uses.** `engine/jurisdictions/<CC>/jurisdiction.json` has `packs`: `{"electrical": "aea90364"}` (a list when several norms apply). Its domain folders stay: they are the disciplines a project of that country may have.
3. **Consumers ask the norm engine, never build its paths:** the backend (`norms`, `engineering.criteria`) and the drawing engine (`board_design.catalog_file`) use `norm_data`; the backend finds the engine of a domain with `projects.norm_engine(jurisdiction, discipline)`.
4. **Promotion goes to the norm engine:** `epc_standards.promote_rules` writes `engine/<pack>/src/epc_<pack>/standards/<ID>/rules.json` (`--pack` when the jurisdiction names several) and `epc_rules.RuleSet.load(jurisdiction, domain)` reads the promoted standards of every engine the jurisdiction names for the domain.
5. **The private material stays out**: PDFs and study notes remain in `local/dev-knowledge/standards/<CC>/<ID>/`.

## Consequences
- (+) A norm can be taken, reviewed and released as one unit; adding a norm is adding an engine and one line in a jurisdiction; the review state travels with the data it approves.
- (+) A plugin that carries the engine carries the criteria with it: the generated copy (`engine_data`) of `board-design` is no longer needed.
- (-) The old name `epc_calc` disappears from code and tools (history in ADRs, the changelog and `docs/refactor/` keeps it). Environments with an editable install of `epc-calc` need `pip install -e engine/aea90364`.
- Open: `hazen_williams`, `hvac_airflow` and `lighting` are not AEA calculations and should move to engines of their own; there is still no selector of norm inside the calculation (see `docs/architecture/GUIA_NORMAS.md`); the norms screen reviews only the AEA calculation data, not the promoted `rules.json`.
