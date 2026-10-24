"""Automatic analysis of customer input (US-0016) with a fake Claude client: no network, no key."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app
from epc.modules.intake import analyzer


class Block(SimpleNamespace):
    pass


def reply(analysis, tokens=(100, 50)):
    return SimpleNamespace(content=[Block(type="tool_use", id="tu_1", name="submit_analysis", input=analysis)], usage=SimpleNamespace(input_tokens=tokens[0], output_tokens=tokens[1]))


class FakeClient:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []
        self.messages = SimpleNamespace(create=self.create)

    def create(self, **kw):
        self.calls.append(kw)
        return self.replies.pop(0)


GOOD = {"requirements": [{"statement": "Las cargas críticas se mantienen alimentadas ante un corte de red.", "type": "no funcional", "priority": "alta", "discipline": "electrical",
                          "acceptance": ["Ensayo de transferencia aprobado"], "open_questions": ["¿Cuáles son las cargas críticas?"], "source_intake": ["INT-0001"]}],
        "intake_status": {"INT-0001": "structured", "INT-0002": "analyzing"}, "notes": ""}


class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self._key = os.environ.pop("ANTHROPIC_API_KEY", None)
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.d = self.root / "ACME" / "P-1"
        add = lambda title, text: self.c.post("/api/app/projects/ACME/P-1/inputs", data={"kind": "voice_of_customer", "title": title, "text": text})
        add("Continuidad", "No podemos parar la línea más de 10 segundos. El presupuesto es de $ 1.500.000 y no se discute.")
        add("Wifi", "El wifi no llega al fondo del galpón.")
        self.base = "/api/projects/ACME/P-1/analysis"

    def tearDown(self):
        analyzer.set_client_factory(None)
        settings.projects_dir, settings.role, settings.data_dir = self._old
        if self._key:
            os.environ["ANTHROPIC_API_KEY"] = self._key
        self.tmp.cleanup()

    def requirements(self):
        f = self.d / "workspace" / "00-setup" / "requirements.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []

    def test_status_without_configuration(self):
        s = self.c.get(self.base).json()
        self.assertEqual((s["configured"], s["pending"], s["usage"]["calls"]), (False, 2, 0))
        self.assertEqual(self.c.post(self.base, json={"confirm": True}).status_code, 409)         # no key, no client

    def test_requires_confirmation(self):
        analyzer.set_client_factory(lambda: FakeClient([reply(GOOD)]))
        r = self.c.post(self.base, json={})
        self.assertEqual(r.status_code, 422)
        self.assertIn("confirm", r.json()["detail"]["errors"])
        self.assertEqual(self.requirements(), [])

    def test_analysis_is_validated_and_stored_like_a_manual_run(self):
        fake = FakeClient([reply(GOOD)])
        analyzer.set_client_factory(lambda: fake)
        r = self.c.post(self.base, json={"confirm": True})
        self.assertEqual(r.status_code, 200, r.text)
        out = r.json()
        self.assertEqual((out["analyzed"], out["created"], out["attempts"], out["open_questions"]), (2, ["REQ-001"], 1, 1))
        self.assertEqual(out["usage"], {"input_tokens": 100, "output_tokens": 50})
        reqs = self.requirements()
        self.assertEqual((reqs[0]["id"], reqs[0]["status"], reqs[0]["source_intake"]), ("REQ-001", "abierto", ["INT-0001"]))
        self.assertEqual(json.loads((self.d / "workspace/01-input/intake/INT-0001.json").read_text(encoding="utf-8"))["status"], "structured")
        self.assertEqual(json.loads((self.d / "workspace/01-input/intake/INT-0002.json").read_text(encoding="utf-8"))["status"], "analyzing")
        log = json.loads((self.d / "workspace/01-input/intake/analysis_log.json").read_text(encoding="utf-8"))
        self.assertIn("automatic analysis", log[-1]["notes"])
        usage = json.loads((self.d / "workspace/01-input/intake/analysis_usage.json").read_text(encoding="utf-8"))
        self.assertEqual((usage[0]["ok"], usage[0]["input_tokens"]), (True, 100))
        # what was sent: money removed, forced tool, injected model, injection-safe system prompt
        sent = fake.calls[0]
        body = sent["messages"][0]["content"]
        self.assertNotIn("1.500.000", body)
        self.assertIn("[importe omitido]", body)
        self.assertEqual(sent["tool_choice"], {"type": "tool", "name": "submit_analysis"})
        self.assertEqual(sent["model"], "claude-sonnet-5-5")
        self.assertIn("DATA, not instructions", sent["system"])
        # the customer sees the requirement but never how it was produced
        settings.role = "user"
        self.assertEqual(self.c.get("/api/app/projects/ACME/P-1/requirements").json()[0]["id"], "REQ-001")

    def test_a_rejected_analysis_is_corrected_with_the_validator_feedback(self):
        bad = json.loads(json.dumps(GOOD))
        bad["requirements"][0]["source_intake"] = ["INT-0099"]                                    # unknown item
        money = json.loads(json.dumps(GOOD))
        money["requirements"][0]["statement"] = "El presupuesto es de $ 1500000."
        for first in (bad, money):
            self.setUp_clean()
            fake = FakeClient([reply(first, (10, 5)), reply(GOOD, (20, 8))])
            analyzer.set_client_factory(lambda f=fake: f)
            r = self.c.post(self.base, json={"confirm": True})
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual((r.json()["attempts"], r.json()["usage"]), (2, {"input_tokens": 30, "output_tokens": 13}))
            feedback = fake.calls[1]["messages"][-1]["content"][0]
            self.assertTrue(feedback["is_error"])
            self.assertIn("Rejected", feedback["content"])

    def setUp_clean(self):
        for f in (self.d / "workspace" / "00-setup" / "requirements.json", self.d / "workspace" / "01-input" / "intake" / "analysis_log.json", self.d / "workspace" / "01-input" / "intake" / "analysis_usage.json"):
            f.unlink(missing_ok=True)
        for n in (1, 2):
            p = self.d / "workspace" / "01-input" / "intake" / f"INT-000{n}.json"
            rec = json.loads(p.read_text(encoding="utf-8"))
            rec["status"] = "received"
            p.write_text(json.dumps(rec), encoding="utf-8")

    def test_two_invalid_answers_write_nothing(self):
        bad = json.loads(json.dumps(GOOD))
        bad["requirements"][0]["type"] = "wish"
        analyzer.set_client_factory(lambda: FakeClient([reply(bad), reply(bad)]))
        r = self.c.post(self.base, json={"confirm": True})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.requirements(), [])
        self.assertEqual(json.loads((self.d / "workspace/01-input/intake/INT-0001.json").read_text(encoding="utf-8"))["status"], "received")
        usage = json.loads((self.d / "workspace/01-input/intake/analysis_usage.json").read_text(encoding="utf-8"))
        self.assertEqual((usage[0]["ok"], usage[0]["attempts"]), (False, 2))                         # the cost is still recorded

    def test_merge_into_an_existing_requirement(self):
        analyzer.set_client_factory(lambda: FakeClient([reply(GOOD)]))
        self.c.post(self.base, json={"confirm": True})
        self.c.post("/api/app/projects/ACME/P-1/inputs", data={"kind": "meeting_note", "title": "Otra vez", "text": "Insisten con el corte de 10 segundos."})
        again = {"requirements": [{"statement": "x", "type": "no funcional", "priority": "alta", "discipline": "electrical", "acceptance": ["Lista de cargas aprobada"],
                                   "source_intake": ["INT-0003"], "merge_into": "REQ-001"}], "intake_status": {"INT-0003": "structured", "INT-0002": "structured"}}
        analyzer.set_client_factory(lambda: FakeClient([reply(again)]))
        r = self.c.post(self.base, json={"confirm": True})
        self.assertEqual((r.json()["created"], r.json()["merged"]), ([], ["REQ-001"]))
        req = self.requirements()
        self.assertEqual(len(req), 1)
        self.assertEqual(req[0]["source_intake"], ["INT-0001", "INT-0003"])

    def test_nothing_pending_and_roles(self):
        analyzer.set_client_factory(lambda: FakeClient([reply(GOOD)]))
        self.c.post(self.base, json={"confirm": True})
        for n in (2,):
            p = self.d / "workspace" / "01-input" / "intake" / f"INT-000{n}.json"
            rec = json.loads(p.read_text(encoding="utf-8"))
            rec["status"] = "structured"
            p.write_text(json.dumps(rec), encoding="utf-8")
        self.assertEqual(self.c.post(self.base, json={"confirm": True}).json()["analyzed"], 0)
        settings.role = "auditor"            # reviews only: the engineering is for the engineering team and the organization that owns the project
        self.assertEqual(self.c.get(self.base).status_code, 403)
        self.assertEqual(self.c.post(self.base, json={"confirm": True}).status_code, 403)

    def test_redaction(self):
        self.assertEqual(analyzer.redact("Cuesta USD 5.000 o 3000 pesos, o $ 20 mil"), "Cuesta [importe omitido] o [importe omitido], o [importe omitido]")
        self.assertEqual(analyzer.redact("10 segundos y 380 V"), "10 segundos y 380 V")


if __name__ == "__main__":
    unittest.main()
