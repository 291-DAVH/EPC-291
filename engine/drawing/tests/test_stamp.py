"""DXF stamping: the delivered copy carries its issue data; the master stays untouched."""
import tempfile
import unittest
from pathlib import Path

import ezdxf


class TestStamp(unittest.TestCase):
    def test_stamp_adds_properties_and_leaves_the_master(self):
        from epc_drawing.export.stamp import read_stamp, sha256_of, stamp_dxf
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "m.dxf", Path(tmp) / "out" / "s.dxf"
            doc = ezdxf.new("R2010")
            doc.modelspace().add_line((0, 0), (10, 10))
            doc.saveas(src)
            before = sha256_of(src)
            stamp_dxf(src, dst, {"CLIENT_REV": "Rev 00", "TRANSMITTAL": "TR-001"})
            self.assertEqual(sha256_of(src), before)                                   # master untouched
            st = read_stamp(dst)
            self.assertEqual((st["EPC_CLIENT_REV"], st["EPC_TRANSMITTAL"], st["EPC_SOURCE_SHA256"]), ("Rev 00", "TR-001", before))
            stamp_dxf(dst, Path(tmp) / "s2.dxf", {"CLIENT_REV": "Rev 01"})            # re-stamping replaces
            st2 = read_stamp(Path(tmp) / "s2.dxf")
            self.assertEqual(st2["EPC_CLIENT_REV"], "Rev 01")
            self.assertNotIn("EPC_TRANSMITTAL", st2)
            self.assertEqual(len(ezdxf.readfile(str(dst)).modelspace()), 1)             # drawing content preserved


if __name__ == "__main__":
    unittest.main()
