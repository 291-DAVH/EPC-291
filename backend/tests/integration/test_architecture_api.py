"""Architecture recognition on a sheet: the plan that was uploaded is read for walls, doors and windows, and what is found is kept with the sheet."""
import io
import tempfile
import unittest
from pathlib import Path

import ezdxf
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from epc.core.config import settings
from epc.main import create_app


def flat_dxf() -> bytes:
    """A room of 6 x 4 m (metres), walls 0.2 m thick drawn as two lines, a door gap with its swing in the bottom wall and a window gap in the top one."""
    doc = ezdxf.new("R2010")
    doc.units = 6
    msp = doc.modelspace()
    for y, gap in ((0.0, (2.0, 2.9)), (0.2, (2.0, 2.9)), (3.8, (3.0, 4.2)), (4.0, (3.0, 4.2))):
        msp.add_line((0, y), (gap[0], y))
        msp.add_line((gap[1], y), (6, y))
    for x in (0.0, 0.2, 5.8, 6.0):
        msp.add_line((x, 0), (x, 4))
    msp.add_arc((2.0, 0.1), 0.9, 0, 90)
    msp.add_line((2.0, 0.1), (2.0, 1.0))
    for y in (3.85, 3.95):
        msp.add_line((3.0, y), (4.2, y))
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "flat.dxf"
        doc.saveas(str(path))
        return path.read_bytes()


def flat_png() -> bytes:
    img = Image.new("L", (1100, 800), 255)
    d = ImageDraw.Draw(img)
    for box in ((100, 100, 1000, 112), (100, 688, 400, 700), (535, 688, 1000, 700), (100, 100, 112, 700), (988, 100, 1000, 700)):
        d.rectangle(box, fill=0)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


class TestArchitecture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old = (settings.projects_dir, settings.role, settings.data_dir)
        settings.projects_dir, settings.role, settings.data_dir = self.root, "admin", self.root / "_data"
        self.c = TestClient(create_app())
        r = self.c.post("/api/projects", json={"client_name": "Acme SA", "client_code": "ACME", "project_code": "P-1", "project_name": "Planta",
                                                "jurisdiction": "AR", "methodology": "pm2", "disciplines": ["electrical"]})
        self.assertEqual(r.status_code, 201, r.text)
        self.base = "/api/projects/ACME/P-1/layout"
        self.c.put(f"{self.base}/L0", json={"discipline": "arquitectura"})

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def upload(self, name, data):
        r = self.c.post(f"{self.base}/L0/underlay", files={"file": (name, data)})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_a_dxf_gives_its_walls_door_and_window_and_its_svg_becomes_the_underlay(self):
        self.assertEqual(self.upload("flat.dxf", flat_dxf())["architecture"], None)
        r = self.c.post(f"{self.base}/L0/architecture", json={})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["architecture"]["counts"], {"walls": 6, "doors": 1, "windows": 1, "openings": 0})
        self.assertTrue(body["underlay_replaced"])
        self.assertEqual(body["view"]["architecture"]["counts"]["walls"], 6)
        self.assertEqual(body["view"]["underlay"]["kind"], "svg")
        svg = self.c.get(f"{self.base}/L0/underlay")
        self.assertIn(b"ARQ-MUROS", svg.content)
        stored = self.c.get(f"{self.base}/L0/architecture").json()
        self.assertEqual(stored["counts"], body["architecture"]["counts"])

    def test_an_image_is_read_in_its_own_pixels_and_keeps_its_underlay(self):
        self.upload("flat.png", flat_png())
        body = self.c.post(f"{self.base}/L0/architecture", json={}).json()
        self.assertEqual(body["architecture"]["source"], "image")
        self.assertFalse(body["underlay_replaced"])
        self.assertEqual(body["view"]["underlay"]["kind"], "png")
        self.assertEqual(body["architecture"]["size"], [1100.0, 800.0])
        self.assertGreaterEqual(body["architecture"]["counts"]["walls"], 4)

    def test_a_known_scale_is_used_and_nothing_to_read_is_refused(self):
        r = self.c.post(f"{self.base}/L0/architecture", json={})
        self.assertEqual(r.status_code, 422)
        self.assertIn("upload the plan", r.json()["detail"]["errors"]["file"])
        self.upload("flat.dxf", flat_dxf())
        body = self.c.post(f"{self.base}/L0/architecture", json={"units_per_metre": 3000 / 6}).json()
        self.assertEqual(body["architecture"]["units_per_metre"], 500.0)
        self.assertEqual(self.c.post(f"{self.base}/L0/architecture", json={"units_per_metre": -1}).status_code, 422)

    def test_a_new_plan_forgets_what_was_found_in_the_old_one_and_it_can_be_removed(self):
        self.upload("flat.dxf", flat_dxf())
        self.c.post(f"{self.base}/L0/architecture", json={})
        self.assertEqual(self.c.get(f"{self.base}/L0/architecture").status_code, 200)
        self.assertIsNone(self.upload("flat.png", flat_png())["architecture"])
        self.assertEqual(self.c.get(f"{self.base}/L0/architecture").status_code, 404)
        self.c.post(f"{self.base}/L0/architecture", json={})
        self.assertIsNone(self.c.delete(f"{self.base}/L0/architecture").json()["architecture"])

    def test_a_file_the_engine_cannot_read_gives_its_reason(self):
        self.upload("flat.png", flat_png())
        original = next((self.root / "ACME" / "P-1" / "workspace" / "02-engineering" / "layout" / "L0" / "src").glob("original.*"))
        original.write_bytes(b"\x89PNG not an image")
        r = self.c.post(f"{self.base}/L0/architecture", json={})
        self.assertEqual(r.status_code, 422)
        self.assertIn("image cannot be read", r.json()["detail"]["errors"]["file"])

    def test_a_pdf_underlay_is_the_page_the_engine_renders(self):
        pdf = Path(self.root / "p.pdf")
        import pypdfium2
        doc = pypdfium2.PdfDocument.new()
        doc.new_page(200, 100)
        doc.save(str(pdf))
        r = self.upload("plan.pdf", pdf.read_bytes())
        self.assertEqual(r["underlay"]["kind"], "png")


if __name__ == "__main__":
    unittest.main()
