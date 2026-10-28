# epc-aea90364

The AEA 90364 norm as an engine: everything that belongs to the norm is in this one package, `epc_aea90364`.

```
src/epc_aea90364/
├── aea_*.py, board_*.py, ...     the calculation: demand, protection, ampacity, cable section, voltage drop, short circuit, earthing, route, special locations
├── aea_tables.json               tables and constants of the norm (capacity tables, correction factors), each with its clause
├── rules/*.json                  the engineering rules derived from the norm (paraphrased; norm, edition, clause and page as reference) and `_indice.json`
├── data/
│   ├── standard-solutions.json   which symbols build each circuit
│   ├── design-criteria.json      the catalog of base design criteria (the norm reviewer corrects the values here; a project overrides them)
│   ├── review.json               who approved which point of the norm data, when, and the fingerprint of the approved value
│   └── review-log.jsonl          every review action, appended
├── standards/<STANDARD-ID>/rules.json   standards ingested with `epc_standards` and promoted (schema 1.1), one folder per part of the norm
├── norm_data.py                  where the data above lives (the backend and the drawing engine ask here instead of building paths)
└── policy.py                     the protection constants (to move to aea_tables.json)
```
Other norms get an engine of their own with the same shape (`engine/iec60364/`, `engine/nfpa70/`...): the calculation, the data and the rules of a norm are never spread over other folders.
The private material (the PDFs and the study notes) stays out of the repository, in `local/dev-knowledge/standards/<country>/<id>/`.

Which norm engine a country uses for a domain is said by `engine/jurisdictions/<CC>/jurisdiction.json` (`packs`: `{"electrical": "aea90364"}`).
Run: `python -m epc_aea90364.aea_pipeline input.xlsx`. Tests: `python -m unittest discover -s tests` from this folder with `PYTHONPATH` on the `engine/*/src` folders.
Limits: `hazen_williams.py`, `hvac_airflow.py` and `lighting.py` are not AEA calculations and should move to engines of their own; the calculation is written for this norm only (no selector of norm yet, see `docs/architecture/GUIA_NORMAS.md`).
