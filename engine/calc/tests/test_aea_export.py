"""Pruebas de aea_export.py."""
import json
import os
import tempfile
import unittest

from epc_calc import aea_export as X


def _ok():
    return {"L-01": X.circuito_json(10, 7.6, 36, 1.5, 2.61, "MCB (10 A)")}


class TestExport(unittest.TestCase):
    def test_circuit(self):
        c = X.circuito_json(250.0, 250.04, 36.0, 240.0, 0.4812, "MCCB (250 A)")
        self.assertEqual(c, {"In": 250, "Ib": 250.0, "icu": 36, "S": 240, "dU": 0.48, "disp": "MCCB (250 A)"})
        self.assertIsInstance(c["In"], int)
        self.assertEqual(list(c), ["In", "Ib", "icu", "S", "dU", "disp"])

    def test_valida(self):
        self.assertEqual(X.validate_calculation(_ok()), {"errores": [], "avisos": []})

    def test_errors(self):
        d = _ok()
        d["L-01"]["extra"] = 1
        del d["L-01"]["S"]
        self.assertEqual(len(X.validate_calculation(d)["errores"]), 2)
        d = _ok()
        d["L-01"]["In"] = -1
        d["L-01"]["disp"] = " "
        self.assertEqual(len(X.validate_calculation(d)["errores"]), 2)
        self.assertTrue(X.validate_calculation({})["errores"])
        self.assertTrue(X.validate_calculation({"": {}})["errores"])

    def test_avisos(self):
        d = {"A": X.circuito_json(10, 12, 36, 1.5, 6.0, "MCB (16 A)"), "B": X.circuito_json(10, 5, 36, 3, 1, "MCB (10 A)")}
        av = X.validate_calculation(d)["avisos"]
        self.assertEqual(len(av), 4)   # In<Ib, In fuera de disp, dU>5 (A) ; S=3 fuera de serie (B)

    def test_ida_y_vuelta(self):
        with tempfile.TemporaryDirectory() as t:
            ruta = os.path.join(t, "P_calculo.json")
            self.assertEqual(X.export_calculation(_ok(), ruta), [])
            self.assertEqual(X.load_calculation(ruta), _ok())
            self.assertFalse(open(ruta, "rb").read().startswith(b"\xef\xbb\xbf"))

    def test_without_pdf(self):
        with tempfile.TemporaryDirectory() as t:
            for ext in (".pdf", ".docx", ".md"):
                with self.assertRaises(ValueError):
                    X.export_calculation(_ok(), os.path.join(t, "x" + ext))

    def test_exporta_invalido(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                X.export_calculation({"A": {"In": 1}}, os.path.join(t, "x.json"))

    def test_example(self):
        d = X.load_calculation(os.path.join(os.path.dirname(os.path.abspath(X.__file__)), "example_calculo.json"))
        self.assertEqual(d["G-02"]["disp"], "RCCB 4P 63 A 30 mA")
        self.assertEqual(X.validate_calculation(d)["errores"], [])


if __name__ == "__main__":
    unittest.main()
