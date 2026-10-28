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


class TestFigure(unittest.TestCase):
    FIGURE = {"type": "figure", "title": "Plano", "caption": "Plano de la hoja", "bounds": [0, 0, 200, 100],
              "shapes": [{"s": "poly", "points": [[0, 0], [200, 0], [200, 100], [0, 100]], "fill": None, "stroke": "#222222"}, {"s": "rect", "x": 10, "y": 10, "w": 50, "h": 20, "fill": "#88aaff"},
                         {"s": "circle", "x": 100, "y": 50, "r": 5, "fill": "#fbbf24", "stroke": "#d97706"}, {"s": "line", "points": [[0, 50], [200, 50]], "stroke": "#999999"},
                         {"s": "text", "x": 20, "y": 90, "text": "Aula", "size": 9}]}

    def test_a_figure_is_scaled_to_the_page_and_drawn_with_its_shapes_and_caption(self):
        from epc_drawing.export.report_pdf import layout
        pages = layout({"title": "T", "blocks": [self.FIGURE]})
        kinds = [op[0] for op in pages[0]]
        for kind in ("poly", "circle", "rect", "line", "text"):
            self.assertIn(kind, kinds)
        circle = next(op for op in pages[0] if op[0] == "circle")
        self.assertAlmostEqual(circle[3], 5 * (595 - 100) / 200, places=6)                             # the radius follows the scale of the figure (page width 495 pt for 200 units)
        poly = next(op for op in pages[0] if op[0] == "poly")
        self.assertAlmostEqual(poly[1][2][0] - poly[1][0][0], 495, places=6)
        self.assertTrue(any(op[0] == "text" and op[3] == "Plano" for op in pages[0]))                  # the heading is part of the figure

    def test_a_tall_figure_is_limited_in_height_and_a_figure_that_does_not_fit_starts_a_page(self):
        from epc_drawing.export.report_pdf import layout
        tall = {**self.FIGURE, "bounds": [0, 0, 100, 1000], "max_height": 200}
        pages = layout({"title": "T", "blocks": [tall]})
        self.assertLessEqual(max(op[4] for op in pages[0] if op[0] == "rect" and op[5] == "#fbfbfd"), 200.0001)
        many = layout({"title": "T", "blocks": [self.FIGURE] * 6})
        self.assertGreater(len(many), 1)

    def test_it_renders_to_a_pdf_with_the_caption(self):
        self.tmp = tempfile.TemporaryDirectory()
        from epc_drawing.export.report_pdf import render
        out = Path(self.tmp.name) / "f.pdf"
        render({"title": "Memoria", "blocks": [self.FIGURE]}, out)
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(out))
        text = doc[0].get_textpage().get_text_range()
        doc.close()
        self.tmp.cleanup()
        self.assertIn("Plano de la hoja", text)
