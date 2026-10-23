# epc-documents

| Module | Purpose |
|---|---|
| `epc_documents.document_verifier` | Closure self-check of a package (revisions, references, marks, Pandoc format) |
| `epc_documents.specification_verifier` | Heuristic checks for technical specifications (`PG`) |
| `epc_documents.input_converter` | Office -> PDF/images/Markdown reading copies (needs LibreOffice, optional) |
| `epc_documents.ccpm` | Critical-chain scheduling, buffers, work packages |
| `epc_documents.charter_exporter` / `canvas_exporter` | PM2 charter and canvases to HTML/PDF (needs Pandoc/poppler, optional) |

Run with `PYTHONPATH=engine/documents/src`, for example `python -m epc_documents.document_verifier <project_dir>`.
Tests: `python -m unittest discover -s tests` from this folder with `PYTHONPATH=src`. Environment-dependent tests are skipped explicitly: 5 `input_converter` tests on Windows (their fake soffice is a shell script) and the PDF-stamp test (needs poppler and the Playwright chromium).
Templates: `src/epc_documents/templates/`. Examples: `src/epc_documents/example_*.json`.
