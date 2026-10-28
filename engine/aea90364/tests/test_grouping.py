"""Automatic groups of differentials: which circuits are put behind one and how many each differential serves."""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from epc_aea90364 import aea_pipeline as P  # noqa: E402
from epc_aea90364 import grouping as G  # noqa: E402
from epc_aea90364 import solutions as S  # noqa: E402
from test_aea_pipeline import CIRC, TABLERO  # noqa: E402


def lighting(n, kw=1.0, kind="auto", phase="1F"):
    return {"TAG": f"L-{n:02d}", "DESCRIPCION": "ILUMINACION", "CARGA": kw, "UNIDAD_CARGA": "kW", "TOPOLOGY": "single", "FASE": phase, "LONGITUD_m": 20, "FP": 0.9, "KIND": kind}


def doc(enabled=True, **changes):
    d = S.load()
    for rule in d["groups"].values():
        rule["enabled"] = enabled
        rule.update(changes)
    return d


class TestPlan(unittest.TestCase):
    def test_nothing_changes_while_the_rules_are_off(self):
        self.assertEqual(G.plan(TABLERO, [lighting(i) for i in range(1, 5)], None, doc(False)), [])
        self.assertEqual(S.validate(S.defaults()), {})

    def test_circuits_are_put_behind_a_differential_up_to_the_circuits_and_the_current_it_may_serve(self):
        rows = [lighting(i) for i in range(1, 9)]                                  # eight lighting circuits of 1 kW, about 5 A each
        groups = G.plan(TABLERO, rows, None, doc(max_circuits=3, max_ib_a=100))
        lights = [g for g in groups if g["rule"] == "differential-lighting"]
        self.assertEqual([g["members"] for g in lights], [["L-01", "L-02", "L-03"], ["L-04", "L-05", "L-06"], ["L-07", "L-08"]])
        self.assertEqual([g["tag"] for g in lights], ["GD-L01", "GD-L02", "GD-L03"])
        by_current = G.plan(TABLERO, rows, None, doc(max_circuits=10, max_ib_a=12))                # 5.07 A each: two per differential
        self.assertEqual([len(g["members"]) for g in by_current if g["rule"] == "differential-lighting"], [2, 2, 2, 2])

    def test_circuits_of_another_phase_or_type_are_not_mixed_and_those_with_a_differential_or_a_kind_of_their_own_are_left_alone(self):
        rows = [lighting(1), lighting(2, phase="3F"), lighting(3, kind="mcb"), lighting(4), {**lighting(5), "PARENT_TAG": "G-X"}, {"TAG": "G-X", "DESCRIPCION": "GRUPO", "UNIDAD_CARGA": "A",
                "TOPOLOGY": "single", "FASE": "1F", "KIND": "rccb", "CARGA": None}]
        groups = [g for g in G.plan(TABLERO, rows, None, doc()) if g["rule"] == "differential-lighting"]
        self.assertEqual(sorted(sorted(g["members"]) for g in groups), [["L-01", "L-04"], ["L-02"]])
        with_own = doc()
        with_own["solutions"]["lighting-differential-mcb"]["enabled"] = True                      # the circuits then carry their own differential
        self.assertEqual([g for g in G.plan(TABLERO, [lighting(1), lighting(2)], None, with_own) if g["rule"] == "differential-lighting"], [])

    def test_the_groups_become_circuits_the_calculation_reads_like_any_other(self):
        rows = [lighting(i) for i in range(1, 4)]
        groups = G.plan(TABLERO, rows, None, doc())
        new = G.apply_rows(rows, groups)
        self.assertEqual([r["TAG"] for r in new], ["GD-L01", "L-01", "L-02", "L-03"])
        self.assertEqual({r["TAG"]: r["PARENT_TAG"] for r in new if r["PARENT_TAG"]}, {"L-01": "GD-L01", "L-02": "GD-L01", "L-03": "GD-L01"})
        detail = {}
        data, _ = P.calculate(TABLERO, new, detalle=detail)
        self.assertEqual(data["GD-L01"]["disp"], "RCCB 2P 16 A 30 mA")
        self.assertEqual(detail["GD-L01"]["solucion"], "group-differential")
        self.assertEqual(detail["L-02"]["padre"], "GD-L01")

    def test_a_tag_already_used_is_skipped_and_a_wrong_rule_is_refused(self):
        rows = [lighting(1), {**lighting(2), "TAG": "GD-L01"}]
        self.assertEqual(G.plan(TABLERO, rows, None, doc())[0]["tag"], "GD-L02")
        bad = copy.deepcopy(S.defaults())
        bad["groups"]["differential-lighting"].update(by=["colour"], max_circuits=0, tag="no-number", description={"es": "{nope}"})
        errors = S.validate(bad)
        self.assertTrue({"groups.differential-lighting.by", "groups.differential-lighting.max_circuits", "groups.differential-lighting"} & set(errors), errors)


if __name__ == "__main__":
    unittest.main()
