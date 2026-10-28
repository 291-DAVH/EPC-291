# jurisdictions

One folder per country (ISO 3166 alpha-2). It holds only what is about the country: `jurisdiction.json` (name, locale, currency, frequency, voltages and `packs`: the norm engine each domain uses, e.g. `{"electrical": "aea90364"}`), the domain folders (they are the disciplines a project of that country may have) and the legacy index.

The norms themselves are **not** here: each norm is an engine of its own (`engine/aea90364/`) with its calculation, tables, rules, design criteria, review state and promoted standards (`standards/<STANDARD-ID>/rules.json`, schema `shared/schemas/rules.schema.json`, promoted from `local/dev-knowledge/standards/<CC>/<STANDARD-ID>/draft/` by `epc_standards.promote_rules`).
