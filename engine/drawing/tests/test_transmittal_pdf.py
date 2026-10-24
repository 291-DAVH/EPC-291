"""Transmittal document: A4 pages, every text given by the caller, long tables continue on the next page."""
import tempfile
import unittest
from pathlib import Path

DATA = {"title": "TRANSMITTAL", "subtitle": "TR-002", "header": [["Proyecto", "Nave de mecanizado (CUYO-2026-004)"], ["Cliente", "Metalúrgica Cuyo"]],
        "columns": [["N°", 0.07], ["Código", 0.25], ["Descripción", 0.48], ["Formatos", 0.20]],
        "rows": [["1", "CUYO-ELE-001", "Unifilar TGBT-02 hoja 1", "DXF, PDF"]], "sections": [["Observaciones", "Sin observaciones."]],
        "footer": "Emitido por Oficina", "page_label": "Página {n} de {total}"}


class TestTransmittalPdf(unittest.TestCase):
    def render(self, data):
        from epc_drawing.export.transmittal_pdf import render
        out = Path(self.tmp.name) / "t.pdf"
        render(data, out)
        import pypdfium2 as pdfium
        return pdfium.PdfDocument(str(out))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_one_page_a4_with_the_given_texts(self):
        doc = self.render(DATA)
        self.assertEqual(len(doc), 1)
        w, h = doc[0].get_size()
        self.assertAlmostEqual(w / 72 * 25.4, 210, delta=2)
        self.assertAlmostEqual(h / 72 * 25.4, 297, delta=2)
        text = doc[0].get_textpage().get_text_range()
        for s in ("TRANSMITTAL", "TR-002", "Metalúrgica Cuyo", "CUYO-ELE-001", "Observaciones", "Página 1 de 1"):
            self.assertIn(s, text)

    def test_a_long_table_continues_with_its_header_and_numbers_the_pages(self):
        rows = [[str(i), f"CUYO-ELE-{i:03d}", "Descripción larga del documento " * 3, "DXF, PDF"] for i in range(1, 80)]
        doc = self.render({**DATA, "rows": rows})
        self.assertGreater(len(doc), 1)
        first, last = (doc[0].get_textpage().get_text_range(), doc[len(doc) - 1].get_textpage().get_text_range())
        self.assertIn(f"Página 1 de {len(doc)}", first)
        self.assertIn(f"Página {len(doc)} de {len(doc)}", last)
        self.assertIn("CUYO-ELE-079", last)
        self.assertIn("Código", doc[1].get_textpage().get_text_range())           # the header repeats


if __name__ == "__main__":
    unittest.main()
