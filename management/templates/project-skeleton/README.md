# Project template

Copy to `projects/<CLIENT>/<PROJECT>/`.

- `workspace/` editable, internal, versioned in git (svg, dxf masters, md sources, calc json).
- `deliverables/` client-facing, read-only, written only by the publish step (see `shared/schemas/deliverable-policy.json`).
- `.epc/` platform state: `project.json`, `plugins.lock` (`python tools/build/epc_build.py lock <project>`), `ledger/`.
- `_out/` temporary files, not versioned.
