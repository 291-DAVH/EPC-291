"""The deliverable service: an SVG whose elements say what they are becomes a DXF with the layers of the catalog, and several sheets become a package with an index."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import ezdxf  # noqa: E402

from epc_dxf import deliverable, package, roles  # noqa: E402

SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="100mm" viewBox="0 0 200 100">
<rect id="papel" x="0" y="0" width="200" height="100" fill="#fff"/>
<g id="recuadro"><rect x="5" y="5" width="190" height="90" fill="none" stroke="#000" stroke-width="0.5"/></g>
<g id="dibujo">
<line data-layer="sld.diagram" x1="20" y1="20" x2="80" y2="20" stroke="#0000ff" stroke-width="0.25"/>
<line data-layer="sld.text" x1="20" y1="30" x2="80" y2="30" stroke="#000000" stroke-width="0.25"/>
<text data-layer="sld.text" x="20" y="40" font-size="2.8" fill="#000000">hola</text>
</g></svg>"""


class TestDeliverable(unittest.TestCase):
    def sheet(self, tmp: Path, name="HOJA") -> Path:
        svg = tmp / f"{name}.svg"
        svg.write_text(roles.tag_iram_sheet(SVG), encoding="utf-8")
        return svg

    def test_every_entity_goes_to_the_layer_of_its_role(self):
        with tempfile.TemporaryDirectory() as t:
            done = deliverable.convert(self.sheet(Path(t)))
            self.assertTrue(done["dxf"])
            layers = done["layers"]
            self.assertEqual(layers.get("291-E-DIAGRAMA"), 1)
            self.assertEqual(layers.get("291-A-LAMINA", 0) >= 1, True)               # the frame group of the IRAM template
            self.assertGreaterEqual(layers.get("291-E-TEXTOS", 0), 2)                # an annotation line and its text
            self.assertFalse(list(Path(t).glob("*_trazos.*")))                       # nothing of the work in progress is left behind

    def test_the_catalog_renames_the_layers_of_the_deliverable(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "layers.json"
            f.write_text(json.dumps({"layers": {"sld.diagram": {"name": "MI-DIAGRAMA", "color": 3}}}), encoding="utf-8")
            done = deliverable.convert(self.sheet(Path(t)), layers_file=f)
            self.assertIn("MI-DIAGRAMA", done["layers"])
            self.assertNotIn("291-E-DIAGRAMA", done["layers"])
            self.assertEqual(ezdxf.readfile(done["dxf"]).layers.get("MI-DIAGRAMA").color, 3)

    def test_the_weight_of_the_layer_governs_when_the_catalog_sets_one_and_the_stroke_when_it_does_not(self):
        with tempfile.TemporaryDirectory() as t:
            plain = deliverable.convert(self.sheet(Path(t), "A"))["dxf"]
            f = Path(t) / "layers.json"
            f.write_text(json.dumps({"layers": {"sld.diagram": {"lineweight": 0.5}}}), encoding="utf-8")
            fixed = deliverable.convert(self.sheet(Path(t), "B"), layers_file=f)["dxf"]

            def weights(path):
                doc = ezdxf.readfile(path)
                return {e.dxf.layer: e.dxf.get("lineweight", -1) for e in doc.modelspace() if e.dxftype() == "LINE"}
            self.assertEqual(weights(plain)["291-E-DIAGRAMA"], 25)                       # the stroke of the SVG (0.25 mm)
            self.assertEqual(weights(fixed)["291-E-DIAGRAMA"], -1)                      # by layer: the catalog says 0.5 mm
            self.assertEqual(ezdxf.readfile(fixed).layers.get("291-E-DIAGRAMA").dxf.lineweight, 50)
            self.assertEqual(weights(fixed)["291-E-TEXTOS"], 25)                        # a layer without a weight in the catalog keeps the strokes

    def test_the_sheet_template_is_marked_once(self):
        tagged = roles.tag_iram_sheet(SVG)
        self.assertIn('<g id="recuadro" data-layer="sld.sheet">', tagged)
        self.assertEqual(roles.tag_iram_sheet(tagged), tagged)

    def test_a_package_converts_every_sheet_and_writes_an_index_without_dates_or_dxf_hashes(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            sheets = [{"svg": self.sheet(tmp, "H1")}, {"svg": self.sheet(tmp, "H2")}]
            index = package.deliver(sheets, tmp / "out", "PAQ")
            self.assertEqual([s["sheet"] for s in index["sheets"]], ["H1", "H2"])
            self.assertTrue((tmp / "out" / "H1.dxf").is_file() and (tmp / "out" / "PAQ_entregable.json").is_file())
            self.assertEqual(index["sheets"][0]["layers"]["291-E-DIAGRAMA"], {"entities": 1, "role": "sld.diagram"})
            again = package.deliver(sheets, tmp / "out", "PAQ")
            self.assertEqual(again, index)                                              # the same drawing gives the same index
            self.assertNotIn("dxf_sha256", json.dumps(index))


if __name__ == "__main__":
    unittest.main()


class TestDraftDxf(unittest.TestCase):
    """A drawing made straight as DXF (the plan) hands over a draft whose layers are roles; the service gives them their name and look."""

    def draft(self):
        doc = ezdxf.new("R2018", setup=True)
        doc.layers.add("plan.ELEC-LUM")
        doc.layers.add("plan.PLAN-TAG")
        blk = doc.blocks.new("LUM")
        blk.add_circle((0, 0), 1)
        blk.add_attdef("TAG", (0, 0), height=1)
        doc.modelspace().add_blockref("LUM", (5, 5), dxfattribs={"layer": "plan.ELEC-LUM"}).add_auto_attribs({"TAG": "LU-001"})
        doc.modelspace().add_text("LU-001", dxfattribs={"layer": "plan.PLAN-TAG"})
        return doc

    def test_the_roles_become_the_layers_of_the_catalog_and_the_entities_follow(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "layers.json"
            f.write_text(json.dumps({"layers": {"plan.ELEC-LUM": {"name": "LUMINARIAS", "color": 3}}}), encoding="utf-8")
            done = deliverable.finish_draft(self.draft(), Path(t) / "plan.dxf", f)
            doc = ezdxf.readfile(done["dxf"])
            names = {lay.dxf.name for lay in doc.layers}
            self.assertTrue({"LUMINARIAS", "PLAN-TAG"} <= names)
            self.assertFalse({"plan.ELEC-LUM", "plan.PLAN-TAG"} & names)                              # no draft layer is left
            insert = next(e for e in doc.modelspace() if e.dxftype() == "INSERT")
            self.assertEqual((insert.dxf.layer, insert.attribs[0].dxf.layer, doc.layers.get("LUMINARIAS").color), ("LUMINARIAS", "LUMINARIAS", 3))
            self.assertEqual((done["layers"], done["blocks"]), ({"LUMINARIAS": 1, "PLAN-TAG": 1}, 1))

    def test_the_index_of_a_native_drawing_lists_its_layers_and_roles(self):
        with tempfile.TemporaryDirectory() as t:
            done = deliverable.finish_draft(self.draft(), Path(t) / "plan.dxf")
            index = package.describe_dxf([done["dxf"]], Path(t), "PLAN")
            sheet = index["sheets"][0]
            self.assertEqual((sheet["svg"], sheet["blocks"], sheet["layers"]["ELEC-LUM"]), (None, 1, {"entities": 1, "role": "plan.ELEC-LUM"}))
            self.assertTrue((Path(t) / "PLAN_entregable.json").is_file())
