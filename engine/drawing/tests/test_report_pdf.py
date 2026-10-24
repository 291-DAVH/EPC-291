"""Generic report PDF: headings, paragraphs, bullets and tables flow over A4 pages; every text comes from the caller."""
import tempfile
import unittest
from pathlib import Path

REPORT = {"title": "Informe de Estado", "subtitle": "STATUS-01", "footer": "Proyecto X", "page_label": "Página {n} de {total}",
          "blocks": [{"type": "kv", "rows": [["Proyecto", "Nave (CUYO-1)"], ["Fase", "Ejecución"]]},
                     {"type": "h", "text": "Estado general"}, {"type": "p", "text": "Resumen del período."},
                     {"type": "bullets", "items": ["Primer logro", "Segundo logro"]},
                     {"type": "table", "columns": [["Hito", 0.6], ["Fecha", 0.4]], "rows": [["Arranque", "2026-08-15"]], "empty": "Sin hitos"},
                     {"type": "table", "columns": [["Riesgo", 0.6], ["Nivel", 0.4]], "rows": [], "empty": "Sin riesgos registrados"}]}


class TestReportPdf(unittest.TestCase):
    def render(self, rep):
        from epc_drawing.export.report_pdf import render
        self.tmp = tempfile.TemporaryDirectory()
        out = Path(self.tmp.name) / "r.pdf"
        render(rep, out)
        import pypdfium2 as pdfium
        return pdfium.PdfDocument(str(out))

    def tearDown(self):
        if hasattr(self, "tmp"):
            self.tmp.cleanup()

    def test_blocks_are_drawn(self):
        doc = self.render(REPORT)
        self.assertEqual(len(doc), 1)
        text = doc[0].get_textpage().get_text_range()
        for s in ("Informe de Estado", "STATUS-01", "Nave (CUYO-1)", "Estado general", "Primer logro", "Arranque", "Sin riesgos registrados", "Página 1 de 1"):
            self.assertIn(s, text)

    def test_long_content_continues_on_next_pages(self):
        rows = [[f"Fila {i} " + "texto largo " * 6, "x"] for i in range(120)]
        rep = {**REPORT, "blocks": REPORT["blocks"][:2] + [{"type": "table", "columns": [["Detalle", 0.8], ["Col", 0.2]], "rows": rows}]}
        doc = self.render(rep)
        self.assertGreater(len(doc), 2)
        self.assertIn("Detalle", doc[1].get_textpage().get_text_range())            # header repeated
        self.assertIn(f"Página {len(doc)} de {len(doc)}", doc[len(doc) - 1].get_textpage().get_text_range())


if __name__ == "__main__":
    unittest.main()
