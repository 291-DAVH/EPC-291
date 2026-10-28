"""The differential groups of the standard solutions reach the board design: the memo, the single-line and the multi-line draw them as any group."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import characterization as C   # noqa: E402

from epc_aea90364 import solutions as S   # noqa: E402


def board():
    d = {"board": C.board("TGBT-01"), "titleblock": C.TB, "circuits": [C.circuit(f"L-{i:02d}", "ILUMINACION", 1.0, phase="1F", length=20) for i in range(1, 5)]}
    d["circuits"].append(C.circuit("M-01", "BOMBA", 7.5, topology="dol_ol", length=30))
    return d


class TestGroupsInDesign(unittest.TestCase):
    def run_design(self, solutions_file=None):
        with tempfile.TemporaryDirectory() as t:
            if solutions_file:
                os.environ[S.ENV_VAR] = str(solutions_file)
            try:
                summary = C.B.design(board(), Path(t) / "work", "T1", None, None, 18, ("sld", "mld"))
            finally:
                os.environ.pop(S.ENV_VAR, None)
            out = Path(t) / "work" / "out"
            return summary, (out / "SLD_T1_TABLA.svg").read_text(encoding="utf-8"), (out / "MLD_T1.svg").read_text(encoding="utf-8"), json.loads((out / "T1_dimensionado.json").read_text(encoding="utf-8"))

    def test_with_the_rules_off_there_are_no_groups_and_with_them_on_the_lighting_hangs_from_one(self):
        summary, table, _, calc = self.run_design()
        self.assertEqual((summary["groups"], "GD-L01" in calc), ({}, False))
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "solutions.json"
            rule = S.defaults()["groups"]["differential-lighting"]
            rule["enabled"] = True
            f.write_text(json.dumps({"groups": {"differential-lighting": rule}}), encoding="utf-8")
            summary, table, mld, calc = self.run_design(f)
        self.assertEqual(summary["groups"], {"GD-L01": ["L-01", "L-02", "L-03", "L-04"]})
        self.assertEqual(calc["GD-L01"]["disp"], "RCCB 2P 25 A 30 mA")
        self.assertIn("GD-L01", table)                                             # the table of the single-line lists the group like any circuit
        self.assertIn("lv_rccb_2p_mld", mld)                                       # the multi-line draws its differential and the circuits behind it
        self.assertIn(">L-04<", mld)
        self.assertTrue(summary["ok"], summary.get("error"))


if __name__ == "__main__":
    unittest.main()
