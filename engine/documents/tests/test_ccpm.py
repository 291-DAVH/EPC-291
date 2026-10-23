#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de ccpm.py (unittest). Los valores esperados se calcularon a mano.

Calendario de referencia: inicio lunes 2026-10-05, lunes a viernes. Numeración de días
hábiles: 1=lun 5/10, 2=mar 6, 3=mié 7, 4=jue 8, 5=vie 9, 6=lun 12, 7=mar 13, 8=mié 14,
9=jue 15, 10=vie 16, 11=lun 19, 12=mar 20.

Ejecutar (desde esta carpeta): python3 -B -m unittest test_ccpm -v
O desde cualquier lugar: python3 -B -m unittest discover -s <esta carpeta> -p test_ccpm.py -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
from epc_documents import ccpm  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(ccpm.__file__))


def tarea(id_, seg, agr=None, preds=(), recurso="R", **kw):
    t = {"id": id_, "nombre": f"Tarea {id_}", "recurso": recurso, "dur_segura": seg,
         "predecesores": list(preds)}
    # Estas pruebas calculan a mano con agresiva = ceil(segura / 2); se fija explícita para no depender del
    # valor por defecto del módulo (70 % de la segura), que se prueba aparte.
    t["dur_agresiva"] = agr if agr is not None else max(1, (seg + 1) // 2)
    t.update(kw)
    return t


def proyecto(tareas, **kw):
    d = {"inicio": "2026-10-05", "tareas": tareas}
    d.update(kw)
    return d


def lineal(**kw):
    """Cadena lineal: seguras 4, 6, 2; agresivas 2, 3, 1; un solo recurso."""
    return proyecto([tarea("T1", 4, 2), tarea("T2", 6, 3, ["T1"]), tarea("T3", 2, 1, ["T2"])], **kw)


def por_id(res):
    return {t["id"]: t for t in res["tareas"]}


class TestCadenaLineal(unittest.TestCase):
    def test_valores_a_mano(self):
        r = ccpm.calcular_ccpm(lineal())
        s = r["resumen"]
        self.assertEqual(s["dias_habiles_hasta_fin_cadena"], 6)
        self.assertEqual(s["buffer_proyecto_dias"], 3)       # ceil(0,5 x 6)
        self.assertEqual(s["dias_habiles_hasta_fin_proyecto"], 9)
        self.assertEqual(s["fin_cadena"], "2026-10-12")
        self.assertEqual(s["fin_proyecto"], "2026-10-15")
        t = por_id(r)
        self.assertEqual((t["T1"]["inicio"], t["T1"]["fin"]), ("2026-10-05", "2026-10-06"))
        self.assertEqual((t["T2"]["inicio"], t["T2"]["fin"]), ("2026-10-07", "2026-10-09"))
        self.assertEqual((t["T3"]["inicio"], t["T3"]["fin"]), ("2026-10-12", "2026-10-12"))
        self.assertEqual([e["id"] for e in r["cadena_critica"]["eslabones"]], ["T1", "T2", "T3"])
        self.assertEqual(r["buffers"]["alimentacion"], [])
        bp = r["buffers"]["proyecto"]
        self.assertEqual((bp["inicio"], bp["fin"]), ("2026-10-13", "2026-10-15"))
        self.assertEqual((bp["inicio_dia"], bp["fin_dia"]), (7, 9))

    def test_vinculos_de_la_cadena(self):
        e = ccpm.calcular_ccpm(lineal())["cadena_critica"]["eslabones"]
        self.assertEqual(e[0]["vinculo_con_anterior"], "inicio del proyecto")
        self.assertEqual(e[1]["vinculo_con_anterior"], "precedencia y recurso")
        self.assertIsNone(e[0]["predecesor"])
        self.assertEqual(e[2]["predecesor"], "T2")

    def test_rss(self):
        r = ccpm.calcular_ccpm(lineal(metodo_buffer="rss"))
        # raiz(2^2 + 3^2 + 1^2) = raiz(14) = 3,74 -> 4
        self.assertEqual(r["resumen"]["buffer_proyecto_dias"], 4)
        self.assertEqual(r["resumen"]["dias_habiles_hasta_fin_proyecto"], 10)

    def test_duracion_agresiva_por_defecto(self):
        # regla del proyecto: recorte del 30 % -> agresiva = ceil(70 % de la segura), mínimo 1
        tareas = [{"id": f"T{s}", "nombre": f"T{s}", "recurso": f"R{s}", "dur_segura": s, "predecesores": []}
                  for s in (1, 2, 4, 5, 7, 10)]
        r = ccpm.calcular_ccpm(proyecto(tareas))
        agr = {t["id"]: t["dur_agresiva"] for t in r["tareas"]}
        self.assertEqual(agr, {"T1": 1, "T2": 2, "T4": 3, "T5": 4, "T7": 5, "T10": 7})

    def test_buffer_minimo_un_dia(self):
        r = ccpm.calcular_ccpm(proyecto([tarea("A", 1)]))
        self.assertEqual(r["resumen"]["buffer_proyecto_dias"], 1)   # ceil(0,5) = 1
        self.assertEqual(r["resumen"]["dias_habiles_hasta_fin_proyecto"], 2)


class TestRutaDeAlimentacion(unittest.TestCase):
    def datos(self):
        # A(R1) -> B(R1) es la cadena; C(R2) alimenta a B.
        return proyecto([tarea("A", 8, 4, recurso="R1"),
                         tarea("B", 4, 2, ["A", "C"], recurso="R1"),
                         tarea("C", 4, 2, recurso="R2")])

    def test_buffer_de_alimentacion(self):
        r = ccpm.calcular_ccpm(self.datos())
        self.assertEqual([e["id"] for e in r["cadena_critica"]["eslabones"]], ["A", "B"])
        self.assertEqual(r["resumen"]["dias_habiles_hasta_fin_cadena"], 6)
        self.assertEqual(r["resumen"]["buffer_proyecto_dias"], 3)       # ceil(0,5 x 6)
        self.assertEqual(r["resumen"]["fin_proyecto"], "2026-10-15")
        fb = r["buffers"]["alimentacion"]
        self.assertEqual(len(fb), 1)
        self.assertEqual((fb[0]["id"], fb[0]["se_une_a"], fb[0]["tamano_dias"]), ("FB-1", "B", 1))
        self.assertEqual(fb[0]["tareas_protegidas"], ["C"])
        self.assertEqual((fb[0]["inicio"], fb[0]["fin"]), ("2026-10-08", "2026-10-08"))
        t = por_id(r)
        # C se reprograma lo más tarde posible: días 2-3, buffer día 4, B arranca el día 5.
        self.assertEqual((t["C"]["inicio_dia"], t["C"]["fin_dia"]), (2, 3))
        self.assertEqual((t["C"]["inicio"], t["C"]["fin"]), ("2026-10-06", "2026-10-07"))
        self.assertEqual(t["C"]["inicio_temprano"], "2026-10-05")
        self.assertEqual(t["C"]["rol"], "alimentacion")
        self.assertEqual(t["C"]["buffer_alimentacion"], "FB-1")
        self.assertEqual((t["B"]["inicio_dia"], t["B"]["fin_dia"]), (5, 6))
        self.assertEqual(r["advertencias"], [])

    def test_sin_holgura_retrasa_la_union(self):
        # A y C de 4 días agresivos terminan juntos; el buffer de C (ceil(0,5 x 4) = 2)
        # no cabe sin retrasar B 2 días.
        r = ccpm.calcular_ccpm(proyecto([tarea("A", 8, 4, recurso="R1"),
                                         tarea("B", 4, 2, ["A", "C"], recurso="R1"),
                                         tarea("C", 8, 4, recurso="R2")]))
        t = por_id(r)
        self.assertEqual((t["B"]["inicio_dia"], t["B"]["fin_dia"]), (7, 8))
        self.assertEqual((t["C"]["inicio_dia"], t["C"]["fin_dia"]), (1, 4))
        fb = r["buffers"]["alimentacion"][0]
        self.assertEqual((fb["tamano_dias"], fb["inicio_dia"], fb["fin_dia"]), (2, 5, 6))
        self.assertEqual(r["resumen"]["dias_habiles_hasta_fin_cadena"], 8)
        self.assertEqual(r["resumen"]["buffer_proyecto_dias"], 3)
        self.assertEqual(r["resumen"]["dias_habiles_hasta_fin_proyecto"], 11)
        self.assertTrue(any("retrasó 2" in a for a in r["advertencias"]))
        eslabon_b = r["cadena_critica"]["eslabones"][1]
        self.assertEqual(eslabon_b["desfase_por_buffer_alimentacion"], 2)
        self.assertEqual(eslabon_b["alternativas"][0]["id"], "C")   # empate informado

    def test_no_se_solapa_con_el_mismo_recurso(self):
        # X (R1) alimenta a la cadena y comparte recurso con la tarea crítica A (R1) que
        # la precede en el recurso: el reprogramado no debe superponerlas.
        r = ccpm.calcular_ccpm(proyecto([
            tarea("A", 4, 2, recurso="R1"), tarea("X", 4, 2, recurso="R1"),
            tarea("F", 2, 1, ["A", "X"], recurso="R2"),
            tarea("G", 20, 10, recurso="R3"), tarea("Z", 2, 1, ["F", "G"], recurso="R2")]))
        t = por_id(r)
        for a in t.values():
            for b in t.values():
                if a["id"] < b["id"] and a["recurso"] == b["recurso"]:
                    self.assertTrue(a["fin_dia"] <= b["inicio_dia"] - 1 or b["fin_dia"] <= a["inicio_dia"] - 1,
                                    f"{a['id']} y {b['id']} se solapan")
        for tt in t.values():
            for p in tt["predecesores"]:
                self.assertLess(t[p]["fin_dia"], tt["inicio_dia"])


class TestRecursos(unittest.TestCase):
    def test_serializacion_y_vinculo_de_recurso(self):
        # A (agr 2) y B (agr 3) independientes con el mismo recurso: ruta restante mayor
        # primero -> B, luego A.
        r = ccpm.calcular_ccpm(proyecto([tarea("A", 4, 2), tarea("B", 6, 3)]))
        t = por_id(r)
        self.assertEqual((t["B"]["inicio_dia"], t["B"]["fin_dia"]), (1, 3))
        self.assertEqual((t["A"]["inicio_dia"], t["A"]["fin_dia"]), (4, 5))
        e = r["cadena_critica"]["eslabones"]
        self.assertEqual([x["id"] for x in e], ["B", "A"])
        self.assertEqual(e[1]["vinculo_con_anterior"], "recurso")
        self.assertEqual(e[0]["vinculo_con_anterior"], "inicio del proyecto")
        self.assertEqual(r["resumen"]["dias_habiles_hasta_fin_cadena"], 5)
        self.assertEqual(r["resumen"]["buffer_proyecto_dias"], 3)       # ceil(2,5)
        self.assertEqual(r["resumen"]["dias_habiles_hasta_fin_proyecto"], 8)
        self.assertTrue(any("aisladas" in a for a in r["advertencias"]))

    def test_prioridad_por_ruta_restante(self):
        # B tiene sucesor C (ruta restante 1+3) y A no: B va primero aunque su id sea mayor.
        r = ccpm.calcular_ccpm(proyecto([tarea("A", 2, 1, recurso="R1"),
                                         tarea("B", 2, 1, recurso="R1"),
                                         tarea("C", 6, 3, ["B"], recurso="R2")]))
        t = por_id(r)
        self.assertEqual(t["B"]["inicio_dia"], 1)
        self.assertEqual(t["A"]["inicio_dia"], 2)
        self.assertTrue(any("aisladas" in a and "A" in a for a in r["advertencias"]))

    def test_empate_por_id_natural(self):
        r = ccpm.calcular_ccpm(proyecto([tarea("T10", 2, 1), tarea("T2", 2, 1)]))
        t = por_id(r)
        self.assertEqual(t["T2"]["inicio_dia"], 1)
        self.assertEqual(t["T10"]["inicio_dia"], 2)

    def test_recurso_externo_no_se_serializa(self):
        r = ccpm.calcular_ccpm(proyecto([
            tarea("E1", 4, 2, recurso="Cliente", tipo_recurso="externo"),
            tarea("E2", 2, 1, recurso="Cliente", tipo_recurso="externo"),
            tarea("X", 2, 1, ["E1", "E2"], recurso="Equipo")]))
        t = por_id(r)
        self.assertEqual(t["E1"]["inicio_temprano"], t["E2"]["inicio_temprano"])
        self.assertEqual(t["E1"]["inicio_dia"], 1)
        self.assertEqual((t["X"]["inicio_dia"], t["X"]["fin_dia"]), (3, 3))
        self.assertEqual(r["buffers"]["alimentacion"][0]["tareas_protegidas"], ["E2"])
        self.assertTrue(any("externo" in a for a in r["advertencias"]))   # E1 en la cadena

    def test_fecha_no_antes_de(self):
        r = ccpm.calcular_ccpm(proyecto([tarea("A", 2, 1, fecha_no_antes_de="2026-10-08")]))
        t = por_id(r)["A"]
        self.assertEqual((t["inicio"], t["inicio_dia"]), ("2026-10-08", 4))
        e = r["cadena_critica"]["eslabones"][0]
        self.assertEqual(e["vinculo_con_anterior"], "fecha_no_antes_de")
        self.assertEqual(r["resumen"]["dias_habiles_hasta_fin_proyecto"], 5)   # 4 + buffer 1

    def test_fecha_no_antes_de_en_fin_de_semana_pasa_al_lunes(self):
        r = ccpm.calcular_ccpm(proyecto([tarea("A", 2, 1, fecha_no_antes_de="2026-10-10")]))
        self.assertEqual(por_id(r)["A"]["inicio"], "2026-10-12")


class TestCalendario(unittest.TestCase):
    def test_feriado_en_medio(self):
        r = ccpm.calcular_ccpm(lineal(feriados=["2026-10-07"]))
        t = por_id(r)
        # días hábiles: 5, 6, 8, 9, 12, 13, 14, 15, 16
        self.assertEqual((t["T1"]["inicio"], t["T1"]["fin"]), ("2026-10-05", "2026-10-06"))
        self.assertEqual((t["T2"]["inicio"], t["T2"]["fin"]), ("2026-10-08", "2026-10-12"))
        self.assertEqual((t["T3"]["inicio"], t["T3"]["fin"]), ("2026-10-13", "2026-10-13"))
        self.assertEqual(r["resumen"]["dias_habiles_hasta_fin_proyecto"], 9)
        self.assertEqual(r["resumen"]["fin_cadena"], "2026-10-13")
        self.assertEqual(r["resumen"]["fin_proyecto"], "2026-10-16")

    def test_inicio_en_dia_no_habil(self):
        r = ccpm.calcular_ccpm(lineal(inicio="2026-10-10"))
        self.assertEqual(r["resumen"]["inicio_efectivo"], "2026-10-12")
        self.assertTrue(any("no es día hábil" in a for a in r["advertencias"]))

    def test_dias_laborables_con_nombres(self):
        d = proyecto([tarea("A", 6, 3)], inicio="2026-10-08",
                     dias_laborables=["lunes", "martes", "miércoles", "jueves", "viernes", "sábado"])
        r = ccpm.calcular_ccpm(d)
        self.assertEqual(por_id(r)["A"]["fin"], "2026-10-10")   # jue, vie, sáb


class TestFechaLimite(unittest.TestCase):
    def test_excedida(self):
        r = ccpm.calcular_ccpm(lineal(fecha_limite_contractual="2026-10-13"))
        fl = r["fecha_limite"]
        # días hábiles hasta el 13/10 = 7; fin con buffer = día 9 -> déficit 2; caben 7 - 6 = 1.
        self.assertFalse(fl["cumple"])
        self.assertEqual(fl["deficit_dias_habiles"], 2)
        self.assertEqual(fl["buffer_que_cabe_dias"], 1)
        self.assertEqual(fl["buffer_propuesto_dias"], 3)
        self.assertIn("ALERTA", fl["alerta"])
        self.assertIn(fl["alerta"], r["advertencias"])

    def test_ni_la_cadena_cabe(self):
        r = ccpm.calcular_ccpm(lineal(fecha_limite_contractual="2026-10-09"))
        fl = r["fecha_limite"]
        self.assertEqual(fl["deficit_dias_habiles"], 4)     # 9 - 5
        self.assertEqual(fl["buffer_que_cabe_dias"], 0)
        self.assertIn("no cabe ningún buffer", fl["alerta"])

    def test_cumple_con_holgura(self):
        r = ccpm.calcular_ccpm(lineal(fecha_limite_contractual="2026-10-20"))
        fl = r["fecha_limite"]
        self.assertTrue(fl["cumple"])
        self.assertEqual(fl["holgura_dias_habiles"], 3)     # 12 - 9
        self.assertEqual(fl["deficit_dias_habiles"], 0)
        self.assertIsNone(fl["alerta"])

    def test_limite_exacto(self):
        r = ccpm.calcular_ccpm(lineal(fecha_limite_contractual="2026-10-15"))
        self.assertTrue(r["fecha_limite"]["cumple"])
        self.assertEqual(r["fecha_limite"]["holgura_dias_habiles"], 0)

    def test_sin_limite(self):
        self.assertIsNone(ccpm.calcular_ccpm(lineal())["fecha_limite"])


class TestHitos(unittest.TestCase):
    def test_hitos(self):
        r = ccpm.calcular_ccpm(lineal(hitos=[
            {"nombre": "H1", "fecha": "2026-10-07", "tarea": "T1"},
            {"nombre": "H2", "fecha": "2026-10-06", "tarea": "T2"},
            {"nombre": "H3", "fecha": "2026-10-15", "tarea": "T3"}]))
        h = {x["nombre"]: x for x in r["hitos"]}
        self.assertEqual((h["H1"]["holgura_dias_habiles"], h["H1"]["estado"]), (1, "CUMPLE"))
        self.assertEqual((h["H2"]["holgura_dias_habiles"], h["H2"]["estado"]), (-3, "NO CUMPLE"))
        self.assertEqual((h["H3"]["holgura_dias_habiles"], h["H3"]["estado"]), (0, "CUMPLE"))
        self.assertIn("fin de proyecto", h["H3"]["comparado_con"])

    def test_hito_con_tarea_inexistente(self):
        with self.assertRaisesRegex(ValueError, "inexistente"):
            ccpm.calcular_ccpm(lineal(hitos=[{"nombre": "H", "fecha": "2026-10-07", "tarea": "ZZ"}]))


class TestErrores(unittest.TestCase):
    def test_ciclo(self):
        d = proyecto([tarea("A", 2, 1, ["C"]), tarea("B", 2, 1, ["A"]), tarea("C", 2, 1, ["B"])])
        with self.assertRaisesRegex(ValueError, r"Ciclo en la red de precedencias: .*->"):
            ccpm.calcular_ccpm(d)

    def test_ciclo_con_cola_no_cíclica(self):
        d = proyecto([tarea("X", 2, 1), tarea("A", 2, 1, ["X", "B"]), tarea("B", 2, 1, ["A"])])
        with self.assertRaises(ValueError) as cm:
            ccpm.calcular_ccpm(d)
        msg = str(cm.exception)
        self.assertTrue("A -> B -> A" in msg or "B -> A -> B" in msg, msg)
        self.assertNotIn("X", msg.split(":", 1)[1])   # la tarea X no forma parte del ciclo

    def test_autoreferencia(self):
        with self.assertRaisesRegex(ValueError, "Ciclo"):
            ccpm.calcular_ccpm(proyecto([tarea("A", 2, 1, ["A"])]))

    def test_predecesor_inexistente(self):
        with self.assertRaisesRegex(ValueError, r"predecesor inexistente: 'Q'"):
            ccpm.calcular_ccpm(proyecto([tarea("A", 2, 1, ["Q"])]))

    def test_id_duplicado(self):
        with self.assertRaisesRegex(ValueError, "duplicado"):
            ccpm.calcular_ccpm(proyecto([tarea("A", 2), tarea("A", 3)]))

    def test_datos_invalidos(self):
        casos = [
            (proyecto([tarea("A", 0)]), ">= 1"),
            (proyecto([tarea("A", 2.5)]), "entero"),
            (proyecto([tarea("A", 2, 3)]), "no puede superar"),
            (proyecto([tarea("A", 2, tipo_recurso="raro")]), "tipo_recurso"),
            (proyecto([tarea("A", 2)], inicio="05/10/2026"), "inicio"),
            (proyecto([tarea("A", 2)], metodo_buffer="xx"), "metodo_buffer"),
            (proyecto([tarea("A", 2)], feriados=["no-fecha"]), "feriados"),
            (proyecto([tarea("A", 2)], dias_laborables=[9]), "rango"),
            ({"tareas": [tarea("A", 2)]}, "inicio"),
            ({"inicio": "2026-10-05", "tareas": []}, "tareas"),
        ]
        for datos, patron in casos:
            with self.subTest(patron=patron):
                with self.assertRaisesRegex(ValueError, patron):
                    ccpm.calcular_ccpm(datos)


class TestSemaforo(unittest.TestCase):
    def test_zonas_por_defecto(self):
        self.assertEqual(ccpm.estado_buffer(0.5, 0.2), "VERDE")      # <= 0,265
        self.assertEqual(ccpm.estado_buffer(0.5, 0.5), "AMARILLO")   # 0,265 < c < 0,665
        self.assertEqual(ccpm.estado_buffer(0.5, 0.7), "ROJO")       # >= 0,665
        self.assertEqual(ccpm.estado_buffer(0.0, 0.10), "VERDE")     # borde verde
        self.assertEqual(ccpm.estado_buffer(0.0, 0.33), "ROJO")      # borde rojo
        self.assertEqual(ccpm.estado_buffer(1.0, 1.0), "ROJO")
        self.assertEqual(ccpm.estado_buffer(1.0, 0.43), "VERDE")     # 0,33 + 0,10
        self.assertEqual(ccpm.estado_buffer(0.0, 0.2), "AMARILLO")

    def test_parametros_configurables(self):
        p = {"verde_pendiente": 0.2, "verde_ordenada": 0.0, "rojo_pendiente": 0.5, "rojo_ordenada": 0.2}
        self.assertEqual(ccpm.estado_buffer(0.5, 0.2, p), "AMARILLO")  # verde 0,1; rojo 0,45
        self.assertEqual(ccpm.estado_buffer(0.5, 0.1, p), "VERDE")
        self.assertEqual(ccpm.estado_buffer(0.5, 0.45, p), "ROJO")

    def test_validaciones(self):
        for a, c in ((-0.1, 0.2), (0.5, 1.1), ("x", 0.1)):
            with self.assertRaises(ValueError):
                ccpm.estado_buffer(a, c)
        with self.assertRaises(ValueError):
            ccpm.estado_buffer(0.5, 0.5, {"inventado": 1})
        with self.assertRaises(ValueError):   # verde por encima de rojo
            ccpm.estado_buffer(0.5, 0.5, {"verde_ordenada": 0.5})


class TestSalidas(unittest.TestCase):
    def test_json_serializable_y_markdown(self):
        r = ccpm.calcular_ccpm(lineal(fecha_limite_contractual="2026-10-13"))
        json.dumps(r, ensure_ascii=False)
        md = ccpm.generar_markdown(r)
        for titulo in ("## Cronograma por tarea", "## Cadena crítica", "## Buffers", "## Hitos",
                       "## Comparación con la fecha límite contractual", "## Advertencias",
                       "## Gestión de buffers"):
            self.assertIn(titulo, md)
        self.assertIn("ALERTA", md)
        self.assertIn("a validar", md)

    def test_ejemplo_incluido(self):
        r = ccpm.calcular_desde_archivo(os.path.join(AQUI, "example_ccpm.json"))
        self.assertEqual([e["id"] for e in r["cadena_critica"]["eslabones"]], ["T2", "T3", "T5", "T7", "T8"])
        self.assertEqual(r["resumen"]["dias_habiles_hasta_fin_cadena"], 27)
        self.assertEqual(r["resumen"]["buffer_proyecto_dias"], 12)         # ceil(0,5 x 24); agresivas con recorte del 30 %
        self.assertEqual(r["resumen"]["fin_proyecto"], "2026-11-30")
        self.assertEqual([b["tamano_dias"] for b in r["buffers"]["alimentacion"]], [3, 2, 3])
        self.assertTrue(r["fecha_limite"]["cumple"])

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            ent = os.path.join(tmp, "e.json")
            md = os.path.join(tmp, "s.md")
            js = os.path.join(tmp, "s.json")
            with open(ent, "w", encoding="utf-8") as f:
                json.dump(lineal(), f)
            cp = subprocess.run([sys.executable, "-B", "-m", "epc_documents.ccpm", ent,
                                 "--md", md, "--json", js], capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            with open(js, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["resumen"]["dias_habiles_hasta_fin_proyecto"], 9)
            with open(md, encoding="utf-8") as f:
                self.assertIn("# Cronograma por Cadena Crítica", f.read())
            # entrada con ciclo -> código 2 y mensaje en español
            mal = os.path.join(tmp, "mal.json")
            with open(mal, "w", encoding="utf-8") as f:
                json.dump(proyecto([tarea("A", 2, 1, ["B"]), tarea("B", 2, 1, ["A"])]), f)
            cp = subprocess.run([sys.executable, "-B", "-m", "epc_documents.ccpm", mal],
                                capture_output=True, text=True)
            self.assertEqual(cp.returncode, 2)
            self.assertIn("Ciclo", cp.stderr)


class TestEstadosYReplanificacion(unittest.TestCase):
    """H-033 / H-040. Base: cadena lineal T1(4,2) -> T2(6,3) -> T3(2,1), un recurso."""

    def test_hecha_con_fin_real_no_se_reprograma(self):
        # T1 hecha, fin_real vie 2026-10-06 (día hábil 2). T2 arranca el día 3 (mié 7/10):
        # T2 = 7, 8, 9/10 ; T3 = lun 12/10 (el 10 y 11 son fin de semana). Fin de cadena 12/10.
        d = lineal()
        d["tareas"][0].update(inicio_real="2026-10-05", fin_real="2026-10-06")
        r = ccpm.calcular_ccpm(d)
        self.assertNotIn("T1", por_id(r))
        t = por_id(r)
        self.assertEqual((t["T2"]["inicio"], t["T2"]["fin"]), ("2026-10-07", "2026-10-09"))
        self.assertEqual(t["T3"]["inicio"], "2026-10-12")
        self.assertEqual(r["resumen"]["fin_cadena"], "2026-10-12")
        # buffer = ceil(0,5 x (3 + 1)) = 2 -> fin de proyecto martes 14/10
        self.assertEqual(r["resumen"]["buffer_proyecto_dias"], 2)
        self.assertEqual(r["resumen"]["fin_proyecto"], "2026-10-14")
        self.assertEqual(r["resumen"]["tareas_hechas"], ["T1"])
        self.assertEqual(r["tareas_fuera_de_calculo"][0]["fin_real"], "2026-10-06")

    def test_estado_hecha_sin_fechas(self):
        d = lineal()
        d["tareas"][0]["estado"] = "hecha"
        r = ccpm.calcular_ccpm(d)
        self.assertEqual(por_id(r)["T2"]["inicio"], "2026-10-05")

    def test_desde_replanifica_desde_hoy(self):
        # T1 hecha; desde lun 19/10: T2 = 19, 20, 21/10 ; T3 = 22/10 ; buffer 2 -> 23 y 26/10.
        d = lineal()
        d["tareas"][0].update(inicio_real="2026-10-05", fin_real="2026-10-08")
        r = ccpm.calcular_ccpm(d, desde="2026-10-19")
        t = por_id(r)
        self.assertEqual(t["T2"]["inicio"], "2026-10-19")
        self.assertEqual(t["T3"]["inicio"], "2026-10-22")
        self.assertEqual(r["resumen"]["fin_cadena"], "2026-10-22")
        self.assertEqual(r["resumen"]["fin_proyecto"], "2026-10-26")
        self.assertEqual(r["resumen"]["desde"], "2026-10-19")

    def test_desde_sin_tareas_hechas_equivale_a_nuevo_inicio(self):
        r1 = ccpm.calcular_ccpm(lineal(), desde="2026-10-19")
        r2 = ccpm.calcular_ccpm(proyecto(lineal()["tareas"], inicio="2026-10-19"))
        self.assertEqual(r1["resumen"]["fin_proyecto"], r2["resumen"]["fin_proyecto"])

    def test_excluida_no_entra_en_la_cadena(self):
        d = proyecto([tarea("A", 4, 2), tarea("B", 6, 3, ["A"]), tarea("C", 20, 10, ["A"], recurso="Q")])
        d["tareas"][2]["estado"] = "excluida"
        r = ccpm.calcular_ccpm(d)
        self.assertEqual([e["id"] for e in r["cadena_critica"]["eslabones"]], ["A", "B"])
        self.assertNotIn("C", por_id(r))
        self.assertEqual(r["resumen"]["tareas_excluidas"], ["C"])
        # sin excluir, la cadena pasaría por C
        d["tareas"][2]["estado"] = "pendiente"
        self.assertEqual([e["id"] for e in ccpm.calcular_ccpm(d)["cadena_critica"]["eslabones"]], ["A", "C"])

    def test_dependencia_hacia_excluida_se_ignora_con_aviso(self):
        d = proyecto([tarea("A", 2, 1), tarea("B", 2, 1, ["A"])])
        d["tareas"][0]["estado"] = "excluida"
        r = ccpm.calcular_ccpm(d)
        self.assertEqual(por_id(r)["B"]["inicio"], "2026-10-05")
        self.assertTrue(any("excluida" in a for a in r["advertencias"]))

    def test_bloqueada_se_informa_y_no_es_cumplible(self):
        d = lineal(fecha_limite_contractual="2026-12-31",
                   hitos=[{"nombre": "Fin", "fecha": "2026-12-31", "tarea": "T3"}])
        d["tareas"][1]["estado"] = "bloqueada"
        r = ccpm.calcular_ccpm(d)
        t = por_id(r)
        self.assertEqual(t["T1"]["cumplible"], True)
        self.assertEqual((t["T2"]["cumplible"], t["T3"]["cumplible"]), (False, False))
        self.assertEqual(r["resumen"]["tareas_bloqueadas"], ["T2"])
        self.assertEqual(r["resumen"]["tareas_afectadas_por_bloqueo"], ["T2", "T3"])
        self.assertFalse(r["resumen"]["fin_proyecto_cumplible"])
        self.assertFalse(r["fecha_limite"]["cumple"])
        self.assertTrue(r["fecha_limite"]["cumple_por_fechas"])
        self.assertEqual(r["hitos"][0]["estado"], "NO CUMPLIBLE (bloqueo)")
        self.assertTrue(any("BLOQUEADAS" in a for a in r["advertencias"]))
        self.assertIn("NO CUMPLIBLE", ccpm.generar_markdown(r))

    def test_sin_bloqueos_todo_cumplible(self):
        r = ccpm.calcular_ccpm(lineal(fecha_limite_contractual="2026-12-31"))
        self.assertTrue(r["resumen"]["fin_proyecto_cumplible"])
        self.assertTrue(r["fecha_limite"]["cumple"])

    def test_lote_excluye_tareas_de_otro_lote(self):
        d = proyecto([tarea("A", 2, 1, lote="L1"), tarea("B", 2, 1, ["A"], lote="L1"),
                      tarea("C", 8, 4, ["A"], lote="L2", recurso="Q"), tarea("D", 2, 1, ["B"])])
        r = ccpm.calcular_ccpm(d, lote="L1")
        self.assertEqual(r["resumen"]["tareas_excluidas"], ["C"])
        self.assertEqual(r["resumen"]["lote"], "L1")
        self.assertEqual([e["id"] for e in r["cadena_critica"]["eslabones"]], ["A", "B", "D"])
        r2 = ccpm.calcular_ccpm(d, lote="L2")
        self.assertEqual(r2["resumen"]["tareas_excluidas"], ["A", "B"])

    def test_errores_de_estado(self):
        d = lineal()
        d["tareas"][0]["estado"] = "volando"
        with self.assertRaises(ValueError):
            ccpm.calcular_ccpm(d)
        d = lineal()
        d["tareas"][0].update(estado="pendiente", fin_real="2026-10-06")
        with self.assertRaises(ValueError):
            ccpm.calcular_ccpm(d)
        d = lineal()
        d["tareas"][0].update(inicio_real="2026-10-07", fin_real="2026-10-06")
        with self.assertRaises(ValueError):
            ccpm.calcular_ccpm(d)
        d = lineal()
        for t in d["tareas"]:
            t["estado"] = "hecha"
        with self.assertRaises(ValueError):
            ccpm.calcular_ccpm(d)


class TestAvanceYConsumo(unittest.TestCase):
    """H-039 / H-055 / H-056. Valores a mano."""

    def test_avance_entregable(self):
        # generado 0,40 + revisado 0,20 = 0,60
        self.assertAlmostEqual(ccpm.avance_entregable(["generado", "revisado"]), 0.6)
        self.assertEqual(ccpm.avance_entregable([]), 0.0)
        self.assertAlmostEqual(ccpm.avance_entregable(["generado", "revisado", "auditado", "emitido"]), 1.0)
        with self.assertRaises(ValueError):
            ccpm.avance_entregable(["inventado"])

    def test_avance_global_promedio_de_aplicables(self):
        ents = [{"id": "E1", "hitos": ["generado", "revisado", "auditado", "emitido"]},   # 1,0
                {"id": "E2", "hitos": ["generado"]},                                      # 0,4
                {"id": "E3", "hitos": []},                                                # 0
                {"id": "E4", "hitos": [], "aplica": False}]                               # no cuenta
        # (1,0 + 0,4 + 0) / 3 = 0,4667
        self.assertAlmostEqual(ccpm.avance_global(ents), 1.4 / 3, places=6)
        with self.assertRaises(ValueError):
            ccpm.avance_global([{"id": "E", "hitos": [], "aplica": False}])

    def test_avance_global_con_pesos_por_entregable(self):
        # E1 = 1,0 con peso 3 ; E2 = 0,4 con peso 1 -> (3·1,0 + 1·0,4)/4 = 0,85
        ents = [{"id": "E1", "hitos": ["generado", "revisado", "auditado", "emitido"], "peso": 3},
                {"id": "E2", "hitos": ["generado"]}]
        self.assertAlmostEqual(ccpm.avance_global(ents), 0.85)
        with self.assertRaises(ValueError):
            ccpm.avance_global([{"id": "E", "hitos": [], "peso": 0}])

    def test_pesos_propios_deben_sumar_uno(self):
        self.assertAlmostEqual(ccpm.avance_entregable(["generado"], {"generado": 0.5, "emitido": 0.5}), 0.5)
        with self.assertRaises(ValueError):
            ccpm.avance_entregable(["generado"], {"generado": 0.5, "emitido": 0.4})

    def test_consumo_de_buffer_y_zona(self):
        # retraso 2 d / buffer 8 d = 25 %; con avance 0,5 VERDE si consumo <= 0,33·0,5+0,10 = 0,265
        c = ccpm.consumo_buffer(2, 8, True, 0.5)
        self.assertAlmostEqual(c["consumo"], 0.25)
        self.assertEqual(c["zona"], "VERDE")
        # retraso 4 / 8 = 50 %: entre 0,265 y 0,67 -> AMARILLO
        self.assertEqual(ccpm.consumo_buffer(4, 8, True, 0.5)["zona"], "AMARILLO")
        # retraso 6 / 8 = 75 % >= 0,67 -> ROJO
        self.assertEqual(ccpm.consumo_buffer(6, 8, True, 0.5)["zona"], "ROJO")
        # consumo >= 100 % -> ROJO aunque el avance sea alto
        self.assertEqual(ccpm.consumo_buffer(9, 8, True, 1.0)["zona"], "ROJO")
        # sin retraso -> 0 % VERDE
        self.assertEqual(ccpm.consumo_buffer(-3, 8, True, 0.2)["consumo"], 0.0)

    def test_consumo_sin_avance_usa_tercios(self):
        self.assertEqual(ccpm.consumo_buffer(2, 6)["zona"], "VERDE")      # 33,3 %
        self.assertEqual(ccpm.consumo_buffer(3, 6)["zona"], "AMARILLO")   # 50 %
        self.assertEqual(ccpm.consumo_buffer(4, 6)["zona"], "ROJO")       # 66,7 %

    def test_buffer_cero_o_cadena_que_no_cabe(self):
        c = ccpm.consumo_buffer(3, 0, True, 0.5)
        self.assertIsNone(c["consumo"])
        self.assertEqual(c["zona"], "ROJO")
        self.assertIn("retraso proyectado 3 día(s) hábil(es) frente al límite", c["texto"])
        self.assertEqual(ccpm.consumo_buffer(1, 5, False)["zona"], "ROJO")
        self.assertEqual(ccpm.consumo_buffer(0, 0, True)["zona"], "VERDE")
        with self.assertRaises(ValueError):
            ccpm.consumo_buffer(1, -1)

    def test_seguimiento_en_replanificacion(self):
        # Base: cadena T1-T2-T3 (agresivas 2+3+1 = 6), fin de cadena lun 12/10, buffer 3.
        # T1 hecha (fin 06/10). Replanificado: T2 = 7-9/10, T3 = 12/10 -> sin retraso.
        d = lineal(base={"fin_cadena": "2026-10-12", "buffer_proyecto_dias": 3,
                         "cadena": ["T1", "T2", "T3"]})
        d["tareas"][0].update(inicio_real="2026-10-05", fin_real="2026-10-06")
        sg = ccpm.calcular_ccpm(d)["seguimiento"]
        self.assertAlmostEqual(sg["avance_cadena"], 2 / 6, places=4)   # T1 (2) de 6
        self.assertEqual(sg["retraso_proyectado_dias_habiles"], 0)
        self.assertEqual(sg["consumo"]["zona"], "VERDE")
        # Si T2 no puede empezar antes del 14/10 (info tardía): T2 = 14-16, T3 = 19 -> retraso 5 d
        d["tareas"][1]["fecha_no_antes_de"] = "2026-10-14"
        sg = ccpm.calcular_ccpm(d)["seguimiento"]
        self.assertEqual(sg["retraso_proyectado_dias_habiles"], 5)
        self.assertEqual(sg["consumo"]["zona"], "ROJO")                 # 5/3 >= 100 %


class TestMdSecciones(unittest.TestCase):
    def test_tablas_b_y_c_con_columnas_de_schedule(self):
        d = lineal(fecha_limite_contractual="2026-10-09")
        d["tareas"][0]["entregable"] = "ENT-001"
        md = ccpm.generar_md_secciones(ccpm.calcular_ccpm(d))
        self.assertIn("| ID | Entregable / actividad | Recurso | Dur. segura | Dur. agresiva | Predecesores | Estado |", md)
        self.assertIn("| T1 | ENT-001 - Tarea T1 | R | 4 | 2 | - | pendiente |", md)
        self.assertIn("| Concepto | Valor |", md)
        for fila in ("Fin de la cadena crítica", "Buffer de proyecto (días)",
                     "Fecha de fin del proyecto (con buffer)",
                     "Margen o déficit frente al límite contractual (días)",
                     "Cadena crítica (tareas)", "Buffers de alimentación"):
            self.assertIn("| " + fila + " |", md)
        # fin de proyecto jueves 15/10 vs límite vie 9/10 -> déficit de 4 días hábiles
        self.assertIn("DÉFICIT de 4", md)
        self.assertIn("T1 > T2 > T3", md)

    def test_cli_md_secciones_desde_y_lote(self):
        with tempfile.TemporaryDirectory() as tmp:
            ent = os.path.join(tmp, "e.json")
            d = lineal()
            d["tareas"][0].update(fin_real="2026-10-06")
            with open(ent, "w", encoding="utf-8") as f:
                json.dump(d, f)
            sec = os.path.join(tmp, "sec.md")
            cp = subprocess.run([sys.executable, "-B", "-m", "epc_documents.ccpm", ent,
                                 "--md-secciones", sec, "--desde", "2026-10-19", "--lote", "X"],
                                capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            with open(sec, encoding="utf-8") as f:
                txt = f.read()
            self.assertIn("| T1 | Tarea T1 | R | 4 | 2 | - | hecha |", txt)
            self.assertIn("2026-10-26", txt)
            cp = subprocess.run([sys.executable, "-B", "-m", "epc_documents.ccpm", ent, "--md-secciones"],
                                capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertIn("## C. Resultado del cálculo", cp.stdout)
            cp = subprocess.run([sys.executable, "-B", "-m", "epc_documents.ccpm", ent, "--desde", "no-fecha"],
                                capture_output=True, text=True)
            self.assertEqual(cp.returncode, 2)


def tp(id_, seg, pq, fase, preds=(), recurso=None, agr=None, **kw):
    """Tarea de un paquete: Claude elabora/procesa; el usuario revisa (recurso distinto)."""
    if recurso is None:
        recurso = "Usuario" if fase == "revisar" else "Claude"
    return tarea(id_, seg, agr, preds, recurso, paquete=pq, fase_paquete=fase, **kw)


def dos_paquetes():
    """PQ-01 y PQ-02 en secuencia; la revisión del usuario es un recurso distinto de Claude.

    Calendario: lunes 2026-10-05, lunes a viernes. Agresivas = ceil(segura / 2):
    T1 elaborar PQ-01 (4 -> 2): días 1-2 (lun 5, mar 6)
    T2 revisar PQ-01  (2 -> 1): día 3 (mié 7)
    T3 elaborar PQ-02 (6 -> 3): días 4-6 (jue 8, vie 9, lun 12)
    T4 revisar PQ-02  (4 -> 2): días 7-8 (mar 13, mié 14)
    """
    return proyecto([tp("T1", 4, "PQ-01", "elaborar"), tp("T2", 2, "PQ-01", "revisar", ["T1"]),
                     tp("T3", 6, "PQ-02", "elaborar", ["T2"]), tp("T4", 4, "PQ-02", "revisar", ["T3"])])


class TestPaquetes(unittest.TestCase):
    def test_plan_de_paquetes_orden_y_fechas_a_mano(self):
        res = ccpm.calcular_ccpm(dos_paquetes())
        pl = res["plan_paquetes"]
        q1, q2 = pl["paquetes"]
        self.assertEqual([q1["id"], q2["id"]], ["PQ-01", "PQ-02"])
        self.assertEqual([q1["orden"], q2["orden"]], [1, 2])
        self.assertEqual(q1["depende_de"], [])
        self.assertEqual(q2["depende_de"], ["PQ-01"])
        self.assertEqual((q1["inicio"], q1["entrega_al_usuario"]), ("2026-10-05", "2026-10-06"))
        self.assertEqual((q1["inicio_revision"], q1["fin_revision"]), ("2026-10-07", "2026-10-07"))
        self.assertEqual((q2["inicio"], q2["entrega_al_usuario"]), ("2026-10-08", "2026-10-12"))
        self.assertEqual((q2["inicio_revision"], q2["fin_revision"]), ("2026-10-13", "2026-10-14"))
        self.assertEqual((q1["dias_revision_usuario"], q2["dias_revision_usuario"]), (1, 2))
        self.assertEqual((q1["dias_elaboracion"], q2["dias_elaboracion"]), (2, 3))
        self.assertEqual(q2["tareas"], ["T3", "T4"])
        self.assertEqual(q1["estado"], "pendiente")
        self.assertEqual(res["resumen"]["cantidad_paquetes"], 2)
        self.assertEqual(por_id(res)["T3"]["paquete"], "PQ-02")
        self.assertEqual(por_id(res)["T3"]["fase_paquete"], "elaborar")
        self.assertEqual(res["advertencias"], [])

    def test_la_cadena_critica_pasa_por_la_revision_del_usuario(self):
        res = ccpm.calcular_ccpm(dos_paquetes())
        self.assertEqual([e["id"] for e in res["cadena_critica"]["eslabones"]], ["T1", "T2", "T3", "T4"])
        cb = res["plan_paquetes"]["cuello_de_botella"]
        # revisión: T2 (1 d) + T4 (2 d) = 3 de 8 días agresivos de la cadena
        self.assertEqual((cb["tareas_cadena"], cb["tareas_revision_en_cadena"]), (4, 2))
        self.assertEqual((cb["dias_cadena"], cb["dias_revision_en_cadena"]), (8, 3))
        self.assertAlmostEqual(cb["porcentaje_revision_en_cadena"], 0.375)
        self.assertEqual(res["plan_paquetes"]["paquetes"][1]["tareas_en_cadena_critica"], ["T3", "T4"])

    def test_cuello_de_botella_se_advierte_si_la_revision_domina(self):
        d = proyecto([tp("T1", 2, "PQ-01", "elaborar"), tp("T2", 10, "PQ-01", "revisar", ["T1"])])
        res = ccpm.calcular_ccpm(d)      # agresivas 1 y 5: la revisión es 5 de 6 días
        self.assertTrue(any("Cuello de botella" in a for a in res["advertencias"]))
        self.assertAlmostEqual(res["plan_paquetes"]["cuello_de_botella"]["porcentaje_revision_en_cadena"], 5 / 6, places=4)

    def test_orden_topologico_no_depende_del_orden_de_declaracion(self):
        d = dos_paquetes()
        d["tareas"] = d["tareas"][2:] + d["tareas"][:2]       # PQ-02 declarado antes que PQ-01
        res = ccpm.calcular_ccpm(d)
        self.assertEqual([q["id"] for q in res["plan_paquetes"]["paquetes"]], ["PQ-01", "PQ-02"])

    def test_paquetes_independientes_dependen_de_nada_y_ordenan_por_inicio(self):
        d = proyecto([tp("T1", 2, "PQ-A", "elaborar"), tp("T2", 2, "PQ-A", "revisar", ["T1"]),
                      tp("T3", 2, "PQ-B", "elaborar", recurso="Otro"),
                      tp("T4", 2, "PQ-B", "revisar", ["T3"], recurso="Otro2")])
        res = ccpm.calcular_ccpm(d)
        qs = res["plan_paquetes"]["paquetes"]
        self.assertEqual([q["depende_de"] for q in qs], [[], []])
        self.assertEqual({q["id"] for q in qs}, {"PQ-A", "PQ-B"})

    def test_sin_paquetes_no_cambia_la_salida(self):
        res = ccpm.calcular_ccpm(lineal())
        self.assertIsNone(res["plan_paquetes"])
        self.assertEqual(res["resumen"]["cantidad_paquetes"], 0)
        self.assertNotIn("Plan de paquetes", ccpm.generar_markdown(res))
        self.assertNotIn("B2. Plan de paquetes", ccpm.generar_md_secciones(res))
        self.assertIsNone(por_id(res)["T1"]["paquete"])

    def test_tareas_hechas_dan_paquete_hecho_con_fechas_reales(self):
        d = dos_paquetes()
        d["tareas"][0].update(inicio_real="2026-10-05", fin_real="2026-10-06")
        d["tareas"][1].update(inicio_real="2026-10-07", fin_real="2026-10-08")
        res = ccpm.calcular_ccpm(d, desde="2026-10-09")
        q1, q2 = res["plan_paquetes"]["paquetes"]
        self.assertEqual(q1["estado"], "hecho")
        self.assertEqual((q1["inicio"], q1["fin"], q1["fin_revision"]), ("2026-10-05", "2026-10-08", "2026-10-08"))
        self.assertEqual(q2["estado"], "pendiente")
        # PQ-02 arranca el día siguiente al fin real de la revisión de PQ-01, no antes de 'desde'
        self.assertEqual(q2["inicio"], "2026-10-09")

    def test_tareas_bloqueadas_marcan_el_paquete_y_el_siguiente(self):
        d = dos_paquetes()
        d["tareas"][0]["estado"] = "bloqueada"
        res = ccpm.calcular_ccpm(d)
        self.assertEqual([q["estado"] for q in res["plan_paquetes"]["paquetes"]], ["bloqueado", "bloqueado"])

    def test_tareas_excluidas_no_forman_parte_del_plan(self):
        d = dos_paquetes()
        d["tareas"].append(tp("T5", 2, "PQ-09", "elaborar", estado="excluida", recurso="Z"))
        res = ccpm.calcular_ccpm(d)
        self.assertEqual([q["id"] for q in res["plan_paquetes"]["paquetes"]], ["PQ-01", "PQ-02"])

    def test_avisa_si_un_paquete_depende_de_una_tarea_que_no_es_la_revision(self):
        d = dos_paquetes()
        d["tareas"][2]["predecesores"] = ["T1"]          # PQ-02 depende de la elaboración de PQ-01
        res = ccpm.calcular_ccpm(d)
        self.assertTrue(any("T3" in a and "T1" in a and "REVISADO" in a for a in res["advertencias"]), res["advertencias"])

    def test_no_avisa_si_depende_de_la_revision_o_del_procesamiento(self):
        d = dos_paquetes()
        d["tareas"].insert(2, tp("T2b", 1, "PQ-01", "procesar", ["T2"]))
        d["tareas"][3]["predecesores"] = ["T2b"]
        res = ccpm.calcular_ccpm(d)
        self.assertEqual([a for a in res["advertencias"] if "REVISADO" in a], [])

    def test_avisa_paquete_sin_tarea_de_revision(self):
        d = proyecto([tp("T1", 2, "PQ-01", "elaborar"), tp("T2", 2, "PQ-02", "elaborar", ["T1"], recurso="C2")])
        d["tareas"][0]["fase_paquete"] = "elaborar"
        res = ccpm.calcular_ccpm(d)
        self.assertTrue(any("'PQ-01'" in a and "revisar" in a for a in res["advertencias"]))

    def test_avisa_si_revision_y_elaboracion_comparten_recurso(self):
        d = dos_paquetes()
        d["tareas"][1]["recurso"] = "Claude"
        res = ccpm.calcular_ccpm(d)
        self.assertTrue(any("comparten el recurso" in a and "'PQ-01'" in a for a in res["advertencias"]))

    def test_avisa_dependencias_circulares_entre_paquetes(self):
        d = proyecto([tp("A1", 2, "PQ-A", "elaborar", recurso="R1"),
                      tp("B1", 2, "PQ-B", "elaborar", ["A1"], recurso="R2"),
                      tp("B2", 2, "PQ-B", "revisar", ["B1"], recurso="R3"),
                      tp("A2", 2, "PQ-A", "revisar", ["B2"], recurso="R4")])
        res = ccpm.calcular_ccpm(d)
        self.assertTrue(any("circulares" in a for a in res["advertencias"]))
        self.assertEqual({q["id"] for q in res["plan_paquetes"]["paquetes"]}, {"PQ-A", "PQ-B"})

    def test_errores_de_campos_de_paquete(self):
        d = dos_paquetes()
        d["tareas"][0]["fase_paquete"] = "revisión final"
        with self.assertRaisesRegex(ValueError, "fase_paquete"):
            ccpm.calcular_ccpm(d)
        d = proyecto([tarea("T1", 2, fase_paquete="revisar")])
        with self.assertRaisesRegex(ValueError, "requiere 'paquete'"):
            ccpm.calcular_ccpm(d)

    def test_la_fase_admite_acentos_y_mayusculas(self):
        d = dos_paquetes()
        d["tareas"][1]["fase_paquete"] = "REVISAR"
        self.assertEqual(ccpm.calcular_ccpm(d)["plan_paquetes"]["paquetes"][0]["dias_revision_usuario"], 1)

    def test_los_paquetes_no_alteran_el_calculo_de_la_cadena_ni_los_buffers(self):
        con = dos_paquetes()
        sin = json.loads(json.dumps(con))
        for t in sin["tareas"]:
            t.pop("paquete")
            t.pop("fase_paquete")
        a, b = ccpm.calcular_ccpm(con), ccpm.calcular_ccpm(sin)
        self.assertEqual(a["resumen"]["fin_proyecto"], b["resumen"]["fin_proyecto"])
        self.assertEqual(a["buffers"]["proyecto"]["tamano_dias"], b["buffers"]["proyecto"]["tamano_dias"])
        self.assertEqual([e["id"] for e in a["cadena_critica"]["eslabones"]],
                         [e["id"] for e in b["cadena_critica"]["eslabones"]])

    def test_markdown_y_secciones_incluyen_el_plan(self):
        res = ccpm.calcular_ccpm(dos_paquetes())
        md = ccpm.generar_markdown(res)
        self.assertIn("## Plan de paquetes", md)
        self.assertIn("| 2 | PQ-02 | T3, T4 | PQ-01 | 2026-10-08 jue | 2026-10-12 lun | "
                      "2026-10-13 mar a 2026-10-14 mié | 2026-10-14 mié | 2 | pendiente |", md)
        sec = ccpm.generar_md_secciones(res)
        self.assertIn("## B2. Plan de paquetes", sec)
        self.assertIn("| ID | Entregable / actividad | Recurso | Dur. segura | Dur. agresiva | Predecesores | Estado |", sec)
        json.dumps(res)             # serializable

    def test_ejemplo_de_paquetes_incluido(self):
        res = ccpm.calcular_desde_archivo(os.path.join(AQUI, "example_ccpm_packages.json"))
        ids = [q["id"] for q in res["plan_paquetes"]["paquetes"]]
        self.assertEqual(ids, ["EJ-PQ-01", "EJ-PQ-02", "EJ-PQ-03", "EJ-PQ-10"])
        # el pliego (EJ-PQ-10) depende del dimensionamiento de cables (EJ-PQ-03)
        self.assertEqual(res["plan_paquetes"]["paquetes"][3]["depende_de"], ["EJ-PQ-03"])
        self.assertEqual([a for a in res["advertencias"] if "REVISADO" in a], [])

    def test_cli_md_secciones_y_json_con_paquetes(self):
        with tempfile.TemporaryDirectory() as tmp:
            ent = os.path.join(tmp, "e.json")
            with open(ent, "w", encoding="utf-8") as f:
                json.dump(dos_paquetes(), f)
            sal = os.path.join(tmp, "s.json")
            cp = subprocess.run([sys.executable, "-B", "-m", "epc_documents.ccpm", ent,
                                 "--md-secciones", "--json", sal], capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertIn("## B2. Plan de paquetes", cp.stdout)
            with open(sal, encoding="utf-8") as f:
                self.assertEqual(len(json.load(f)["plan_paquetes"]["paquetes"]), 2)


class TestHorasYPlazo(unittest.TestCase):
    """Duraciones en horas, horas por día y plazo en horas (transcurrido o de esfuerzo)."""

    def _tareas_por_id(self, res):
        return {t["id"]: t for t in res["tareas"]}

    def test_duraciones_en_horas_se_convierten_a_dias(self):
        # 20 h / 8 h por día = 2,5 -> 3 días; 12 h / 8 = 1,5 -> 2 días
        t = {"id": "T1", "recurso": "R", "dur_segura_h": 20, "dur_agresiva_h": 12}
        res = ccpm.calcular_ccpm(proyecto([t]))
        info = res["tareas_entrada"][0] if "tareas_entrada" in res else None
        out = self._tareas_por_id(res)["T1"]
        self.assertEqual(out["dur_agresiva"], 2)
        if info:
            self.assertEqual(info["dur_segura"], 3)

    def test_horas_por_dia_distinto_de_8(self):
        # 20 h con 6 h por día = 3,33 -> 4 días
        t = {"id": "T1", "recurso": "R", "dur_segura_h": 20}
        res = ccpm.calcular_ccpm(proyecto([t], horas_por_dia=6))
        # agresiva por defecto = ceil(70 % de 4) = 3
        self.assertEqual(self._tareas_por_id(res)["T1"]["dur_agresiva"], 3)

    def test_plazo_horas_transcurrido_deriva_la_fecha_limite(self):
        # 120 h / 8 = 15 días hábiles desde lun 2026-10-05 -> viernes 2026-10-23
        res = ccpm.calcular_ccpm(proyecto([tarea("T1", 4)], plazo_horas=120))
        self.assertEqual(res["fecha_limite"]["fecha_limite"], "2026-10-23")
        self.assertEqual(res["plazo_horas"]["dias_habiles_equivalentes"], 15)
        self.assertTrue(any("derivada de plazo_horas" in a for a in res["advertencias"]))

    def test_fecha_explicita_prevalece_sobre_plazo_horas(self):
        res = ccpm.calcular_ccpm(proyecto([tarea("T1", 4)], plazo_horas=120,
                                          fecha_limite_contractual="2026-10-30"))
        self.assertEqual(res["fecha_limite"]["fecha_limite"], "2026-10-30")
        self.assertTrue(any("no coincide con plazo_horas" in a for a in res["advertencias"]))

    def test_plazo_de_esfuerzo_informa_deficit_sin_fijar_fecha(self):
        # T1: segura 5 / agresiva 3; T2: segura 4 / agresiva 2 (recurso interno)
        tareas = [tarea("T1", 5, 3), tarea("T2", 4, 2, preds=["T1"])]
        res = ccpm.calcular_ccpm(proyecto(tareas, plazo_horas=30, tipo_plazo="esfuerzo"))
        pi = res["plazo_horas"]
        self.assertEqual(pi["esfuerzo_agresivo_horas"], 40)    # (3 + 2) d x 8 h
        self.assertEqual(pi["esfuerzo_seguro_horas"], 72)      # (5 + 4) d x 8 h
        self.assertEqual(pi["deficit_esfuerzo_horas"], 10)
        self.assertIsNone(res["fecha_limite"])                 # no deriva fecha
        self.assertTrue(any("déficit de 10 h" in a for a in res["advertencias"]))

    def test_plazo_de_esfuerzo_suficiente_no_da_deficit(self):
        tareas = [tarea("T1", 5, 3), tarea("T2", 4, 2, preds=["T1"])]
        res = ccpm.calcular_ccpm(proyecto(tareas, plazo_horas=80, tipo_plazo="esfuerzo"))
        self.assertEqual(res["plazo_horas"]["deficit_esfuerzo_horas"], 0)

    def test_markdown_incluye_la_seccion_de_plazo_en_horas(self):
        res = ccpm.calcular_ccpm(proyecto([tarea("T1", 4)], plazo_horas=120))
        md = ccpm.generar_markdown(res)
        self.assertIn("## Plazo en horas hábiles", md)

    def test_sin_plazo_horas_no_hay_seccion(self):
        res = ccpm.calcular_ccpm(proyecto([tarea("T1", 4)]))
        self.assertIsNone(res["plazo_horas"])
        self.assertNotIn("## Plazo en horas hábiles", ccpm.generar_markdown(res))

    def test_errores_de_entrada_en_horas(self):
        with self.assertRaises(ValueError):
            ccpm.calcular_ccpm(proyecto([{"id": "T1", "dur_segura": 3, "dur_segura_h": 24}]))
        with self.assertRaises(ValueError):
            ccpm.calcular_ccpm(proyecto([tarea("T1", 3)], horas_por_dia=25))
        with self.assertRaises(ValueError):
            ccpm.calcular_ccpm(proyecto([tarea("T1", 3)], tipo_plazo="otro"))
        with self.assertRaises(ValueError):
            ccpm.calcular_ccpm(proyecto([tarea("T1", 3)], plazo_horas=0))


if __name__ == "__main__":
    unittest.main()
