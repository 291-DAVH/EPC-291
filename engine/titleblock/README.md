# epc-titleblock

IRAM A0-A4 sheets (frame, coordinates, IRAM 4504/4508 title block, optional list of modifications) with company and client logos, as a **service**: a JSON request in, the filled sheets out.
No Excel, no subprocess, nothing written unless the caller asks.

```python
from epc_titleblock import service
result = service.render({"common": {"empresa": "ACME", "cliente": "CLIENTE SA"},
                         "logos": {"provider": "logo-empresa.svg"},
                         "sheets": [{"name": "SLD_T1_H1", "format": "A1", "fields": {"denominacion": "TGBT-01", "proyecto": "PRJ-1"}}]})
svg = result["sheets"][0]["svg"]          # the sheet; <g id="dibujo"> is where the drawing goes
```
The fields are those of the title block (`service.FIELDS`); `service.project_request(titleblock_of_the_project)` turns the platform's data (company, client, who drew, checked and approved, description...) into the common part
of a request. A field nobody gives stays blank. Command line: `python -m epc_titleblock.service request.json out_dir [--dxf]`; one sheet by hand: `python -m epc_titleblock.sheet_generator A4 out.svg`.
