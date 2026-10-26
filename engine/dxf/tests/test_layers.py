"""The catalog of DXF layers: default, overrides by role, checks and what a document gets."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import ezdxf  # noqa: E402

from epc_dxf import layers as L  # noqa: E402


class TestCatalog(unittest.TestCase):
    def test_the_default_catalog_is_valid_and_has_the_diagram_and_plan_roles(self):
        cat = L.load()
        self.assertEqual(L.validate(cat), {})
        self.assertEqual(L.name("sld.diagram", cat), "291-E-DIAGRAMA")
        self.assertTrue({"sld.text", "sld.titleblock", "sld.sheet", "plan.ELEC-LUM", "plan.SAN-CLOACA", "plan.PLAN-TAG"} <= set(cat))

    def test_a_file_overrides_role_by_role_and_field_by_field(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "layers.json"
            f.write_text(json.dumps({"layers": {"sld.diagram": {"name": "DIAGRAMA", "color": 3}, "custom.x": {**L.BLANK, "name": "X"}}}), encoding="utf-8")
            cat = L.load(f)
            self.assertEqual((cat["sld.diagram"]["name"], cat["sld.diagram"]["color"], cat["sld.diagram"]["lineweight"]), ("DIAGRAMA", 3, None))
            self.assertEqual(cat["sld.text"]["name"], "291-E-TEXTOS")
            self.assertIn("custom.x", cat)
            os.environ[L.ENV_VAR] = str(f)                                   # the global file the MASTER edits
            try:
                self.assertEqual(L.name("sld.diagram"), "DIAGRAMA")
            finally:
                del os.environ[L.ENV_VAR]

    def test_validation_names_each_wrong_field(self):
        cat = L.load()
        cat["sld.text"] = {**cat["sld.text"], "name": "291-E-DIAGRAMA", "color": 300, "lineweight": 0.27, "linetype": "WAVY", "on": "yes"}
        cat["sld.sheet"] = {**cat["sld.sheet"], "name": "bad:name"}
        errors = L.validate(cat)
        self.assertEqual({"sld.text.name", "sld.text.color", "sld.text.lineweight", "sld.text.linetype", "sld.text.on", "sld.sheet.name"}, set(errors))
        self.assertIn("already used by sld.diagram", errors["sld.text.name"])

    def test_a_document_gets_the_layer_with_its_attributes(self):
        doc = ezdxf.new("R2018")
        cat = L.load()
        cat["sld.diagram"] = {**cat["sld.diagram"], "color": 3, "lineweight": 0.5, "locked": True, "plot": False}
        self.assertEqual(L.apply(doc, "sld.diagram", cat), "291-E-DIAGRAMA")
        lay = doc.layers.get("291-E-DIAGRAMA")
        self.assertEqual((lay.color, lay.dxf.lineweight, lay.is_locked, lay.dxf.plot), (3, 50, True, 0))

    def test_an_unknown_role_gets_plain_defaults(self):
        self.assertEqual(L.get("plan.NEW-LAYER")["name"], "NEW-LAYER")


if __name__ == "__main__":
    unittest.main()
