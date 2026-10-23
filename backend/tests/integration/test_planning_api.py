"""WBS, schedule and backlog through the HTTP API."""
import json
import tempfile
import unittest
from pathlib import Path

import jsonschema
from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app

SCHEMAS = Path(__file__).resolve().parents[3] / "shared" / "schemas"


def schema(name):
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role)
        settings.projects_dir, settings.role = self.root, "admin"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.base = "/api/projects/ACME/P-1"
        self.user_base = "/api/app/projects/ACME/P-1"
        self.file = lambda n: self.root / "ACME" / "P-1" / "workspace" / "05-management" / n

    def tearDown(self):
        settings.projects_dir, settings.role = self._old
        self.tmp.cleanup()


class TestWbs(Base):
    nodes = [{"id": "1", "name": "Engineering"}, {"id": "1.1", "name": "Calculations", "weight": 3, "progress": 100},
             {"id": "1.2", "name": "Drawings", "weight": 1, "progress": 0}, {"id": "2", "name": "Procurement", "weight": 4, "progress": 50}]

    def test_template_starts_empty(self):
        v = self.c.get(f"{self.user_base}/wbs").json()
        self.assertEqual((v["nodes"], v["progress"]), ([], 0))

    def test_rollup_is_weighted(self):
        r = self.c.put(f"{self.base}/wbs", json={"nodes": self.nodes})
        self.assertEqual(r.status_code, 200, r.text)
        by = {n["id"]: n for n in r.json()["nodes"]}
        self.assertEqual(by["1"]["progress"], 75.0)            # (3*100 + 1*0) / 4
        self.assertEqual(by["1"]["weight"], 4)
        self.assertEqual(by["1.1"]["status"], "done")
        self.assertEqual(by["1"]["status"], "in_progress")
        self.assertFalse(by["1"]["leaf"])
        self.assertEqual(r.json()["progress"], 62.5)           # (4*75 + 4*50) / 8
        self.assertEqual(r.json()["counts"], {"nodes": 4, "leaves": 3, "done": 1})
        jsonschema.validate(json.loads(self.file("wbs.json").read_text(encoding="utf-8")), schema("wbs"))

    def test_validation(self):
        for nodes, key in [([{"id": "1.1", "name": "orphan"}], "id:1.1"), ([{"id": "a", "name": "x"}], "id:a"),
                           ([{"id": "1", "name": "x"}, {"id": "1", "name": "y"}], "id:1"), ([{"id": "1", "name": " "}], "name:1"),
                           ([{"id": "1", "name": "x", "progress": 120}], "progress:1"), ([{"id": "1", "name": "x", "weight": -1}], "weight:1")]:
            r = self.c.put(f"{self.base}/wbs", json={"nodes": nodes})
            self.assertEqual(r.status_code, 422, nodes)
            self.assertIn(key, r.json()["detail"]["errors"])

    def test_users_can_read_but_not_write(self):
        self.c.put(f"{self.base}/wbs", json={"nodes": self.nodes})
        settings.role = "user"
        self.assertEqual(self.c.get(f"{self.user_base}/wbs").status_code, 200)
        self.assertEqual(self.c.put(f"{self.base}/wbs", json={"nodes": []}).status_code, 403)


class TestSchedule(Base):
    def acts(self, **over):
        a = [{"id": "A", "name": "Design", "start": "2026-01-05", "end": "2026-01-14"},
             {"id": "B", "name": "Review", "start": "2026-01-15", "end": "2026-01-19", "depends_on": ["A"]},
             {"id": "C", "name": "Side task", "start": "2026-01-15", "end": "2026-01-16", "depends_on": ["A"]},
             {"id": "M", "name": "Issue", "start": "2026-01-20", "end": "2026-01-20", "depends_on": ["B", "C"], "milestone": True}]
        return a

    def test_critical_path_and_slack(self):
        r = self.c.put(f"{self.base}/schedule", json={"activities": self.acts()})
        self.assertEqual(r.status_code, 200, r.text)
        v = r.json()
        by = {a["id"]: a for a in v["activities"]}
        self.assertEqual(v["critical_path"], ["A", "B", "M"])
        self.assertEqual(by["C"]["slack_days"], 3)             # B lasts 5 days, C 2
        self.assertFalse(by["C"]["critical"])
        self.assertEqual((v["start"], v["end"], v["span_days"]), ("2026-01-05", "2026-01-20", 16))
        self.assertEqual(by["M"]["duration_days"], 0)
        self.assertEqual(v["counts"]["conflicts"], 0)
        self.assertEqual(v["counts"]["late"], 3 + 1)           # all dates are in the past, none at 100 %
        jsonschema.validate(json.loads(self.file("schedule.json").read_text(encoding="utf-8")), schema("schedule"))

    def test_conflict_when_dates_overlap_a_predecessor(self):
        a = self.acts()
        a[1]["start"] = "2026-01-10"
        v = self.c.put(f"{self.base}/schedule", json={"activities": a}).json()
        self.assertEqual([x["id"] for x in v["activities"] if x["conflict"]], ["B"])

    def test_validation(self):
        base = self.acts()
        cases = [({"dates:A": "end before start"}, lambda a: a[0].update(end="2026-01-01")),
                 ({"dates:A": "x"}, lambda a: a[0].update(start="yesterday")),
                 ({"depends_on:B": "x"}, lambda a: a[1].update(depends_on=["Z"])),
                 ({"depends_on": "x"}, lambda a: a[0].update(depends_on=["B"])),
                 ({"wbs_id:A": "x"}, lambda a: a[0].update(wbs_id="9.9")),
                 ({"dates:M": "x"}, lambda a: a[3].update(end="2026-01-21"))]
        for expect, mutate in cases:
            a = json.loads(json.dumps(base))
            mutate(a)
            r = self.c.put(f"{self.base}/schedule", json={"activities": a})
            self.assertEqual(r.status_code, 422, expect)
            self.assertIn(next(iter(expect)), r.json()["detail"]["errors"])

    def test_activity_links_to_existing_wbs_node(self):
        self.c.put(f"{self.base}/wbs", json={"nodes": [{"id": "1", "name": "Eng"}]})
        a = self.acts()
        a[0]["wbs_id"] = "1"
        self.assertEqual(self.c.put(f"{self.base}/schedule", json={"activities": a}).status_code, 200)
        self.assertEqual(self.c.get(f"{self.user_base}/schedule").json()["activities"][0]["wbs_id"], "1")


class TestBacklog(Base):
    def test_create_update_and_counts(self):
        r = self.c.post(f"{self.base}/backlog", json={"title": "Check short-circuit levels", "priority": "P1", "estimate_h": 6})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual((r.json()["id"], r.json()["status"], r.json()["type"]), ("BL-001", "backlog", "task"))
        self.assertEqual(self.c.post(f"{self.base}/backlog", json={"title": "Ask about UPS", "type": "question"}).json()["id"], "BL-002")
        p = self.c.patch(f"{self.base}/backlog/BL-001", json={"status": "doing"})
        self.assertEqual(p.json()["status"], "doing")
        v = self.c.get(f"{self.base}/backlog").json()
        self.assertEqual(v["counts"], {"backlog": 1, "todo": 0, "doing": 1, "done": 0})
        self.assertEqual(v["estimate_open_h"], 6)
        self.c.patch(f"{self.base}/backlog/BL-001", json={"status": "done"})
        self.assertEqual(self.c.get(f"{self.base}/backlog").json()["estimate_open_h"], 0)
        jsonschema.validate(json.loads(self.file("backlog.json").read_text(encoding="utf-8")), schema("backlog"))

    def test_validation_and_not_found(self):
        for body, key in [({"title": " "}, "title"), ({"title": "x", "type": "idea"}, "type"), ({"title": "x", "priority": "P9"}, "priority"),
                          ({"title": "x", "estimate_h": -2}, "estimate_h"), ({"title": "x", "wbs_id": "7"}, "wbs_id")]:
            r = self.c.post(f"{self.base}/backlog", json=body)
            self.assertEqual(r.status_code, 422, body)
            self.assertIn(key, r.json()["detail"]["errors"])
        self.assertEqual(self.c.patch(f"{self.base}/backlog/BL-999", json={"status": "done"}).status_code, 404)
        self.c.post(f"{self.base}/backlog", json={"title": "ok"})
        self.assertEqual(self.c.patch(f"{self.base}/backlog/BL-001", json={"status": "nope"}).status_code, 422)

    def test_backlog_is_internal(self):
        settings.role = "user"
        self.assertEqual(self.c.get(f"{self.base}/backlog").status_code, 403)
        self.assertEqual(self.c.post(f"{self.base}/backlog", json={"title": "x"}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
