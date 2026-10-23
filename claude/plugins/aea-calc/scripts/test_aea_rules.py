"""Pruebas de aea_rules y de la consistencia de los JSON de reglas."""
import unittest

import aea_rules as R


class TestReglas(unittest.TestCase):
    def test_indice_coincide_con_archivos(self):
        ind = R.indice()
        self.assertEqual(ind["total_reglas"], len(R.reglas()))
        for g, d in ind["grupos"].items():
            self.assertEqual(d["cantidad"], len(R.reglas(g)))

    def test_estructura_de_cada_regla(self):
        ids = set()
        for r in R.reglas():
            self.assertNotIn(r["id"], ids)
            ids.add(r["id"])
            self.assertTrue(r["id"].startswith(r["grupo"] + "."))
            self.assertIn(r["tipo"], R.TIPOS)
            self.assertTrue(r["regla"].strip() and r["tema"].strip())
            self.assertTrue(r["aplica_a"])
            f = r["fuente"]
            self.assertTrue(f["norma"].startswith("AEA 90364-"))
            self.assertTrue(f["clausula"] and f["cita"].strip())
            if f["norma"].startswith("AEA 90364-7-"):          # Parte 7: texto digital, página como número
                self.assertIsInstance(f["pagina_impresa"], int)
            else:                                              # Partes 4 y 5: OCR, "54-5" y página del PDF
                self.assertRegex(f["pagina_impresa"], r"^\d{2}-\d{1,2}$")
                self.assertIsInstance(f["pagina_pdf"], int)
                self.assertIn(f["verificacion"], ("ocr", "visual"))
            self.assertIsInstance(r["parametros"], dict)

    def test_valores_de_referencia_leidos_a_mano(self):
        self.assertEqual(R.valor("bandejas.reserva_20pct", "reserva_min_pct"), 20)
        self.assertEqual(R.valor("tomacorrientes.altura_arista_inferior_771", "altura_min_m"), 0.15)
        self.assertEqual(R.valor("tomacorrientes.altura_arista_inferior_770", "altura_max_m"), 0.3)
        self.assertEqual(R.valor("interruptores.altura_centro", "altura_recomendada_m"), 1.1)
        self.assertEqual(R.valor("canalizaciones.llenado_max_caños_no_tabulados", "ocupacion_max_pct"), 35)
        self.assertEqual(R.valor("tableros.reserva_771", "reserva_min_pct"), 20)
        self.assertEqual(R.valor("circuitos.tug_bocas_max", "bocas_max"), 15)
        self.assertEqual(R.valor("circuitos.iug_proteccion_max", "proteccion_max_a"), 16)
        self.assertEqual(R.valor("enterrados.profundidad_cables_directos", "profundidad_min_m"), 0.7)
        self.assertEqual(R.valor("banos.zona1_altura", "altura_cm"), 225)

    def test_cita_contiene_el_valor_numerico(self):
        # lo esencial: los umbrales numéricos de estas reglas aparecen escritos en su cita
        for id_, texto in (("bandejas.reserva_20pct", "20 %"), ("canalizaciones.curvas_max_entre_cajas", "tres"),
                           ("interruptores.pasillos_mayores_3m", "6 m"), ("tableros.altura_comandos", "0,40 m y 2 m")):
            self.assertIn(texto, R.regla(id_)["fuente"]["cita"])

    def test_partes_4_y_5(self):
        self.assertEqual(R.valor("puesta_a_tierra.tt_ra_maxima", "ra_max_ohm"), 40)
        self.assertEqual(R.valor("conductores_proteccion.equipotencial_principal", "min_cu_mm2"), 6)
        self.assertEqual(R.valor("conductores_proteccion.equipotencial_principal", "max_cu_mm2"), 25)
        self.assertEqual(R.valor("conductores_proteccion.pen_seccion_minima", "cu_mm2"), 10)
        self.assertEqual(R.valor("conductores_proteccion.pe_formula_adiabatica", "t_max_s"), 5)
        self.assertEqual(R.valor("conductores.neutro_armonicas_145", "factor_corriente_neutro"), 1.45)
        self.assertEqual(R.valor("conductores.caida_tension_iluminacion", "du_max_pct"), 3)
        self.assertEqual(R.valor("proteccion_choques.tn_s_tiempo_2s", "t_max_s"), 2)
        self.assertEqual(R.valor("proteccion_choques.dd_30ma_proteccion_adicional", "idn_max_ma"), 30)
        self.assertEqual(R.valor("curvas_canerias.max_tres_curvas", "curvas_max_entre_cajas"), 3)
        self.assertEqual(R.regla("puesta_a_tierra.tt_ra_maxima")["fuente"]["pagina_impresa"], "54-4")

    def test_tablas_de_las_partes_4_y_5(self):
        # Tabla 54.1: Ra decrece al aumentar IΔn y la columna 3 nunca supera 40 Ω
        t = R.regla("puesta_a_tierra.tt_ra_tabla_54_1")["tabla"]["filas"]
        self.assertEqual(len(t), 9)
        self.assertTrue(all(f[3] <= 40 for f in t))
        # Tabla 54.6: k de XLPE (cobre 170) y de PVC (136/126)
        k = {f[0]: f for f in R.regla("conductores_proteccion.k_pe_aislado_tabla_54_6")["tabla"]["filas"]}
        self.assertEqual(k["EPR o XLPE 90 °C"][3:], [170, 113, 62])
        self.assertEqual(k["PVC 70 °C"][3], "136/126")
        # Tabla 54.8 (cables agrupados): XLPE cobre 143
        k8 = {f[0]: f for f in R.regla("conductores_proteccion.k_pe_en_cable_tabla_54_8")["tabla"]["filas"]}
        self.assertEqual(k8["EPR o XLPE 90 °C"][3], 143)
        # Tabla 43.1: XLPE 90/130/250
        x = [f for f in R.regla("proteccion_sobrecorrientes.temperaturas_tabla_43_1")["tabla"]["filas"] if "XLPE" in f[0]][0]
        self.assertEqual(x[1:], [90, 130, 250])
        # Tabla 52.12: 7 diámetros, rígidas solo hasta 25 mm
        r = R.regla("curvas_canerias.radios_sinteticos_tabla_52_12")["tabla"]["filas"]
        self.assertEqual([f[0] for f in r], [16, 20, 25, 32, 40, 50, 63])
        self.assertTrue(all(f[3] is None for f in r[3:]))

    def test_tablas(self):
        t = R.regla("canalizaciones.curvas_fabrica_tabla")["tabla"]
        self.assertEqual(len(t), 7)
        self.assertEqual((t[0]["designacion_iram_mm"], t[0]["radio_min_mm"], t[0]["radio_max_mm"]), (16, 35, 45))
        for fila in t:
            self.assertLess(fila["radio_min_mm"], fila["radio_max_mm"])

    def test_busqueda(self):
        self.assertTrue(R.buscar("reserva"))
        self.assertTrue(all(r["tipo"] == "prohibido" for r in R.buscar(tipo="prohibido")))
        self.assertTrue(all("771" in r["fuente"]["norma"] for r in R.buscar(norma="771")))
        self.assertTrue(R.buscar(grupo="banos"))
        with self.assertRaises(ValueError):
            R.regla("tableros.no_existe")
        with self.assertRaises(ValueError):
            R.reglas("inexistente")
        with self.assertRaises(ValueError):
            R.valor("tableros.reserva_771", "xyz")


if __name__ == "__main__":
    unittest.main()
