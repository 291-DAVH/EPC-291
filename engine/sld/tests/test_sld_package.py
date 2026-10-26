"""The single-line generator only draws: it needs the calculation, and finds its symbols and title blocks in their own packages."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
SRC = [str(ENGINE / a / "src") for a in ("sld", "calc", "symbols", "titleblock")]


class TestSldPackage(unittest.TestCase):
    def test_the_symbol_library_comes_from_epc_symbols(self):
        sys.path[:0] = SRC
        from epc_symbols import library_dir
        self.assertTrue((Path(library_dir("sld-lv-symbol")) / "_catalog.json").is_file())

    def test_without_the_calculation_it_refuses_to_draw(self):
        with tempfile.TemporaryDirectory() as t:
            env = {"PYTHONPATH": os.pathsep.join(SRC), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
            res = subprocess.run([sys.executable, "-m", "epc_sld.sld_generator", "default", "x.xlsx", t, "SLD_X", "default", "default"], capture_output=True, text=True, env=env, cwd=t)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("SLD_CALC_JSON", res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
