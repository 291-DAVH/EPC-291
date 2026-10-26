"""The layers a delivered DXF has are the ones the catalog says: what the MASTER changes in the global file reaches the single-line and the multi-line."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import characterization as C   # noqa: E402

import ezdxf   # noqa: E402


class TestLayerOverride(unittest.TestCase):
    def test_the_global_file_renames_and_recolours_the_diagram_layers(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "layers.json"
            f.write_text(json.dumps({"layers": {"sld.diagram": {"name": "DIAGRAMA-X", "color": 3}, "sld.text": {"name": "TEXTOS-X"}}}), encoding="utf-8")
            os.environ["EPC_LAYERS_JSON"] = str(f)
            try:
                data, criteria, maxl, diagrams = C.CASES["small_sld_mld"]
                summary = C.B.design(data, Path(t) / "work", "T1", criteria, None, maxl, diagrams)
            finally:
                del os.environ["EPC_LAYERS_JSON"]
            self.assertTrue(summary["ok"], summary.get("error"))
            for name in ("SLD_T1.dxf", "MLD_T1.dxf"):
                doc = ezdxf.readfile(str(Path(t) / "work" / "out" / name))
                names = {layer.dxf.name for layer in doc.layers}
                self.assertTrue({"DIAGRAMA-X", "TEXTOS-X"} <= names, (name, sorted(names)))
                self.assertNotIn("291-E-DIAGRAMA", names)
                self.assertEqual(doc.layers.get("DIAGRAMA-X").color, 3)
                used = {e.dxf.layer for e in doc.modelspace()}
                self.assertIn("DIAGRAMA-X", used)


if __name__ == "__main__":
    unittest.main()
