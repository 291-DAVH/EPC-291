"""Pure validation and editing logic of the SLD, norms and engineering modules, without HTTP. Pinned as it behaves today (messages included)."""
import unittest

from epc.core.errors import Invalid
from epc.modules.engineering import service as eng
from epc.modules.norms import service as norms
from epc.modules.sld import service as sld
from epc.modules.sld.models import Board, Circuit


def data(circuits=None, **board):
    cs = circuits if circuits is not None else [Circuit(tag="C-1", load=10)]
    return {"board": {**Board(name="TGBT", **board).model_dump()}, "circuits": [c.model_dump() if hasattr(c, "model_dump") else c for c in cs]}


def circuit(tag="C-1", **kw):
    return Circuit(tag=tag, **{"load": 10, **kw})


class TestSldValidate(unittest.TestCase):
    def test_a_valid_board_has_no_errors(self):
        self.assertEqual(sld.validate(data()), {})

    def test_board_fields(self):
        e = sld.validate(data(voltage_v=20, system="XX", icc_ka=0, fp_default=2, frequency_hz=45, feeder_length_m=-1))
        self.assertEqual(e, {"board.voltage_v": "between 50 and 1000 V", "board.system": "one of TN-S, TN-C-S, IT", "board.icc_ka": "between 0.1 and 100 kA",
                             "board.fp_default": "between 0.1 and 1", "board.frequency_hz": "50 or 60", "board.feeder_length_m": "must be >= 0"})
        d = data()
        d["board"]["name"] = " "
        self.assertEqual(sld.validate(d), {"board.name": "required"})

    def test_circuit_list_limits(self):
        self.assertEqual(sld.validate(data(circuits=[])), {"circuits": "at least one circuit"})
        many = [circuit(f"C-{i}") for i in range(sld.MAX_CIRCUITS + 1)]
        self.assertEqual(sld.validate(data(circuits=many)), {"circuits": f"up to {sld.MAX_CIRCUITS} circuits"})

    def test_circuit_fields(self):
        bad = circuit("C-1", unit="X", topology="x", phase="2F", kind="x", cable_type="x", length_m=-3, fp=1.5, efficiency=0)
        e = sld.validate(data(circuits=[bad]))
        self.assertEqual(e["circuit:C-1.unit"], "one of A, W, kW, MW, VA, kVA, MVA, HP")
        self.assertEqual(e["circuit:C-1.topology"], "invalid")
        self.assertEqual(e["circuit:C-1.phase"], "one of 3F, 1F, 3F+N")
        self.assertEqual(e["circuit:C-1.kind"], "invalid")
        self.assertEqual(e["circuit:C-1.cable_type"], "invalid")
        self.assertEqual(e["circuit:C-1.length_m"], "must be >= 0")
        self.assertEqual(e["circuit:C-1.fp"], "between 0 and 1")
        self.assertEqual(e["circuit:C-1.efficiency"], "between 0 and 1")

    def test_tags_and_load(self):
        e = sld.validate(data(circuits=[circuit("A"), circuit("A"), circuit("B,C"), circuit(""), circuit("Z", load=None), circuit("Y", load=0)]))
        self.assertEqual(e["circuit:A.tag"], "duplicated")
        self.assertEqual(e["circuit:B,C.tag"], "required, without commas")
        self.assertEqual(e["circuit:4.tag"], "required, without commas")
        self.assertEqual(e["circuit:Z.load"], "required (a parent device may leave it empty)")
        self.assertEqual(e["circuit:Y.load"], "must be > 0")

    def test_a_parent_may_leave_its_load_empty(self):
        self.assertEqual(sld.validate(data(circuits=[circuit("P", load=None), circuit("K", parent_tag="P")])), {})

    def test_parents(self):
        e = sld.validate(data(circuits=[circuit("A", parent_tag="A"), circuit("B", parent_tag="NOPE")]))
        self.assertEqual(e, {"circuit:A.parent_tag": "unknown or self parent", "circuit:B.parent_tag": "unknown or self parent"})

    def test_a_parent_cycle_is_reported_only_when_nothing_else_is_wrong(self):
        e = sld.validate(data(circuits=[circuit("A", parent_tag="B"), circuit("B", parent_tag="A")]))
        self.assertEqual(list(e), ["circuits"])
        self.assertTrue(e["circuits"].startswith("parent cycle at "))

    def test_route_errors_are_prefixed_with_the_circuit(self):
        e = sld.validate(data(circuits=[circuit("R", route=[{"kind": "no_such_kind", "length_m": 5}])]))
        self.assertTrue(any(k.startswith("circuit:R.route.") for k in e), e)

    def test_output_base_name(self):
        self.assertEqual(sld._name("TGBT Planta #1"), "TGBT-Planta-1")
        self.assertEqual(sld._name("   "), "TABLERO")
        self.assertEqual(len(sld._name("x" * 80)), 30)


class TestNormsEdits(unittest.TestCase):
    RULE = {"tema": "Tema", "regla": "Texto", "tipo": "obligatorio", "parametros": {"a": 1}, "aplica_a": ["x"], "fuente": {"norma": "AEA", "clausula": "7.1"}}
    CRITERION_NUM = {"type": "number", "label": {"es": "a", "en": "a"}, "unit": "%", "min": 1, "max": 5, "default": 3}
    CRITERION_CHOICE = {"type": "choice", "label": {"es": "a", "en": "a"}, "unit": "", "options": ["a", "b"], "default": "a"}

    def errors(self, fn, old, patch):
        with self.assertRaises(Invalid) as cm:
            fn(old, patch)
        return cm.exception.detail["errors"]

    def test_edit_rule_accepts_valid_fields_and_merges_the_source(self):
        new = norms._edit_rule(self.RULE, {"tema": " Nuevo ", "tipo": "prohibido", "fuente": {"pagina_impresa": "12"}, "aplica_a": ["y", "z"], "parametros": {"b": 2}})
        self.assertEqual((new["tema"], new["tipo"], new["aplica_a"], new["parametros"]), ("Nuevo", "prohibido", ["y", "z"], {"b": 2}))
        self.assertEqual(new["fuente"], {"norma": "AEA", "clausula": "7.1", "pagina_impresa": "12"})
        self.assertEqual(self.RULE["tipo"], "obligatorio")                    # the original is not touched

    def test_edit_rule_reports_each_field(self):
        e = self.errors(norms._edit_rule, self.RULE, {"tema": "", "regla": "x" * 1001, "tipo": "x", "parametros": [], "aplica_a": [1], "fuente": {"otra": 1}, "extra": 1})
        self.assertEqual(e, {"tema": "text, up to 200 characters", "regla": "text, up to 1000 characters", "tipo": "one of obligatorio, recomendado, prohibido", "parametros": "an object",
                             "aplica_a": "a list of text", "fuente": "only norma, edicion, clausula, pagina_impresa", "extra": "not editable"})

    def test_edit_criterion_valid(self):
        new = norms._edit_criterion(self.CRITERION_NUM, {"min": 0, "max": 10, "default": 7, "unit": "pct", "label": {"es": "b", "en": "b"}})
        self.assertEqual((new["min"], new["max"], new["default"], new["unit"]), (0, 10, 7, "pct"))
        self.assertEqual(norms._edit_criterion(self.CRITERION_CHOICE, {"options": ["a", "c"]})["options"], ["a", "c"])

    def test_edit_criterion_errors(self):
        self.assertEqual(self.errors(norms._edit_criterion, self.CRITERION_NUM, {"default": 9}), {"default": "a number between 1 and 5"})
        self.assertEqual(self.errors(norms._edit_criterion, self.CRITERION_CHOICE, {"options": ["x"]}), {"default": "must be one of the options"})
        self.assertEqual(self.errors(norms._edit_criterion, self.CRITERION_CHOICE, {"min": 1}), {"min": "a number (number criteria only)"})
        self.assertEqual(self.errors(norms._edit_criterion, self.CRITERION_NUM, {"options": ["a"]}), {"options": "a non-empty list without repeated values (choice criteria only)"})
        self.assertEqual(self.errors(norms._edit_criterion, self.CRITERION_NUM, {"label": {"es": "x"}, "unit": 3, "type": "choice"}),
                         {"label": "es and en texts", "unit": "text", "type": "not editable"})

    def test_same_shape(self):
        old = {"a": 1, "b": [1, 2], "c": {"d": "x"}, "e": None}
        self.assertIsNone(norms._same_shape(old, {"a": 2.5, "b": [3, 4], "c": {"d": "y"}, "e": 7}))
        self.assertEqual(norms._same_shape(old, {"a": 1}), "value: the keys cannot change")
        self.assertEqual(norms._same_shape(old, {**old, "b": [1]}), "b: the number of elements cannot change")
        self.assertEqual(norms._same_shape(old, {**old, "a": "x"}), "a: must be a number")
        self.assertEqual(norms._same_shape(old, {**old, "a": True}), "a: must be a number")
        self.assertEqual(norms._same_shape(old, {**old, "c": {"d": 1}}), "c/d: must keep its type")

    def test_diff(self):
        self.assertEqual(norms._diff({"a": 1, "b": [1, 2], "c": {"d": "x"}}, {"a": 2, "b": [1, 3], "c": {"d": "x"}}), [["a", 1, 2], ["b[1]", 2, 3]])
        self.assertEqual(norms._diff({"a": 1}, {"b": 1}), [["a", 1, None], ["b", None, 1]])
        self.assertEqual(len(norms._diff(list(range(500)), list(range(1, 501)))), 200)

    def test_slug_and_hash(self):
        self.assertEqual(norms.sha({"b": 1, "a": 2}), norms.sha({"a": 2, "b": 1}))
        self.assertNotEqual(norms.sha({"a": 1}), norms.sha({"a": 2}))


class TestEngineeringHelpers(unittest.TestCase):
    def test_drawing_kind_from_the_file_name(self):
        for name, kind in (("MLD_T1", "multi_line"), ("Tablero Multifilar", "multi_line"), ("multi-line board", "multi_line"), ("SLD_T1", "single_line"),
                           ("Unifilar", "single_line"), ("single-line", "single_line"), ("Planta baja", "drawing")):
            self.assertEqual(eng._kind(name), kind, name)

    def test_how_a_document_is_shown(self):
        self.assertEqual(eng._doc({"name": "T1_dimensionado", "ext": ".json"}), {"name": "T1", "ext": ".json", "kind": "calculation"})
        self.assertIsNone(eng._doc({"name": "datos", "ext": ".json"}))
        self.assertEqual(eng._doc({"name": "lista", "ext": ".csv"})["kind"], "list")
        self.assertEqual(eng._doc({"name": "lista", "ext": ".xlsx"})["kind"], "list")
        self.assertEqual(eng._doc({"name": "memoria", "ext": ".md"})["kind"], "text")

    def test_criterion_values_are_cleaned_by_type(self):
        num = {"type": "number", "min": 1, "max": 5}
        self.assertEqual(eng._clean(num, "2,5"), 2.5)
        self.assertEqual(eng._clean(num, 3), 3.0)
        self.assertEqual(eng._clean(num, 1.23456), 1.235)
        for bad in ("x", True, 0, 6):
            with self.assertRaises(Invalid):
                eng._clean(num, bad)
        choice = {"type": "choice", "options": [1, "xlpe"]}
        self.assertEqual(eng._clean(choice, "1"), 1)
        self.assertEqual(eng._clean(choice, "xlpe"), "xlpe")
        with self.assertRaises(Invalid) as cm:
            eng._clean(choice, "pvc")
        self.assertEqual(cm.exception.detail["errors"], {"value": "one of 1, xlpe"})
        self.assertEqual(eng._clean({"type": "text"}, "  hola "), "hola")
        for bad in ("", "  ", "x" * 201):
            with self.assertRaises(Invalid):
                eng._clean({"type": "text"}, bad)


if __name__ == "__main__":
    unittest.main()
