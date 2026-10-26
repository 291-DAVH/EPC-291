"""The title block service: a JSON request in, the filled sheets out; no workbook, no process."""
import datetime
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from epc_titleblock import service  # noqa: E402

LOGO = '<svg xmlns="http://www.w3.org/2000/svg" width="10mm" height="5mm" viewBox="0 0 10 5"><rect width="10" height="5" fill="#00f"/></svg>'


def request(**over):
    base = {"schema_version": "1.0", "common": {"empresa": "ACME & Hijos", "cliente": "CLIENTE SA", "proy_nombre": "D. Proyecta", "proy_fecha": "26/10/2026"},
            "sheets": [{"name": "SLD_T1_H1", "format": "A1", "fields": {"denominacion": "TGBT-01", "proyecto": "PRJ-1"}},
                       {"name": "SLD_T1_H2", "format": "A3", "modifications": True, "fields": {"denominacion": "TGBT-01", "pagina": "9 / 9"}}]}
    base.update(over)
    return base


class TestRender(unittest.TestCase):
    def test_every_requested_sheet_comes_back_with_its_title_block_filled(self):
        out = service.render(request())
        self.assertEqual([(s["name"], s["format"]) for s in out["sheets"]], [("SLD_T1_H1", "A1"), ("SLD_T1_H2", "A3")])
        svg = out["sheets"][0]["svg"]
        self.assertIn(">ACME &amp; Hijos<", svg)                          # escaped
        self.assertIn(">TGBT-01<", svg)
        self.assertIn(">1 / 2<", svg)                                     # the page is counted by the service ...
        self.assertIn(">9 / 9<", out["sheets"][1]["svg"])                 # ... unless the sheet says it
        self.assertNotRegex(svg, r"\{[a-z_0-9]+\}")                       # nothing is left to fill
        self.assertIn('id="modificaciones_IRAM4508"', out["sheets"][1]["svg"])
        self.assertNotIn('id="modificaciones_IRAM4508"', svg)

    def test_a_field_nobody_gave_stays_blank_and_dates_are_printed_as_day_month_year(self):
        svg = service.render(request())["sheets"][0]["svg"]
        self.assertIn('data-key="tipo_plano" data-placeholder=""></text>', svg)
        out = service.render(request(common={"proy_fecha": datetime.date(2026, 1, 5)}))
        self.assertIn(">05/01/2026<", out["sheets"][0]["svg"])

    def test_the_project_data_becomes_the_common_part_of_the_request(self):
        req = service.project_request({"company": "ACME", "drawn_by": "D. Proyecta", "scale": "1:50", "status": "Emitido"}, {"client": "x.svg"}, datetime.date(2026, 10, 26))
        self.assertEqual((req["common"]["empresa"], req["common"]["proy_nombre"], req["common"]["escala"], req["common"]["val_fecha"]), ("ACME", "D. Proyecta", "1:50", "26/10/2026"))
        self.assertEqual(req["logos"], {"client": "x.svg"})
        self.assertEqual(req["common"]["revision"], "")

    def test_a_logo_that_exists_is_embedded_and_one_that_does_not_is_a_warning(self):
        with tempfile.TemporaryDirectory() as t:
            logo = Path(t) / "provider-logo-X.svg"
            logo.write_text(LOGO, encoding="utf-8")
            out = service.render(request(logos={"provider": str(logo), "client": str(Path(t) / "falta.svg")}))
            self.assertIn("rotulo_IRAM4508_rotulo_logos", out["sheets"][0]["svg"])
            self.assertGreater(len(out["sheets"][0]["svg"]), len(service.render(request())["sheets"][0]["svg"]))
            self.assertEqual(len(out["warnings"]), 1)
            self.assertIn("client", out["warnings"][0])

    def test_a_wrong_request_is_refused_field_by_field(self):
        with self.assertRaises(service.RequestError) as e:
            service.render({"common": {"nope": 1}, "sheets": [{"name": "", "format": "A9", "fields": {"x": 1}}]})
        self.assertEqual({"common.nope", "sheets[0].name", "sheets[0].format", "sheets[0].fields.x"}, set(e.exception.errors))
        with self.assertRaises(service.RequestError):
            service.render({"sheets": []})


class TestCommandLine(unittest.TestCase):
    def test_the_command_writes_the_sheets_of_a_request(self):
        with tempfile.TemporaryDirectory() as t:
            req = Path(t) / "request.json"
            req.write_text(json.dumps(request()), encoding="utf-8")
            res = subprocess.run([sys.executable, "-m", "epc_titleblock.service", str(req), str(Path(t) / "out")], capture_output=True, text=True,
                                 env={"PYTHONPATH": str(HERE.parent / "src"), "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")})
            self.assertEqual(res.returncode, 0, res.stderr[-300:])
            self.assertTrue((Path(t) / "out" / "SLD_T1_H1.svg").is_file() and (Path(t) / "out" / "SLD_T1_H2.svg").is_file())


if __name__ == "__main__":
    unittest.main()
