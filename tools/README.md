# tools

Repository tooling (no product code).

| Folder | Content |
|---|---|
| `ci/` | `run_gate.py` (the test battery), skill-conflict check, import-linter config generator, frontend and infra checks |
| `build/` | `epc_build.py`: plugin registry, packaging, marketplace, project `plugins.lock` |
| `planning/` | `board.py`: generates `planning/BOARD.md` |
| `dev/` | `seed_demo.py` (20 simulated projects), preview and skill helpers |
| `hooks/` | `pre-commit` safety hook (`git config core.hooksPath tools/hooks`) |
| `migrate/` | one-off scripts of the original migration (historical, they still mention the old `platform/` layout) |
