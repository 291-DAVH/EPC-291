"""Architecture rules checked directly on the source (no import-linter needed)."""
import ast
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "epc"
MODULES = SRC / "modules"
INTERNAL = {"api", "service", "repository", "models", "guard"}
MODS = sorted(p.name for p in MODULES.iterdir() if (p / "__init__.py").exists())


def imports(path: Path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module
            for a in node.names:                      # `from epc.modules.x import service`
                yield f"{node.module}.{a.name}"


class TestBoundaries(unittest.TestCase):
    def test_modules_exist(self):
        for m in ("identity", "projects", "knowledge", "management", "deliverables", "intake", "requirements", "admin"):
            self.assertIn(m, MODS)

    def test_every_module_has_public_facade(self):
        for m in MODS:
            self.assertTrue((MODULES / m / "public.py").exists(), m)

    def test_cross_module_imports_use_public_only(self):
        bad = []
        for m in MODS:
            for f in (MODULES / m).rglob("*.py"):
                for imp in imports(f):
                    parts = imp.split(".")
                    if len(parts) >= 4 and parts[:2] == ["epc", "modules"] and parts[2] != m and parts[3] != "public":
                        bad.append(f"{f.relative_to(SRC)} -> {imp}")
        self.assertEqual(bad, [])

    def test_core_and_modules_do_not_import_main(self):
        bad = [f"{f.relative_to(SRC)}" for f in list((SRC / "core").rglob("*.py")) + list(MODULES.rglob("*.py"))
               if any(i == "epc.main" or i.startswith("epc.main.") for i in imports(f))]
        self.assertEqual(bad, [])

    def test_core_does_not_import_modules(self):
        bad = [f"{f.relative_to(SRC)}" for f in (SRC / "core").rglob("*.py") if any(i.startswith("epc.modules") for i in imports(f))]
        self.assertEqual(bad, [])

    def test_layering_inside_a_module(self):
        order = ["api", "service", "repository", "models"]
        bad = []
        for m in MODS:
            for i, layer in enumerate(order):
                f = MODULES / m / f"{layer}.py"
                if not f.exists():
                    continue
                for imp in imports(f):
                    p = imp.split(".")
                    if len(p) >= 4 and p[:3] == ["epc", "modules", m] and p[3] in order and order.index(p[3]) < i:
                        bad.append(f"{m}.{layer} -> {p[3]}")
        self.assertEqual(bad, [])

    def test_engine_does_not_import_backend(self):
        engine = SRC.parents[3] / "engine"
        bad = [str(f.relative_to(engine)) for f in engine.glob("*/src/**/*.py")
               if any(i == "epc" or i.startswith("epc.") for i in imports(f))]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
