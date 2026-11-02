"""The typical values of the receptacles engine (outlets per use, mounting heights, outlets per circuit) are reviewed once, in the norms review, for every project."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app
from epc.modules.norms import repository

UNIT = "table:receptacles-valores-tipicos"


class TestReceptacleValues(unittest.TestCase):
    def setUp(self):
        from epc_receptacles import config
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copy2(config.USES, self.root / "uses.json")
        real = repository.paths()
        repository.override({**real, "receptacle_values": self.root / "uses.json", "review": self.root / "review.json", "log": self.root / "review-log.jsonl"})
        self._old = (settings.role, settings.user)
        settings.role, settings.user = "standards", "Ing. Revisor"
        self.c = TestClient(create_app())
        self.base = "/api/norms"

    def tearDown(self):
        repository.override(None)
        settings.role, settings.user = self._old
        self.tmp.cleanup()

    def file(self):
        return json.loads((self.root / "uses.json").read_text(encoding="utf-8"))

    def test_the_unit_lists_every_typical_value_as_a_point_to_confirm(self):
        units = {u["id"]: u for u in self.c.get(f"{self.base}/units").json()}
        self.assertEqual(units[UNIT]["counts"]["approved"], 0)
        self.assertEqual(units[UNIT]["counts"]["pending"], units[UNIT]["counts"]["total"])
        pts = self.c.get(f"{self.base}/units/{UNIT}/points").json()["items"]
        self.assertEqual({p["group"] for p in pts}, {"Cantidad de tomacorrientes por uso del ambiente", "Alturas de montaje", "Tomacorrientes por circuito"})
        keys = {p["key"] for p in pts}
        self.assertTrue({"uses:office", "uses:warehouse", "mounting:771", "circuits:TUG"} <= keys)
        self.assertNotIn("uses:note", keys)                                                          # the notes are not values to confirm

    def test_correcting_a_use_rewrites_the_data_file_and_approving_it_is_recorded(self):
        key = "uses:office"
        d = self.c.get(f"{self.base}/units/{UNIT}/points/{key}").json()
        self.assertEqual((d["value"]["per_m2"], d["status"]), (9, "pending"))
        r = self.c.put(f"{self.base}/units/{UNIT}/points/{key}", json={"patch": {"value": {**d["value"], "per_m2": 6}}, "note": "criterio del cliente", "approve": True})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual((self.file()["uses"]["office"]["per_m2"], r.json()["status"]), (6, "approved"))
        self.assertEqual(self.file()["uses"]["classroom"]["per_m"], 4)                              # the other uses are not touched

    def test_a_corrected_value_is_read_by_the_engine_after_the_cache_is_cleared(self):
        from epc_receptacles import config
        config.clear_cache()
        self.assertEqual(config.data("uses")["uses"]["office"]["per_m2"], 9)


if __name__ == "__main__":
    unittest.main()
