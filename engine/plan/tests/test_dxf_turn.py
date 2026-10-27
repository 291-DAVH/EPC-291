"""A symbol turned in the editor is turned in the DXF."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import ezdxf   # noqa: E402
from epc_plan import core, dxfout   # noqa: E402


def drawing(attrs):
    return {"schema_version": "1.0", "plan": {"id": "T", "level": "L0", "scale": {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}, "origin": [0, 0]}, "discipline": "electrica_BT",
            "nodes": [{"id": "n1", "kind": "LU", "x": 10, "y": 10, "attrs": attrs}, {"id": "n2", "kind": "LU", "x": 50, "y": 10}], "lines": []}


class TestTurn(unittest.TestCase):
    def test_the_rotation_of_a_node_reaches_the_block_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.dxf"
            dxfout.write_dxf(core.process(drawing({"rot_deg": 90})), path)
            inserts = ezdxf.readfile(path).modelspace().query("INSERT")
            self.assertEqual(sorted(i.dxf.rotation for i in inserts), [-90.0, 0.0])


if __name__ == "__main__":
    unittest.main()
