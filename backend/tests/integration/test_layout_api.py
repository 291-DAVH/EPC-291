"""Plan-drawing editor: levels, drawing, what the engine derives, the underlay, the DXF and the permissions."""
import base64
import tempfile
import unittest
from pathlib import Path

import ezdxf
from fastapi.testclient import TestClient

from epc.core.config import settings
from epc.main import create_app
from tests.integration.test_identity_api import PW, PROJECT, Base

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
DRAWING = {
    "discipline": "electrica_BT", "scale": {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}, "origin": [0, 0],
    "nodes": [{"id": "n1", "kind": "TB", "x": 0, "y": 0}, {"id": "n2", "kind": "CM", "x": 200, "y": 0}],
    "lines": [{"id": "l1", "kind": "BN", "points": [[0, 0], [200, 0]], "circuit": "C-01"}],
}


class TestLayout(unittest.TestCase):
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

    def tearDown(self):
        settings.projects_dir, settings.role, settings.data_dir = self._old
        self.tmp.cleanup()

    def test_the_overview_offers_profiles_versions_and_no_levels_yet(self):
        o = self.c.get(self.base).json()
        self.assertEqual(o["levels"], [])
        self.assertEqual({p["id"] for p in o["profiles"]}, {"electrica_BT", "sanitaria_cloacas"})
        self.assertEqual((o["default_dxf_version"], o["dxf_versions"][-1]), ("R2018", "R2018"))

    def test_levels_are_named_from_l0_up_and_down_and_nothing_else_is_accepted(self):
        for level in ("L0", "L1", "L-1"):
            self.assertEqual(self.c.put(f"{self.base}/{level}", json=DRAWING).status_code, 200, level)
        self.assertEqual([x["level"] for x in self.c.get(self.base).json()["levels"]], ["L-1", "L0", "L1"])
        r = self.c.put(f"{self.base}/PB", json=DRAWING)
        self.assertEqual(r.status_code, 422)
        self.assertIn("L0 for the ground level", r.json()["detail"]["errors"]["level"])

    def test_saving_returns_what_the_engine_derived(self):
        v = self.c.put(f"{self.base}/L0", json=DRAWING).json()
        self.assertTrue(v["saved"])
        res = v["result"]
        self.assertTrue(res["ready"])
        self.assertEqual(res["schedule"]["total_length_m"], 20.0)
        self.assertEqual(res["schedule"]["circuit_routes"]["C-01"]["length_m"], 20.0)
        self.assertEqual([n["tag"] for n in res["nodes"]], ["TB-001", "CM-001"])
        again = self.c.get(f"{self.base}/L0").json()
        self.assertEqual(again["drawing"]["lines"][0]["id"], "l1")

    def test_derive_does_not_save_and_waits_for_the_scale(self):
        r = self.c.post(f"{self.base}/L0/derive", json={**DRAWING, "scale": None}).json()
        self.assertEqual(r, {"ready": False, "reason": "scale"})
        self.assertEqual(self.c.post(f"{self.base}/L0/derive", json=DRAWING).json()["schedule"]["total_length_m"], 20.0)
        self.assertFalse(self.c.get(f"{self.base}/L0").json()["saved"])

    def test_what_the_engine_refuses_is_refused_with_its_message(self):
        bad = {**DRAWING, "nodes": [{"id": "n1", "kind": "ZZ", "x": 0, "y": 0}]}
        r = self.c.put(f"{self.base}/L0", json=bad)
        self.assertEqual(r.status_code, 422)
        self.assertIn("does not exist in the discipline", r.json()["detail"]["errors"]["drawing"])
        self.assertFalse(self.c.get(f"{self.base}/L0").json()["saved"])

    def test_the_underlay_is_an_image_and_a_dxf_becomes_a_view_never_a_script(self):
        self.c.put(f"{self.base}/L0", json=DRAWING)
        r = self.c.post(f"{self.base}/L0/underlay", files={"file": ("plano.png", PNG, "image/png")})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["underlay"]["kind"], "png")
        got = self.c.get(f"{self.base}/L0/underlay")
        self.assertEqual((got.status_code, got.headers["content-type"]), (200, "image/png"))
        self.assertIn("sandbox", got.headers["content-security-policy"])
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><script>alert(1)</script></svg>'
        self.assertEqual(self.c.post(f"{self.base}/L0/underlay", files={"file": ("plano.svg", svg, "image/svg+xml")}).json()["underlay"]["kind"], "svg")
        served = self.c.get(f"{self.base}/L0/underlay")
        self.assertEqual(served.headers["content-type"], "image/svg+xml")
        self.assertIn("default-src 'none'", served.headers["content-security-policy"])
        for name, data in (("x.exe", b"MZ..."), ("x.txt", b"hello"), ("x.dxf", b"not a dxf"), ("x.png", b"")):
            self.assertEqual(self.c.post(f"{self.base}/L0/underlay", files={"file": (name, data, "application/octet-stream")}).status_code, 422, name)

    def test_a_pdf_becomes_an_image_underlay(self):
        self.c.put(f"{self.base}/L0", json=DRAWING)
        made = self.c.post(f"{self.base}/L0/generate").json()          # the PDF the platform itself makes is a real, valid PDF
        pdf = self.c.get(f"{self.base}/L0/files/{made['files']['pdf']}").content
        r = self.c.post(f"{self.base}/L0/underlay", files={"file": ("plano.pdf", pdf, "application/pdf")})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["underlay"]["kind"], "png")
        self.assertEqual(self.c.get(f"{self.base}/L0/underlay").content[1:4], b"PNG")
        bad = self.c.post(f"{self.base}/L0/underlay", files={"file": ("roto.pdf", b"%PDF-1.4 broken", "application/pdf")})
        self.assertEqual(bad.status_code, 422)

    def test_generate_writes_a_dxf_in_the_chosen_version_and_it_downloads(self):
        self.c.put(f"{self.base}/L0", json=DRAWING)
        v = self.c.post(f"{self.base}/L0/generate", params={"version": "R2013"}).json()
        self.assertEqual(v["files"]["dxf_version"], "R2013")
        dxf = self.c.get(f"{self.base}/L0/files/{v['files']['dxf']}")
        self.assertEqual(dxf.status_code, 200)
        path = self.root / "dxf_test.dxf"
        path.write_bytes(dxf.content)
        self.assertEqual(ezdxf.readfile(str(path)).dxfversion, "AC1027")
        latest = self.c.post(f"{self.base}/L0/generate").json()
        self.assertEqual(latest["files"]["dxf_version"], "R2018")
        self.assertEqual(self.c.post(f"{self.base}/L0/generate", params={"version": "R14"}).status_code, 422)
        self.assertEqual(self.c.get(f"{self.base}/L0/files/../src/drawing.json").status_code, 404)
        self.assertEqual(self.c.get(f"{self.base}/L0/files/other.dxf").status_code, 404)

    def test_generate_needs_a_drawing_and_a_scale(self):
        self.assertEqual(self.c.post(f"{self.base}/L0/generate").status_code, 404)
        self.c.put(f"{self.base}/L0", json={**DRAWING, "scale": None})
        r = self.c.post(f"{self.base}/L0/generate")
        self.assertEqual(r.status_code, 422)
        self.assertIn("scale", r.json()["detail"]["errors"])

    def test_a_level_can_be_deleted(self):
        self.c.put(f"{self.base}/L1", json=DRAWING)
        self.assertEqual(self.c.delete(f"{self.base}/L1").json()["levels"], [])
        self.assertEqual(self.c.delete(f"{self.base}/L1").status_code, 404)


class TestLayoutPermissions(Base):
    def test_only_the_organization_that_owns_the_project_can_draw_on_it(self):
        staff = self.staff()
        a, slug_a = self.new_org(staff, "Alfa SRL", seats=3, owner="a@alfa.com")
        b, slug_b = self.new_org(staff, "Beta SRL", seats=3, owner="b@beta.com")
        self.assertEqual(a.post("/api/projects", json=PROJECT).status_code, 201)
        base = "/api/projects/ACME/P-1/layout"
        self.assertEqual(a.put(f"{base}/L0", json=DRAWING).status_code, 200)
        self.assertEqual(b.get(f"{base}/L0").status_code, 404)
        self.assertEqual(b.put(f"{base}/L0", json=DRAWING).status_code, 404)
        self.assertEqual(self.client().get(f"{base}/L0").status_code, 401)


if __name__ == "__main__":
    unittest.main()
