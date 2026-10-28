"""Standard solutions: the document that says which devices make up a circuit, and how the calculation uses it."""
import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from epc_aea90364 import aea_pipeline as P  # noqa: E402
from epc_aea90364 import board_figures as F  # noqa: E402
from epc_aea90364 import solutions as S  # noqa: E402
from test_aea_pipeline import CIRC, TABLERO  # noqa: E402


def facts(topology="single", kind="auto", phase="3F", in_a=16, children=False, description="", notes="", ctype="seccional"):
    return S.facts("C-01", description, notes, topology, kind, phase, ctype, in_a, in_a * 0.8, 25, 30, children, topology != "single")


def symbols(f, doc=None):
    return [c["symbol"] for c in S.resolve(f, doc)["chain"]]


class TestDocument(unittest.TestCase):
    def test_the_default_document_is_valid_and_reproduces_the_chains_the_diagrams_always_drew(self):
        doc = S.defaults()
        self.assertEqual(S.validate(doc), {})
        self.assertEqual(symbols(facts("dol_ol", in_a=16)), ["lv_mcb", "lv_contactor", "lv_thermal_overload"])
        self.assertEqual(symbols(facts("dol_ol", in_a=80)), ["lv_mccb_basic", "lv_contactor", "lv_thermal_overload"])           # the head changes above 63 A
        self.assertEqual(symbols(facts("star_delta", in_a=16)), ["lv_mcb", "lv_contactor", "lv_contactor", "lv_contactor", "lv_thermal_overload"])
        self.assertEqual(symbols(facts("single", "mccb_motorized")), ["lv_mccb_motorized"])
        self.assertEqual(symbols(facts("single", "auto", in_a=100)), ["lv_mccb_basic"])
        self.assertEqual(symbols(facts("single", "auto", in_a=16)), ["lv_mcb"])
        self.assertEqual(symbols(facts("single", "rcbo", "1F")), ["lv_rcbo"])
        self.assertEqual(symbols(facts(children=True, phase="1F")), ["lv_rccb"])
        self.assertEqual(symbols(facts("single", "mcb", in_a=100)), ["lv_mcb"])                                               # an explicit kind is respected

    def test_poles_and_labels_come_from_the_phase_and_the_texts_from_the_criteria(self):
        one = S.resolve(facts("single", "rcbo", "1F"))["chain"][0]
        three = S.resolve(facts("single", "rcbo", "3F"))["chain"][0]
        self.assertEqual((one["poles"], one["label"], three["poles"], three["label"]), (2, "1P+N", 4, "3P+N"))
        self.assertEqual(one["slots"]["sensitivity"], "30 mA")
        group = S.resolve(facts(children=True))
        self.assertEqual((group["disp"], group["chain"][0]["slots"]["rated_current"]), ("RCCB 4P 16 A 30 mA", "16 A"))

    def test_the_ups_add_on_follows_the_description_or_the_notes_but_not_a_group(self):
        self.assertEqual(symbols(facts(description="UPS SERVIDORES")), ["lv_mcb", "lv_ups"])
        self.assertEqual(symbols(facts(notes="ups")), ["lv_mcb", "lv_ups"])
        self.assertEqual(S.resolve(facts(description="UPS"))["disp"], "MCB > UPS (16 A)")
        self.assertEqual(symbols(facts(children=True, description="UPS")), ["lv_rccb"])

    def test_a_solution_the_master_switches_on_takes_over_and_a_count_can_be_arithmetic(self):
        doc = S.load()
        doc["solutions"]["lighting-differential-mcb"]["enabled"] = True
        self.assertEqual(symbols(facts(ctype="iluminacion"), doc), ["lv_rccb", "lv_mcb"])
        self.assertEqual(S.resolve(facts(ctype="iluminacion"), doc)["disp"], "RCCB > MCB (16 A)")
        self.assertEqual(symbols(facts(ctype="tomacorrientes"), doc), ["lv_mcb"])
        doc["solutions"]["lighting-differential-mcb"]["chain"][1]["count"] = "ceil(ib_a / 6)"            # 12.8 A / 6 -> 3 breakers
        self.assertEqual(symbols(facts(ctype="iluminacion"), doc), ["lv_rccb", "lv_mcb", "lv_mcb", "lv_mcb"])

    def test_a_file_overrides_solution_by_solution_and_null_removes_one(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "solutions.json"
            mine = copy.deepcopy(S.defaults()["solutions"]["circuit-mcb"])
            mine["chain"] = [{"symbol": "lv_mccb_basic", "short": "MCCB", "slots": {"tag": "{tag}"}}]
            f.write_text(json.dumps({"solutions": {"circuit-mcb": mine, "motor-vfd": None}}), encoding="utf-8")
            doc = S.load(f)
            self.assertEqual(symbols(facts(), doc), ["lv_mccb_basic"])
            self.assertNotIn("motor-vfd", doc["solutions"])
            self.assertEqual(set(S.override_of(doc)["solutions"]), {"circuit-mcb", "motor-vfd"})
            self.assertEqual(S.override_of(S.defaults()), {})
            os.environ[S.ENV_VAR] = str(f)                                                           # the global file the MASTER edits
            try:
                self.assertEqual(symbols(facts()), ["lv_mccb_basic"])
            finally:
                del os.environ[S.ENV_VAR]

    def test_a_level_stores_only_what_differs_from_what_it_inherits(self):
        base = S.load()
        mine = copy.deepcopy(base)
        mine["solutions"]["circuit-mcb"]["priority"] = 11
        del mine["solutions"]["motor-vfd"]
        self.assertEqual({k: set(v) for k, v in S.override_of(mine, base).items()}, {"solutions": {"circuit-mcb", "motor-vfd"}})
        self.assertEqual(S.override_of(base, base), {})

    def test_validation_names_what_is_wrong_and_a_circuit_without_a_solution_is_refused(self):
        doc = S.defaults()
        doc["solutions"]["bad"] = {"priority": "high", "when": {"colour": ["red"], "in_a": {"around": 3}}, "chain": [{"symbol": "lv_x", "slots": {"a": "{nope}"}, "count": "__import__('os')"}]}
        errors = S.validate(doc, known_symbols={"lv_mcb", "lv_contactor"})
        self.assertTrue({"solutions.bad.priority", "solutions.bad.when.colour", "solutions.bad.when.in_a", "solutions.bad.chain[0]", "solutions.bad.chain[0].symbol"} <= set(errors), errors)
        empty = S.defaults()
        empty["solutions"] = {i: s for i, s in empty["solutions"].items() if s["when"]}
        self.assertIn("solutions", S.validate(empty))
        with self.assertRaises(ValueError):
            S.resolve(facts(), empty)


class TestPipeline(unittest.TestCase):
    def test_the_calculation_delivers_the_chain_and_the_text_of_each_circuit(self):
        detail = {}
        data, _ = P.calculate(TABLERO, CIRC, detalle=detail)
        self.assertEqual(data["M-01"]["disp"], "MCB > KM > OL (25 A)")
        self.assertEqual([i["symbol"] for i in detail["M-01"]["cadena"]], ["lv_mcb", "lv_contactor", "lv_thermal_overload"])
        self.assertEqual((detail["M-01"]["solucion"], detail["G-02"]["solucion"]), ("motor-dol-ol", "group-differential"))
        self.assertEqual(data["G-02"]["disp"], "RCCB 4P 25 A 30 mA")

    def test_a_different_document_changes_the_devices_and_the_differential_check_follows(self):
        board = {"icc_ka": 36, "voltage_v": 380, "fp_default": 0.85, "system": "TN-S", "frequency_hz": 50, "feeder_length_m": 20}
        limits = {"seccional": 1.0, "terminal": 3.0, "motor": 5.0}
        circuits = [{**c, "KIND": "auto"} if c["TAG"] == "L-01" else c for c in CIRC]                 # an explicit kind is the engineer's choice and wins over a standard solution
        base_detail = {}
        base, _ = P.calculate(TABLERO, circuits, detalle=base_detail)
        self.assertEqual(F.build(board, base, base_detail, limits, 30, {"dato_faltante": True})["differential_missing"], ["L-01"])
        doc = S.load()
        doc["solutions"]["lighting-differential-mcb"]["enabled"] = True
        detail = {}
        data, _ = P.calculate(TABLERO, circuits, detalle=detail, soluciones=doc)
        self.assertEqual(data["L-01"]["disp"], "RCCB > MCB (10 A)")
        self.assertEqual([i["symbol"] for i in detail["L-01"]["cadena"]], ["lv_rccb", "lv_mcb"])
        self.assertEqual(F.build(board, data, detail, limits, 30, {"dato_faltante": True})["differential_missing"], [])


if __name__ == "__main__":
    unittest.main()
