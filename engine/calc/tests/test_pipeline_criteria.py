"""Design criteria govern the circuit calculation (aea_pipeline): limits, minimum sections, material, insulation, RCD."""
import unittest

from epc_calc import aea_pipeline as P

BOARD = {"TENSION_V": 380, "ICC_KA": 25, "FP_DEFAULT": 0.85}


def circuits():
    return [
        {"TAG": "C-01", "DESCRIPCION": "ALIMENTADOR TD-1", "CARGA": 100, "UNIDAD_CARGA": "A", "TOPOLOGY": "single", "FASE": "3F", "LONGITUD_m": 60, "KIND": "mccb"},
        {"TAG": "M-01", "DESCRIPCION": "BOMBA", "CARGA": 15, "UNIDAD_CARGA": "kW", "TOPOLOGY": "dol_ol", "FASE": "3F", "LONGITUD_m": 80, "FP": 0.85, "RENDIMIENTO": 0.9},
        {"TAG": "L-01", "DESCRIPCION": "ILUMINACION NAVE", "CARGA": 2, "UNIDAD_CARGA": "kW", "TOPOLOGY": "single", "FASE": "1F", "LONGITUD_m": 20, "FP": 0.9},
        {"TAG": "T-01", "DESCRIPCION": "TOMAS OFICINA", "CARGA": 2, "UNIDAD_CARGA": "kW", "TOPOLOGY": "single", "FASE": "1F", "LONGITUD_m": 15, "FP": 0.9},
        {"TAG": "G-01", "DESCRIPCION": "RCCB TOMAS", "UNIDAD_CARGA": "A", "TOPOLOGY": "single", "FASE": "3F", "KIND": "rccb"},
        {"TAG": "G-01-A", "DESCRIPCION": "Tomas 2", "CARGA": 1.5, "UNIDAD_CARGA": "kW", "PARENT_TAG": "G-01", "TOPOLOGY": "single", "FASE": "1F", "LONGITUD_m": 12, "FP": 0.9},
    ]


def run(criterios=None):
    det = {}
    datos, avisos = P.calculate(BOARD, circuits(), criterios=criterios, detalle=det)
    return datos, avisos, det


class TestCriteria(unittest.TestCase):
    def test_without_criteria_nothing_changes(self):
        base, _ = P.calculate(BOARD, circuits())
        again, _, det = run(None)
        self.assertEqual(base, again)
        self.assertEqual([det[t]["limite_pct"] for t in ("C-01", "M-01", "L-01", "T-01")], [1.0, 5.0, 3.0, 3.0])        # 1 % / 5 % / 3 % / 3 %
        self.assertEqual((det["C-01"]["tipo"], det["M-01"]["tipo"], det["L-01"]["tipo"], det["T-01"]["tipo"], det["G-01"]["tipo"]),
                         ("seccional", "motor", "iluminacion", "tomacorrientes", "seccional"))

    def test_limits_come_from_the_criteria(self):
        loose, _, d1 = run({"vd_sectional_pct": 3, "vd_motors_pct": 5})
        strict, _, d2 = run({"vd_sectional_pct": 0.5, "vd_motors_pct": 2})
        self.assertEqual((d1["C-01"]["limite_pct"], d2["C-01"]["limite_pct"], d2["M-01"]["limite_pct"]), (3.0, 0.5, 2.0))
        self.assertGreater(strict["C-01"]["S"], loose["C-01"]["S"])                  # a tighter feeder limit needs more copper
        self.assertGreaterEqual(strict["M-01"]["S"], loose["M-01"]["S"])
        for det in (d1, d2):
            for t in ("C-01", "M-01"):
                self.assertLessEqual(det[t]["du_propia_pct"], det[t]["limite_pct"] + 1e-9)

    def test_minimum_sections_from_the_criteria(self):
        datos, _, det = run({"min_section_lighting_mm2": 4, "min_section_sockets_mm2": 6})
        self.assertGreaterEqual(datos["L-01"]["S"], 4)
        self.assertGreaterEqual(datos["T-01"]["S"], 6)
        self.assertEqual((det["L-01"]["seccion_min_mm2"], det["T-01"]["seccion_min_mm2"]), (4.0, 6.0))

    def test_material_and_insulation(self):
        al, _, dal = run({"conductor_material": "aluminio", "insulation": "XLPE"})
        self.assertTrue(all(d["material"] == "al" and d["aislacion"] == "xlpe" and d["metodo"] == "B2" for d in dal.values()))
        self.assertTrue(all(v["S"] >= 16 for v in al.values()))                       # aluminium starts at 16 mm²
        cu, _, dcu = run({"conductor_material": "cobre", "insulation": "XLPE"})
        self.assertTrue(all(d["material"] == "cu" and d["metodo"] == "B2" for d in dcu.values()))
        self.assertLessEqual(cu["C-01"]["S"], al["C-01"]["S"])                        # copper never needs more section than aluminium
        with self.assertRaises(ValueError):
            run({"insulation": "teflon"})

    def test_row_columns_still_win_over_criteria(self):
        cs = circuits()
        cs[0]["MATERIAL"] = "cu"
        det = {}
        P.calculate(BOARD, cs, criterios={"conductor_material": "aluminio"}, detalle=det)
        self.assertEqual((det["C-01"]["material"], det["M-01"]["material"]), ("cu", "al"))

    def test_rcd_sensitivity_in_the_device_text(self):
        datos, _, _ = run({"rcd_sensitivity_ma": 300})
        self.assertIn("300 mA", datos["G-01"]["disp"])
        datos, _, _ = run(None)
        self.assertIn("30 mA", datos["G-01"]["disp"])

    def test_detail_reports_compliance(self):
        _, avisos, det = run({"vd_sectional_pct": 0.01})                            # impossible limit: warns, flags the circuit
        self.assertFalse(det["C-01"]["cumple"])
        self.assertTrue(any("C-01" in a for a in avisos))
        _, _, ok = run(None)
        self.assertTrue(all(d["cumple"] for d in ok.values()))


if __name__ == "__main__":
    unittest.main()
