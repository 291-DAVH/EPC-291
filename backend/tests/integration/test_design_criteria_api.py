"""Design criteria: view, quick edit (client requirement), reset, history and generated report."""
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc_aea90364 import norm_data
from epc.core.config import settings
from epc.main import create_app


def catalog() -> dict:
    """The real catalog: the tests follow its current state (the norm reviewer corrects and validates it), they do not freeze its values."""
    return json.loads((norm_data.criteria_file("electrical")).read_text(encoding="utf-8"))


class TestDesignCriteria(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role)
        settings.projects_dir, settings.role = self.root, "admin"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.base = "/api/projects/ACME/P-1/engineering/criteria"
        self.file = self.root / "ACME" / "P-1" / "workspace" / "00-setup" / "design-criteria.json"

    def tearDown(self):
        settings.projects_dir, settings.role = self._old
        self.tmp.cleanup()

    def item(self, view, key):
        return next(i for i in view["items"] if i["id"] == key)

    def test_defaults_come_from_the_catalog(self):
        v = self.c.get(self.base).json()
        self.assertEqual((v["jurisdiction"], v["discipline"], v["validated"], v["changed"]), ("AR", "electrical", catalog()["validated"], 0))
        s = self.item(v, "socket_height_m")
        self.assertEqual((s["value"], s["default"], s["overridden"], s["source"]), (0.3, 0.3, False, "default"))
        self.assertTrue(s["label"]["es"] and s["group"]["en"])

    def test_change_socket_height_for_the_client(self):
        r = self.c.put(self.base + "/socket_height_m", json={"value": 1, "source": "client", "note": "Pedido por el cliente en reunión del 20/10"})
        self.assertEqual(r.status_code, 200, r.text)
        s = self.item(r.json(), "socket_height_m")
        self.assertEqual((s["value"], s["overridden"], s["source"]), (1.0, True, "client"))
        self.assertEqual(r.json()["changed"], 1)
        self.assertEqual(r.json()["history"][0]["from"], 0.3)
        saved = json.loads(self.file.read_text(encoding="utf-8"))
        self.assertEqual(saved["overrides"]["electrical"]["socket_height_m"]["value"], 1.0)

    def test_choice_and_validation(self):
        ok = self.c.put(self.base + "/rcd_sensitivity_ma", json={"value": "300", "source": "project"})
        self.assertEqual(self.item(ok.json(), "rcd_sensitivity_ma")["value"], 300)         # normalized to the catalog option
        for key, body in [("socket_height_m", {"value": 9}), ("socket_height_m", {"value": "abc"}), ("rcd_sensitivity_ma", {"value": 25}),
                          ("socket_height_m", {"value": 1, "source": "boss"}), ("socket_height_m", {"value": 1, "note": "x" * 301})]:
            r = self.c.put(f"{self.base}/{key}", json=body)
            self.assertEqual(r.status_code, 422, body)
        self.assertEqual(self.c.put(self.base + "/nope", json={"value": 1}).status_code, 404)
        self.assertEqual(self.c.get(self.base, params={"discipline": "hvac"}).status_code, 404)
        self.assertEqual(self.c.get(self.base, params={"discipline": "../x"}).status_code, 422)

    def test_reset_and_history(self):
        self.c.put(self.base + "/socket_height_m", json={"value": 1, "source": "client"})
        v = self.c.delete(self.base + "/socket_height_m").json()
        self.assertEqual((self.item(v, "socket_height_m")["value"], v["changed"]), (0.3, 0))
        self.assertEqual([(h["from"], h["to"]) for h in v["history"]], [(1.0, 0.3), (0.3, 1.0)])      # newest first
        self.assertEqual(self.c.delete(self.base + "/socket_height_m").status_code, 200)            # idempotent

    def test_report_lists_changes_in_the_project_language(self):
        self.c.put(self.base + "/socket_height_m", json={"value": 1, "source": "client", "note": "Pedido del cliente"})
        es = self.c.get(self.base + "/report").json()["markdown"]
        self.assertIn("Altura de tomacorrientes**: 1.0 m (pedido del cliente) - Pedido del cliente", es)
        self.assertEqual("sin validar" in es, not catalog()["validated"])        # the report warns only while the catalog is not validated
        en = self.c.get(self.base + "/report", params={"lang": "en"}).json()["markdown"]
        self.assertIn("Socket outlets height**: 1.0 m (client requirement)", en)

    def test_users_cannot_edit(self):
        settings.role = "auditor"            # reviews only: the engineering is for the engineering team and the organization that owns the project
        self.assertEqual(self.c.get(self.base).status_code, 403)
        self.assertEqual(self.c.put(self.base + "/socket_height_m", json={"value": 1}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
