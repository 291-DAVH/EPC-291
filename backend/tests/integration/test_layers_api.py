"""The catalog of DXF layers: the MASTER reads and changes it in the console, and the drawings are delivered with it."""
import json
import tempfile
import unittest
from pathlib import Path

import ezdxf
from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app
from tests.integration.test_layout_api import DRAWING


class TestLayers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def test_the_default_catalog_is_offered_with_what_each_field_accepts(self):
        v = self.c.get("/api/layers").json()
        self.assertEqual((v["layers"]["sld.diagram"]["name"], v["changed"]), ("291-E-DIAGRAMA", []))
        self.assertIn(0.25, v["options"]["lineweights"])
        self.assertIn("DASHED", v["options"]["linetypes"])

    def test_a_change_is_stored_as_a_difference_and_a_reset_goes_back_to_the_default(self):
        body = {"layers": {"sld.diagram": {"name": "DIAGRAMA", "color": 3, "lineweight": 0.5}}}
        v = self.c.put("/api/layers", json=body).json()
        self.assertEqual((v["layers"]["sld.diagram"]["name"], v["changed"]), ("DIAGRAMA", ["sld.diagram"]))
        stored = json.loads(settings.layers_file.read_text(encoding="utf-8"))["layers"]
        self.assertEqual(stored, {"sld.diagram": {"name": "DIAGRAMA", "color": 3, "lineweight": 0.5}})
        events = [e["action"] for e in self.c.get("/api/identity/audit", params={"limit": 20}).json()]
        self.assertIn("drawing_layers_changed", events)                                       # the change leaves a record
        back = self.c.delete("/api/layers").json()
        self.assertEqual((back["layers"]["sld.diagram"]["name"], back["changed"]), ("291-E-DIAGRAMA", []))
        self.assertFalse(settings.layers_file.exists())
        self.assertIn("drawing_layers_reset", [e["action"] for e in self.c.get("/api/identity/audit", params={"limit": 20}).json()])

    def test_wrong_values_and_unknown_roles_are_refused_and_nothing_is_stored(self):
        bad = self.c.put("/api/layers", json={"layers": {"sld.text": {"name": "291-E-DIAGRAMA", "color": 999}}})
        self.assertEqual(bad.status_code, 422)
        self.assertEqual({"sld.text.name", "sld.text.color"}, set(bad.json()["detail"]["errors"]))
        self.assertEqual(self.c.put("/api/layers", json={"layers": {"nope.x": {"name": "X"}}}).status_code, 422)
        self.assertFalse(settings.layers_file.exists())

    def test_the_plan_dxf_is_delivered_with_the_layers_of_the_catalog(self):
        self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                           "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        base = "/api/projects/ACME/P-1/layout"
        self.c.put(f"{base}/L0", json=DRAWING)
        self.c.put("/api/layers", json={"layers": {"plan.ELEC-TABLERO": {"name": "TABLEROS", "color": 1}}})
        v = self.c.post(f"{base}/L0/generate").json()
        dxf = self.c.get(f"{base}/L0/files/{v['files']['dxf']}").content
        path = self.root / "plan.dxf"
        path.write_bytes(dxf)
        doc = ezdxf.readfile(str(path))
        names = {layer.dxf.name for layer in doc.layers}
        self.assertIn("TABLEROS", names)
        self.assertNotIn("ELEC-TABLERO", names)
        self.assertEqual(doc.layers.get("TABLEROS").color, 1)


if __name__ == "__main__":
    unittest.main()
