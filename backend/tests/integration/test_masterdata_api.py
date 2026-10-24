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
        self.assertEqual(self.c.post("/api/data/logos/organization", files={"file": ("l.svg", io.BytesIO(SVG_OK.replace(b"{n}", b"A")), "image/svg+xml")}).status_code, 404)    # no issuing company yet
        self.c.put("/api/data/organization", json={"legal_name": "Villena y Sosa S.R.L."})
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

    def test_an_organization_reaches_its_own_master_data(self):
        settings.role = "user"                                           # simulated customer: an organization of one person
        for path in ("/api/data/organization", "/api/data/clients", "/api/data/people", "/api/data/issuers"):
            self.assertEqual(self.c.get(path).status_code, 200, path)


class TestIssuersAndTeam(Base):
    def project(self, code="P-1", disciplines=("electrical", "hvac"), client=("ACME", "Acme SA")):
        r = self.c.post("/api/projects", json={"client_name": client[1], "client_code": client[0], "project_code": code, "project_name": "Planta", "jurisdiction": "AR",
                                                "methodology": "pm2", "disciplines": list(disciplines)})
        self.assertEqual(r.status_code, 201, r.text)
        return f"/api/projects/{client[0]}/{code}/parties"

    def test_a_professional_issues_in_the_name_of_several_companies(self):
        a = self.c.post("/api/data/issuers", json={"legal_name": "Empresa X S.A.", "tax_id": "30-1-1"})
        self.assertEqual(a.status_code, 201, a.text)
        b = self.c.post("/api/data/issuers", json={"legal_name": "Empresa Y S.R.L.", "tax_id": "30-2-2"}).json()
        self.assertEqual([(i["legal_name"], i["default"]) for i in self.c.get("/api/data/issuers").json()], [("Empresa X S.A.", True), ("Empresa Y S.R.L.", False)])
        self.assertEqual(self.c.post("/api/data/issuers", json={"legal_name": " "}).status_code, 422)
        self.assertEqual(self.c.put(f"/api/data/issuers/{b['id']}", json={"legal_name": "Empresa Y SRL", "email": "mal"}).status_code, 422)
        self.assertEqual(self.c.put(f"/api/data/issuers/{b['id']}", json={"legal_name": "Empresa Y SRL"}).json()["legal_name"], "Empresa Y SRL")
        self.assertEqual(self.c.get("/api/data/organization").json()["legal_name"], "Empresa X S.A.")                      # the default one
        self.assertEqual(self.c.post(f"/api/data/issuers/{b['id']}/default").json()[0]["id"], b["id"])
        url = self.project()
        self.assertEqual(self.c.get(url).json()["issuer"]["legal_name"], "Empresa Y SRL")                               # no choice: the default
        self.assertEqual(self.c.put(url, json={"issuer": a.json()["id"]}).json()["issuer"]["legal_name"], "Empresa X S.A.")
        self.assertEqual(self.c.put(url, json={"issuer": "nope"}).status_code, 422)
        self.assertEqual(self.c.delete(f"/api/data/issuers/{a.json()['id']}").status_code, 409)                          # a project issues in its name
        self.assertEqual(self.c.put(url, json={"issuer": b["id"]}).status_code, 200)
        self.assertEqual(self.c.delete(f"/api/data/issuers/{a.json()['id']}").status_code, 204)

    def test_a_project_before_issuers_keeps_its_company_and_logo(self):
        (self.root / "data").mkdir(parents=True)
        (self.root / "data" / "organization.json").write_text('{"schema_version": "1.0", "legal_name": "Villena y Sosa S.R.L.", "tax_id": "30-1-2"}', encoding="utf-8")
        (self.root / "data" / "logos").mkdir()
        (self.root / "data" / "logos" / "organization.svg").write_bytes(SVG_OK.replace(b"{n}", b"A"))
        got = self.c.get("/api/data/issuers").json()
        self.assertEqual([(i["id"], i["legal_name"], i["has_logo"]) for i in got], [("principal", "Villena y Sosa S.R.L.", True)])

    def test_each_discipline_has_its_own_team_and_every_board_uses_it(self):
        self.c.put("/api/data/organization", json={"legal_name": "Villena y Sosa S.R.L.", "tax_id": "30-1-2"})
        self.c.post("/api/data/clients", json={"id": "ACME", "name": "Acme SA", "tax_id": "30-9-9"})
        url = self.project()
        v = self.c.get(url).json()
        self.assertEqual((v["disciplines"], v["client"]["name"], v["team"]["hvac"]), (["electrical", "hvac"], "Acme SA", {"drawn_by": "", "checked_by": "", "approved_by": ""}))
        body = {"team": {"electrical": {"drawn_by": "D. Villena", "checked_by": "M. Sosa", "approved_by": "R. Paz"}, "hvac": {"drawn_by": "L. Gil", "checked_by": "J. Ruiz"}}}
        self.assertEqual(self.c.put(url, json=body).status_code, 200)
        self.assertEqual(self.c.put(url, json={"team": {"fire": {"drawn_by": "X"}}}).status_code, 422)                       # not a discipline of this project
        self.assertEqual(self.c.put(url, json={"team": {"hvac": {"drawn_by": "x" * 101}}}).status_code, 422)
        got = self.c.get(url).json()["team"]
        self.assertEqual((got["electrical"]["checked_by"], got["hvac"]["drawn_by"]), ("M. Sosa", "L. Gil"))
        sld = "/api/projects/ACME/P-1/sld"
        tb = self.c.get(sld).json()["input"]["titleblock"]
        self.assertEqual((tb["company"], tb["client"], tb["drawn_by"], tb["checked_by"], tb["approved_by"]), ("Villena y Sosa S.R.L.", "Acme SA", "D. Villena", "M. Sosa", "R. Paz"))
        # a board stores only what is its own: whatever the form sends for company, client or people is ignored
        board = {"name": "TGBT-01", "icc_ka": 10}
        circuits = [{"tag": "C-01", "description": "ALIMENTADOR", "load": 20, "unit": "A", "destination": "TD-1", "topology": "single", "phase": "3F", "length_m": 20, "kind": "mccb"}]
        r = self.c.put(sld, json={"board": board, "circuits": circuits, "titleblock": {**tb, "company": "OTRA", "drawn_by": "Intruso", "scale": "1:100", "location": "Planta baja"}})
        self.assertEqual(r.status_code, 200, r.text)
        out = r.json()["input"]["titleblock"]
        self.assertEqual((out["company"], out["drawn_by"], out["scale"], out["location"]), ("Villena y Sosa S.R.L.", "D. Villena", "1:100", "Planta baja"))
        saved = (self.root / "projects" / "ACME" / "P-1" / "workspace" / "02-engineering" / "electrical" / "PQ-01" / "src" / "boards" / "tgbt-01" / "sld-input.json").read_text(encoding="utf-8")
        self.assertNotIn("Intruso", saved)
        # changing the project's team changes the next sheet without touching the board
        self.c.put(url, json={"team": {"electrical": {"drawn_by": "N. Nuevo"}}})
        self.assertEqual(self.c.get(sld).json()["input"]["titleblock"]["drawn_by"], "N. Nuevo")

    def test_users_cannot_reach_parties_or_issuers(self):
        url = self.project()
        settings.role = "user"
        self.assertEqual(self.c.get("/api/data/issuers").status_code, 200)                                              # its own companies
        self.assertEqual(self.c.get(url).status_code, 200)                                                              # and the team of its own project


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
