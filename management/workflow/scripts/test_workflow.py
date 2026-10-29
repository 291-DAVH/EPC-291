#!/usr/bin/env python3
"""Pruebas de los scripts de flujo por ubicación (WF-001).

    cd <raíz del proyecto> && python3 -B -m unittest discover -s .claude/hooks
"""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwlib as W
import workflow as F
from fwlib import FwError

AQUI = os.path.dirname(os.path.abspath(__file__))
LME_REAL = os.path.join(AQUI, "..", "..", "90_MANAGEMENT", "DELIVERABLES.md")


def cabecera_lme():
    """Cabecera real de la LME de la plantilla (garantiza compatibilidad del parser)."""
    with open(LME_REAL, encoding="utf-8") as f:
        for l in f:
            if l.startswith("| ID | Código"):
                return l.rstrip("\n")
    raise RuntimeError("no se encontró la cabecera de la LME")


def fila(ent, cod, pq, dep="—", emision="IFA", aplica="SÍ"):
    c = [ent, f"`{cod}`", "Titulo", "Cat", "IC", "MC", aplica, pq, dep, "DRAFT", "00.0", "", emision, "", "", "", "", ""]
    return "| " + " | ".join(c) + " |"


def crear_proyecto(d, filas):
    for sub in ("03_ENGINEERING/Calculations", "03_ENGINEERING/Drawings", "03_ENGINEERING/Drawing_Inputs",
                "04_REVIEW/Review_Sheets", "05_AUDIT/Audit_Reports", "06_RELEASED", "07_DELIVERABLES/TRANSMITTALS",
                "07_DELIVERABLES/IFA", "07_DELIVERABLES/IFC", "07_DELIVERABLES/AS_BUILT", "90_MANAGEMENT"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    h = cabecera_lme()
    n = h.count("|") - 1
    txt = "# DELIVERABLES\n\n" + h + "\n|" + "---|" * n + "\n" + "\n".join(filas) + "\n\nFin.\n"
    for rel, t in (("90_MANAGEMENT/DELIVERABLES.md", txt), ("CHANGELOG.md", "# CHANGELOG\n")):
        with open(os.path.join(d, rel), "w", encoding="utf-8") as f:
            f.write(t)


def esc(d, rel, contenido="x"):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    mode = "wb" if isinstance(contenido, bytes) else "w"
    with open(p, mode) as f:
        f.write(contenido)
    return p


def hoja(d, nn, pq, resultado, fecha="20261012"):
    esc(d, f"04_REVIEW/Review_Sheets/REVIEW-{nn:02d}_{fecha}_{pq}.md", f"# Hoja\n\nResultado: {resultado}\n")


def aud(d, nn, emision, pqs, resultado, fecha="20261013"):
    esc(d, f"05_AUDIT/Audit_Reports/AUD-{nn:02d}_{fecha}.md",
        f"# Informe\n\nEmisión: {emision}\nPaquetes: {', '.join(pqs)}\nResultado: {resultado}\n")


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.environ["FW_FECHA"] = "2026-10-12"
        self.addCleanup(shutil.rmtree, self.d, True)
        self.addCleanup(os.environ.pop, "FW_FECHA", None)

    def existe(self, rel):
        return os.path.exists(os.path.join(self.d, rel))

    def sample(self):
        crear_proyecto(self.d, [fila("ENT-001", "AB01-E-MC-001", "PQ-01"),
                                fila("ENT-002", "AB01-E-MC-002", "PQ-02", dep="PQ-01")])
        esc(self.d, "03_ENGINEERING/Calculations/AB01-E-MC-001_Rev00.0.md", "uno")
        esc(self.d, "03_ENGINEERING/Calculations/AB01-E-MC-002_Rev00.0.md", "dos")

    def pasar_a_auditoria(self, pq, nn):
        F.send_to_review(self.d, pq)
        hoja(self.d, nn, pq, "APPROVED")
        F.send_to_audit(self.d, pq)


class TestLME(Base):
    def test_parser_lee_columnas_reales(self):
        self.sample()
        l = W.LME(self.d)
        self.assertEqual(l.paquetes(), ["PQ-01", "PQ-02"])
        self.assertEqual(l.dependencias("PQ-02"), ["PQ-01"])
        self.assertEqual(l.emision("PQ-01"), "IFA")

    def test_plantilla_sin_filas_validas(self):
        l = W.LME(os.path.join(AQUI, "..", ".."))
        self.assertEqual(l.paquetes(), [])        # la LME maestra no tiene paquetes reales

    def test_codigo_no_confunde_prefijos(self):
        self.sample()
        esc(self.d, "03_ENGINEERING/Calculations/AB01-E-MC-0010_Rev00.0.md")
        self.assertEqual(W.archivos_del_codigo(os.path.join(self.d, "03_ENGINEERING"), "AB01-E-MC-001"),
                         ["Calculations/AB01-E-MC-001_Rev00.0.md"])


class TestEnvioARevision(Base):
    def test_mueve_y_registra_manifiesto(self):
        self.sample()
        led = F.send_to_review(self.d, "PQ-01")
        self.assertFalse(self.existe("03_ENGINEERING/Calculations/AB01-E-MC-001_Rev00.0.md"))
        self.assertTrue(self.existe("04_REVIEW/Review_Packages/PQ-01/Calculations/AB01-E-MC-001_Rev00.0.md"))
        self.assertEqual(led["ronda"], 1)
        self.assertEqual(len(led["miembros"]["Calculations/AB01-E-MC-001_Rev00.0.md"]["sha256"]), 64)
        self.assertEqual(W.LME(self.d).valor(W.LME(self.d).filas[0], "estado"), "FOR_REVIEW")
        self.assertTrue(self.existe("90_MANAGEMENT/LEDGER/EVENTS.md"))

    def test_dependencia_en_ingenieria_bloquea(self):
        self.sample()
        with self.assertRaises(FwError):
            F.send_to_review(self.d, "PQ-02")

    def test_dependencia_en_revision_sin_aprobar_bloquea(self):
        self.sample()
        F.send_to_review(self.d, "PQ-01")
        with self.assertRaises(FwError):
            F.send_to_review(self.d, "PQ-02", permitir_varios="DEC-001")
        hoja(self.d, 1, "PQ-01", "APPROVED")
        F.send_to_review(self.d, "PQ-02", permitir_varios="DEC-001")

    def test_solo_un_paquete_en_revision(self):
        self.sample()
        crear_proyecto(self.d, [fila("ENT-001", "AB01-E-MC-001", "PQ-01"), fila("ENT-002", "AB01-E-MC-002", "PQ-02")])
        F.send_to_review(self.d, "PQ-01")
        with self.assertRaises(FwError):
            F.send_to_review(self.d, "PQ-02")
        F.send_to_review(self.d, "PQ-02", permitir_varios="DEC-005")

    def test_sin_archivos_falla_sin_mover(self):
        crear_proyecto(self.d, [fila("ENT-001", "AB01-E-MC-001", "PQ-01")])
        with self.assertRaises(FwError):
            F.send_to_review(self.d, "PQ-01")

    def test_emision_obligatoria(self):
        crear_proyecto(self.d, [fila("ENT-001", "AB01-E-MC-001", "PQ-01", emision="")])
        esc(self.d, "03_ENGINEERING/Calculations/AB01-E-MC-001_Rev00.0.md")
        with self.assertRaises(FwError):
            F.send_to_review(self.d, "PQ-01")
        F.send_to_review(self.d, "PQ-01", emision="IFA")

    def test_extras_de_pliego(self):
        crear_proyecto(self.d, [fila("ENT-001", "AB01-E-MC-001", "PQ-01")])
        esc(self.d, "03_ENGINEERING/Calculations/AB01-E-MC-001_Rev00.0.md")
        esc(self.d, "03_ENGINEERING/Technical_Specs/01_Scope.md")
        led = F.send_to_review(self.d, "PQ-01", extras=["Technical_Specs/01_Scope.md"])
        self.assertIn("Technical_Specs/01_Scope.md", led["miembros"])
        self.assertTrue(self.existe("04_REVIEW/Review_Packages/PQ-01/Technical_Specs/01_Scope.md"))


class TestDWG(Base):
    def proyecto(self):
        crear_proyecto(self.d, [fila("ENT-001", "AB01-E-PL-110", "PQ-01")])

    def test_dwg_sin_pdf_falla(self):
        self.proyecto()
        esc(self.d, "03_ENGINEERING/Drawings/E/AB01-E-PL-110_Rev00.0.dwg", b"dwg")
        with self.assertRaises(FwError):
            F.send_to_review(self.d, "PQ-01")
        self.assertTrue(self.existe("03_ENGINEERING/Drawings/E/AB01-E-PL-110_Rev00.0.dwg"))

    def test_dwg_xref_pdf_viajan_juntos_y_se_emiten_sin_insumos(self):
        self.proyecto()
        for rel, c in (("Drawings/E/AB01-E-PL-110_Rev00.0.dwg", b"d"), ("Drawings/E/AB01-E-PL-110_Rev00.0.pdf", b"p"),
                       ("Drawings/E/AB01-E-PL-110_XREF_base_Rev00.0.dwg", b"x"),
                       ("Drawing_Inputs/AB01-E-PL-110_DIN_Rev00.0.md", "ins")):
            esc(self.d, "03_ENGINEERING/" + rel, c)
        led = F.send_to_review(self.d, "PQ-01")
        self.assertEqual(len(led["miembros"]), 4)
        hoja(self.d, 1, "PQ-01", "APPROVED")
        F.send_to_audit(self.d, "PQ-01")
        aud(self.d, 1, "IFA", ["PQ-01"], "APPROVED")
        F.approve_audit(self.d, "IFA")
        F.release_documents(self.d, "IFA")
        tr, carpeta = F.issue(self.d, "IFA")
        b = f"07_DELIVERABLES/IFA/{carpeta}"
        self.assertTrue(self.existe(f"{b}/Drawings_DWG/AB01-E-PL-110_Rev00.dwg"))
        self.assertTrue(self.existe(f"{b}/Drawings_DWG/AB01-E-PL-110_XREF_base_Rev00.dwg"))
        self.assertTrue(self.existe(f"{b}/Drawings_PDF/AB01-E-PL-110_Rev00.pdf"))
        self.assertFalse(any("_DIN_" in n for _, _, fs in os.walk(os.path.join(self.d, b)) for n in fs))


class TestResultados(Base):
    def test_solo_approved_avanza(self):
        for res in ("APPROVED_WITH_COMMENTS", "REJECTED", "REJECTED_WITH_COMMENTS"):
            self.sample()
            F.send_to_review(self.d, "PQ-01")
            hoja(self.d, 1, "PQ-01", res)
            with self.assertRaises(FwError) as c:
                F.send_to_audit(self.d, "PQ-01")
            self.assertIn(res, str(c.exception))
            F.return_to_engineering(self.d, ["PQ-01"], "comentarios", resultado=res)
            self.assertTrue(self.existe("03_ENGINEERING/Calculations/AB01-E-MC-001_Rev00.0.md"))
            shutil.rmtree(self.d)
            self.d = tempfile.mkdtemp()

    def test_hoja_ausente_o_sin_resultado(self):
        self.sample()
        F.send_to_review(self.d, "PQ-01")
        with self.assertRaises(FwError):
            F.send_to_audit(self.d, "PQ-01")
        esc(self.d, "04_REVIEW/Review_Sheets/REVIEW-01_20261012_PQ-01.md", "sin campo")
        with self.assertRaises(FwError):
            F.send_to_audit(self.d, "PQ-01")

    def test_hoja_de_ronda_anterior_no_vale(self):
        self.sample()
        F.send_to_review(self.d, "PQ-01")
        hoja(self.d, 1, "PQ-01", "REJECTED", fecha="20261012")
        F.return_to_engineering(self.d, ["PQ-01"], "rehacer")
        os.environ["FW_FECHA"] = "2026-10-20"
        F.send_to_review(self.d, "PQ-01")
        hoja(self.d, 1, "PQ-01", "APPROVED", fecha="20261012")        # hoja vieja
        with self.assertRaises(FwError):
            F.send_to_audit(self.d, "PQ-01")

    def test_modificacion_bloquea_y_check_state_la_detecta(self):
        self.sample()
        F.send_to_review(self.d, "PQ-01")
        hoja(self.d, 1, "PQ-01", "APPROVED")
        esc(self.d, "04_REVIEW/Review_Packages/PQ-01/Calculations/AB01-E-MC-001_Rev00.0.md", "editado")
        with self.assertRaises(FwError) as c:
            F.send_to_audit(self.d, "PQ-01")
        self.assertIn("RETURN_TO_ENGINEERING", str(c.exception))
        errores = F.check_state(self.d)[0]
        self.assertTrue(any("MODIFICADO" in e for e in errores))
        self.assertEqual(F.cli_check_state(["--root", self.d]), 1)


class TestAuditoriaPorConjunto(Base):
    def test_conjunto_incompleto_no_se_aprueba(self):
        self.sample()
        self.pasar_a_auditoria("PQ-01", 1)
        aud(self.d, 1, "IFA", ["PQ-01"], "APPROVED")
        with self.assertRaises(FwError) as c:
            F.approve_audit(self.d, "IFA")
        self.assertIn("PQ-02", str(c.exception))

    def test_informe_no_approved_o_con_otro_conjunto(self):
        self.sample()
        self.pasar_a_auditoria("PQ-01", 1)
        self.pasar_a_auditoria("PQ-02", 2)
        aud(self.d, 1, "IFA", ["PQ-01", "PQ-02"], "APPROVED_WITH_COMMENTS")
        with self.assertRaises(FwError):
            F.approve_audit(self.d, "IFA")
        aud(self.d, 2, "IFA", ["PQ-01"], "APPROVED", fecha="20261014")
        with self.assertRaises(FwError):
            F.approve_audit(self.d, "IFA")

    def test_vuelta_desde_liberado_invalida_la_auditoria_del_conjunto(self):
        self.sample()
        self.pasar_a_auditoria("PQ-01", 1)
        self.pasar_a_auditoria("PQ-02", 2)
        aud(self.d, 1, "IFA", ["PQ-01", "PQ-02"], "APPROVED")
        F.approve_audit(self.d, "IFA")
        pqs, avisos = F.return_to_engineering(self.d, ["PQ-01"], "cambio de dato")
        self.assertEqual(W.leer_ledger(self.d, "PQ-02")["estado"], "FOR_AUDIT")
        self.assertTrue(self.existe("05_AUDIT/Audit_Packages/PQ-02/Calculations/AB01-E-MC-002_Rev00.0.md"))
        self.assertTrue(any("invalidada" in a for a in avisos))

    def test_con_dependientes(self):
        self.sample()
        self.pasar_a_auditoria("PQ-01", 1)
        self.pasar_a_auditoria("PQ-02", 2)
        pqs, _ = F.return_to_engineering(self.d, ["PQ-01"], "cambio", con_dependientes=True)
        self.assertEqual(sorted(pqs), ["PQ-01", "PQ-02"])
        self.assertEqual(W.leer_ledger(self.d, "PQ-02")["estado"], "ENGINEERING")

    def test_dependiente_genera_aviso(self):
        self.sample()
        self.pasar_a_auditoria("PQ-01", 1)
        self.pasar_a_auditoria("PQ-02", 2)
        _, avisos = F.return_to_engineering(self.d, ["PQ-01"], "cambio")
        self.assertTrue(any("PQ-02" in a and "depende" in a for a in avisos))


class TestCicloCompleto(Base):
    def test_ifa_ifc_asbuilt_cierre(self):
        self.sample()
        for nn, pq in ((1, "PQ-01"), (2, "PQ-02")):
            self.pasar_a_auditoria(pq, nn)
        aud(self.d, 1, "IFA", ["PQ-01", "PQ-02"], "APPROVED")
        F.approve_audit(self.d, "IFA")
        self.assertEqual(F.check_state(self.d)[0], [])
        F.release_documents(self.d, "IFA")
        tr, carpeta = F.issue(self.d, "IFA")
        self.assertEqual(tr, "TR-001")
        self.assertTrue(self.existe(f"07_DELIVERABLES/IFA/{carpeta}/Documents/AB01-E-MC-001_Rev00.md"))
        self.assertTrue(self.existe("07_DELIVERABLES/TRANSMITTALS/TR-001.md"))
        lme = W.LME(self.d)
        self.assertIn("borrador", lme.valor(lme.filas[0], "entrega"))
        F.confirm_sent(self.d, "TR-001")
        lme = W.LME(self.d)
        self.assertEqual(lme.valor(lme.filas[0], "estado"), "IFA")
        self.assertEqual(lme.valor(lme.filas[0], "auditado"), "AUD-01")
        self.assertEqual(F.check_state(self.d)[0], [])
        # el IFA emitido y confirmado no deja pendiente a nadie en IFA
        self.assertEqual(W.conjunto_pendiente(self.d, "IFA"), [])
        # --- IFC: se reutilizan los mismos paquetes con emisión IFC tras una nueva ronda
        for pq in ("PQ-01", "PQ-02"):
            F.return_to_engineering(self.d, [pq], "fase IE")
        for nn, pq in ((3, "PQ-01"), (4, "PQ-02")):
            F.send_to_review(self.d, pq, emision="IFC")
            hoja(self.d, nn, pq, "APPROVED")
            F.send_to_audit(self.d, pq)
        aud(self.d, 2, "IFC", ["PQ-01", "PQ-02"], "APPROVED", fecha="20261014")
        F.approve_audit(self.d, "IFC")
        F.release_documents(self.d, "IFC")
        tr2, _ = F.issue(self.d, "IFC")
        self.assertEqual(tr2, "TR-002")
        F.confirm_sent(self.d, tr2)
        # --- as-built
        self.assertEqual(sorted(F.start_asbuilt(self.d)), ["PQ-01", "PQ-02"])
        for nn, pq in ((5, "PQ-01"), (6, "PQ-02")):
            F.send_to_review(self.d, pq)
            hoja(self.d, nn, pq, "APPROVED")
            F.send_to_audit(self.d, pq)
        aud(self.d, 3, "AS_BUILT", ["PQ-01", "PQ-02"], "APPROVED", fecha="20261015")
        F.approve_audit(self.d, "AS_BUILT")
        F.release_documents(self.d, "AS_BUILT")
        tr3, carpeta3 = F.issue(self.d, "AS_BUILT")
        self.assertTrue(carpeta3.endswith("_Rev01"))
        self.assertTrue(self.existe(f"07_DELIVERABLES/AS_BUILT/{carpeta3}/Documents/AB01-E-MC-001_Rev01.md"))
        with self.assertRaises(FwError):
            F.close_project(self.d)                    # sin confirmar el envío
        F.confirm_sent(self.d, tr3)
        F.close_project(self.d)
        self.assertEqual(W.LME(self.d).valor(W.LME(self.d).filas[0], "estado"), "CLOSED")
        self.assertTrue(self.existe("90_MANAGEMENT/LEDGER/CLOSURE.md"))
        with open(os.path.join(self.d, "CHANGELOG.md"), encoding="utf-8") as f:
            self.assertIn("Proyecto CERRADO", f.read())

    def test_issue_sin_release_falla(self):
        self.sample()
        with self.assertRaises(FwError):
            F.issue(self.d, "IFA")

    def test_emision_tocada_en_07_se_detecta(self):
        self.sample()
        self.pasar_a_auditoria("PQ-01", 1)
        self.pasar_a_auditoria("PQ-02", 2)
        aud(self.d, 1, "IFA", ["PQ-01", "PQ-02"], "APPROVED")
        F.approve_audit(self.d, "IFA")
        F.release_documents(self.d, "IFA")
        tr, carpeta = F.issue(self.d, "IFA")
        os.remove(os.path.join(self.d, f"07_DELIVERABLES/IFA/{carpeta}/Documents/AB01-E-MC-001_Rev00.md"))
        self.assertTrue(any("falta en 07_DELIVERABLES" in e for e in F.check_state(self.d)[0]))

    def test_copia_suelta_en_ingenieria_es_error(self):
        self.sample()
        F.send_to_review(self.d, "PQ-01")
        esc(self.d, "03_ENGINEERING/Calculations/AB01-E-MC-001_Rev00.0.md", "otra copia")
        self.assertTrue(any("INCONSISTENTE" in e for e in F.check_state(self.d)[0]))

    def test_cli_y_wrappers(self):
        self.sample()
        self.assertEqual(F.cli_send_to_review(["--root", self.d, "PQ-01"]), 0)
        self.assertEqual(F.cli_check_state(["--root", self.d, "--escribir"]), 0)
        self.assertTrue(self.existe("90_MANAGEMENT/LEDGER/COMPUTED_STATE.md"))
        for n in ("SEND_TO_REVIEW", "RETURN_TO_ENGINEERING", "SEND_TO_AUDIT", "APPROVE_AUDIT", "RELEASE_DOCUMENTS",
                  "ISSUE_IFA", "ISSUE_IFC", "ISSUE_ASBUILT", "CONFIRM_SENT", "START_ASBUILT", "CLOSE_PROJECT", "CHECK_STATE"):
            self.assertTrue(os.path.exists(os.path.join(AQUI, n + ".py")), n)

    def test_rollback_si_el_destino_ya_existe(self):
        self.sample()
        esc(self.d, "04_REVIEW/Review_Packages/PQ-01/Calculations/AB01-E-MC-001_Rev00.0.md", "ocupado")
        with self.assertRaises(FwError):
            F.send_to_review(self.d, "PQ-01")
        self.assertTrue(self.existe("03_ENGINEERING/Calculations/AB01-E-MC-001_Rev00.0.md"))


class TestFaseFinal(Base):
    """Un proyecto que termina antes de la última fase no ofrece ni permite lo que viene después (la fase final está en .epc/project.json)."""

    def termina_en(self, fase):
        esc(self.d, ".epc/project.json", json.dumps({"end_phase": fase}))

    def emitir_ifa(self):
        self.sample()
        for nn, pq in ((1, "PQ-01"), (2, "PQ-02")):
            self.pasar_a_auditoria(pq, nn)
        aud(self.d, 1, "IFA", ["PQ-01", "PQ-02"], "APPROVED")
        F.approve_audit(self.d, "IFA")
        F.release_documents(self.d, "IFA")
        tr, _ = F.issue(self.d, "IFA")
        F.confirm_sent(self.d, tr)

    def test_la_fase_final_se_lee_del_proyecto_y_sin_ella_se_pasa_por_todas(self):
        self.assertIsNone(W.fase_final(self.d))
        self.assertTrue(W.fase_alcanzada(self.d, "ASB"))
        self.termina_en("ID")
        self.assertEqual(W.fase_final(self.d), "ID")
        self.assertTrue(W.fase_alcanzada(self.d, "ID"))
        self.assertFalse(W.fase_alcanzada(self.d, "IE"))
        self.termina_en("XX")
        self.assertIsNone(W.fase_final(self.d))                      # una fase desconocida no limita nada

    def test_no_se_prepara_ni_se_emite_lo_que_esta_despues_de_la_fase_final(self):
        self.termina_en("ID")
        for llamada in (lambda: W.exigir_fase(self.d, "IFC"), lambda: F.release_documents(self.d, "IFC"), lambda: F.approve_audit(self.d, "AS_BUILT"),
                        lambda: F.issue(self.d, "IFC"), lambda: F.start_asbuilt(self.d)):
            with self.assertRaises(FwError) as e:
                llamada()
            self.assertIn("termina en la fase ID", str(e.exception))
        W.exigir_fase(self.d, "IFA")                                  # la de su propia fase sí

    def test_la_proxima_puerta_no_ofrece_pasos_mas_alla_de_la_fase_final(self):
        self.emitir_ifa()
        ledgers = W.todos_los_ledgers(self.d)
        self.assertEqual(W.fase_limitada(ledgers, self.d), ("IE", "IFA", "entregar IFC o iniciar as-built"))
        self.termina_en("ID")
        self.assertEqual(W.fase_limitada(ledgers, self.d), ("ID", "IFA", "fase final (ID) alcanzada: CLOSE_PROJECT.py"))
        self.termina_en("IE")
        self.assertEqual(W.fase_limitada(ledgers, self.d), ("IE", "IFA", "entregar IFC"))             # el as-built ya no se ofrece
        self.termina_en("ASB")
        self.assertEqual(W.fase_limitada(ledgers, self.d), ("IE", "IFA", "entregar IFC o iniciar as-built"))

    def test_un_proyecto_que_termina_en_detalle_se_cierra_con_el_ifa_sin_decision_de_as_built(self):
        self.emitir_ifa()
        with self.assertRaises(FwError):
            F.close_project(self.d)                                   # sin fase final se pide el as-built
        self.termina_en("ID")
        F.close_project(self.d)
        self.assertEqual(W.LME(self.d).valor(W.LME(self.d).filas[0], "estado"), "CLOSED")
        with open(os.path.join(self.d, "90_MANAGEMENT/LEDGER/CLOSURE.md"), encoding="utf-8") as f:
            self.assertIn("Emisión final: IFA (sin as-built, el proyecto termina en la fase ID)", f.read())


if __name__ == "__main__":
    unittest.main()
