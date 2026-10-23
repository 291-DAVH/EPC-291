## What and why

## Checklist
- [ ] `python tools/ci/run_gate.py` is green
- [ ] CHANGELOG updated (and plugin version bumped if behavior changed)
- [ ] No PDF/DWG, client data or `local/` content staged
- [ ] Module boundaries respected (`lint-imports`, frontend boundaries)
- [ ] Database changes come with a reversible Alembic migration
