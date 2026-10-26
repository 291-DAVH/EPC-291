import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from epc_symbols import KINDS, library_dir  # noqa: E402


def symbol_file(folder: Path, sid: str):
    """Symbols are named <id>.svg (old) or 291_E_LV_SLD_IEC60617_<id without lv_>.svg (library >= 0.4.14)."""
    for name in (sid + ".svg", f"291_E_LV_SLD_IEC60617_{sid[3:] if sid.startswith('lv_') else sid}.svg"):
        if (folder / name).exists():
            return folder / name
    return None


class TestSymbolLibrary(unittest.TestCase):
    def test_main_libraries_have_a_catalog(self):
        for k in ("sld-lv-symbol", "sld-mv-symbol", "mld-lv-symbol"):
            self.assertTrue((library_dir(k) / "_catalog.json").exists(), k)

    def test_every_sld_lv_catalog_id_resolves_to_a_file(self):
        folder = library_dir("sld-lv-symbol")
        cat = json.loads((folder / "_catalog.json").read_text(encoding="utf-8-sig"))["symbols"]
        missing = [s["id"] for s in cat if symbol_file(folder, s["id"]) is None]
        # Known data issue in iec-symbols 0.4.16: the catalog lists lv_acb_basic but the file is named ..._acb.svg.
        # Fix the library, then remove this allowance.
        self.assertEqual([m for m in missing if m != "lv_acb_basic"], [])

    def test_unknown_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            library_dir("nope")


if __name__ == "__main__":
    unittest.main()
