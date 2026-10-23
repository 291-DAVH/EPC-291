import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import intake  # noqa: E402


def make_project(root):
    d = Path(root) / "ACME" / "P-1"
    (d / ".epc").mkdir(parents=True)
    (d / ".epc" / "project.json").write_text(json.dumps({"client": "Acme", "locale": "es-AR", "disciplines": ["electrical"]}), encoding="utf-8")
    idir = d / "workspace" / "01-input" / "intake"
    idir.mkdir(parents=True)
    for n, status in [(1, "received"), (2, "received"), (3, "structured")]:
        (idir / f"INT-000{n}.json").write_text(json.dumps({"id": f"INT-000{n}", "title": f"t{n}", "text": "x", "status": status}), encoding="utf-8")
    (d / "workspace" / "00-setup").mkdir(parents=True)
    (d / "workspace" / "00-setup" / "requirements.json").write_text(json.dumps([
        {"id": "REQ-001", "statement": "old", "type": "funcional", "priority": "media", "discipline": "general", "acceptance": ["a"],
         "open_questions": [], "source_intake": ["INT-0003"], "status": "definido"}]), encoding="utf-8")
    return d


GOOD = {"requirements": [
    {"statement": "El tablero muestra el estado de cada circuito.", "type": "funcional", "priority": "media", "discipline": "electrical",
     "acceptance": ["Rótulo legible"], "open_questions": ["¿Cuántos circuitos?"], "source_intake": ["INT-0001"]},
    {"statement": "ignored text", "type": "funcional", "priority": "alta", "discipline": "general", "acceptance": ["b"],
     "source_intake": ["INT-0002"], "merge_into": "REQ-001"}],
    "intake_status": {"INT-0001": "structured", "INT-0002": "structured"}}


class TestIntake(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = make_project(self.tmp.name)
        self.af = Path(self.tmp.name) / "analysis.json"

    def tearDown(self):
        self.tmp.cleanup()

    def apply(self, analysis):
        self.af.write_text(json.dumps(analysis), encoding="utf-8")
        return intake.main(["apply", str(self.d), str(self.af)])

    def test_apply_creates_merges_and_updates_status(self):
        self.assertEqual(self.apply(GOOD), 0)
        reqs = json.loads((self.d / "workspace/00-setup/requirements.json").read_text(encoding="utf-8"))
        self.assertEqual([r["id"] for r in reqs], ["REQ-001", "REQ-002"])
        self.assertEqual(reqs[1]["status"], "abierto")
        self.assertEqual(reqs[0]["source_intake"], ["INT-0002", "INT-0003"])
        self.assertIn("b", reqs[0]["acceptance"])
        st = {i: json.loads((self.d / f"workspace/01-input/intake/{i}.json").read_text(encoding="utf-8"))["status"] for i in ("INT-0001", "INT-0002")}
        self.assertEqual(set(st.values()), {"structured"})
        log = json.loads((self.d / "workspace/01-input/intake/analysis_log.json").read_text(encoding="utf-8"))
        self.assertEqual(log[0]["created"], ["REQ-002"])

    def test_invalid_analysis_writes_nothing(self):
        bad = {"requirements": [{"statement": "x" * 400, "type": "otro", "priority": "urgente", "discipline": "nuclear", "source_intake": ["INT-9999"]}],
               "intake_status": {"INT-0001": "done"}}
        before = (self.d / "workspace/00-setup/requirements.json").read_text(encoding="utf-8")
        self.assertEqual(self.apply(bad), 1)
        self.assertEqual((self.d / "workspace/00-setup/requirements.json").read_text(encoding="utf-8"), before)
        self.assertEqual(json.loads((self.d / "workspace/01-input/intake/INT-0001.json").read_text(encoding="utf-8"))["status"], "received")

    def test_money_is_rejected(self):
        a = {"requirements": [{"statement": "El presupuesto máximo es de USD 50000 para la obra.", "type": "restricción", "priority": "media",
                               "discipline": "general", "acceptance": ["x"], "source_intake": ["INT-0001"]}]}
        self.assertEqual(self.apply(a), 1)

    def test_pending_lists_only_waiting_items(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            intake.main(["pending", "--projects", self.tmp.name])
        out = json.loads(buf.getvalue())
        self.assertEqual([i["id"] for i in out[0]["pending"]], ["INT-0001", "INT-0002"])
        self.assertEqual(out[0]["existing_requirements"][0]["id"], "REQ-001")


if __name__ == "__main__":
    unittest.main()
