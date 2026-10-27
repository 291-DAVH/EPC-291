"""The catalog of DXF layers: default, overrides by role, checks and what a document gets."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import ezdxf  # noqa: E402

from epc_dxf import layers as L  # noqa: E402


class TestCatalog(unittest.TestCase):
    def test_the_default_catalog_is_valid_and_has_the_diagram_and_plan_roles(self):
        cat = L.load()
        self.assertEqual(L.validate(cat), {})
        self.assertEqual(L.name("sld.diagram", cat), "291-E-DIAGRAMA")
        self.assertTrue({"sld.text", "sld.titleblock", "sld.sheet", "plan.ELEC-LUM", "plan.SAN-CLOACA", "plan.PLAN-TAG"} <= set(cat))

    def test_the_layers_are_grouped_by_discipline_by_the_prefix_of_their_names(self):
        groups = {g["id"]: g for g in L.by_discipline()}
        self.assertEqual(list(groups)[:3], ["arquitectura", "electrica", "hvac"])
        self.assertIn("ELEC-CABLE", [x["name"] for x in groups["electrica"]["layers"]])
        self.assertTrue({"HVAC-DUCTO", "HVAC-EQUIPO"} <= {x["name"] for x in groups["hvac"]["layers"]})
        self.assertTrue({"PCI-ROCIADOR", "PCI-DETECTOR"} <= {x["name"] for x in groups["pci"]["layers"]})
        self.assertEqual(groups["sanitaria"]["profile"], "sanitaria_cloacas")
        self.assertEqual([groups[k]["profile"] for k in ("hvac", "pci", "comunicaciones")], ["hvac", "pci", "comunicaciones"])
        self.assertIsNone(groups["arquitectura"]["profile"])                     # the architecture is the plan the others are drawn over, not a drawing of its own
        self.assertIn("291-E-DIAGRAMA", [x["name"] for x in groups["diagramas"]["layers"]])
        grouped = {x["name"] for g in groups.values() for x in g["layers"]}
        self.assertEqual(grouped, {a["name"] for a in L.load().values()})                       # every layer of the catalog belongs to some discipline

    def test_a_layer_renamed_in_a_file_moves_with_its_prefix_and_a_colour_has_a_hex(self):
        cat = L.load()
        cat["plan.ELEC-CABLE"] = {**cat["plan.ELEC-CABLE"], "name": "HVAC-X"}
        names = {g["id"]: [x["name"] for x in g["layers"]] for g in L.by_discipline(cat)}
        self.assertIn("HVAC-X", names["hvac"])
        self.assertNotIn("HVAC-X", names["electrica"])
        self.assertEqual(L.aci_hex(1), "#ff0000")
        self.assertEqual(L.aci_hex(7), "#000000")

    def test_a_file_overrides_role_by_role_and_field_by_field(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "layers.json"
            f.write_text(json.dumps({"layers": {"sld.diagram": {"name": "DIAGRAMA", "color": 3}, "custom.x": {**L.BLANK, "name": "X"}}}), encoding="utf-8")
            cat = L.load(f)
            self.assertEqual((cat["sld.diagram"]["name"], cat["sld.diagram"]["color"], cat["sld.diagram"]["lineweight"]), ("DIAGRAMA", 3, None))
            self.assertEqual(cat["sld.text"]["name"], "291-E-TEXTOS")
            self.assertIn("custom.x", cat)
            os.environ[L.ENV_VAR] = str(f)                                   # the global file the MASTER edits
            try:
                self.assertEqual(L.name("sld.diagram"), "DIAGRAMA")
            finally:
                del os.environ[L.ENV_VAR]

    def test_validation_names_each_wrong_field(self):
        cat = L.load()
        cat["sld.text"] = {**cat["sld.text"], "name": "291-E-DIAGRAMA", "color": 300, "lineweight": 0.27, "linetype": "WAVY", "on": "yes"}
        cat["sld.sheet"] = {**cat["sld.sheet"], "name": "bad:name"}
        errors = L.validate(cat)
        self.assertEqual({"sld.text.name", "sld.text.color", "sld.text.lineweight", "sld.text.linetype", "sld.text.on", "sld.sheet.name"}, set(errors))
        self.assertIn("already used by sld.diagram", errors["sld.text.name"])

    def test_a_document_gets_the_layer_with_its_attributes(self):
        doc = ezdxf.new("R2018")
        cat = L.load()
        cat["sld.diagram"] = {**cat["sld.diagram"], "color": 3, "lineweight": 0.5, "locked": True, "plot": False}
        self.assertEqual(L.apply(doc, "sld.diagram", cat), "291-E-DIAGRAMA")
        lay = doc.layers.get("291-E-DIAGRAMA")
        self.assertEqual((lay.color, lay.dxf.lineweight, lay.is_locked, lay.dxf.plot), (3, 50, True, 0))

    def test_an_unknown_role_gets_plain_defaults(self):
        self.assertEqual(L.get("plan.NEW-LAYER")["name"], "NEW-LAYER")


if __name__ == "__main__":
    unittest.main()


class TestScopes(unittest.TestCase):
    def test_files_apply_in_order_of_authority_and_a_diff_is_made_against_what_a_level_inherits(self):
        with tempfile.TemporaryDirectory() as t:
            g, c, p = (Path(t) / n for n in ("global.json", "company.json", "project.json"))
            g.write_text(json.dumps({"layers": {"sld.diagram": {"name": "GLOBAL-D", "color": 3}}}), encoding="utf-8")
            c.write_text(json.dumps({"layers": {"sld.diagram": {"color": 4}, "sld.text": {"name": "EMPRESA-T"}}}), encoding="utf-8")
            p.write_text(json.dumps({"layers": {"sld.text": {"color": 6}}}), encoding="utf-8")
            cat = L.load([g, c, p])
            self.assertEqual((cat["sld.diagram"]["name"], cat["sld.diagram"]["color"], cat["sld.text"]["name"], cat["sld.text"]["color"]), ("GLOBAL-D", 4, "EMPRESA-T", 6))
            os.environ[L.ENV_VAR] = os.pathsep.join([str(g), str(c)])                          # the environment may name several files too
            try:
                self.assertEqual(L.load(p)["sld.text"]["color"], 6)
                self.assertEqual(L.name("sld.diagram"), "GLOBAL-D")
            finally:
                del os.environ[L.ENV_VAR]
            inherited = L.load([g, c])
            mine = {r: dict(a) for r, a in inherited.items()}
            mine["sld.text"]["color"] = 9
            self.assertEqual(L.override_of(mine, inherited), {"sld.text": {"color": 9}})
