"""The title block as a service: a request in JSON, the sheets out.

Whoever draws (the single-line, the multi-line...) does not know IRAM. It says "I have to deliver these sheets, with this information": the formats, how many, the fields of the project and
of each sheet, the logos. It gets back the sheets with their title block filled in. Nothing is written, there is no Excel and no process is started.

Request:
  {"schema_version": "1.0",
   "logos":  {"provider": "<file>", "client": "<file>"},                  optional, svg or png
   "common": {"empresa": "...", "cliente": "...", "proy_nombre": "...", ...},   fields every sheet shares
   "sheets": [{"name": "SLD_T1_H1", "format": "A1", "modifications": false, "fields": {"denominacion": "...", "pagina": "1 / 2"}}]}
`name` is the sheet's own drawing code (the field `plano_propio`); `pagina` defaults to "<n> / <total>" and `formato` to the format of the sheet. A field a sheet does not give stays blank.
"""
import datetime
import html
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from epc_titleblock import sheet_generator

SCHEMA_VERSION = "1.0"
FIELDS = ("formato", "proy_fecha", "proy_nombre", "ver_fecha", "ver_nombre", "val_fecha", "val_nombre", "empresa", "empresa_cuit", "empresa_email", "empresa_web",
          "cliente", "cliente_cuit", "cliente_email", "cliente_web", "proyecto", "descripcion", "ubicacion", "tipo_plano", "denominacion", "denominacion_2", "escala",
          "reemplaza", "reemplazado_por", "plano_n", "pagina", "estado", "revision", "plano_propio")


PROJECT_FIELDS = {"company": "empresa", "company_cuit": "empresa_cuit", "client": "cliente", "client_cuit": "cliente_cuit", "drawn_by": "proy_nombre", "checked_by": "ver_nombre",
                  "approved_by": "val_nombre", "description": "descripcion", "location": "ubicacion", "scale": "escala", "revision": "revision", "status": "estado"}


def project_request(titleblock: dict, logos: dict = None, today: datetime.date = None) -> dict:
    """The common part of a request from the title block data of a project (company, client, who drew, checked and approved, description...):
    the three dates are the day the drawing is made. `sheets` are added by whoever draws."""
    day = (today or datetime.date.today()).strftime("%d/%m/%Y")
    common = {field: titleblock.get(key) or "" for key, field in PROJECT_FIELDS.items()}
    common.update(proy_fecha=day, ver_fecha=day, val_fecha=day)
    return {"schema_version": SCHEMA_VERSION, "logos": {k: str(v) for k, v in (logos or {}).items()}, "common": common}


class RequestError(ValueError):
    """The request is not valid: `errors` says where, field by field."""

    def __init__(self, errors: Dict[str, str]):
        super().__init__("; ".join(f"{k}: {v}" for k, v in errors.items()))
        self.errors = errors


def text_of(value: Any) -> str:
    """A field as the title block prints it: dates as dd/mm/yyyy, nothing as blank."""
    if value is None:
        return ""
    return value.strftime("%d/%m/%Y") if hasattr(value, "strftime") else str(value)


def _sheet_errors(i: int, sheet: dict) -> Dict[str, str]:
    errors: Dict[str, str] = {}
    where = f"sheets[{i}]"
    if not str(sheet.get("name") or "").strip():
        errors[f"{where}.name"] = "required"
    if str(sheet.get("format", "")).upper() not in sheet_generator.FORMATOS:
        errors[f"{where}.format"] = "one of " + ", ".join(sheet_generator.FORMATOS)
    errors.update({f"{where}.fields.{k}": "unknown field" for k in (sheet.get("fields") or {}) if k not in FIELDS})
    return errors


def validate(request: dict) -> Dict[str, str]:
    """{path: message} for what a request may not contain; empty when it is valid."""
    errors: Dict[str, str] = {}
    if request.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
        errors["schema_version"] = f"only {SCHEMA_VERSION} is understood"
    errors.update({f"common.{k}": "unknown field" for k in (request.get("common") or {}) if k not in FIELDS})
    sheets = request.get("sheets") or []
    if not sheets:
        errors["sheets"] = "at least one sheet"
    for i, sheet in enumerate(sheets):
        errors.update(_sheet_errors(i, sheet))
    return errors


def _fill(svg: str, values: Dict[str, str]) -> str:
    for key in FIELDS:
        svg = svg.replace("{%s}" % key, html.escape(values.get(key, ""), quote=False))
    return svg


def _values(request: dict, sheet: dict, position: int, total: int) -> Dict[str, str]:
    fmt = str(sheet["format"]).upper()
    merged = {"formato": fmt, "pagina": f"{position} / {total}", "plano_propio": sheet["name"], **(request.get("common") or {}), **(sheet.get("fields") or {})}
    return {k: text_of(v) for k, v in merged.items()}


def _logos(request: dict) -> tuple:
    """(the logos that exist, the warnings about those that do not)."""
    found, warnings = {}, []
    for who, path in (request.get("logos") or {}).items():
        if path and Path(path).is_file():
            found[who] = path
        elif path:
            warnings.append(f"logo {who}: file not found: {path}")
    return found, warnings


def render(request: dict) -> dict:
    """The sheets of a request: {"sheets": [{"name", "format", "svg", "title_block", "modifications_block", "info"}], "warnings": [...]}.
    `svg` is the IRAM sheet with its title block filled in and the space for the drawing (<g id="dibujo">) empty."""
    errors = validate(request)
    if errors:
        raise RequestError(errors)
    logos, warnings = _logos(request)
    sheets: List[dict] = []
    total = len(request["sheets"])
    for position, sheet in enumerate(request["sheets"], 1):
        values = _values(request, sheet, position, total)
        built = sheet_generator.build(str(sheet["format"]), bool(sheet.get("modifications")), logos)
        sheets.append({"name": sheet["name"], "format": values["formato"], "svg": _fill(built["svg"], values), "title_block": _fill(built["title_block"], values),
                       "modifications_block": _fill(built["modifications_block"], values), "info": built["info"]})
    return {"sheets": sheets, "warnings": warnings}


def write(result: dict, out_dir: Path, dxf: bool = False) -> List[Path]:
    """Save the sheets of a result as <name>.svg in a folder (and their DXF when asked: it uses epc_dxf, the deliverable service)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files: List[Path] = []
    for sheet in result["sheets"]:
        svg = out / f"{sheet['name']}.svg"
        svg.write_text(sheet["svg"], encoding="utf-8", newline="\n")
        files.append(svg)
        if dxf:
            from epc_dxf import deliverable
            done = deliverable.convert(svg)
            files += [Path(done["dxf"])] if done["dxf"] else []
    return files


def main(argv=None) -> int:
    """python -m epc_titleblock.service request.json out_dir [--dxf]"""
    argv = sys.argv[1:] if argv is None else argv
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print("usage: python -m epc_titleblock.service request.json out_dir [--dxf]", file=sys.stderr)
        return 2
    try:
        result = render(json.loads(Path(args[0]).read_text(encoding="utf-8-sig")))
    except RequestError as e:
        print("INVALID", json.dumps(e.errors, ensure_ascii=False), file=sys.stderr)
        return 1
    for path in write(result, Path(args[1]), "--dxf" in argv):
        print(path)
    for w in result["warnings"]:
        print("AVISO", w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
