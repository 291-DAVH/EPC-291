"""Deliverables: PDF next to DXF drawings and the ZIP package of what was delivered."""
import csv
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app


class TestPackage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role)
        settings.projects_dir, settings.role = self.root, "user"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        d = self.root / "ACME" / "P-1"
        folder = d / "deliverables" / "ifa" / "TR-001_Rev00" / "electrical"
        folder.mkdir(parents=True)
        (folder / "P-1-ELE-002.dxf").write_bytes(b"0\nEOF\n")
        (folder / "P-1-ELE-002.pdf").write_bytes(b"%PDF-1.4 drawing")
        (folder / "P-1-ELE-002.svg").write_text("<svg/>", encoding="utf-8")                 # internal: must never be offered
        (folder / "P-1-ELE-003.xlsx").write_bytes(b"PK xlsx")
        (folder / "P-1-ELE-009.dxf").write_text("planned", encoding="utf-8")
        (d / "workspace" / "05-management" / "deliverables.json").write_text(json.dumps([
            {"id": "ENT-001", "code": "P-1-ELE-002", "name": "Unifilar", "discipline": "electrical", "format": "dxf", "revision": "Rev 00",
             "status": "delivered", "delivered_on": "2026-03-01", "file": "ifa/TR-001_Rev00/electrical/P-1-ELE-002.dxf"},
            {"id": "ENT-002", "code": "P-1-ELE-003", "name": "Planilla", "discipline": "electrical", "format": "xlsx", "revision": "Rev 00",
             "status": "delivered", "delivered_on": "2026-03-02", "file": "ifa/TR-001_Rev00/electrical/P-1-ELE-003.xlsx"},
            {"id": "ENT-003", "code": "P-1-ELE-009", "name": "Plano", "discipline": "electrical", "format": "dxf", "revision": "Rev 00",
             "status": "in_progress", "file": "ifa/TR-001_Rev00/electrical/P-1-ELE-009.dxf"}]), encoding="utf-8")
        self.base = "/api/app/projects/ACME/P-1/deliverables"

    def tearDown(self):
        settings.projects_dir, settings.role = self._old
        self.tmp.cleanup()

    def test_formats_offered_per_deliverable(self):
        items = {x["id"]: x for x in self.c.get(self.base).json()}
        self.assertEqual(items["ENT-001"]["formats"], ["dxf", "pdf"])           # svg is not a deliverable format
        self.assertEqual(items["ENT-002"]["formats"], ["xlsx"])

    def test_download_pdf_of_a_drawing(self):
        r = self.c.get(self.base + "/ENT-001/download", params={"format": "pdf"})
        self.assertEqual((r.status_code, r.content), (200, b"%PDF-1.4 drawing"))
        self.assertIn("P-1-ELE-002.pdf", r.headers["content-disposition"])
        self.assertEqual(self.c.get(self.base + "/ENT-001/download").content, b"0\nEOF\n")      # default = primary format
        self.assertEqual(self.c.get(self.base + "/ENT-001/download", params={"format": "svg"}).status_code, 404)
        self.assertEqual(self.c.get(self.base + "/ENT-002/download", params={"format": "pdf"}).status_code, 404)

    def test_packages_listing(self):
        p = self.c.get(self.base + "/packages").json()
        self.assertEqual((p["count"], p["rev"]), (3, "Rev00"))                       # dxf + pdf + xlsx; not the planned one
        self.assertEqual(p["groups"], [{"id": "ifa/TR-001_Rev00", "emission": "IFA", "transmittal": "TR-001", "rev": "Rev00", "count": 3}])

    def test_zip_with_everything_delivered(self):
        r = self.c.get(self.base + "/package")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "application/zip")
        self.assertIn("P-1_Paquete_Rev00.zip", r.headers["content-disposition"])
        z = zipfile.ZipFile(io.BytesIO(r.content))
        names = sorted(z.namelist())
        self.assertEqual(names, ["INDICE.csv", "ifa/TR-001_Rev00/electrical/P-1-ELE-002.dxf", "ifa/TR-001_Rev00/electrical/P-1-ELE-002.pdf",
                                 "ifa/TR-001_Rev00/electrical/P-1-ELE-003.xlsx"])
        rows = list(csv.reader(io.StringIO(z.read("INDICE.csv").decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(rows[0][:4], ["codigo", "nombre", "disciplina", "revision"])
        pdf_row = next(x for x in rows if x[6].endswith(".pdf"))
        self.assertEqual(pdf_row[7], hashlib.sha256(b"%PDF-1.4 drawing").hexdigest())
        self.assertFalse(any(n.endswith(".svg") for n in names))

    def test_zip_of_one_transmittal_and_errors(self):
        r = self.c.get(self.base + "/package", params={"group": "ifa/TR-001_Rev00"})
        self.assertIn("P-1_IFA_TR-001_Rev00.zip", r.headers["content-disposition"])
        self.assertEqual(self.c.get(self.base + "/package", params={"group": "../../x"}).status_code, 422)
        (self.root / "ACME" / "P-1" / "workspace" / "05-management" / "deliverables.json").write_text("[]", encoding="utf-8")
        self.assertEqual(self.c.get(self.base + "/package").status_code, 404)


if __name__ == "__main__":
    unittest.main()
