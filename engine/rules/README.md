# epc-rules

Rules engine (pure Python, standard library only). Loads the promoted `rules.json` of the norm engines a jurisdiction names (`engine/jurisdictions/<CC>/jurisdiction.json`, `packs`), queries them and checks project data: PASS, FAIL or not evaluated (a missing datum is reported, never guessed). Production sees only verified standards.

```
from epc_rules import RuleSet
rs = RuleSet.load("AR", "electrical", env="production")
rs.check({"reserva_pct": 15}, installation_type="dwellings", topic="bandejas")
```

CLI (from `engine/rules/src`): `python -m epc_rules list|query|check`.
Tests: `python -m unittest discover -s tests` with `PYTHONPATH=src`.
Rule format: `shared/schemas/rules.schema.json`. Ingestion pipeline: `engine/standards`.
