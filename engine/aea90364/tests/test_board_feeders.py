"""Acometidas de un tablero: dimensionadas como cualquier circuito, con su propia instalación, aislación y conductor."""
import unittest

from epc_aea90364 import board_feeders as F
from epc_aea90364 import board_memo as BM

TABLERO = {"TENSION_V": 380, "ICC_KA": 10, "FP_DEFAULT": 0.85}


def feeder(**kw):
    return {"name": "ACOM-RED", "source": "Red", "phase": "3F", "length_m": 40, "load_a": 166, "method": "E", "insulation": "xlpe", "material": "cu", **kw}


class TestFeeders(unittest.TestCase):
    def test_the_head_of_the_board_is_the_circuits_that_hang_from_no_other(self):
        datos = {"A": {"Ib": 50.0}, "B": {"Ib": 20.0}, "C": {"Ib": 7.0}}
        self.assertEqual(F.head_current(datos, {"A": {"padre": ""}, "B": {"padre": "A"}, "C": {"padre": ""}}), 57.0)         # B is inside A: it is not added twice

    def test_each_acometida_is_sized_with_its_own_cable_and_installation(self):
        red, grupo = F.calculate(TABLERO, [feeder(), feeder(name="ACOM-GE", source="", length_m=20, method="B2", insulation="pvc", material="al")], 100.0)
        self.assertEqual((red["S_mm2"], red["In"], red["Ib"], red["cumple"]), (95, 200, 166.0, True))         # 70 mm2 would drop 1.0 % over 40 m: the limit of a seccional is 1 %
        self.assertEqual((red["metodo"], red["aislacion"], red["material"]), ("E", "xlpe", "cu"))
        self.assertEqual((grupo["metodo"], grupo["aislacion"], grupo["material"]), ("B2", "pvc", "al"))      # another cable for another source
        self.assertEqual((grupo["S_mm2"], grupo["cumple"]), (240, True))                                    # aluminium PVC in a conduit needs far more copper-equivalent

    def test_without_a_current_the_acometida_carries_what_the_head_of_the_board_draws(self):
        (a,) = F.calculate(TABLERO, [feeder(load_a=None, name="")], 57.0)
        self.assertEqual((a["name"], a["Ib"], a["load_given"]), ("ACOMETIDA-1", 57.0, False))

    def test_a_single_phase_acometida_is_calculated_on_the_phase_voltage(self):
        (three,) = F.calculate(TABLERO, [feeder(load_a=30, length_m=60)], 0.0)
        (one,) = F.calculate(TABLERO, [feeder(load_a=30, length_m=60, phase="1F")], 0.0)
        self.assertGreater(one["du_pct"], three["du_pct"])                                                  # the same current and length drops more on one phase and neutral


class TestMemoWithFeeders(unittest.TestCase):
    def build(self, feeders, board=None, upstream=None):
        circuits = [{"tag": "C-01", "description": "ALIM", "load": 10, "unit": "A", "topology": "single", "phase": "3F", "length_m": 10, "kind": "auto", "parent_tag": ""}]
        datos = {"C-01": {"In": 10, "Ib": 10.0, "icu": 10, "S": 2.5, "dU": 0.1, "disp": "MCB (10 A)"}}
        detalle = {"C-01": {"tipo": "seccional", "limite_pct": 1, "du_propia_pct": 0.1, "du_acum_pct": 0.1, "iz_a": 30, "cumple": True, "in_a": 10, "ib_a": 10, "padre": "", "kind": "mcb", "fases": 3,
                            "s_termica_mm2": 2.5, "largo_m": 10, "icc_min_a": 900, "ruta": [], "ruta_limitante": None, "solucion": "", "cadena": [], "material": "cu", "aislacion": "xlpe", "metodo": "B2"}}
        b = {"name": "T", "voltage_v": 380, "system": "TN-S", "icc_ka": 10, "fp_default": 0.85, "frequency_hz": 50, "feeder_length_m": 20, **(board or {})}
        return BM.build(b, circuits, datos, detalle, {"seccional": 1, "terminal": 3, "motor": 5}, {"material": "cu", "aislacion": "xlpe"}, 30, upstream=upstream, feeders=feeders)

    def test_without_acometidas_the_memo_has_no_new_fields(self):
        ac = self.build([])["acometida"]
        self.assertEqual((ac["dato_faltante"], "lista" in ac, "propia" in ac), (True, False, False))

    def test_the_first_acometida_is_the_cable_that_feeds_the_board_and_all_are_listed(self):
        feeders = F.calculate(TABLERO, [feeder(), feeder(name="ACOM-GE", source="Grupo electrógeno", method="B2")], 10.0)
        m = self.build(feeders)
        ac = m["acometida"]
        self.assertEqual((ac["dato_faltante"], ac["propia"], ac["tag"], ac["S_mm2"], ac["desde"]), (False, True, "ACOM-RED", 95, "Red"))
        self.assertEqual([f["name"] for f in ac["lista"]], ["ACOM-RED", "ACOM-GE"])
        text = " ".join(str(b) for b in BM.memoria_doc(m)["blocks"])
        self.assertIn("ACOM-GE (Grupo electrógeno)", text)                                           # the memo says each one

    def test_an_upstream_board_still_wins_over_the_acometidas_for_the_cable_that_feeds_it(self):
        feeders = F.calculate(TABLERO, [feeder()], 10.0)
        ac = self.build(feeders, upstream={"board": "TGBT-0", "tag": "C-9", "S": 120, "In": 250, "dU": 0.4, "disp": "MCCB (250 A)", "length_m": 30})["acometida"]
        self.assertEqual((ac["desde"], ac["tag"], ac["S_mm2"], ac["propia"]), ("TGBT-0", "C-9", 120, False))


if __name__ == "__main__":
    unittest.main()
