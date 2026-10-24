"""Issuing: engineering outputs become stamped client deliverables with a transmittal."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import ezdxf
import openpyxl
from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app


def make_dxf(path: Path, label: str):
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (420, 0), (420, 297), (0, 297)], close=True)
    msp.add_text(label, dxfattribs={"height": 8}).set_placement((20, 20))
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(path)


class TestIssuing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.d = self.root / "ACME" / "P-1"
        pkg = self.d / "workspace" / "02-engineering" / "electrical" / "PQ-01"
        make_dxf(pkg / "drawings" / "dxf" / "SLD_TGBT-01.dxf", "SLD")
        (pkg / "drawings" / "pdf").mkdir(parents=True)
        (pkg / "drawings" / "pdf" / "SLD_TGBT-01.pdf").write_bytes(b"%PDF-1.4 existing twin")
        make_dxf(pkg / "drawings" / "dxf" / "layout.dxf", "LAYOUT")                     # no PDF twin: rendered at issue time
        (pkg / "drawings" / "svg").mkdir(parents=True)
        (pkg / "drawings" / "svg" / "SLD_TGBT-01.svg").write_text("<svg/>", encoding="utf-8")   # internal, never issued
        (pkg / "calc").mkdir(parents=True, exist_ok=True)
        wb = openpyxl.Workbook()
        wb.active.append(["circuito", "potencia"])
        wb.save(pkg / "calc" / "cargas.xlsx")
        (pkg / "calc" / "notas.md").write_text("# internal", encoding="utf-8")              # md is not a deliverable format
        self.base = "/api/projects/ACME/P-1/issuing"
        self.pkg = pkg

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def test_candidates_follow_the_format_policy(self):
        c = self.c.get(self.base).json()
        by = {x["name"]: x for x in c["candidates"]}
        self.assertEqual(set(by), {"SLD_TGBT-01", "layout", "cargas"})                 # no svg, no md
        self.assertEqual(by["SLD_TGBT-01"]["formats"], ["dxf", "pdf"])
        self.assertTrue(by["layout"]["pdf_will_be_rendered"])
        self.assertEqual((c["next_transmittal"], c["emissions"]), ("TR-001", ["ifa", "ifc", "as-built"]))

    def test_issue_stamps_the_dxf_and_registers_the_deliverables(self):
        r = self.c.post(self.base, json={"emission": "ifa", "client_rev": "00", "internal_rev": "00.0.2", "notes": "primer envío",
                                         "items": [{"source": "electrical/PQ-01/drawing/SLD_TGBT-01", "name": "Diagrama unifilar"},
                                                   {"source": "electrical/PQ-01/drawing/layout"}, {"source": "electrical/PQ-01/calc/cargas.xlsx"}]})
        self.assertEqual(r.status_code, 201, r.text)
        tr = r.json()
        self.assertEqual((tr["id"], tr["status"], tr["internal_rev"]), ("TR-001", "prepared", "00.0.2"))
        folder = self.d / "deliverables" / "ifa" / "TR-001_Rev00" / "electrical"
        self.assertEqual(sorted(p.name for p in folder.iterdir()), ["P-1-ELE-001.dxf", "P-1-ELE-001.pdf", "P-1-ELE-002.dxf", "P-1-ELE-002.pdf", "P-1-ELE-003.xlsx"])
        from epc_drawing.export.stamp import read_stamp
        st = read_stamp(folder / "P-1-ELE-001.dxf")
        self.assertEqual((st["EPC_CLIENT_REV"], st["EPC_INTERNAL_REV"], st["EPC_TRANSMITTAL"], st["EPC_EMISSION"]), ("Rev 00", "00.0.2", "TR-001", "IFA"))
        self.assertIn("EPC_SOURCE_SHA256", st)
        self.assertTrue((folder / "P-1-ELE-001.pdf").read_bytes().startswith(b"%PDF-1.4 existing"))        # existing twin copied
        self.assertTrue((folder / "P-1-ELE-002.pdf").read_bytes().startswith(b"%PDF"))                       # rendered
        self.assertNotIn(b"existing", (folder / "P-1-ELE-002.pdf").read_bytes()[:30])
        # the master in the workspace is untouched
        self.assertEqual(read_stamp(self.pkg / "drawings" / "dxf" / "SLD_TGBT-01.dxf"), {})
        # registered as in_review, transmittal and ledger written
        items = json.loads((self.d / "workspace" / "05-management" / "deliverables.json").read_text(encoding="utf-8"))
        self.assertEqual([(i["code"], i["status"], i["format"], i["revision"]) for i in items],
                         [("P-1-ELE-001", "in_review", "dxf", "Rev 00"), ("P-1-ELE-002", "in_review", "dxf", "Rev 00"), ("P-1-ELE-003", "in_review", "xlsx", "Rev 00")])
        self.assertEqual(items[0]["name"], "Diagrama unifilar")
        t = json.loads((self.d / "deliverables" / "transmittals" / "TR-001.json").read_text(encoding="utf-8"))
        self.assertEqual(len(t["items"]), 3)
        self.assertTrue(all(len(f["sha256"]) == 64 for it in t["items"] for f in it["files"]))
        self.assertIn("aea-calc", t["plugins"])
        self.assertTrue(list((self.d / ".epc" / "ledger").glob("*issue_prepared.json")))
        # not delivered yet: the client sees it as in review and the package does not include it
        settings.role = "user"
        lst = {x["code"]: x for x in self.c.get("/api/app/projects/ACME/P-1/deliverables").json()}
        self.assertEqual(lst["P-1-ELE-001"]["status"], "in_review")
        self.assertEqual(self.c.get("/api/app/projects/ACME/P-1/deliverables/package").status_code, 404)
        # confirm sent -> delivered -> in the package (DXF + PDF per drawing)
        settings.role = "admin"
        self.assertEqual(self.c.post(f"{self.base}/TR-001/sent").json()["status"], "sent")
        self.assertEqual(self.c.post(f"{self.base}/TR-001/sent").status_code, 409)
        settings.role = "user"
        z = zipfile.ZipFile(io.BytesIO(self.c.get("/api/app/projects/ACME/P-1/deliverables/package").content))
        self.assertIn("ifa/TR-001_Rev00/electrical/P-1-ELE-001.pdf", z.namelist())
        self.assertIn("ifa/TR-001_Rev00/electrical/P-1-ELE-002.dxf", z.namelist())
        pk = self.c.get("/api/app/projects/ACME/P-1/deliverables/packages").json()
        self.assertEqual(pk["groups"][0]["id"], "ifa/TR-001_Rev00")

    def test_package_message_and_transmittal_document(self):
        self.c.post(self.base, json={"emission": "ifa", "client_rev": "00", "internal_rev": "00.0.2", "notes": "primer envío",
                                     "items": [{"source": "electrical/PQ-01/drawing/SLD_TGBT-01", "name": "Diagrama unifilar"}, {"source": "electrical/PQ-01/calc/cargas.xlsx"}]})
        # email text: formal, third person, lists what is delivered, no first person
        m = self.c.get(f"{self.base}/TR-001/message").json()
        self.assertEqual(m["subject"], "[P-1] Transmittal TR-001 – IFA Rev 00 – Planta")
        body = m["body"]
        self.assertTrue(body.startswith("Estimado equipo de Acme SA:\n\nNos dirigimos a ustedes para hacer entrega del transmittal TR-001, correspondiente a la emisión IFA (Emitido para Aprobación), revisión Rev 00"))
        self.assertIn("* P-1-ELE-001 – Diagrama unifilar (Formatos: DXF, PDF)", body)
        self.assertIn("* P-1-ELE-002 – cargas (Formatos: XLSX)", body)
        self.assertIn("Observaciones de la emisión: primer envío", body)
        self.assertIn("«P-1_IFA_TR-001_Rev00.zip»", body)
        self.assertTrue(body.endswith("La oficina de ingeniería queda a su entera disposición para resolver cualquier duda o aclaración.\nAtentamente,\n\n[Nombre / Firma]"))
        self.assertTrue(self.c.get(f"{self.base}/TR-001/message?lang=en").json()["body"].startswith("Dear Acme SA team,\n\nWe are writing to deliver transmittal TR-001"))
        # transmittal document: a real PDF
        r = self.c.get(f"{self.base}/TR-001/document")
        self.assertEqual((r.status_code, r.headers["content-type"]), (200, "application/pdf"))
        self.assertTrue(r.content.startswith(b"%PDF"))
        import pypdfium2 as pdfium
        text = pdfium.PdfDocument(io.BytesIO(r.content))[0].get_textpage().get_text_range()
        for s in ("TRANSMITTAL", "TR-001", "Acme SA", "P-1-ELE-001", "Diagrama unifilar", "00.0.2", "primer envío", "SHA-256"):
            self.assertIn(s, text)
        self.assertNotIn("Estimad", text)
        # package: files of the transmittal + the transmittal document + index with hashes
        r = self.c.get(f"{self.base}/TR-001/package")
        self.assertEqual(r.status_code, 200)
        self.assertIn("P-1_IFA_TR-001_Rev00.zip", r.headers["content-disposition"])
        z = zipfile.ZipFile(io.BytesIO(r.content))
        names = set(z.namelist())
        self.assertEqual(names, {"TRANSMITTAL_TR-001_Rev00.pdf", "INDICE.csv", "ifa/TR-001_Rev00/electrical/P-1-ELE-001.dxf", "ifa/TR-001_Rev00/electrical/P-1-ELE-001.pdf",
                                 "ifa/TR-001_Rev00/electrical/P-1-ELE-002.xlsx"})
        self.assertTrue(z.read("TRANSMITTAL_TR-001_Rev00.pdf").startswith(b"%PDF"))
        index = z.read("INDICE.csv").decode("utf-8-sig")
        self.assertIn("P-1-ELE-001;Diagrama unifilar;electrical;Rev 00;dxf;", index)
        self.assertEqual(self.c.get(f"{self.base}/TR-099/package").status_code, 404)
        self.assertEqual(self.c.get(f"{self.base}/TR-099/message").status_code, 404)
        settings.role = "user"                                                    # an engineer action: the customer never reaches it
        for path in ("message", "document", "package"):
            self.assertEqual(self.c.get(f"{self.base}/TR-001/{path}").status_code, 403)

    def test_second_issue_gets_the_next_transmittal_and_new_codes(self):
        src = [{"source": "electrical/PQ-01/drawing/layout"}]
        self.c.post(self.base, json={"items": src})
        r = self.c.post(self.base, json={"emission": "ifc", "client_rev": "01", "internal_rev": "01.0.0", "items": src})
        self.assertEqual((r.json()["id"], r.json()["items"][0]["code"]), ("TR-002", "P-1-ELE-002"))
        self.assertTrue((self.d / "deliverables" / "ifc" / "TR-002_Rev01" / "electrical" / "P-1-ELE-002.dxf").exists())
        c = self.c.get(self.base).json()
        self.assertEqual(c["next_transmittal"], "TR-003")
        self.assertIn("TR-002", next(x for x in c["candidates"] if x["name"] == "layout")["last_issue"])

    def test_validation(self):
        ok = {"source": "electrical/PQ-01/drawing/layout"}
        for body, key in [({"items": []}, "items"), ({"items": [ok], "emission": "ifr"}, "emission"), ({"items": [ok], "client_rev": "0"}, "client_rev"),
                          ({"items": [ok], "internal_rev": "1.0"}, "internal_rev"), ({"items": [{"source": "nope"}]}, "items"), ({"items": [ok, ok]}, "items")]:
            r = self.c.post(self.base, json=body)
            self.assertEqual(r.status_code, 422, body)
            self.assertIn(key, r.json()["detail"]["errors"])
        self.assertEqual(self.c.post(f"{self.base}/TR-999/sent").status_code, 404)
        self.assertEqual(self.c.get(f"{self.base}/..%2Fx").status_code, 404)

    def test_clients_cannot_issue(self):
        settings.role = "user"
        self.assertEqual(self.c.get(self.base).status_code, 403)
        self.assertEqual(self.c.post(self.base, json={"items": [{"source": "x"}]}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
