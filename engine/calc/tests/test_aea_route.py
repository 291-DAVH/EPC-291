"""Recorrido real de un cable: tramos con instalaciones distintas y tramo limitante."""
import unittest

from epc_calc import aea_ampacity as AMP
from epc_calc import aea_pipeline as P
from epc_calc import aea_route as AR

TAB = {"NOMBRE": "T", "TENSION_V": 380, "ICC_KA": 10, "FP_DEFAULT": 0.85}
FEEDER = {"TAG": "C-01", "DESCRIPCION": "ALIMENTADOR TS", "CARGA": 250, "UNIDAD_CARGA": "A", "TOPOLOGY": "single", "FASE": "3F", "KIND": "mccb", "LONGITUD_m": 20}
CRIT = {"insulation": "XLPE"}


def calc(row, **kw):
    det = {}
    datos, avisos = P.calculate(TAB, [row], criterios=kw.pop("criterios", CRIT), detalle=det, **kw)
    return datos["C-01"], det["C-01"], avisos


class TestRoute(unittest.TestCase):
    def test_validation(self):
        self.assertEqual(AR.validate([]), {})
        self.assertEqual(AR.validate([{"kind": "tray_perforated", "length_m": 10}]), {})
        bad = AR.validate([{"kind": "ducto", "length_m": 0}, {"kind": "buried_direct", "length_m": 5, "circuits": 0, "soil_c": 99}])
        self.assertEqual(sorted(bad), ["segment 1.kind", "segment 1.length_m", "segment 2.circuits", "segment 2.soil_c"])
        self.assertIn("route", AR.validate([{"kind": "tray_perforated", "length_m": 1}] * 21))

    def test_each_kind_uses_its_method_and_the_cable_type(self):
        base = AMP.parametros({"AISLACION": "xlpe", "METODO": "B2"})
        d = {"t_amb": 40.0, "t_suelo": 25.0, "rho": 1.0}
        got = {k: AR.segment_params(base, {"kind": k, "length_m": 1}, d, True)["metodo"] for k in AR.KINDS}
        self.assertEqual(got, {"tray_perforated": "E", "tray_solid": "C", "conduit_air": "B2", "chamber": "E", "buried_direct": "D2", "buried_duct": "D1", "road_crossing": "D1"})
        self.assertEqual(AR.segment_params(base, {"kind": "tray_perforated", "length_m": 1}, d, False)["metodo"], "F")        # single-core cables
        self.assertEqual(AR.total_length([{"kind": "tray_perforated", "length_m": 12.5}, {"kind": "buried_direct", "length_m": 7.5}]), 20.0)

    def test_the_most_unfavourable_segment_governs_the_capacity(self):
        base = AMP.parametros({"AISLACION": "xlpe", "METODO": "B2"})
        d = {"t_amb": 40.0, "t_suelo": 25.0, "rho": 1.0}
        route = [{"kind": "tray_perforated", "length_m": 20}, {"kind": "buried_direct", "length_m": 80, "rho_kmw": 2.5},
                 {"kind": "road_crossing", "length_m": 8, "circuits": 3}, {"kind": "tray_perforated", "length_m": 30}]
        r = AR.iz_ruta(base, route, 95, 3, d)
        self.assertEqual(len(r["tramos"]), 4)
        self.assertEqual(r["iz_a"], min(t["iz_a"] for t in r["tramos"]))
        self.assertTrue(r["tramos"][r["limitante"]]["limitante"])
        self.assertEqual(sum(1 for t in r["tramos"] if t["limitante"]), 1)
        self.assertLess(r["iz_a"], r["tramos"][0]["iz_a"])                                      # the buried part is worse than the tray
        self.assertEqual(r["tramos"][1]["f_suelo"], round(AMP.factores({**base, "metodo": "D2", "rho": 2.5}, True)["f_suelo"], 3))

    def test_a_buried_stretch_can_demand_more_section_than_the_tray_alone(self):
        _, d_tray, _ = calc({**FEEDER, "RUTA": [{"kind": "tray_perforated", "length_m": 20}]})
        route = [{"kind": "tray_perforated", "length_m": 5}, {"kind": "buried_direct", "length_m": 10, "rho_kmw": 2.5, "soil_c": 35}, {"kind": "tray_perforated", "length_m": 5}]
        s_mix, d_mix, _ = calc({**FEEDER, "RUTA": route})
        s_tray, _, _ = calc({**FEEDER, "RUTA": [{"kind": "tray_perforated", "length_m": 20}]})
        self.assertGreater(s_mix["S"], s_tray["S"])                                                # same 20 m: the route, not the length, sets the section
        self.assertEqual(d_mix["largo_m"], 20.0)
        self.assertEqual(d_mix["ruta_limitante"], 2)
        self.assertEqual([t["kind"] for t in d_mix["ruta"]], ["tray_perforated", "buried_direct", "tray_perforated"])
        self.assertGreaterEqual(d_mix["iz_a"], d_mix["in_a"])

    def test_the_length_is_the_sum_of_the_segments_and_drives_the_voltage_drop(self):
        short = calc({**FEEDER, "RUTA": [{"kind": "tray_perforated", "length_m": 10}]})
        long_ = calc({**FEEDER, "RUTA": [{"kind": "tray_perforated", "length_m": 10}, {"kind": "buried_duct", "length_m": 90}]})
        self.assertEqual(long_[1]["largo_m"], 100.0)
        self.assertGreater(long_[0]["dU"], short[0]["dU"])

    def test_wiring_inside_the_board_ignores_the_route(self):
        s, d, _ = calc({**FEEDER, "RUTA": [{"kind": "buried_direct", "length_m": 10, "rho_kmw": 3.0, "soil_c": 40}]})
        self.assertLess(d["s_termica_mm2"], s["S"])                                                 # inside the board: the thermal section; the buried cable needs more

    def test_without_route_nothing_changes_and_project_conditions_apply(self):
        s0, d0, _ = calc(FEEDER)
        self.assertEqual((d0["ruta"], d0["ruta_limitante"]), ([], None))
        s1, d1, _ = calc(FEEDER, criterios={**CRIT, "ambient_temp_c": 55})
        self.assertGreaterEqual(s1["S"], s0["S"])                                                   # hotter ambient: never less section
        self.assertEqual(d1["instalacion"]["t_amb"], 55.0)

    def test_warnings(self):
        _, _, av = calc({**FEEDER, "RUTA": [{"kind": "road_crossing", "length_m": 8, "depth_m": 1.2}, {"kind": "conduit_air", "length_m": 5}]})
        self.assertTrue(any("profundidad" in a for a in av))
        self.assertEqual(AR.route_warnings([{"kind": "tray_perforated", "length_m": 5, "depth_m": 3}]), [])


if __name__ == "__main__":
    unittest.main()
