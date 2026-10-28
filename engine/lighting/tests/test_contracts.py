"""Rules every EPC-291 engine keeps: isolation, data as data, schemas that match what the engine does."""
import json
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "src" / "epc_lighting"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting import run  # noqa: E402
import helpers  # noqa: E402

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

IMPORT = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][\w]*)", re.M)


class TestIsolation(unittest.TestCase):
    def test_no_import_of_the_backend_the_web_or_a_sibling_engine(self):
        allowed_third_party = set(sys.stdlib_module_names) | {"epc_lighting"}
        for path in SRC.rglob("*.py"):
            for module in IMPORT.findall(path.read_text(encoding="utf-8")):
                self.assertIn(module, allowed_third_party, f"{path.name} imports {module}")

    def test_pyproject_declares_no_dependency(self):
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("dependencies = []", text)
        self.assertIn('name = "epc-lighting"', text)

    def test_importing_does_not_write_anything(self):
        import importlib
        before = sorted(p.name for p in ROOT.iterdir())
        importlib.reload(sys.modules["epc_lighting"])
        self.assertEqual(sorted(p.name for p in ROOT.iterdir()), before)

    def test_no_print_outside_the_cli(self):
        for path in SRC.rglob("*.py"):
            if path.name != "__main__.py":
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"^\s*print\(", path.name)


class TestDataIsData(unittest.TestCase):
    def test_every_data_file_is_json_with_a_schema_version(self):
        files = list((SRC / "data").glob("*.json")) + [SRC / "params.json"]
        self.assertGreaterEqual(len(files), 7)
        for path in files:
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], "1.0", path.name)

    def test_catalogue_labels_come_in_both_languages(self):
        for name in ("levels", "reflectances", "lighting_systems", "spacing", "maintenance"):
            text = (SRC / "data" / f"{name}.json").read_text(encoding="utf-8")
            self.assertEqual(text.count('"es"'), text.count('"en"'), name)

    def test_no_two_data_files_are_identical(self):
        contents = [p.read_bytes() for p in (SRC / "data").glob("*.json")]
        self.assertEqual(len(contents), len(set(contents)))

    def test_package_data_is_declared(self):
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        for pattern in ("params.json", "data/*.json", "schema/*.json"):
            self.assertIn(pattern, text)


@unittest.skipIf(jsonschema is None, "jsonschema is not installed")
class TestSchemas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input_schema = json.loads((SRC / "schema" / "input.schema.json").read_text(encoding="utf-8"))
        cls.output_schema = json.loads((SRC / "schema" / "output.schema.json").read_text(encoding="utf-8"))

    def test_both_schemas_are_valid_2020_12(self):
        jsonschema.Draft202012Validator.check_schema(self.input_schema)
        jsonschema.Draft202012Validator.check_schema(self.output_schema)

    def test_the_example_and_the_helpers_documents_satisfy_the_input_schema(self):
        validator = jsonschema.Draft202012Validator(self.input_schema)
        docs = [json.loads((ROOT / "examples" / "classroom.json").read_text(encoding="utf-8")), helpers.document()]
        for doc in docs:
            self.assertEqual(list(validator.iter_errors(doc)), [])

    def test_the_input_schema_refuses_what_the_engine_refuses(self):
        validator = jsonschema.Draft202012Validator(self.input_schema)
        room = helpers.room_dict()
        del room["target_lux"]
        self.assertTrue(list(validator.iter_errors(helpers.document([room]))))
        self.assertTrue(list(validator.iter_errors(helpers.document([helpers.room_dict(width_m=-1)]))))

    def test_the_output_satisfies_the_output_schema(self):
        validator = jsonschema.Draft202012Validator(self.output_schema)
        example = json.loads((ROOT / "examples" / "classroom.json").read_text(encoding="utf-8"))
        for doc in (example, helpers.document(areas=[{"id": "A", "area_m2": 50, "target_lux": 20, "luminaire": "F1"}])):
            self.assertEqual(list(validator.iter_errors(run(doc).as_dict())), [])


if __name__ == "__main__":
    unittest.main()
