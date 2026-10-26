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
