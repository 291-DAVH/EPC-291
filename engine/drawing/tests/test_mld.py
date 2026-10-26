"""Multi-line diagram generator: conductors per circuit, symbols per pole, pagination."""
import tempfile
import unittest
from pathlib import Path

from epc_drawing import board_design as B
from epc_mld import mld_generator as M


def board(n_extra=0):
    circuits = [
        {"tag": "C-01", "description": "ALIMENTADOR", "load": 63, "unit": "A", "topology": "single", "phase": "3F", "length_m": 30, "kind": "mccb"},
        {"tag": "M-01", "description": "BOMBA", "load": 7.5, "unit": "kW", "topology": "dol_ol", "phase": "3F", "length_m": 25, "fp": 0.85, "efficiency": 0.9},
        {"tag": "G-01", "description": "RCCB TOMAS", "unit": "A", "topology": "single", "phase": "3F", "kind": "rccb"},
        {"tag": "G-01-A", "description": "Tomas", "load": 2.2, "unit": "kW", "parent_tag": "G-01", "topology": "single", "phase": "1F", "length_m": 15, "fp": 0.9, "kind": "mcb"},
    ]
    circuits += [{"tag": f"X-{i:02d}", "description": "CARGA", "load": 5, "unit": "kW", "topology": "single", "phase": "3F", "length_m": 20, "fp": 0.85} for i in range(n_extra)]
    return {"board": {"name": "TGBT-01", "voltage_v": 380, "system": "TN-S", "icc_ka": 25, "fp_default": 0.85, "frequency_hz": 50, "project": "P-1", "feeder_length_m": 20},
            "circuits": circuits, "titleblock": {"company": "Oficina SA"}}


class TestPoles(unittest.TestCase):
    def test_pole_id_picks_the_available_symbol(self):
        cat = M.Sheet(M.library_dir()).cat
        self.assertEqual(M.pole_id("lv_mcb", 3, cat), "lv_mcb_3p_mld")
        self.assertEqual(M.pole_id("lv_rccb", 3, cat), "lv_rccb_4p_mld")            # no 3P RCCB: next available
        self.assertEqual(M.pole_id("lv_motor_3ph", 3, cat), "lv_motor_3ph_3p_mld")
        self.assertEqual(M.pole_id("lv_vfd", 3, cat), "lv_vfd_3p_mld")

    def test_poles_and_chains(self):
        self.assertEqual((M.poles_of({"phase": "3F"}, False), M.poles_of({"phase": "1F"}, False), M.poles_of({"phase": "3F"}, True), M.poles_of({"phase": "3F+N"}, False)), (3, 2, 4, 4))
        chain = M.device_chain({"topology": "dol_ol"}, 16, 25, 3, False, "M-01")
        self.assertEqual([b for b, _, _ in chain], ["lv_mcb", "lv_contactor", "lv_thermal_overload"])
        self.assertEqual([b for b, _, _ in M.device_chain({"topology": "single", "kind": "auto"}, 100, 25, 3, False, "C")], ["lv_mccb_basic"])


class TestGenerate(unittest.TestCase):
    def run_mld(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            made = M.generate(data, B.calculate(data, B.catalog_defaults()), tmp / "out", "MLD_TGBT-01")          # the title block comes from the input's own data
            return made, [Path(m["svg"]).read_text(encoding="utf-8") for m in made], [Path(m["dxf"]).exists() if m["dxf"] else False for m in made]

    def test_one_sheet_with_symbols_per_pole_and_conductors(self):
        made, svgs, dxfs = self.run_mld(board())
        self.assertEqual(len(made), 1)
        svg = svgs[0]
        for sid in ("lv_mccb_basic_3p_mld", "lv_mcb_3p_mld", "lv_contactor_3p_mld", "lv_thermal_overload_3p_mld", "lv_rccb_4p_mld", "lv_motor_3ph_3p_mld", "lv_mcb_2p_mld"):
            self.assertIn(f'data-sid="{sid}"', svg, sid)
        for tag in ("C-01", "M-01", "G-01-A", "L1", "L2", "L3"):
            self.assertIn(tag, svg)
        self.assertIn("MULTIFILAR", svg.upper())
        self.assertIn("Oficina SA", svg)
        self.assertTrue(dxfs[0])

    def test_many_circuits_paginate_into_several_sheets(self):
        made, svgs, dxfs = self.run_mld(board(n_extra=14))
        self.assertGreater(len(made), 1)
        self.assertTrue(all(m["name"].startswith("MLD_TGBT-01_H") for m in made))
        self.assertIn("CONTINÚA EN HOJA 2", svgs[0])
        self.assertIn("VIENE DE HOJA 1", svgs[1])
        self.assertTrue(all(dxfs))


if __name__ == "__main__":
    unittest.main()
