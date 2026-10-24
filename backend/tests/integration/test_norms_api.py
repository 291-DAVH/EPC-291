"""Norm review: every rule, calculation table and design criterion can be corrected and approved by a norm reviewer; the data files are rewritten in place."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app
from epc.modules.norms import repository

RULE = "tomacorrientes.altura_arista_inferior_771"
UNIT_771 = "rule:aea-90364-7-771-2006"
TABLES = "table:aea-calculo"
CRIT = "criterion:ar-electrical"


class TestNorms(unittest.TestCase):
    def setUp(self):
        import epc_calc
        pkg = Path(epc_calc.__file__).parent
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "rules").mkdir()
        for f in (pkg / "rules").glob("*.json"):
            shutil.copy2(f, self.root / "rules" / f.name)
        shutil.copy2(pkg / "aea_tables.json", self.root / "aea_tables.json")
        shutil.copy2(settings.engine / "jurisdictions" / "AR" / "electrical" / "design-criteria.json", self.root / "design-criteria.json")
        cat = json.loads((self.root / "design-criteria.json").read_text(encoding="utf-8"))
        cat["validated"] = False                                            # start from an unreviewed catalog whatever the real one says now
        repository.write_atomic(self.root / "design-criteria.json", repository.dumps_criteria(cat))
        repository.override({"rules": self.root / "rules", "tables": self.root / "aea_tables.json", "criteria": self.root / "design-criteria.json",
                             "review": self.root / "review.json", "log": self.root / "review-log.jsonl"})
        self._old = (settings.role, settings.user)
        settings.role, settings.user = "standards", "Ing. Revisor"
        self.c = TestClient(create_app())
        self.base = "/api/norms"

    def tearDown(self):
        repository.override(None)
        settings.role, settings.user = self._old
        self.tmp.cleanup()

    def read(self, name):
        return json.loads((self.root / name).read_text(encoding="utf-8"))

    def test_the_reviewer_sees_every_norm_with_its_points(self):
        units = {u["id"]: u for u in self.c.get(f"{self.base}/units").json()}
        self.assertEqual(units[UNIT_771]["counts"], {"total": 82, "approved": 0, "rejected": 0, "pending": 82, "stale": 0})
        self.assertEqual(sum(u["counts"]["total"] for u in units.values() if u["kind"] == "rule"), 177)
        self.assertEqual((units[TABLES]["counts"]["total"], units[CRIT]["counts"]["total"]), (29, len(self.read("design-criteria.json")["criteria"])))
        self.assertIn("AEA 90364-7-771 (2006)", units[UNIT_771]["name"])
        pts = self.c.get(f"{self.base}/units/{UNIT_771}/points?q=tomacorriente").json()
        self.assertTrue(pts["total"] >= 1 and all(p["status"] == "pending" for p in pts["items"]))
        self.assertEqual(self.c.get(f"{self.base}/units/{UNIT_771}/points?status=approved").json()["total"], 0)
        d = self.c.get(f"{self.base}/units/{UNIT_771}/points/{RULE}").json()
        self.assertEqual((d["kind"], d["status"], d["value"]["parametros"]["altura_min_m"]), ("rule", "pending", 0.15))
        self.assertIn("parametros", d["editable"])
        self.assertEqual(self.c.get(f"{self.base}/units/nope/points").status_code, 404)
        self.assertEqual(self.c.get(f"{self.base}/units/{UNIT_771}/points/nope").status_code, 404)

    def test_approve_records_who_when_and_the_value(self):
        r = self.c.post(f"{self.base}/units/{UNIT_771}/points/{RULE}/approve", json={"note": "Contrastado con la norma"}).json()
        self.assertEqual((r["status"], r["review"]["by"], r["review"]["note"]), ("approved", "Ing. Revisor", "Contrastado con la norma"))
        self.assertTrue(r["review"]["at"] and len(r["review"]["sha"]) == 64)
        self.assertEqual(r["history"][0]["action"], "approved")
        counts = {u["id"]: u["counts"] for u in self.c.get(f"{self.base}/units").json()}[UNIT_771]
        self.assertEqual((counts["approved"], counts["pending"]), (1, 81))

    def test_editing_a_rule_rewrites_its_file_and_needs_a_new_approval(self):
        self.c.post(f"{self.base}/units/{UNIT_771}/points/{RULE}/approve")
        before = {f.name: f.read_bytes() for f in (self.root / "rules").glob("*.json")}
        r = self.c.put(f"{self.base}/units/{UNIT_771}/points/{RULE}", json={"patch": {"parametros": {"altura_min_m": 0.2, "referencia": "arista inferior de la caja"}}, "note": "Corrige a 0,20 m"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["status"], "pending")                      # a new value is not approved yet
        self.assertEqual(r.json()["history"][0]["changes"], [["parametros/altura_min_m", 0.15, 0.2]])
        after = {f.name: f.read_bytes() for f in (self.root / "rules").glob("*.json")}
        self.assertEqual([n for n in after if after[n] != before[n]], ["tomacorrientes.json"])      # only the file of that group changed
        old_lines, new_lines = before["tomacorrientes.json"].decode().splitlines(), after["tomacorrientes.json"].decode().splitlines()
        self.assertEqual(sum(1 for a, b in zip(old_lines, new_lines) if a != b), 1)                   # and only that line: the formatting is preserved
        self.assertEqual(len(old_lines), len(new_lines))
        ok = self.c.put(f"{self.base}/units/{UNIT_771}/points/{RULE}", json={"patch": {"tipo": "recomendado"}, "approve": True}).json()
        self.assertEqual((ok["status"], ok["value"]["tipo"], ok["history"][0]["action"]), ("approved", "recomendado", "edited_approved"))

    def test_rule_validation(self):
        url = f"{self.base}/units/{UNIT_771}/points/{RULE}"
        for patch, field in (({"tipo": "quizás"}, "tipo"), ({"regla": " "}, "regla"), ({"parametros": [1]}, "parametros"), ({"aplica_a": "viviendas"}, "aplica_a"),
                             ({"fuente": {"libro": "x"}}, "fuente"), ({"id": "otro"}, "id")):
            r = self.c.put(url, json={"patch": patch})
            self.assertEqual(r.status_code, 422, patch)
            self.assertIn(field, r.json()["detail"]["errors"])
        self.assertEqual(self.c.put(url, json={"patch": {"tema": d_tema(self)}}).status_code, 422)     # nothing changed

    def test_tables_keep_their_shape_and_the_engine_reloads(self):
        from epc_calc import aea_tables
        key = "const:771.13_pen_minima_mm2"
        url = f"{self.base}/units/{TABLES}/points/{key}"
        d = self.c.get(url).json()
        self.assertEqual(d["value"], {"cu": 10.0, "al": 16.0})
        for bad in ({"cu": 10.0}, {"cu": 10.0, "al": "16"}, {"cu": 10.0, "al": 16.0, "mg": 1}, [10, 16]):
            r = self.c.put(url, json={"patch": {"value": bad}})
            self.assertEqual(r.status_code, 422, bad)
        aea_tables._CACHE["marker"] = {}
        r = self.c.put(url, json={"patch": {"value": {"cu": 10.0, "al": 25.0}}, "note": "Valor de la tabla corregido", "approve": True})
        self.assertEqual((r.status_code, r.json()["status"]), (200, "approved"))
        self.assertEqual(self.read("aea_tables.json")["constantes"]["771.13_pen_minima_mm2"], {"cu": 10.0, "al": 25.0})
        self.assertNotIn("marker", aea_tables._CACHE)                          # the calculation engine reads the corrected file
        self.assertEqual(self.c.put(f"{self.base}/units/{TABLES}/points/cap:771.16.I", json={"patch": {"x": 1}}).status_code, 422)

    def test_criteria_are_validated_only_when_all_are_approved(self):
        self.assertFalse(self.read("design-criteria.json")["validated"])
        pts = self.c.get(f"{self.base}/units/{CRIT}/points").json()["items"]
        n = len(self.read("design-criteria.json")["criteria"])
        self.assertEqual(len(pts), n)                                          # one review point per criterion of the catalog
        url = f"{self.base}/units/{CRIT}/points/vd_sectional_pct"
        for patch, field in (({"default": 50}, "default"), ({"options": [1, 2]}, "options"), ({"label": {"es": "x"}}, "label"), ({"group": {}}, "group")):
            r = self.c.put(url, json={"patch": patch})
            self.assertEqual(r.status_code, 422, patch)
            self.assertIn(field, r.json()["detail"]["errors"])
        r = self.c.put(url, json={"patch": {"default": 1.5}, "approve": True})
        self.assertEqual(r.status_code, 200, r.text)
        cat = self.read("design-criteria.json")
        self.assertEqual(next(c for c in cat["criteria"] if c["id"] == "vd_sectional_pct")["default"], 1.5)
        self.assertEqual(len(cat["criteria"]), n)
        self.assertFalse(cat["validated"])
        for p in pts:
            self.c.post(f"{self.base}/units/{CRIT}/points/{p['key']}/approve")
        self.assertTrue(self.read("design-criteria.json")["validated"])
        self.c.put(url, json={"patch": {"default": 2}})                         # one value changes again: the catalog is no longer fully validated
        self.assertFalse(self.read("design-criteria.json")["validated"])
        # the design pipeline reads the corrected catalog
        from epc_drawing import board_design
        self.assertTrue(board_design.catalog_defaults() is not None)

    def test_a_value_changed_after_approval_is_stale(self):
        self.c.post(f"{self.base}/units/{UNIT_771}/points/{RULE}/approve")
        f = self.root / "rules" / "tomacorrientes.json"
        f.write_text(f.read_text(encoding="utf-8").replace('"altura_min_m": 0.15', '"altura_min_m": 0.18', 1), encoding="utf-8")      # changed outside the review (e.g. a merge)
        self.assertEqual(self.c.get(f"{self.base}/units/{UNIT_771}/points/{RULE}").json()["status"], "stale")
        self.assertEqual({u["id"]: u["counts"] for u in self.c.get(f"{self.base}/units").json()}[UNIT_771]["stale"], 1)

    def test_rejecting_needs_a_reason_and_everything_is_logged(self):
        url = f"{self.base}/units/{UNIT_771}/points/{RULE}"
        self.assertEqual(self.c.post(url + "/reject", json={"note": " "}).status_code, 422)
        r = self.c.post(url + "/reject", json={"note": "La altura no coincide con la cláusula"}).json()
        self.assertEqual((r["status"], r["review"]["note"]), ("rejected", "La altura no coincide con la cláusula"))
        self.c.post(url + "/approve")
        log = self.c.get(f"{self.base}/log").json()
        self.assertEqual([(e["action"], e["by"]) for e in log[:2]], [("approved", "Ing. Revisor"), ("rejected", "Ing. Revisor")])
        self.assertTrue((self.root / "review-log.jsonl").read_text(encoding="utf-8").count("\n") == 2)

    def test_only_reviewers_and_staff_reach_the_norms(self):
        self.assertEqual(self.c.get("/api/me").json()["role"], "standards")
        self.assertEqual(self.c.get(f"{self.base}/units").status_code, 200)
        for path in ("/api/app/portfolio", "/api/projects/options", "/api/plugins", "/api/projects", "/api/rules/standards", "/api/identity/users", "/api/app/org"):
            self.assertEqual(self.c.get(path).status_code, 403, path)
        self.assertEqual(self.c.post("/api/projects", json={}).status_code, 403)
        settings.role = "user"
        self.assertEqual(self.c.get(f"{self.base}/units").status_code, 403)
        self.assertEqual(self.c.put(f"{self.base}/units/{UNIT_771}/points/{RULE}", json={"patch": {"tipo": "prohibido"}}).status_code, 403)
        settings.role = "admin"
        self.assertEqual(self.c.get(f"{self.base}/units").status_code, 200)


def d_tema(case):
    return case.c.get(f"{case.base}/units/{UNIT_771}/points/{RULE}").json()["value"]["tema"]


if __name__ == "__main__":
    unittest.main()
