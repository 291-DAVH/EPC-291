"""Pruebas de los módulos aea_* — valores de referencia calculados A MANO."""
import math
import unittest

from epc_calc import aea_catalog as CAT
from epc_calc import aea_conductors as CO
from epc_calc import aea_demand as D
from epc_calc import aea_earthing as E
from epc_calc import aea_icc_decay as ID
from epc_calc import aea_icc_factors as IF
from epc_calc import aea_panel_thermal as P
from epc_calc import aea_special_locations as S
from epc_calc import aea_voltage_drop as V


class TestDemand(unittest.TestCase):
    def test_grados(self):
        self.assertEqual(D.grade_electrification_771("vivienda", 100)["grado"], "medio")
        self.assertEqual(D.grade_electrification_771("oficina", 20)["grado"], "minimo")
        self.assertEqual(D.grade_electrification_771("local", 6000)["grado"], "superior")
        # 770: 50 + 0,5·20 = 60 m² -> mínimo
        self.assertEqual(D.grade_electrification_770(50, 20)["grado"], "minimo")

    def test_coefficients(self):
        self.assertEqual(D.coef_simultaneity_771("elevado"), 0.8)
        self.assertEqual([D.coef_simultaneity_770(n) for n in (2, 3, 4, 5, 6, 12)], [1.0, 0.8, 0.8, 0.7, 0.6, 0.6])
        self.assertEqual(D.coef_simultaneidad_conjunto(10, "medio"), 0.8)
        self.assertEqual(D.coef_simultaneidad_conjunto(30, "superior"), 0.4)

    def test_msd(self):
        self.assertAlmostEqual(D.msd_lighting_general(10), 990.0)            # 10·150·0,66
        self.assertAlmostEqual(D.msd_lighting_general(10, "770"), 400.0)     # 10·60·2/3
        self.assertEqual(D.msd_circuits(2, 1, 1), 9900.0)                      # 3·2200 + 3300
        self.assertAlmostEqual(D.dpms_total(6600, 0.8, 3300), 8580.0)

    def test_currents(self):
        self.assertAlmostEqual(D.current_msd(8000, 1), 36.3636, places=3)
        self.assertAlmostEqual(D.current_msd(8000, 3), 8000 / (math.sqrt(3) * 380), places=6)
        self.assertTrue(D.requiere_trifasico(8000))
        self.assertFalse(D.requiere_trifasico(5000, 20))

    def test_imbalance_motors_parallel(self):
        r = D.imbalance_phases([30, 20, 25])
        self.assertAlmostEqual(r["desequilibrio_pct"], 33.3333, places=3)
        self.assertFalse(r["cumple"])
        self.assertAlmostEqual(D.corriente_alimentador_motores([10, 20, 10]), 45.0)
        self.assertEqual(D.factor_parallel(2), 1.0)
        self.assertEqual(D.factor_parallel(3), 0.8)
        self.assertEqual(D.factor_parallel(2, multipolar=True), 0.8)
        self.assertAlmostEqual(D.factor_parallel(2, radiacion_solar=True), 0.85)

    def test_errors(self):
        with self.assertRaises(ValueError):
            D.grade_electrification_771("fabrica", 10)
        with self.assertRaises(ValueError):
            D.current_msd(100, 2)


class TestVoltageDrop(unittest.TestCase):
    def test_table(self):
        r = V.drop_by_table(20, 30, 2.5)      # 15·20·0,03 = 9 V ; 9/220
        self.assertAlmostEqual(r["delta_u_v"], 9.0)
        self.assertAlmostEqual(r["delta_u_pct"], 4.0909, places=3)

    def test_gdc(self):
        r = V.caida_gdc(20, 30, 2.5)             # 0,040·20·30/2,5 = 9,6 V
        self.assertAlmostEqual(r["delta_u_v"], 9.6)
        self.assertAlmostEqual(V.longitud_maxima_gdc(10, 2.5, 2), 27.5)   # 4,4·2,5/(0,04·10)
        self.assertAlmostEqual(V.seccion_minima_gdc(50, 100, 2, "cu", 3), 0.035 * 50 * 100 / 7.6, places=6)
        self.assertEqual(V.coeficiente_gdc("cu", 1, True, 2.5), 0.0160)
        self.assertEqual(V.coeficiente_gdc("cu", 1, True, 50), 0.0205)
        self.assertEqual(V.coeficiente_gdc("al", 3), 0.055)

    def test_limits(self):
        self.assertEqual(V.limite_caida_pct("motor_arranque"), 15.0)
        self.assertAlmostEqual(V.corriente_extremo(10, "iluminacion"), 6.6)
        self.assertAlmostEqual(V.corriente_extremo(10, "iluminacion", "770"), 20 / 3)
        self.assertEqual(V.corriente_extremo(10, "tomacorrientes"), 10)
        self.assertAlmostEqual(V.caida_disponible_terminal_pct(5, 1), 4.0)
        self.assertFalse(V.verify_drop(3.5, "iluminacion"))

    def test_errors(self):
        with self.assertRaises(ValueError):
            V.drop_unit_table(3)
        with self.assertRaises(ValueError):
            V.coeficiente_gdc("cu", 1, True, 95)


class TestEarthing(unittest.TestCase):
    def test_ra(self):
        r = E.ra_maxima(0.03)
        self.assertAlmostEqual(r["col1_50v"], 1666.667, places=2)
        self.assertEqual(r["adoptada"], 40.0)
        self.assertAlmostEqual(E.ra_maxima(0.5)["adoptada"], 24.0)    # 0,5·24/0,5
        self.assertAlmostEqual(E.ra_maxima(5)["adoptada"], 2.4)
        self.assertTrue(E.verifica_ra(30, 0.3))
        self.assertFalse(E.verifica_ra(45, 0.3))

    def test_times(self):
        self.assertEqual(E.tiempo_desconexion_max_s("TN", 230), 0.2)
        self.assertEqual(E.tiempo_desconexion_max_s("TT", 230), 0.06)
        self.assertEqual(E.tiempo_desconexion_max_s("TT", 400, "cc"), 0.02)
        self.assertEqual(E.tiempo_seccional_max_s("TT"), 1.0)

    def test_electrodes(self):
        self.assertAlmostEqual(E.resistance_rod(100, 1.5, 0.019, True), 50.0)    # L/d=78,9 -> 0,75ρ/L
        self.assertAlmostEqual(E.resistance_rod(100, 2.0, 0.019, True), 50.0)    # L/d=105 -> ρ/L
        self.assertAlmostEqual(E.resistance_rod(100, 1.5, 0.019), 57.8074, places=3)
        self.assertAlmostEqual(E.resistance_conductor_horizontal(100, 50, 0.01, 0.6, True), 4.0)
        self.assertAlmostEqual(E.resistencia_placa_circular(100, 0.5, 1.0), 54.2105, places=3)
        self.assertAlmostEqual(E.resistance_parallel([10, 10]), 5.0)

    def test_pe(self):
        self.assertEqual([E.seccion_pe_mm2(s) for s in (10, 25, 70)], [10, 16, 35])
        self.assertAlmostEqual(E.seccion_pe_mm2(25, 1.5, 1.0), 24.0)


class TestConductors(unittest.TestCase):
    def test_tables(self):
        self.assertEqual(CO.section_min_circuit("pe"), 2.5)
        self.assertEqual(CO.k_adiabatico_771("epr_xlpe", "cu"), 143.0)
        self.assertEqual(CO.k_adiabatico_771("pvc_sobre_300", "al"), 68.0)
        self.assertEqual(CO.seccion_pen_minima_mm2("al"), 16.0)

    def test_overload(self):
        self.assertTrue(CO.verify_overload(20, 25, 30, 40)["cumple"])       # 40 ≤ 1,45·30 = 43,5
        self.assertFalse(CO.verify_overload(20, 25, 30, 50)["cumple"])
        self.assertFalse(CO.verify_overload(30, 25, 30)["cumple"])
        self.assertTrue(CO.verifica_poder_corte(6000, 5500))

    def test_harmonics(self):
        h = {1: 100, 3: 40}
        self.assertAlmostEqual(CO.thd_pct(h), 37.1391, places=3)     # 40/√11600
        self.assertAlmostEqual(CO.distorsion_d_pct(h), 40.0)
        self.assertAlmostEqual(CO.d_desde_thd(CO.thd_desde_d(0.4)), 0.4)
        self.assertEqual(CO.factor_harmonics(10), {"factor": 1.0, "aplicado_a": "linea"})
        self.assertEqual(CO.factor_harmonics(20)["factor"], 0.86)
        self.assertEqual(CO.factor_harmonics(40), {"factor": 0.86, "aplicado_a": "neutro"})
        self.assertEqual(CO.factor_harmonics(50), {"factor": 1.0, "aplicado_a": "neutro"})
        self.assertAlmostEqual(CO.current_neutral_harmonics(10, 40), 12.0)
        self.assertAlmostEqual(CO.current_corrected(43, 0.86), 50.0)
        self.assertAlmostEqual(CO.current_phase_three_phase(10000, 380, 0.8), 18.9917, places=3)

    def test_volume(self):
        self.assertAlmostEqual(CO.volumen_combustible_dm3_m(27, [35, 35, 35]), 0.4676, places=3)  # ≈ 0,47 de la norma


class TestPanel(unittest.TestCase):
    def test_k(self):
        self.assertEqual([P.factor_k_circuitos(n) for n in (2, 3, 4, 5, 6, 9, 12)], [0.8, 0.8, 0.7, 0.7, 0.6, 0.6, 0.5])
        self.assertAlmostEqual(P.factor_k_nivel(63, 0.8, [16, 16, 16, 16]), 0.7875)
        self.assertAlmostEqual(P.current_nominal_equivalent(100), 85.0)

    def test_powers(self):
        self.assertEqual([P.potencia_disipada_polo_w(i) for i in (10, 32, 63, 125)], [3.0, 6.0, 13.0, 20.0])
        self.assertAlmostEqual(P.potencia_disipada_aparato_w(16, 2, 0.8), 0.64 * 3.5 * 2)
        self.assertAlmostEqual(P.potencia_tablero_w(10, 5), 17.0)
        self.assertTrue(P.verify_panel(17, 20))
        self.assertEqual([P.poder_corte_minimo_diferencial_a(i) for i in (25, 30, 63, 100)], [500, 500, 630, 1000])


class TestIccFactors(unittest.TestCase):
    def test_k(self):
        self.assertAlmostEqual(IF.k_g(10, 10.5, 1.1, 0.12, 0.6), 0.9773, places=4)     # ejemplo de la norma
        self.assertAlmostEqual(IF.k_gs(1.1, 0.12, 0.6), 1.1 / 1.072)
        self.assertAlmostEqual(IF.k_ts(1.1, 0.1, x_d_pu=2.0), 1.1 / 1.05)
        self.assertAlmostEqual(IF.k_ts(1.1, 0.1, sen_fi_rg=0.6), 1.1 / 0.94)
        self.assertAlmostEqual(IF.k_tso(1.1, 10.5, 10), 1.155)
        self.assertAlmostEqual(IF.k_s(10, 10.5, 10.5, 10, 1.1, 0.12, 0.1, 0.6), 1.1 / 1.012)
        self.assertAlmostEqual(IF.k_so(10, 10.5, 0, 10.5, 10, 1.1, 0.12, 0.6), 1.1 / 1.072)
        self.assertAlmostEqual(IF.k_so(10, 10.5, 0, 10.5, 10, 1.1, 0.12, 0.6, p_t=0.05), 0.95 * 1.1 / 1.072)

    def test_generales(self):
        self.assertAlmostEqual(IF.delta_i_kmax(0.05), -0.047619, places=6)
        self.assertAlmostEqual(IF.delta_i_kmax(0.10), -0.090909, places=6)
        self.assertAlmostEqual(IF.c_max_desde_tension(420, 400), 1.05)
        self.assertTrue(IF.defecto_tierra_rigido(1.3856, 1.0))
        self.assertFalse(IF.defecto_tierra_rigido(1.5, 1.0))

    def test_currents(self):
        # Z_G = j·1,323 Ω (x''d·Z_rG = 0,12·11,025) ; I = 1,1·10000/(√3·1,323·0,97726) ≈ 4911,9 A
        self.assertAlmostEqual(IF.ik_generador(1.1, 10000, IF.k_g(10, 10.5, 1.1, 0.12, 0.6), 1.323j), 4911.9, delta=1.0)
        self.assertAlmostEqual(IF.reactancia_trafo_ohm(4, 400, 500e3), 0.0128)
        i_q = 300e6 / (math.sqrt(3) * 13200)
        self.assertAlmostEqual(IF.reactancia_red_lv_ohm(1.1, 13200, i_q, 400, 13200), 5.8666e-4, places=7)

    def test_motors(self):
        self.assertTrue(IF.motors_contribution_negligible(4, 100))
        self.assertFalse(IF.motors_contribution_negligible(6, 100))
        self.assertTrue(IF.motores_baja_tension_despreciables(0.9, 100))


class TestIccDecay(unittest.TestCase):
    def test_kappa(self):
        self.assertAlmostEqual(ID.kappa_exacto(0, 1), 2.0, places=3)
        k = ID.kappa_exacto(0.1, 1)
        self.assertTrue(1.70 < k < 1.02 + 0.98 * math.exp(-0.3))       # exacto ≤ κ de IEC
        self.assertAlmostEqual(ID.current_peak_to(1.8, 10000), 25455.84, places=1)

    def test_m_n(self):
        self.assertAlmostEqual(ID.constante_aperiodica_s(1.8, 50), 0.044814, places=6)
        self.assertAlmostEqual(ID.factor_m(1.8, 50, 1.0), 0.044814, places=5)     # ≈ T_aN/T_k (e^-44 ≈ 0)
        self.assertAlmostEqual(ID.factor_n_simplificado(1, 1, 1, 1, 1), 1.0)       # lejos del generador: n = 1
        self.assertAlmostEqual(ID.factor_n_generico(1, 1, 1, 1, 0.1, 1.0), 1.0)
        self.assertAlmostEqual(ID.current_thermal_equivalent_to(10000, 0.2, 1.0), 10000 * math.sqrt(1.2))

    def test_mu_q(self):
        self.assertAlmostEqual(ID.mu_generador(0.1, 0.05, 0.2, 0.3), 0.7117785, places=6)
        self.assertAlmostEqual(ID.factor_q(2.4, 0.75, 4.0), 0.8)
        self.assertAlmostEqual(ID.constante_tiempo_mu_q(0.1, 0.75, 0.8), 0.195761, places=5)

    def test_decay_y_tensiones(self):
        self.assertAlmostEqual(ID.corriente_alterna_t(0, 10, 6, 3, 0.05, 1.0), 10.0)
        self.assertAlmostEqual(ID.corriente_alterna_t(1e6, 10, 6, 3, 0.05, 1.0), 3.0)
        self.assertAlmostEqual(ID.voltage_internal_subtransient(10500, 0.12, 0.6), 6498.65, places=1)
        self.assertAlmostEqual(ID.voltage_internal_rated(10500, 2.0, 0.6), 10500 / math.sqrt(3) * math.sqrt(7.4), places=6)
        self.assertEqual(ID.current_steady_to(2.5, 100), 250.0)

    def test_errors(self):
        with self.assertRaises(ValueError):
            ID.factor_m(2.0, 50, 1)
        with self.assertRaises(ValueError):
            ID.constante_tiempo_mu_q(0.1, 1.2, 0.9)


class TestSpecial(unittest.TestCase):
    def test_701(self):
        self.assertAlmostEqual(S.induccion_conductor_t(10, 0.02), 1e-4, places=9)
        self.assertFalse(S.induccion_admisible(10, 0.02))
        self.assertTrue(S.induccion_admisible(10, 0.1))      # 2·10⁻⁵ T
        self.assertAlmostEqual(S.radio_zona2_con_tabique_m(0.2), 0.4)

    def test_722(self):
        self.assertAlmostEqual(S.factor_demand(60, 100), 0.6)
        self.assertTrue(S.load_multiple_complies(4, 4, 32, 16)["cumple"])
        self.assertFalse(S.load_multiple_complies(9, 9, 32, 16)["cumple"])


class TestCatalogo(unittest.TestCase):
    def test_sin_repeticiones(self):
        ids = [r["id"] for r in CAT.catalogo()]
        self.assertEqual(len(ids), len(set(ids)))
        nombres = [r["funcion"] for r in CAT.catalogo()]
        self.assertEqual(len(nombres), len(set(nombres)), "función con el mismo nombre en dos módulos")

    def test_no_duplica_previos(self):
        nombres = {r["funcion"] for r in CAT.catalogo()}
        for previo in CAT.PREVIOS:
            self.assertNotIn(previo.split(".")[1], nombres)

    def test_buscar_y_docstrings(self):
        self.assertTrue(CAT.buscar("kappa"))
        for r in CAT.catalogo():
            self.assertTrue(r["resumen"], f"{r['id']} sin docstring")


if __name__ == "__main__":
    unittest.main()
