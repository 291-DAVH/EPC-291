"""board_design: base criteria, project overrides and the calculation that governs both diagrams."""
import json
import tempfile
import unittest
from pathlib import Path

from epc_drawing import board_design as B

CATALOG = Path(__file__).resolve().parents[2] / "jurisdictions" / "AR" / "electrical" / "design-criteria.json"

DATA = {"board": {"name": "TGBT-01", "voltage_v": 380, "system": "TN-S", "icc_ka": 25, "fp_default": 0.85, "frequency_hz": 50, "project": "P", "feeder_length_m": 20},
        "circuits": [{"tag": "C-01", "description": "ALIMENTADOR", "load": 100, "unit": "A", "topology": "single", "phase": "3F", "length_m": 60, "kind": "mccb"},
                     {"tag": "M-01", "description": "BOMBA", "load": 15, "unit": "kW", "topology": "dol_ol", "phase": "3F", "length_m": 80, "fp": 0.85, "efficiency": 0.9}],
        "titleblock": {}}


class TestBoardDesign(unittest.TestCase):
    @unittest.skipUnless(CATALOG.is_file(), "catalog is part of the repository, not of the installed plugin")
    def test_base_criteria_equal_the_catalog(self):
        cat = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(B.BASE_CRITERIA, {c["id"]: c["default"] for c in cat["criteria"]})

    def test_project_overrides_win(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "workspace" / "00-setup" / "design-criteria.json"
            f.parent.mkdir(parents=True)
            f.write_text(json.dumps({"overrides": {"electrical": {"vd_sectional_pct": {"value": 0.5, "source": "client"}}}}), encoding="utf-8")
            c = B.resolve_criteria(Path(tmp))
            self.assertEqual((c["vd_sectional_pct"], c["vd_motors_pct"]), (0.5, 5))
        self.assertEqual(B.resolve_criteria(None)["vd_sectional_pct"], 1)

    def test_calculation_follows_the_criteria(self):
        loose = B.calculate(DATA, dict(B.BASE_CRITERIA, vd_sectional_pct=3))
        strict = B.calculate(DATA, dict(B.BASE_CRITERIA, vd_sectional_pct=0.5))
        self.assertGreater(strict["datos"]["C-01"]["S"], loose["datos"]["C-01"]["S"])
        self.assertEqual(strict["limites"], {"seccional": 0.5, "terminal": 3.0, "motor": 5.0})
        self.assertIn("seccionales 0.5 %", B.calc_note(strict))

    def test_excel_rows_use_the_plugin_column_names(self):
        tablero, circuitos = B.excel_rows(DATA)
        self.assertEqual((tablero["NOMBRE"], tablero["TENSION_V"]), ("TGBT-01", 380))
        self.assertEqual((circuitos[1]["TAG"], circuitos[1]["UNIDAD_CARGA"], circuitos[1]["TOPOLOGY"], circuitos[1]["RENDIMIENTO"]), ("M-01", "kW", "dol_ol", 0.9))


if __name__ == "__main__":
    unittest.main()
