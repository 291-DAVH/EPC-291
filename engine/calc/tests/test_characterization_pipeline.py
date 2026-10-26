"""The design calculation gives, for a fixed grid of circuits, criteria and installation methods, exactly what it gave when the refactoring started (golden/pipeline.json)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import characterization as C   # noqa: E402

GOLDEN = json.loads(C.GOLDEN.read_text(encoding="utf-8")) if C.GOLDEN.is_file() else {}


class TestPipelineCharacterization(unittest.TestCase):
    def test_the_golden_file_covers_every_case(self):
        self.assertEqual(sorted(GOLDEN), sorted(c["id"] for c in C.cases()))

    def test_every_case_gives_its_golden_result(self):
        for case in C.cases():
            with self.subTest(case=case["id"]):
                self.assertEqual(C.run(case), GOLDEN[case["id"]])

    def test_the_grid_exercises_what_it_claims(self):
        kinds = {r["detalle"][t]["tipo"] for r in GOLDEN.values() if "detalle" in r for t in r["detalle"]}
        self.assertEqual(kinds, {"seccional", "motor", "iluminacion", "tomacorrientes"})
        methods = {r["detalle"]["C-01"]["metodo"] for k, r in GOLDEN.items() if k.startswith("method:") and "detalle" in r}
        self.assertTrue({"B2", "C", "E", "D1", "D2"} <= methods)
        self.assertTrue(any("ruta" in r["detalle"]["C-01"] and r["detalle"]["C-01"]["ruta"] for k, r in GOLDEN.items() if k.startswith("route:")))


if __name__ == "__main__":
    unittest.main()
