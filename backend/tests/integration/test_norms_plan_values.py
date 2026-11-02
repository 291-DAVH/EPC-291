"""The typical values of cables, conduits and trays are reviewed once, in the norms review, for every project: the same page as the standards."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app
from epc.modules.norms import repository

UNIT = "table:plan-valores-tipicos"


class TestPlanValues(unittest.TestCase):
    def setUp(self):
        from epc_plan import core
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copy2(core.TYPICAL, self.root / "typical-values.json")
        real = repository.paths()
        repository.override({**real, "plan_values": self.root / "typical-values.json", "review": self.root / "review.json", "log": self.root / "review-log.jsonl"})
        self._old = (settings.role, settings.user)
        settings.role, settings.user = "standards", "Ing. Revisor"
        self.c = TestClient(create_app())
        self.base = "/api/norms"

    def tearDown(self):
        repository.override(None)
        settings.role, settings.user = self._old
        self.tmp.cleanup()

    def file(self):
        return json.loads((self.root / "typical-values.json").read_text(encoding="utf-8"))

    def test_the_unit_lists_every_typical_value_as_a_point_to_confirm(self):
        units = {u["id"]: u for u in self.c.get(f"{self.base}/units").json()}
        self.assertEqual(units[UNIT]["counts"], {"total": 7, "approved": 0, "rejected": 0, "pending": 7, "stale": 0})
        pts = self.c.get(f"{self.base}/units/{UNIT}/points").json()["items"]
        self.assertEqual({p["group"] for p in pts}, {"Cables y canalizaciones", "Llenado de canalizaciones", "Diseño automático de circuitos"})
        self.assertIn("sizing:conduit_mm", {p["key"] for p in pts})

    def test_correcting_a_value_rewrites_the_data_file_and_approving_it_is_recorded(self):
        key = "occupancy:tray_pct"
        d = self.c.get(f"{self.base}/units/{UNIT}/points/{key}").json()
        self.assertEqual((d["value"], d["status"]), (50, "pending"))
        r = self.c.put(f"{self.base}/units/{UNIT}/points/{key}", json={"patch": {"value": 40}, "note": "catálogo del proveedor", "approve": True})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual((self.file()["occupancy"]["tray_pct"], r.json()["status"]), (40, "approved"))
        again = self.c.put(f"{self.base}/units/{UNIT}/points/sizing:conduit_mm", json={"patch": {"value": [16, 20, 25]}})
        self.assertEqual(again.status_code, 422)                                                # the list of commercial sizes keeps its length: the reviewer corrects, does not reshape

    def test_the_engine_reads_the_corrected_values_without_restarting(self):
        from epc_plan import core, sizing
        key = "occupancy:default_cable_mm"
        self.assertEqual(sizing.cable_mm(None, core.PARAMS["sizing"], core.PARAMS["occupancy"]["default_cable_mm"]), 14.0)
        # the corrected values live in the data file the engine reads: put the temporary copy where the engine looks and ask the module to read it again
        original = core.TYPICAL
        try:
            core.TYPICAL = self.root / "typical-values.json"
            self.c.put(f"{self.base}/units/{UNIT}/points/{key}", json={"patch": {"value": 20.0}})
            self.assertEqual(core.PARAMS["occupancy"]["default_cable_mm"], 20.0)
        finally:
            core.TYPICAL = original
            core.reload_params()
        self.assertEqual(core.PARAMS["occupancy"]["default_cable_mm"], 14.0)


if __name__ == "__main__":
    unittest.main()
