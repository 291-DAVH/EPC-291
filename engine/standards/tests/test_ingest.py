import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from epc_standards import promote_rules  # noqa: E402
from epc_standards.validate_rules import validate  # noqa: E402

SOURCE_TEXT = ("La altura minima de montaje de las bandejas portacables sera de dos con dos metros en interiores "
               "siempre que el personal no este calificado para operar sobre la instalacion electrica")


def make_standard(tmp, summary, status="draft", validated=None):
    sdir = Path(tmp) / "standards" / "ZZ" / "TEST-1"
    (sdir / "extracted" / "doc" / "pages").mkdir(parents=True)
    (sdir / "extracted" / "doc" / "pages" / "p0001.txt").write_text("1.2 Bandejas\n" + SOURCE_TEXT, encoding="utf-8")
    (sdir / "draft").mkdir()
    doc = {"schema_version": "1.1", "standard": {"id": "TEST-1", "country": "ZZ", "body": "T", "edition": "1", "domain": "electrical"},
           "source_status": status,
           "rules": [{"id": "tray.h", "clause": "1.2", "topic": "trays", "type": "mandatory", "summary": {"es": summary},
                      "params": {"height_min_m": 2.2}}]}
    if validated:
        doc["validated_by"], doc["validated_on"] = validated, "2026-10-23"
    (sdir / "draft" / "rules.json").write_text(json.dumps(doc), encoding="utf-8")
    return sdir


class TestValidate(unittest.TestCase):
    def test_verbatim_copy_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            sdir = make_standard(t, SOURCE_TEXT)
            _, errs, _ = validate(sdir / "draft" / "rules.json", sdir)
            self.assertTrue(any("verbatim" in e for e in errs))

    def test_paraphrase_is_accepted(self):
        with tempfile.TemporaryDirectory() as t:
            sdir = make_standard(t, "Altura de montaje minima en interiores: 2,2 m (personal no calificado).")
            _, errs, warns = validate(sdir / "draft" / "rules.json", sdir)
            self.assertEqual(errs, [])
            self.assertEqual(warns, [])

    def test_table_row_width_checked(self):
        with tempfile.TemporaryDirectory() as t:
            sdir = make_standard(t, "ok")
            p = sdir / "draft" / "rules.json"
            d = json.loads(p.read_text(encoding="utf-8"))
            d["tables"] = [{"id": "t", "clause": "1", "columns": ["a", "b"], "rows": [[1]]}]
            p.write_text(json.dumps(d), encoding="utf-8")
            _, errs, _ = validate(p, sdir)
            self.assertTrue(any("cells" in e for e in errs))


class TestPromote(unittest.TestCase):
    def run_promote(self, sdir, plat, *extra):
        """`plat` is an engine folder with the jurisdiction ZZ naming the norm engine `zznorm` for the electrical domain (made when it does not exist yet)."""
        if not plat.exists():
            (plat / "jurisdictions" / "ZZ").mkdir(parents=True)
            (plat / "jurisdictions" / "ZZ" / "jurisdiction.json").write_text(json.dumps({"id": "ZZ", "packs": {"electrical": "zznorm"}}), encoding="utf-8")
            (plat / "zznorm" / "src" / "epc_zznorm").mkdir(parents=True)
        old = sys.argv
        sys.argv = ["promote_rules.py", str(sdir), "--engine", str(plat), *extra]
        try:
            return promote_rules.main()
        finally:
            sys.argv = old

    def test_draft_is_blocked(self):
        with tempfile.TemporaryDirectory() as t:
            sdir = make_standard(t, "Altura minima en interiores 2,2 m.")
            plat = Path(t) / "plat"
            self.assertEqual(self.run_promote(sdir, plat), 1)
            self.assertFalse(list(plat.rglob("rules.json")))                                   # nothing is promoted until a person validated it

    def test_verified_is_promoted_and_indexed(self):
        with tempfile.TemporaryDirectory() as t:
            sdir = make_standard(t, "Altura minima en interiores 2,2 m.")
            plat = Path(t) / "plat"
            self.assertEqual(self.run_promote(sdir, plat, "--mark-verified", "Reviewer"), 0)
            dest = plat / "zznorm" / "src" / "epc_zznorm" / "standards" / "TEST-1" / "rules.json"          # inside the norm engine, not in the jurisdiction
            self.assertTrue(dest.exists())
            j = json.loads((plat / "jurisdictions" / "ZZ" / "jurisdiction.json").read_text(encoding="utf-8"))
            self.assertEqual((j["standards"][0]["validated_by"], j["standards"][0]["engine"]), ("Reviewer", "zznorm"))
            self.assertTrue((sdir / "promotion.json").exists())

    def test_a_jurisdiction_without_a_norm_engine_for_the_domain_blocks_the_promotion(self):
        with tempfile.TemporaryDirectory() as t:
            sdir = make_standard(t, "Altura minima en interiores 2,2 m.")
            plat = Path(t) / "plat"
            (plat / "jurisdictions" / "ZZ").mkdir(parents=True)
            (plat / "jurisdictions" / "ZZ" / "jurisdiction.json").write_text(json.dumps({"id": "ZZ", "packs": {}}), encoding="utf-8")
            self.assertEqual(self.run_promote(sdir, plat, "--mark-verified", "Reviewer"), 1)
            self.assertFalse(list(plat.rglob("rules.json")))

    def test_verbatim_blocks_promotion_even_if_marked_verified(self):
        with tempfile.TemporaryDirectory() as t:
            sdir = make_standard(t, SOURCE_TEXT)
            self.assertEqual(self.run_promote(sdir, Path(t) / "plat", "--mark-verified", "Reviewer"), 1)
            self.assertEqual(json.loads((sdir / "draft" / "rules.json").read_text(encoding="utf-8"))["source_status"], "draft")


if __name__ == "__main__":
    unittest.main()
