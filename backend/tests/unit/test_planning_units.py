"""Pure logic of the planning modules, without HTTP: critical path of the schedule, WBS validation and roll-up, and the cleaning/derivation of register records.
They pin the behaviour as it is today, so a refactoring of the services cannot change it unnoticed."""
import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from epc.core.errors import Invalid
from epc.modules.registers import service as reg
from epc.modules.schedule import repository as sch_repo
from epc.modules.schedule import service as sch
from epc.modules.schedule.models import ScheduleIn
from epc.modules.wbs import repository as wbs_repo
from epc.modules.wbs import service as wbs
from epc.modules.wbs.models import WbsIn


def act(i, start, end, depends=(), milestone=False, progress=0, name=None, wbs_id=""):
    return {"id": i, "name": name if name is not None else f"Act {i}", "start": start, "end": end, "depends_on": list(depends), "milestone": milestone, "progress": progress, "wbs_id": wbs_id}


class TestScheduleValidate(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="schunit_"))

    def test_a_valid_chain_has_no_errors(self):
        self.assertEqual(sch.validate(self.d, [act("A", "2026-01-01", "2026-01-05"), act("B", "2026-01-06", "2026-01-10", ["A"])]), {})

    def test_each_rule_reports_its_own_key_and_message(self):
        acts = [act("A", "2026-01-05", "2026-01-01"), act("A", "bad", "2026-01-01"), act("", "2026-01-01", "2026-01-02", name=" "),
                act("M", "2026-01-01", "2026-01-02", milestone=True), act("P", "2026-01-01", "2026-01-02", progress=101), act("Q", "2026-01-01", "2026-01-02", ["Q", "ZZ"])]
        errors = sch.validate(self.d, acts)
        self.assertEqual(errors["id:A"], "required and unique")
        self.assertEqual(errors["id:"], "required and unique")
        self.assertEqual(errors["name:"], "required")
        self.assertEqual(errors["dates:M"], "a milestone has start = end")
        self.assertEqual(errors["progress:P"], "must be between 0 and 100")
        self.assertEqual(errors["depends_on:Q"], "unknown or self predecessor ZZ")
        self.assertIn(errors["dates:A"], ("end before start", "use ISO dates (YYYY-MM-DD)"))

    def test_a_cycle_is_reported_only_when_nothing_else_is_wrong(self):
        errors = sch.validate(self.d, [act("A", "2026-01-01", "2026-01-02", ["B"]), act("B", "2026-01-03", "2026-01-04", ["A"])])
        self.assertEqual(errors, {"depends_on": "dependencies contain a cycle"})

    def test_a_missing_wbs_node_is_reported(self):
        self.assertEqual(sch.validate(self.d, [act("A", "2026-01-01", "2026-01-02", wbs_id="9.9")]), {"wbs_id:A": "WBS node 9.9 does not exist"})


class TestScheduleCriticalPath(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="schunit_"))

    def run_view(self, acts, today=dt.date(2026, 1, 20)):
        sch_repo.save(self.d, acts)
        with mock.patch.object(sch, "today", return_value=today):
            return sch.view(self.d)

    def test_empty_schedule(self):
        v = self.run_view([])
        self.assertEqual(v, {"activities": [], "start": None, "end": None, "span_days": 0, "critical_path": [], "counts": {"activities": 0, "late": 0, "conflicts": 0}})

    def test_critical_path_slack_late_and_conflicts(self):
        v = self.run_view([act("A", "2026-01-01", "2026-01-05"), act("B", "2026-01-06", "2026-01-15", ["A"], progress=50), act("C", "2026-01-06", "2026-01-08", ["A"]),
                           act("D", "2026-01-14", "2026-01-14", ["B", "C"], milestone=True)])
        by = {a["id"]: a for a in v["activities"]}
        self.assertEqual(v["critical_path"], ["A", "B", "D"])
        self.assertEqual((by["A"]["duration_days"], by["B"]["duration_days"], by["D"]["duration_days"]), (5, 10, 0))
        self.assertEqual(by["C"]["slack_days"], 7)
        self.assertFalse(by["C"]["critical"])
        self.assertTrue(by["B"]["late"] and by["C"]["late"])                    # on the 20th both ended with less than 100 %
        self.assertTrue(by["D"]["conflict"])                                    # the milestone starts before B ends
        self.assertEqual((v["start"], v["end"], v["span_days"]), ("2026-01-01", "2026-01-15", 15))
        self.assertEqual(v["counts"], {"activities": 4, "late": 4, "conflicts": 1})

    def test_replace_validates_then_saves(self):
        with self.assertRaises(Invalid):
            sch.replace(self.d, ScheduleIn(activities=[act("A", "2026-02-01", "2026-01-01")]))
        with mock.patch.object(sch, "today", return_value=dt.date(2026, 1, 1)):
            v = sch.replace(self.d, ScheduleIn(activities=[act("A", "2026-02-01", "2026-02-03")]))
        self.assertEqual(v["counts"]["activities"], 1)


class TestWbs(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="wbsunit_"))

    @staticmethod
    def node(i, weight=1, progress=0, name=None):
        return {"id": i, "name": name if name is not None else f"N{i}", "weight": weight, "progress": progress}

    def test_validation(self):
        errors = wbs.validate([self.node("1"), self.node("1"), self.node("2.1"), self.node("x"), self.node("3", weight=-1), self.node("4", progress=120), self.node("5", name=" ")])
        self.assertEqual(errors["id:1"], "duplicated id")
        self.assertEqual(errors["id:2.1"], "parent 2 does not exist")
        self.assertEqual(errors["id:x"], "WBS ids are dotted numbers such as 1 or 1.2")
        self.assertEqual(errors["weight:3"], "must be >= 0")
        self.assertEqual(errors["progress:4"], "must be between 0 and 100")
        self.assertEqual(errors["name:5"], "required")

    def test_rollup_weights_progress_and_status(self):
        nodes = [self.node("1", 0, 0), self.node("1.1", 3, 100), self.node("1.2", 1, 0), self.node("2", 2, 50), self.node("10", 1, 0)]
        rolled = {n["id"]: n for n in wbs._rollup(nodes)}
        self.assertEqual([n["id"] for n in wbs._rollup(nodes)], ["1", "1.1", "1.2", "2", "10"])           # numeric order, not text order
        self.assertEqual((rolled["1"]["weight"], rolled["1"]["progress"], rolled["1"]["leaf"], rolled["1"]["status"]), (4, 75.0, False, "in_progress"))
        self.assertEqual((rolled["1.1"]["level"], rolled["1.1"]["parent"], rolled["1.1"]["status"]), (2, "1", "done"))
        self.assertEqual(rolled["10"]["status"], "not_started")

    def test_view_overall_progress_and_counts(self):
        wbs_repo.save(self.d, [self.node("1", 3, 100), self.node("2", 1, 0)])
        v = wbs.view(self.d)
        self.assertEqual(v["progress"], 75.0)
        self.assertEqual(v["counts"], {"nodes": 2, "leaves": 2, "done": 1})
        self.assertTrue(wbs.has_node(self.d, "2"))
        self.assertFalse(wbs.has_node(self.d, "3"))
        self.assertEqual(wbs.overall_progress(self.d), 75.0)

    def test_empty_tree_and_zero_weights(self):
        self.assertEqual(wbs.view(self.d)["progress"], 0.0)
        wbs_repo.save(self.d, [self.node("1", 0, 80)])
        self.assertEqual(wbs.view(self.d)["progress"], 0.0)

    def test_replace_sorts_numerically(self):
        v = wbs.replace(self.d, WbsIn(nodes=[self.node("10"), self.node("2"), self.node("1")]))
        self.assertEqual([n["id"] for n in v["nodes"]], ["1", "2", "10"])
        with self.assertRaises(Invalid):
            wbs.replace(self.d, WbsIn(nodes=[self.node("2.1")]))


REGISTER = {"id": "risk", "prefix": "RIE", "closed_states": ["closed"], "derive": "risk_level", "fields": [
    {"id": "title", "type": "text", "required": True, "label": {"es": "T", "en": "T"}},
    {"id": "notes", "type": "longtext", "label": {"es": "N", "en": "N"}},
    {"id": "probability", "type": "number", "min": 1, "max": 5, "label": {"es": "P", "en": "P"}},
    {"id": "impact", "type": "number", "min": 1, "max": 5, "label": {"es": "I", "en": "I"}},
    {"id": "due", "type": "date", "label": {"es": "D", "en": "D"}},
    {"id": "status", "type": "enum", "default": "open", "options": [{"id": "open", "es": "A", "en": "O"}, {"id": "closed", "es": "C", "en": "C"}], "label": {"es": "E", "en": "S"}}]}


class TestRegisterClean(unittest.TestCase):
    def test_a_valid_record_is_cleaned_and_typed(self):
        out = reg._clean(REGISTER, {"title": " Fuga ", "probability": "4", "impact": 5, "due": "2026-10-23", "status": "closed", "notes": ""}, creating=True)
        self.assertEqual(out, {"title": "Fuga", "probability": 4, "impact": 5, "due": "2026-10-23", "status": "closed", "notes": ""})

    def test_errors_are_collected_by_field(self):
        with self.assertRaises(Invalid) as cm:
            reg._clean(REGISTER, {"unknown": 1, "probability": "x", "impact": 9, "due": "23/10", "status": "nope", "notes": "x" * 4001}, creating=True)
        e = cm.exception.detail["errors"]
        self.assertEqual(e["unknown"], "unknown field")
        self.assertEqual(e["title"], "required")
        self.assertEqual(e["probability"], "a whole number")
        self.assertEqual(e["impact"], "between 1 and 5")
        self.assertEqual(e["due"], "ISO date, e.g. 2026-10-23")
        self.assertEqual(e["status"], "one of open, closed")
        self.assertEqual(e["notes"], "at most 4000 characters")

    def test_empty_values(self):
        self.assertEqual(reg._clean(REGISTER, {"probability": "", "due": None, "notes": " "}, creating=False), {"probability": None, "due": None, "notes": ""})
        with self.assertRaises(Invalid):
            reg._clean(REGISTER, {"title": " "}, creating=False)

    def test_text_limit(self):
        with self.assertRaises(Invalid) as cm:
            reg._clean(REGISTER, {"title": "x" * 301}, creating=True)
        self.assertEqual(cm.exception.detail["errors"]["title"], "at most 300 characters")


class TestRegisterDerive(unittest.TestCase):
    def test_risk_level_thresholds(self):
        for p, i, level, name in ((1, 1, 1, "low"), (1, 2, 2, "low"), (1, 3, 3, "medium"), (4, 4, 16, "medium"), (4, 5, 20, "high"), (5, 5, 25, "high"), (None, 5, 0, "low")):
            rec = {"probability": p, "impact": i}
            reg._derive(REGISTER, rec)
            self.assertEqual((rec["level"], rec["level_name"]), (level, name), (p, i))

    def test_no_derivation_for_other_registers(self):
        rec = {"probability": 5, "impact": 5}
        reg._derive({"id": "change"}, rec)
        self.assertEqual(rec, {"probability": 5, "impact": 5})


if __name__ == "__main__":
    unittest.main()
