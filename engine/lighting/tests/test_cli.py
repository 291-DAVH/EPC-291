import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting.__main__ import main  # noqa: E402
import helpers  # noqa: E402

EXAMPLE = HERE.parent / "examples" / "classroom.json"


def call(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class TestCli(unittest.TestCase):
    def test_ok_writes_one_predictable_file_inside_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = call([str(EXAMPLE), "--out", str(Path(tmp) / "result")])
            self.assertEqual(code, 0, err)
            self.assertTrue(out.startswith("OK "))
            files = sorted(p.name for p in (Path(tmp) / "result").iterdir())
            self.assertEqual(files, ["classroom.lighting.json"])
            data = json.loads((Path(tmp) / "result" / "classroom.lighting.json").read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "1.0")

    def test_domain_error_exits_1_with_an_error_line_on_stderr(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            code, out, err = call([str(bad), "--out", str(Path(tmp) / "o")])
            self.assertEqual(code, 1)
            self.assertTrue(err.startswith("ERROR "))
            self.assertFalse((Path(tmp) / "o").exists())

    def test_a_missing_file_exits_1(self):
        code, _, err = call(["/nonexistent/file.json"])
        self.assertEqual(code, 1)
        self.assertIn("ERROR cannot read", err)

    def test_options_reach_the_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "long.json"
            doc.write_text(json.dumps(helpers.document([helpers.room_dict(length_m=12, target_lux=100)])), encoding="utf-8")
            call([str(doc), "--out", str(Path(tmp) / "a")])
            call([str(doc), "--out", str(Path(tmp) / "b"), "--enforce-spacing", "--no-points"])
            a = json.loads((Path(tmp) / "a" / "long.lighting.json").read_text(encoding="utf-8"))
            b = json.loads((Path(tmp) / "b" / "long.lighting.json").read_text(encoding="utf-8"))
            self.assertGreater(b["rooms"][0]["layout"]["installed"], a["rooms"][0]["layout"]["installed"])
            self.assertFalse(b["rooms"][0]["points"]["computed"])

    def test_the_same_run_twice_writes_identical_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            call([str(EXAMPLE), "--out", str(Path(tmp) / "1")])
            call([str(EXAMPLE), "--out", str(Path(tmp) / "2")])
            self.assertEqual((Path(tmp) / "1" / "classroom.lighting.json").read_bytes(), (Path(tmp) / "2" / "classroom.lighting.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
