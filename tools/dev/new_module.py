"""Creates the skeleton of a self-contained module: a folder that can be developed, run and tested on its own (in another chat, on another machine) and handed over by copying it.

  python tools/dev/new_module.py plan                    # -> incoming/plan/
  python tools/dev/new_module.py plan --dest D:\\work     # -> D:\\work\\plan\\
  python tools/dev/new_module.py plan --no-web           # without the React part

The contract every module follows is in docs/modules/MODULE-CONTRACT.md and is copied into the folder as MODULE.md.
"""
import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONTRACT = REPO / "docs" / "modules" / "MODULE-CONTRACT.md"
PROMPT = REPO / "docs" / "modules" / "PROMPT-FOR-A-NEW-CHAT.md"

FILES = {
    "README.md": '''# @NAME@ (module)

What it is: one sentence, written when the module is born. **Read MODULE.md first**: it is the contract this folder follows.

## Run it on its own
```
python -m unittest discover -s tests -t .          # tests, no backend, no network
python -m epc_@PKG@ --demo --out out               # demo with the sample in fixtures/
```
@WEBREADME@
## Layout
```
MODULE.md            the contract (do not edit; it is the same for every module)
SPEC.md              what THIS module does: inputs, outputs, rules, non-goals (edit)
src/epc_@PKG@/       the code (pure Python; no import of the backend)
  core.py            the functions that do the work; deterministic
  jobs.py            long operations as background jobs with a status file
  cli.py             python -m epc_@PKG@ ...
  params.json        every number and every look-and-feel setting (never inline)
schema/              JSON Schemas of what goes in and what comes out
fixtures/            small, synthetic samples and their expected results
tests/               unittest
knowledge/           what the module learned (rules as data, with their source); NO copyrighted files
docs/                decisions taken while building it
```
''',
    "SPEC.md": '''# @NAME@ - what this module does

> Edit this file first. A module without this page is not started.

## Purpose
(one sentence)

## Not in scope
(what it deliberately does NOT do, so that it stays small)

## Input
(documents it receives; each one has a schema in schema/)

## Output
(documents and files it produces; deliverables are DXF and PDF, never SVG)

## Rules it applies
(each rule: statement, source, status pending/approved; they live as data in knowledge/rules.json)

## Open questions
(for the person who integrates it)
''',
    "pyproject.toml": '''[project]
name = "epc-@PKG@"
version = "0.1.0"
description = "@NAME@: self-contained module of the EPC platform"
requires-python = ">=3.10"
dependencies = []          # open-source only; list each with its licence in SPEC.md

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
epc_@PKG@ = ["params.json"]
''',
    "src/epc_@PKG@/__init__.py": '''"""@NAME@: see MODULE.md and SPEC.md."""
__version__ = "0.1.0"
''',
    "src/epc_@PKG@/params.json": '''{
  "schema_version": "1.0",
  "limits": {"max_input_mb": 25, "max_items": 5000},
  "style": {"line_width_mm": 0.25, "font_size_mm": 2.0, "colors": {"line": "#000000", "highlight": "#d62728"}}
}
''',
    "src/epc_@PKG@/core.py": '''"""The work of the module as pure functions: the same input gives the same output; nothing here reads the network, the environment or the backend."""
import json
from pathlib import Path
from typing import Any, Dict

PARAMS = json.loads((Path(__file__).with_name("params.json")).read_text(encoding="utf-8"))


def process(document: Dict[str, Any], params: Dict[str, Any] = PARAMS) -> Dict[str, Any]:
    """Replace this body. Takes the input document (see schema/input.schema.json) and returns the output document (schema/output.schema.json)."""
    return {"schema_version": "1.0", "items": len(document.get("items", [])), "warnings": []}
''',
    "src/epc_@PKG@/jobs.py": '''"""Long operations run in the background: the caller starts a job and reads its status file; it never waits for the work."""
import json
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict

from epc_@PKG@ import core


def _write(status_file: Path, state: Dict[str, Any]) -> None:
    status_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = status_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(status_file)                                   # a reader never sees half a file


def run(document: Dict[str, Any], out_dir: Path, progress: Callable[[float, str], None] = lambda p, m: None) -> Dict[str, Any]:
    """Do the work now, in this thread, reporting progress. Returns the output document and writes it to out_dir/result.json."""
    progress(0.0, "start")
    result = core.process(document)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    progress(1.0, "done")
    return result


def start(document: Dict[str, Any], out_dir: Path) -> threading.Thread:
    """Same work in the background. Status: out_dir/status.json {state: running|done|failed, progress 0..1, message, started, finished, error}."""
    status_file = out_dir / "status.json"
    state: Dict[str, Any] = {"state": "running", "progress": 0.0, "message": "", "started": time.time()}
    _write(status_file, state)

    def report(p: float, m: str) -> None:
        state.update(progress=p, message=m)
        _write(status_file, state)

    def work() -> None:
        try:
            run(document, out_dir, report)
            state.update(state="done", progress=1.0)
        except Exception as e:                                   # noqa: BLE001 - reported through the status, never raised into the caller
            state.update(state="failed", error=str(e)[:500])
        state["finished"] = time.time()
        _write(status_file, state)

    t = threading.Thread(target=work, daemon=True)
    t.start()
    return t
''',
    "src/epc_@PKG@/cli.py": '''"""python -m epc_@PKG@ --demo --out DIR   |   python -m epc_@PKG@ --input FILE.json --out DIR"""
import argparse
import json
import sys
from pathlib import Path

from epc_@PKG@ import jobs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="epc_@PKG@")
    ap.add_argument("--input", help="input document (JSON)")
    ap.add_argument("--demo", action="store_true", help="use the sample of fixtures/")
    ap.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    if a.demo:
        src = Path(__file__).resolve().parents[2] / "fixtures" / "input.json"
    elif a.input:
        src = Path(a.input)
    else:
        ap.error("give --demo or --input")
    result = jobs.run(json.loads(src.read_text(encoding="utf-8")), Path(a.out))
    print(f"OK {Path(a.out) / 'result.json'} ({result['items']} items)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
    "src/epc_@PKG@/__main__.py": '''import sys

from epc_@PKG@.cli import main

sys.exit(main())
''',
    "schema/input.schema.json": '''{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "@NAME@ input",
  "type": "object",
  "required": ["schema_version"],
  "properties": {"schema_version": {"const": "1.0"}, "items": {"type": "array"}}
}
''',
    "schema/output.schema.json": '''{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "@NAME@ output",
  "type": "object",
  "required": ["schema_version", "warnings"],
  "properties": {"schema_version": {"const": "1.0"}, "items": {"type": "integer"}, "warnings": {"type": "array", "items": {"type": "string"}}}
}
''',
    "fixtures/input.json": '''{"schema_version": "1.0", "items": [{"id": "A"}, {"id": "B"}]}
''',
    "fixtures/expected_output.json": '''{"schema_version": "1.0", "items": 2, "warnings": []}
''',
    "tests/__init__.py": "",
    "tests/test_core.py": '''"""Runs on its own: python -m unittest discover -s tests -t .   (needs only the folder, no backend, no network)"""
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from epc_@PKG@ import core, jobs   # noqa: E402


def load(name):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


class TestCore(unittest.TestCase):
    def test_the_sample_gives_the_expected_result(self):
        self.assertEqual(core.process(load("input.json")), load("expected_output.json"))

    def test_it_is_deterministic(self):
        self.assertEqual(core.process(load("input.json")), core.process(load("input.json")))

    def test_the_output_has_the_fields_of_its_schema(self):
        schema = json.loads((ROOT / "schema" / "output.schema.json").read_text(encoding="utf-8"))
        out = core.process(load("input.json"))
        for k in schema["required"]:
            self.assertIn(k, out)

    def test_nothing_imports_the_backend(self):
        for f in (ROOT / "src").rglob("*.py"):
            text = f.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"^\\s*(from|import)\\s+epc\\b", f.name)


class TestJobs(unittest.TestCase):
    def test_a_job_reports_its_status_and_ends(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            jobs.start(load("input.json"), out).join(10)
            st = json.loads((out / "status.json").read_text(encoding="utf-8"))
            self.assertEqual((st["state"], st["progress"]), ("done", 1.0))
            self.assertTrue((out / "result.json").exists())


if __name__ == "__main__":
    unittest.main()
''',
    "knowledge/README.md": '''# What the module learns

Rules the module applies are kept here **as data**, each with where it comes from and whether the norm reviewer approved it (the same way the platform keeps norm data):

```
rules.json   [{"id": "...", "statement": "...", "value": ..., "unit": "...", "source": "book / standard, edition, section", "status": "pending|approved|rejected"}]
```

- The books, PDFs and drawings you study **never go in this folder** (copyright): they stay in `local/dev-knowledge/` of the repository, which git ignores.
- What goes here is what was **extracted** from them: the rule, its value and its source.
- Nothing in `core.py` carries a rule inline: it reads `rules.json`.
''',
    "knowledge/rules.json": '''{"schema_version": "1.0", "rules": []}
''',
    "docs/README.md": '''# Decisions

One short file per decision taken while building the module (what was decided, why, what it costs). They travel with the folder.
''',
}

WEB_FILES = {
    "web/package.json": '''{
  "name": "epc-@PKG@-demo",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {"dev": "vite", "typecheck": "tsc --noEmit"},
  "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"},
  "devDependencies": {"@types/react": "^18.3.3", "@types/react-dom": "^18.3.0", "@vitejs/plugin-react": "^4.3.1", "typescript": "^5.5.4", "vite": "^5.4.0"}
}
''',
    "web/index.html": '''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>@NAME@ (demo)</title></head>
<body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>
''',
    "web/vite.config.ts": '''import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({ plugins: [react()], server: { port: 5190 } });
''',
    "web/tsconfig.json": '''{"compilerOptions": {"target": "ES2020", "lib": ["ES2020", "DOM"], "jsx": "react-jsx", "module": "ESNext", "moduleResolution": "Bundler", "strict": true, "noEmit": true, "skipLibCheck": true}, "include": ["src"]}
''',
    "web/src/main.tsx": '''import { createRoot } from "react-dom/client";
import Component from "./Component";
import sample from "../../fixtures/input.json";

createRoot(document.getElementById("root")!).render(<Component document={sample} />);
''',
    "web/src/Component.tsx": '''/** The screen of the module. It takes its data as props and reports changes through callbacks: it never calls the backend itself (the integration does).
 *  Text goes through a `t()` function with Spanish and English entries; here a minimal one so the demo runs alone. */
const TEXT: Record<string, string> = { title: "@NAME@", items: "elementos" };
const t = (k: string) => TEXT[k] ?? k;

export interface Props { document: { items?: unknown[] }; onChange?: (next: unknown) => void }

export default function Component({ document }: Props) {
  return (
    <div style={{ fontFamily: "system-ui", padding: 16 }}>
      <h1>{t("title")}</h1>
      <p>{document.items?.length ?? 0} {t("items")}</p>
    </div>
  );
}
''',
}

WEBREADME = '''
Screen on its own (needs Node):
```
cd web && npm install && npm run dev        # http://localhost:5190
```
'''


def render(text: str, name: str, pkg: str, web: bool) -> str:
    return text.replace("@NAME@", name).replace("@PKG@", pkg).replace("@WEBREADME@", WEBREADME if web else "")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("name", help="module name: letters, digits and dashes (it becomes the Python package epc_<name>)")
    ap.add_argument("--dest", default=str(REPO / "incoming"), help="folder that will hold the module folder")
    ap.add_argument("--no-web", action="store_true", help="a module without a screen")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,30}", a.name):
        print("the name must be lowercase letters, digits and dashes, starting with a letter")
        return 2
    pkg = a.name.replace("-", "_")
    target = Path(a.dest) / a.name
    if target.exists():
        print(f"{target} already exists: nothing was touched")
        return 1
    files = dict(FILES)
    if not a.no_web:
        files.update(WEB_FILES)
    for rel, text in files.items():
        p = target / render(rel, a.name, pkg, not a.no_web)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(render(text, a.name, pkg, not a.no_web).encode("utf-8"))
    if CONTRACT.is_file():
        (target / "MODULE.md").write_bytes(CONTRACT.read_bytes())
    if PROMPT.is_file():
        (target / "PROMPT-FOR-A-NEW-CHAT.md").write_bytes(render(PROMPT.read_text(encoding="utf-8"), a.name, pkg, not a.no_web).encode("utf-8"))
    print(f"module created: {target}")
    print("next: edit SPEC.md, then  python -m unittest discover -s tests -t .  inside the folder")
    return 0


if __name__ == "__main__":
    sys.exit(main())
