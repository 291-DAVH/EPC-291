"""Master data: company profile, clients, people and logos (entered once), and their use in the SLD titleblock."""
import io
import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app

SVG_OK = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40"><rect width="100" height="40" fill="#123456"/><text x="5" y="25">LOGOMARK{n}</text></svg>'


def png_bytes():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (40, 20), (200, 30, 30)).save(buf, "PNG")
    return buf.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root / "projects", "admin", self.root / "data"
        self.c = TestClient(create_app())

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()


class TestMasterData(Base):
    def test_organization_entered_once(self):
        self.assertEqual(self.c.get("/api/data/organization").json()["legal_name"], "")
        r = self.c.put("/api/data/organization", json={"legal_name": "Villena y Sosa S.R.L.", "tax_id": "30-12345678-9", "email": "info@vys.example"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.c.get("/api/data/organization").json()["legal_name"], "Villena y Sosa S.R.L.")
        self.assertEqual(self.c.put("/api/data/organization", json={"legal_name": " "}).status_code, 422)
        self.assertEqual(self.c.put("/api/data/organization", json={"legal_name": "X", "email": "nope"}).status_code, 422)

    def test_clients_crud(self):
        r = self.c.post("/api/data/clients", json={"id": "ford", "name": "Ford Argentina", "tax_id": "30-1-2"})
        self.assertEqual((r.status_code, r.json()["id"]), (201, "FORD"))
        self.assertEqual(self.c.post("/api/data/clients", json={"id": "FORD", "name": "Other"}).status_code, 409)
        self.assertEqual(self.c.post("/api/data/clients", json={"id": "../x", "name": "Bad"}).status_code, 422)
        self.assertEqual(self.c.put("/api/data/clients/FORD", json={"id": "FORD", "name": "Ford Argentina S.C.A."}).json()["name"], "Ford Argentina S.C.A.")
        self.assertEqual([c["id"] for c in self.c.get("/api/data/clients").json()], ["FORD"])
        self.assertEqual(self.c.delete("/api/data/clients/FORD").status_code, 204)
        self.assertEqual(self.c.delete("/api/data/clients/FORD").status_code, 404)

    def test_people(self):
        a = self.c.post("/api/data/people", json={"name": "Daniel Villena", "role": "Ingeniero"}).json()
        b = self.c.post("/api/data/people", json={"name": "Daniel Villena"}).json()
        self.assertEqual((a["id"], b["id"]), ("Daniel-Villena", "Daniel-Villena-2"))
        self.assertEqual(self.c.put("/api/data/people/" + a["id"], json={"name": "Daniel A. Villena", "registration": "CPI 123"}).json()["registration"], "CPI 123")
        self.assertEqual(self.c.post("/api/data/people", json={"name": ""}).status_code, 422)
        self.assertEqual(self.c.delete("/api/data/people/" + b["id"]).status_code, 204)

    def test_logos(self):
        self.c.post("/api/data/clients", json={"id": "ACME", "name": "Acme SA"})
        up = lambda kind, name, data: self.c.post(f"/api/data/logos/{kind}", files={"file": (name, io.BytesIO(data), "application/octet-stream")})
        self.assertEqual(up("organization", "logo.svg", SVG_OK.replace(b"{n}", b"A")).status_code, 201)
        r = self.c.get("/api/data/logos/organization")
        self.assertEqual((r.status_code, r.headers["content-type"]), (200, "image/svg+xml"))
        self.assertIn("sandbox", r.headers["content-security-policy"])
        self.assertEqual(up("client-ACME", "logo.png", png_bytes()).status_code, 201)
        self.assertEqual(self.c.get("/api/data/logos/client-ACME").headers["content-type"], "image/png")
        self.assertTrue(self.c.get("/api/data/clients").json()[0]["has_logo"])
        # rejected uploads
        self.assertEqual(up("organization", "logo.exe", b"MZ").status_code, 422)
        self.assertEqual(up("organization", "fake.png", b"not a png").status_code, 422)
        self.assertEqual(up("organization", "evil.svg", b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>').status_code, 422)
        self.assertEqual(up("organization", "evil2.svg", b'<svg xmlns="http://www.w3.org/2000/svg" onload="x()"></svg>').status_code, 422)
        self.assertEqual(up("organization", "big.svg", SVG_OK + b" " * 1_100_000).status_code, 413)
        self.assertEqual(up("client-NOPE", "l.svg", SVG_OK).status_code, 404)
        self.assertEqual(up("weird", "l.svg", SVG_OK).status_code, 422)
        self.assertEqual(self.c.delete("/api/data/clients/ACME").status_code, 204)             # its logo goes with it
        self.assertEqual(self.c.get("/api/data/logos/client-ACME").status_code, 404)

    def test_users_cannot_reach_master_data(self):
        settings.role = "user"
        for path in ("/api/data/organization", "/api/data/clients", "/api/data/people", "/api/data/logos/organization"):
            self.assertEqual(self.c.get(path).status_code, 403, path)


class TestSldUsesMasterData(Base):
    def test_titleblock_prefilled_and_logos_reach_the_drawing(self):
        self.c.put("/api/data/organization", json={"legal_name": "Villena y Sosa S.R.L.", "tax_id": "30-1-2"})
        self.c.post("/api/data/clients", json={"id": "ACME", "name": "Acme SA", "tax_id": "30-9-9"})
        self.c.post("/api/data/people", json={"name": "D. Villena"})
        for kind, n in (("organization", b"EMPRESA"), ("client-ACME", b"CLIENTE")):
            r = self.c.post(f"/api/data/logos/{kind}", files={"file": ("l.svg", io.BytesIO(SVG_OK.replace(b"{n}", n)), "image/svg+xml")})
            self.assertEqual(r.status_code, 201, r.text)
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        base = "/api/projects/ACME/P-1/sld"
        v = self.c.get(base).json()
        tb = v["input"]["titleblock"]
        self.assertEqual((tb["company"], tb["company_cuit"], tb["client"], tb["client_cuit"]), ("Villena y Sosa S.R.L.", "30-1-2", "Acme SA", "30-9-9"))
        self.assertEqual((v["people"], v["logos"]), (["D. Villena"], {"company": True, "client": True}))
        body = {"board": {**v["input"]["board"], "name": "TGBT-01", "icc_ka": 10}, "titleblock": tb,
                "circuits": [{"tag": "C-01", "description": "ALIMENTADOR", "load": 20, "unit": "A", "destination": "TD-1", "topology": "single", "phase": "3F", "length_m": 20, "kind": "mccb"}]}
        self.assertEqual(self.c.put(base, json=body).status_code, 200)
        self.assertEqual(self.c.post(base + "/generate", params={"diagrams": "none"}).status_code, 202)           # memo and summary first
        for _ in range(240):
            if self.c.get(base + "/status").json()["state"] in ("done", "failed"):
                break
            time.sleep(0.5)
        self.assertEqual(self.c.post(base + "/generate").status_code, 202)
        for _ in range(240):
            st = self.c.get(base + "/status").json()
            if st["state"] in ("done", "failed"):
                break
            time.sleep(0.5)
        self.assertEqual(st["state"], "done", st)
        pkg = self.root / "projects" / "ACME" / "P-1" / "workspace" / "02-engineering" / "electrical" / "PQ-01"
        svg = (pkg / next(o for o in st["outputs"] if o.endswith(".svg"))).read_text(encoding="utf-8")
        self.assertIn("LOGOMARKEMPRESA", svg)
        self.assertIn("LOGOMARKCLIENTE", svg)
        self.assertIn("Villena y Sosa S.R.L.", svg)


if __name__ == "__main__":
    unittest.main()
