# Dependencies

## Python (>= 3.10)
| Package | Needed by | Required |
|---|---|---|
| openpyxl >= 3.1 | aea-calc, iram-titleblock, sld, mld, procurement | yes |
| lxml | iram-titleblock, sld, mld | yes |
| ezdxf | iram-titleblock, sld, mld (DXF output) | yes |
| svgelements | sld | yes |
| shapely | sld | yes |
| pypdf | standard-ingest (text extraction) | yes, for standard-ingest |
| pypdfium2, pillow | standard-ingest (render scanned pages to PNG) | yes, for standard-ingest |
| jsonschema | standard-ingest (schema validation; falls back to a minimal check) | recommended |
| cairosvg (+ Cairo library on Windows) | iec-symbols build tools, sld PNG previews | optional |
| pillow | iec-symbols build tools | optional |
| pytest, pytest-cov | tests | dev |

The core (`tools/`, registry, skill checks) uses only the standard library.

## System tools (optional)
`pandoc` (Markdown -> Word), `libreoffice`/`soffice` (Office -> PDF, used by doc-quality and pm2-docs), `poppler-utils` (`pdftotext`, `pdftoppm`).

## Plugin graph (hub)
```
sld  -> aea-calc, iec-symbols, iram-titleblock
mld  -> sld, iram-titleblock, iec-symbols
spec-writer -> doc-quality
pm2-docs    -> doc-quality
procurement -> equipment-catalog
standard-ingest -> engine/standards, engine/rules (no plugin dependency)
```
Versions are checked by `tools/build/epc_build.py registry` (semver ranges: `^`, `~`, exact).

## Known runtime notes
- `epc_drawing.sld` resolves symbols named `291_E_LV_SLD_IEC60617_<id>.svg` (library >= 0.4.14) and the old `<id>.svg`. Known data issue: the catalog lists `lv_acb_basic` but no file has that name.
- The old cross-plugin import between `pm2-docs` and `doc-quality` is gone: both live in `epc_documents`.
- Environment-dependent tests are skipped explicitly (5 `input_converter` tests on Windows, the PDF-stamp test without poppler and the Playwright chromium).
