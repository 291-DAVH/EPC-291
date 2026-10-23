"""Pruebas de aea_pipeline.py y de las tablas añadidas a aea_conductors — valores calculados A MANO."""
import json
import math
import os
import tempfile
import unittest
import zipfile

import aea_conductors as CO
import aea_export as EX
import aea_pipeline as P

TABLERO = {"TENSION_V": 380, "ICC_KA": 36, "FP_DEFAULT": 0.85}
CIRC = [
    {"TAG": "M-01", "DESCRIPCION": "EXTRACTOR", "CARGA": 11, "UNIDAD_CARGA": "kW", "TOPOLOGY": "dol_ol",
     "FASE": "3F", "LONGITUD_m": 30, "FP": 0.85, "KIND": "auto"},
    {"TAG": "L-01", "DESCRIPCION": "ILUMINACION PASILLO", "CARGA": 1.5, "UNIDAD_CARGA": "kW", "TOPOLOGY": "single",
     "FASE": "1F", "LONGITUD_m": 35, "FP": 0.9, "KIND": "mcb"},
    {"TAG": "G-02", "DESCRIPCION": "RCCB GRUPO TOMAS", "UNIDAD_CARGA": "A", "TOPOLOGY": "single", "FASE": "3F",
     "KIND": "rccb"},
    {"TAG": "G-02-A", "DESCRIPCION": "Tomas 01", "CARGA": 2.5, "UNIDAD_CARGA": "kW", "PARENT_TAG": "G-02",
     "TOPOLOGY": "single", "FASE": "1F", "LONGITUD_m": 15, "FP": 0.9, "KIND": "mcb"},
    {"TAG": "G-02-B", "DESCRIPCION": "Tomas 02", "CARGA": 2.2, "UNIDAD_CARGA": "kW", "PARENT_TAG": "G-02",
     "TOPOLOGY": "single", "FASE": "1F", "LONGITUD_m": 18, "FP": 0.9, "KIND": "mcb"},
    {"TAG": "C-03", "DESCRIPCION": "MONTACARGAS", "CARGA": 5, "UNIDAD_CARGA": "HP", "TOPOLOGY": "vfd",
     "FASE": "3F", "LONGITUD_m": 35, "FP": 0.85, "RENDIMIENTO": 0.9, "KIND": "auto"},
    {"TAG": "C-02", "DESCRIPCION": "UPS", "CARGA": 15, "UNIDAD_CARGA": "kVA", "TOPOLOGY": "single",
     "FASE": "3F", "LONGITUD_m": 10, "FP": 0.9, "KIND": "auto", "NOTAS": "UPS"},
]


class TestTablas(unittest.TestCase):
    def test_iz_y_r(self):
        self.assertEqual(CO.iz_admisible(4, 3), 25)
        self.assertEqual(CO.iz_admisible(2.5, 2), 21)
        self.assertAlmostEqual(CO.resistencia_cu_ohm_km(4, 20), 4.61)
        self.assertAlmostEqual(CO.resistencia_cu_ohm_km(4), 4.61 * (1 + 0.00393 * 50))   # 5,5159
        with self.assertRaises(ValueError):
            CO.iz_admisible(3, 3)


class TestCalculo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d, cls.av = P.calculate(TABLERO, CIRC)

    def test_currents(self):
        c = {x["TAG"]: x for x in CIRC}
        self.assertAlmostEqual(self.d["M-01"]["Ib"], 19.7)       # 11000/(√3·380·0,85) = 19,66
        self.assertAlmostEqual(self.d["L-01"]["Ib"], 7.6)        # 1500/(219,39·0,9) = 7,597
        self.assertAlmostEqual(self.d["C-03"]["Ib"], 7.4)        # 5·745,7/(√3·380·0,85·0,9) = 7,40
        self.assertAlmostEqual(self.d["C-02"]["Ib"], 22.8)       # 15000/(√3·380) = 22,79
        self.assertAlmostEqual(P.corriente_proyecto(c["G-02-A"], 380, 0.85), 12.661, places=3)
        self.assertAlmostEqual(self.d["G-02"]["Ib"], 23.8)       # 12,661 + 11,142

    def test_in_y_disp(self):
        self.assertEqual(self.d["M-01"]["In"], 25)               # 1,25·19,66 = 24,6 -> 25
        self.assertEqual(self.d["M-01"]["disp"], "MCB > KM > OL (25 A)")
        self.assertEqual(self.d["L-01"]["In"], 10)
        self.assertEqual(self.d["L-01"]["disp"], "MCB (10 A)")
        self.assertEqual(self.d["G-02"]["disp"], "RCCB 4P 25 A 30 mA")
        self.assertEqual(self.d["G-02-A"]["In"], 13)
        self.assertEqual(self.d["C-03"]["disp"], "MCB > VFD (10 A)")
        self.assertEqual(self.d["C-02"]["disp"], "MCB > UPS (25 A)")
        self.assertTrue(all(v["icu"] == 36 for v in self.d.values()))

    def test_sections_and_drop(self):
        # M-01: S=4 (Iz 3x = 25 ≥ 25). R70 = 5,516 -> 5,516·0,85 + 0,08·0,5268 = 4,731 Ω/km
        # ΔU = √3·19,66·0,03·4,731 = 4,833 V = 1,272 % de 380 V
        self.assertEqual(self.d["M-01"]["S"], 4)
        self.assertAlmostEqual(self.d["M-01"]["dU"], 1.27, delta=0.01)
        # L-01: 66 % de 7,597 A al extremo; R70 = 14,478 -> 13,065 Ω/km; ΔU = 2·5,014·0,035·13,065 = 4,585 V = 2,09 %
        self.assertEqual(self.d["L-01"]["S"], 1.5)
        self.assertAlmostEqual(self.d["L-01"]["dU"], 2.09, delta=0.01)
        # G-02 (sin longitud): ΔU = 0 ; S = 4 (3x: 4 mm² -> 25 A ≥ 25 A)
        self.assertEqual(self.d["G-02"]["S"], 4)
        self.assertEqual(self.d["G-02"]["dU"], 0.0)
        # G-02-A: 12,661 A, 15 m, R70 = 8,866 -> 8,015 Ω/km; ΔU = 2·12,661·0,015·8,015 = 3,044 V = 1,39 %
        self.assertEqual(self.d["G-02-A"]["S"], 2.5)
        self.assertAlmostEqual(self.d["G-02-A"]["dU"], 1.39, delta=0.01)

    def test_acumulada_y_orden(self):
        self.assertEqual(list(self.d), [c["TAG"] for c in CIRC])
        circ = [dict(c) for c in CIRC]
        circ[0]["LONGITUD_m"] = 1          # padre RCCB con longitud: sus hijos suman su caída
        g = next(c for c in circ if c["TAG"] == "G-02")
        g["LONGITUD_m"] = 20
        d, _ = P.calculate(TABLERO, circ)
        self.assertGreater(d["G-02"]["dU"], 0)
        self.assertGreater(d["G-02-A"]["dU"], d["G-02"]["dU"])

    def test_margen_iz(self):
        d, _ = P.calculate(TABLERO, CIRC, margen_iz=1.05)     # 25 A·1,05 > Iz(4 mm²)=25 -> sube a 6 mm²
        self.assertEqual(d["M-01"]["S"], 6)

    def test_types_and_errors(self):
        self.assertEqual(P.type_circuit(CIRC[1], False), "iluminacion")
        self.assertEqual(P.type_circuit(CIRC[0], False), "motor")
        self.assertEqual(P.type_circuit(CIRC[2], True), "seccional")
        with self.assertRaises(ValueError):
            P.calculate(TABLERO, [dict(CIRC[0], PARENT_TAG="X")])
        with self.assertRaises(ValueError):
            P.calculate(TABLERO, [dict(CIRC[0], UNIDAD_CARGA="BTU")])
        with self.assertRaises(ValueError):
            P.calculate(TABLERO, [CIRC[0], dict(CIRC[0])])

    def test_json_valido(self):
        self.assertEqual(EX.validate_calculation(self.d)["errores"], [])


def _xlsx_minimo(ruta):
    def fila(n, vals):
        cs = ""
        for i, v in enumerate(vals):
            ref = "ABCDEFGHIJKLMN"[i] + str(n)
            if v is None:
                continue
            cs += (f'<c r="{ref}" t="s"><v>{v[1]}</v></c>' if isinstance(v, tuple) else f'<c r="{ref}"><v>{v}</v></c>')
        return f'<row r="{n}">{cs}</row>'
    ss = ["TAG", "DESCRIPCION", "CARGA", "UNIDAD_CARGA", "TENSION_V", "CAMPO", "VALOR", "M-01", "MOTOR", "kW", "TABLERO", "ICC_KA"]
    s = lambda t: ("s", ss.index(t))
    tablero = fila(2, [s("CAMPO"), s("VALOR")]) + fila(3, [s("TENSION_V"), 380]) + fila(4, [s("ICC_KA"), 36])
    circ = fila(1, [("s", 10)]) + fila(2, [s("TAG"), s("DESCRIPCION"), s("CARGA"), s("UNIDAD_CARGA")]) + \
        fila(3, [s("M-01"), s("MOTOR"), 11, s("kW")])
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("xl/sharedStrings.xml", f'<sst {ns}>' + "".join(f"<si><t>{t}</t></si>" for t in ss) + "</sst>")
        z.writestr("xl/workbook.xml", f'<workbook {ns} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   '<sheets><sheet name="TABLERO" sheetId="1" r:id="rId1"/><sheet name="CIRCUITOS" sheetId="2" r:id="rId2"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Target="worksheets/sheet2.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", f"<worksheet {ns}><sheetData>{tablero}</sheetData></worksheet>")
        z.writestr("xl/worksheets/sheet2.xml", f"<worksheet {ns}><sheetData>{circ}</sheetData></worksheet>")


class TestXlsx(unittest.TestCase):
    def test_lectura_y_flujo_completo(self):
        with tempfile.TemporaryDirectory() as t:
            x = os.path.join(t, "entrada.xlsx")
            _xlsx_minimo(x)
            tab, circ = P.load_input(x)
            self.assertEqual(tab, {"TENSION_V": 380, "ICC_KA": 36})
            self.assertEqual(circ[0]["TAG"], "M-01")
            ruta, datos, _ = P.calcular_desde_xlsx(x)
            self.assertTrue(ruta.endswith("entrada_calculo.json"))
            self.assertEqual(json.load(open(ruta, encoding="utf-8"))["M-01"]["In"], datos["M-01"]["In"])
            self.assertEqual(datos["M-01"]["icu"], 36)

    def test_archivo_real_si_existe(self):
        x = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src", "input_for_sld_V1.xlsx")
        if not os.path.exists(x):
            self.skipTest("sin src/input_for_sld_V1.xlsx")
        tab, circ = P.load_input(x)
        datos, _ = P.calculate(tab, circ)
        self.assertEqual(len(datos), len(circ))
        self.assertEqual(EX.validate_calculation(datos)["errores"], [])
        self.assertEqual(datos["M-02"]["disp"], "MCCB > KM > KM > KM > OL (100 A)")


if __name__ == "__main__":
    unittest.main()


class TestUnidades(unittest.TestCase):
    """Conversión de CARGA a Ib [A] — 380 V de línea, valores a mano."""
    def ib(self, carga, unidad, fases="3F", fp=0.9, eta=None, **kw):
        c = {"TAG": "X", "CARGA": carga, "UNIDAD_CARGA": unidad, "FASE": fases, "FP": fp, "RENDIMIENTO": eta}
        return P.corriente_proyecto(c, 380, 0.85, **kw)

    def test_three_phase_power_active(self):
        # 15000 W / (√3·380·0,9) = 15000/592,36 = 25,32 A  (W, kW, MW, cualquier mayúscula)
        for carga, u in ((15000, "W"), (15, "kW"), (15, "KW"), (0.015, "MW"), (0.015, "mw")):
            self.assertAlmostEqual(self.ib(carga, u), 25.32, places=2, msg=u)

    def test_three_phase_apparent_without_pf(self):
        # 15000 VA / (√3·380) = 22,79 A (el fp no interviene)
        for carga, u in ((15000, "VA"), (15, "kVA"), (15, "KVA"), (0.015, "MVA")):
            self.assertAlmostEqual(self.ib(carga, u), 22.79, places=2, msg=u)
            self.assertAlmostEqual(self.ib(carga, u, fp=0.5), 22.79, places=2)

    def test_hp_cv_y_amperes(self):
        # 10 HP: 7457 W / (√3·380·0,85·0,9) = 7457/503,5 = 14,81 A
        self.assertAlmostEqual(self.ib(10, "HP", fp=0.85, eta=0.9), 14.81, places=2)
        self.assertAlmostEqual(self.ib(10, "hp", fp=0.85, eta=0.9), 14.81, places=2)
        # 10 CV: 7354,99/503,5 = 14,61 A
        self.assertAlmostEqual(self.ib(10, "CV", fp=0.85, eta=0.9), 14.61, places=2)
        self.assertEqual(self.ib(100, "A"), 100)

    def test_single_phase(self):
        # U_f = 380/√3 = 219,39 V ; 2000 W: 2000/(219,39·0,9) = 10,13 A ; 2000 VA: 2000/219,39 = 9,116 A
        self.assertAlmostEqual(self.ib(2, "kW", "1F"), 10.13, places=2)
        self.assertAlmostEqual(self.ib(2, "kVA", "1F"), 9.116, places=3)
        self.assertAlmostEqual(self.ib(0.002, "MW", "1F"), 10.13, places=2)
        self.assertEqual(self.ib(16, "A", "1F"), 16)

    def test_texto_con_unidad(self):
        self.assertAlmostEqual(self.ib("15 kW", None), 25.32, places=2)
        self.assertAlmostEqual(self.ib("7,5 HP", "", fp=0.85, eta=0.9), 7.5 * 745.7 / (math.sqrt(3) * 380 * 0.85 * 0.9), places=6)
        self.assertEqual(P.convert_load("2,5 kVA"), (2500.0, "va"))
        self.assertEqual(P.convert_load(3, " K.W "), (3000.0, "w"))

    def test_eta_en_kw_de_motor_opcional(self):
        c = {"TAG": "M", "CARGA": 11, "UNIDAD_CARGA": "kW", "FASE": "3F", "FP": 0.85, "RENDIMIENTO": 0.9, "TOPOLOGY": "dol"}
        sin = P.corriente_proyecto(c, 380, 0.85)
        con = P.corriente_proyecto(c, 380, 0.85, eta_motores=True)
        self.assertAlmostEqual(con / sin, 1 / 0.9, places=9)

    def test_errors(self):
        for carga, u in ((5, None), (5, "kvar"), (5, "BTU"), (-1, "kW"), ("quince kW", None), (True, "kW")):
            with self.assertRaises(ValueError, msg=repr((carga, u))):
                P.convert_load(carga, u)
        with self.assertRaises(ValueError):
            self.ib(5, "")


class TestIccMinima(unittest.TestCase):
    def test_formula(self):
        # Zs = 1,05·219,39/10000 = 0,023036 Ω ; cable 4 mm², 30 m, R70 = 5,516 -> 0,16548 Ω, X = 0,0024 Ω
        # |Z| = hypot(0,023036 + 0,16548; 0,0024) = 0,188527 -> I = 0,95·380/(2·0,188527) = 957,4 A
        r, x = 5.515865 * 0.03, 0.08 * 0.03
        self.assertAlmostEqual(P.current_sc_min(380, 10, r, x, 3), 957.4, delta=1.0)
        # monofásico: 0,95·219,39/(2·0,188527) = 552,8 A
        self.assertAlmostEqual(P.current_sc_min(380, 10, r, x, 1), 552.8, delta=1.0)

    def test_warning_by_network_weak(self):
        # ICC 0,3 kA: Zs = 1,05·219,39/300 = 0,7679 Ω ; + 0,16548 Ω -> |Z| ≈ 0,9334 Ω ; I = 361/(2·0,9334) = 193 A < 10·25 A
        base = {"TAG": "M-01", "DESCRIPCION": "MOTOR", "CARGA": 11, "UNIDAD_CARGA": "kW", "TOPOLOGY": "dol_ol",
                "FASE": "3F", "FP": 0.85, "LONGITUD_m": 30}
        _, av = P.calculate({"TENSION_V": 380, "ICC_KA": 10, "FP_DEFAULT": 0.85}, [base])
        self.assertFalse([a for a in av if "Icc mín" in a])
        d, av = P.calculate({"TENSION_V": 380, "ICC_KA": 0.3, "FP_DEFAULT": 0.85}, [base])
        self.assertTrue([a for a in av if a.startswith("M-01: Icc mín al final 19")])
        _, av = P.calculate({"TENSION_V": 380, "ICC_KA": 0.3, "FP_DEFAULT": 0.85}, [base], k_magnetico=5)
        self.assertFalse([a for a in av if "Icc mín" in a])
