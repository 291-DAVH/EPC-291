"""Pruebas de current_and_loads.py — valores de referencia calculados A MANO."""
import unittest

import current_and_loads as K


class TestCorrientes(unittest.TestCase):
    def test_monofasica_exacta(self):
        # I = 2300 / (230 · 0,8 · 0,5) = 2300 / 92 = 25 A
        self.assertAlmostEqual(K.corriente_monofasica(2300, 230, 0.8, 0.5), 25.0, places=9)
        # Resistiva: 2300 W / 230 V = 10 A
        self.assertAlmostEqual(K.corriente_monofasica(2300, 230), 10.0, places=9)

    def test_three_phase(self):
        # I = 10 000 / (√3 · 400 · 0,8) = 10 000 / (1,7320508 · 320) = 10 000 / 554,256 = 18,0422 A
        self.assertAlmostEqual(K.corriente_trifasica(10000, 400, 0.8), 18.0422, places=3)

    def test_power_apparent(self):
        # S = 10 000 / 0,8 = 12 500 VA
        self.assertAlmostEqual(K.potencia_aparente_desde_p(10000, 0.8), 12500.0, places=9)
        # Mono 230 V · 10 A = 2 300 VA ; Tri √3 · 400 · 10 = 6 928,2 VA
        self.assertAlmostEqual(K.power_apparent_single_phase(230, 10), 2300.0, places=9)
        self.assertAlmostEqual(K.power_apparent_three_phase(400, 10), 6928.2, places=1)

    def test_validaciones(self):
        for f, args in ((K.corriente_monofasica, (1000, 0, 0.9)),
                        (K.corriente_monofasica, (1000, 230, 1.5)),
                        (K.corriente_monofasica, (1000, 230, 0.9, 0)),
                        (K.corriente_monofasica, (-1, 230, 0.9)),
                        (K.corriente_trifasica, (1000, -400, 0.9)),
                        (K.corriente_trifasica, (1000, 400, 0)),
                        (K.potencia_aparente_desde_p, (1000, 0))):
            with self.assertRaises(ValueError, msg=f"{f.__name__}{args}"):
                f(*args)


class TestBalance(unittest.TestCase):
    def test_balance_dos_cargas(self):
        # A: 10 kW, cosφ 0,8 (tanφ = 0,75), fu 1,0 -> P = 10 kW ; Q = 7,5 kvar
        # B: 20 kW, cosφ 1,0 (tanφ = 0), fu 0,5     -> P = 10 kW ; Q = 0
        # Σ P = 20 kW ; Σ Q = 7,5 kvar ; fs = 0,8 -> P = 16 kW ; Q = 6 kvar
        # S = √(16² + 6²) = √292 = 17,0880 kVA ; fp = 16/17,088 = 0,93633
        # I = 17 088 / (√3 · 400) = 17 088 / 692,82 = 24,664 A
        b = K.balance_cargas([{"p_w": 10000, "fp": 0.8, "fu": 1.0},
                              {"p_w": 20000, "fp": 1.0, "fu": 0.5}], fs=0.8, v_linea_v=400)
        self.assertAlmostEqual(b["p_instalada_w"], 30000.0, places=6)
        self.assertAlmostEqual(b["p_w"], 16000.0, places=6)
        self.assertAlmostEqual(b["q_var"], 6000.0, places=6)
        self.assertAlmostEqual(b["s_va"], 17088.0, places=0)
        self.assertAlmostEqual(b["fp"], 0.93633, places=4)
        self.assertAlmostEqual(b["i_a"], 24.664, places=2)

    def test_sin_tension_no_calcula_corriente(self):
        b = K.balance_cargas([{"p_w": 1000}])
        self.assertIsNone(b["i_a"])
        # Resistiva única: S = P = 1000 VA, fp = 1
        self.assertAlmostEqual(b["s_va"], 1000.0, places=9)
        self.assertAlmostEqual(b["fp"], 1.0, places=9)

    def test_validaciones(self):
        with self.assertRaises(ValueError):
            K.balance_cargas([])
        with self.assertRaises(ValueError):
            K.balance_cargas([{"p_w": 1000}], fs=1.2)
        with self.assertRaises(ValueError):
            K.balance_cargas([{"p_w": 1000, "fu": 0}])
        with self.assertRaises(ValueError):
            K.balance_cargas([{"nombre": "X", "p_w": -5}])
        with self.assertRaises(ValueError):
            K.balance_cargas([{"fp": 0.9}])        # falta p_w
        with self.assertRaises(ValueError):
            K.balance_cargas([{"p_w": 1000, "fp": 1.1}])


class TestReserva(unittest.TestCase):
    def test_reserve(self):
        # I_b = 20 A, I_n = 25 A: reserva = 5 A ; 5/25 = 20 % ; uso = 20/25 = 80 %
        r = K.reserve_breaker(20, 25, reserva_min_pct=20)
        self.assertAlmostEqual(r["reserva_a"], 5.0, places=9)
        self.assertAlmostEqual(r["reserva_pct"], 20.0, places=9)
        self.assertAlmostEqual(r["uso_pct"], 80.0, places=9)
        self.assertTrue(r["cumple"])

    def test_not_complies_and_overload(self):
        # I_b = 22 -> reserva 3 A = 12 % < 20 % -> no cumple
        self.assertFalse(K.reserve_breaker(22, 25, 20)["cumple"])
        # I_b = 30 > 25: reserva = -5 A = -20 %
        r = K.reserve_breaker(30, 25, 0)
        self.assertAlmostEqual(r["reserva_pct"], -20.0, places=9)
        self.assertFalse(r["cumple"])
        self.assertIsNone(K.reserve_breaker(10, 25)["cumple"])

    def test_validaciones(self):
        with self.assertRaises(ValueError):
            K.reserve_breaker(10, 0)
        with self.assertRaises(ValueError):
            K.reserve_breaker(-1, 25)


class TestReparto(unittest.TestCase):
    def test_reparto_perfecto(self):
        # Corrientes 10, 8, 7, 5, 4, 2 (Σ = 36 A -> media 12 A). Orden decreciente, voraz:
        #  10 -> L1 (10,0,0) ; 8 -> L2 (10,8,0) ; 7 -> L3 (10,8,7)
        #  5 -> L3 (la menor, 7)  -> (10,8,12)
        #  4 -> L2 (la menor, 8)  -> (10,12,12)
        #  2 -> L1 (la menor, 10) -> (12,12,12) ; desbalance = 0 %
        r = K.split_phases([("C1", 10), ("C2", 8), ("C3", 7), ("C4", 5), ("C5", 4), ("C6", 2)])
        self.assertEqual(r["asignacion"], [["C1", "C6"], ["C2", "C5"], ["C3", "C4"]])
        self.assertEqual(r["corrientes"], [12.0, 12.0, 12.0])
        self.assertAlmostEqual(r["desbalance_pct"], 0.0, places=9)

    def test_reparto_con_desbalance(self):
        # Corrientes 10, 4 en 3 fases: 10 -> L1 ; 4 -> L2 ; L3 = 0. Media = 14/3 = 4,6667
        # Desbalance = 100·(10 − 4,6667)/4,6667 = 114,2857 %
        r = K.split_phases([("A", 4), ("B", 10)])
        self.assertEqual(r["corrientes"], [10.0, 4.0, 0.0])
        self.assertAlmostEqual(r["desbalance_pct"], 114.2857, places=3)

    def test_two_phases(self):
        # 6, 5, 4 en 2 fases: 6 -> F1 ; 5 -> F2 ; 4 -> F2 (5 < 6) -> (6, 9): media 7,5 ; desbalance = 100·1,5/7,5 = 20 %
        r = K.split_phases([("a", 6), ("b", 5), ("c", 4)], n_fases=2)
        self.assertEqual(r["corrientes"], [6.0, 9.0])
        self.assertAlmostEqual(r["desbalance_pct"], 20.0, places=9)

    def test_validaciones(self):
        with self.assertRaises(ValueError):
            K.split_phases([])
        with self.assertRaises(ValueError):
            K.split_phases([("a", -1)])
        with self.assertRaises(ValueError):
            K.split_phases([("a", 1)], n_fases=0)
        with self.assertRaises(ValueError):
            K.split_phases([5])   # no es tupla


if __name__ == "__main__":
    unittest.main()
