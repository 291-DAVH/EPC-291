"""The IRAM sheet generator gives, for each format, the sheet it gave when it was separated from the drawing engine (tests/fixtures/titleblock)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"


class TestSheets(unittest.TestCase):
    def sheet(self, fmt: str, tmp: Path) -> str:
        dst = tmp / f"sheet-IRAM-{fmt}.svg"
        env = {"PYTHONPATH": str(SRC), "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")}
        res = subprocess.run([sys.executable, "-m", "epc_titleblock.sheet_generator", fmt, str(dst)], capture_output=True, text=True, cwd=tmp, env=env)
        self.assertEqual(res.returncode, 0, res.stderr[-400:])
        return dst.read_text(encoding="utf-8")

    def test_each_format_gives_a_sheet_of_its_size_with_the_iram_4508_title_block(self):
        sizes = {"A4": (210, 297), "A3": (420, 297), "A0": (1189, 841)}
        with tempfile.TemporaryDirectory() as t:
            for fmt, (w, h) in sizes.items():
                svg = self.sheet(fmt, Path(t))
                self.assertIn(f'width="{w}mm" height="{h}mm"', svg, fmt)
                self.assertIn('data-norma="IRAM 4504 / IRAM 4508"', svg)
                self.assertIn("rotulo_IRAM4508", svg)

    def test_the_package_carries_its_templates_and_assets(self):
        base = SRC / "epc_titleblock"
        self.assertTrue((base / "templates" / "input-titleblocks.xlsx").is_file())
        self.assertTrue(any((base / "assets").glob("*-logo-*")))


if __name__ == "__main__":
    unittest.main()
