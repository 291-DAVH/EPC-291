"""The board memo and summary give, for boards that exercise every branch, exactly what they gave when the refactoring started (golden/memo.json)."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import characterization_memo as C   # noqa: E402

GOLDEN = json.loads(C.GOLDEN.read_text(encoding="utf-8")) if C.GOLDEN.is_file() else {}


class TestMemoCharacterization(unittest.TestCase):
    def test_every_board_gives_its_golden_memo_and_documents(self):
        self.assertEqual(sorted(GOLDEN), sorted(C.CASES))
        for name in C.CASES:
            with self.subTest(board=name):
                self.assertEqual(C.run(name), GOLDEN[name])

    def test_the_boards_exercise_the_branches_they_claim(self):
        g = GOLDEN
        self.assertTrue(g["groups_tns"]["memo"]["resumen"]["global"] in (True, False))
        self.assertFalse(g["it_system_unvalidated"]["memo"]["validated"])
        self.assertIn("IT", g["it_system_unvalidated"]["mc_md"])
        self.assertFalse(g["with_upstream"]["memo"]["acometida"]["dato_faltante"])
        self.assertTrue(g["route_and_failures"]["memo"]["circuits"][0]["externo"]["ruta"])
        self.assertEqual(len(g["route_and_failures"]["memo"]["resumen"]["observaciones"]) <= 3, True)
        self.assertTrue(any(s["resultado"] in ("total", "parcial", "revisar") for s in g["groups_tns"]["memo"]["selectividad"] + g["with_upstream"]["memo"]["selectividad"]))


if __name__ == "__main__":
    unittest.main()
