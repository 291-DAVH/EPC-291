import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src" / "epc_receptacles"
sys.path.insert(0, str(HERE.parent / "src"))

import epc_receptacles  # noqa: E402
from epc_receptacles import catalogue  # noqa: E402
from epc_receptacles.__main__ import main  # noqa: E402

EXAMPLE = HERE.parent / "examples" / "office.json"


def validate(value, schema, path="$"):
    """The part of JSON Schema 2020-12 the two schemas use (type, required, properties, items, enum, minimum), enough to hold the contracts without a dependency."""
    types = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}
    if "enum" in schema:
        assert value in schema["enum"], f"{path}: {value!r} not in {schema['enum']}"
    if "type" in schema:
        ok = isinstance(value, types[schema["type"]]) and not (schema["type"] in ("integer", "number") and isinstance(value, bool))
        assert ok, f"{path}: not a {schema['type']}"
    if isinstance(value, dict):
        for key in schema.get("required", []):
            assert key in value, f"{path}: missing {key}"
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                validate(value[key], sub, f"{path}.{key}")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            validate(item, schema["items"], f"{path}[{i}]")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema:
        assert value >= schema["minimum"], f"{path}: below {schema['minimum']}"


class TestContracts(unittest.TestCase):
    def test_the_example_and_its_result_follow_the_schemas(self):
        doc = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        validate(doc, json.loads((SRC / "schema" / "input.schema.json").read_text(encoding="utf-8")))
        out = epc_receptacles.run(doc).as_dict()
        validate(out, json.loads((SRC / "schema" / "output.schema.json").read_text(encoding="utf-8")))
        self.assertEqual(out["counts"]["rooms"], 4)

    def test_the_same_document_gives_the_same_result(self):
        raw = EXAMPLE.read_bytes()
        self.assertEqual(epc_receptacles.run(raw).as_dict(), epc_receptacles.run(raw).as_dict())

    def test_the_document_may_come_as_dict_text_or_bytes(self):
        doc = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(epc_receptacles.run(doc).as_dict(), epc_receptacles.run(json.dumps(doc)).as_dict())


class TestCatalogue(unittest.TestCase):
    def test_the_factory_list_is_valid_and_both_kinds_are_there(self):
        factory = catalogue.defaults()
        self.assertEqual([p for rid, e in factory.items() for p in catalogue.check(rid, e)], [])
        self.assertEqual({e["kind"] for e in factory.values()}, {"general", "special"})

    def test_a_level_replaces_adds_and_removes(self):
        merged = catalogue.merge([{"tug_2x10_t": {"name": {"es": "a", "en": "a"}, "kind": "general", "power_va": 150}, "mine": {"name": {"es": "m", "en": "m"}}}, {"tug_ip54": {"disabled": True}}])
        self.assertEqual(merged["tug_2x10_t"]["power_va"], 150)
        self.assertIn("mine", merged)
        self.assertNotIn("tug_ip54", merged)

    def test_a_bad_entry_says_what_to_correct(self):
        problems = catalogue.check("x", {"name": {"es": "a"}, "kind": "odd", "power_va": -5})
        self.assertEqual(len(problems), 3)
        self.assertIn("both languages", problems[0])

    def test_as_document_takes_the_name_in_the_language_and_drops_what_the_engine_does_not_read(self):
        doc = catalogue.as_document("t", {"name": {"es": "Toma", "en": "Outlet"}, "illustrative": True, "kind": "general", "power_va": 100}, "es")
        self.assertEqual((doc["id"], doc["name"], "illustrative" in doc), ("t", "Toma", False))


class TestCli(unittest.TestCase):
    def call(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_ok_writes_one_file_inside_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = self.call([str(EXAMPLE), "--out", str(Path(tmp) / "r")])
            self.assertEqual(code, 0, err)
            self.assertEqual([p.name for p in (Path(tmp) / "r").iterdir()], ["office.receptacles.json"])
            self.assertTrue(out.startswith("OK 4 rooms"))

    def test_a_bad_document_exits_1_with_what_to_correct(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text('{"rooms": [{"id": "a", "length_m": 0, "width_m": 1}]}', encoding="utf-8")
            code, _, err = self.call([str(bad), "--out", str(Path(tmp) / "o")])
            self.assertEqual(code, 1)
            self.assertTrue(err.startswith("ERROR ") and "length_m" in err)

    def test_a_missing_file_exits_1(self):
        code, _, err = self.call(["/nowhere/none.json"])
        self.assertEqual((code, err.startswith("ERROR cannot read")), (1, True))


if __name__ == "__main__":
    unittest.main()
