#!/usr/bin/env python3
"""Map of who depends on whom, read from the code (stdlib only).

  python tools/build/impact_map.py            write docs/architecture/DEPENDENCIAS.md
  python tools/build/impact_map.py --check    fail if the file differs from what the code gives (the gate runs this)

Units: the engine packages (aea90364, documents, standards, rules, plan and symbols, titleblock, sld, mld and drawing), the modules
of the backend and the plugins. An edge is an import or a reference to an engine module by name (a subprocess `-m epc_drawing.export.pdf`). Nothing here is declared by hand:
if the code changes, the map changes, and the gate asks for the file to be regenerated.
"""
import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Set

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "docs" / "architecture" / "DEPENDENCIAS.md"
ENGINE_PKGS = {"epc_aea90364": "aea90364", "epc_documents": "documents", "epc_standards": "standards", "epc_rules": "rules", "epc_plan": "plan", "epc_symbols": "symbols", "epc_dxf": "dxf",
               "epc_titleblock": "titleblock", "epc_sld": "sld", "epc_mld": "mld", "epc_drawing": "drawing", "epc_arch": "arch"}
ENGINE_ROOTS = {a: f"engine/{a}/src/epc_{a}" for a in ENGINE_PKGS.values()}
PYPROJECT = {a: f"engine/{a}" for a in ENGINE_PKGS.values()}
NAME_REF = re.compile(r"\bepc_(?:aea90364|documents|standards|rules|plan|symbols|dxf|titleblock|sld|mld|drawing|arch)(?:\.[a-z_]+)*")
STD = set(sys.stdlib_module_names)
IGNORED_THIRD_PARTY = {"epc", "tests", "conftest", "pytest"}


def unit_of_module(dotted: str) -> str:
    """The unit a dotted module name belongs to (engine package, backend module) or '' when it is neither."""
    parts = dotted.split(".")
    if parts[0] in ENGINE_PKGS:
        return ENGINE_PKGS[parts[0]] if parts[0] != "epc_drawing" or len(parts) > 1 else ""        # naming epc_drawing alone says nothing about what is used
    if parts[0] == "epc" and len(parts) > 1:
        return f"backend.{parts[2]}" if parts[1] == "modules" and len(parts) > 2 else "backend.core" if parts[1] == "core" else "backend.app"
    return ""


def unit_of_file(path: Path) -> str:
    rel = path.relative_to(REPO).as_posix()
    for base, root in ENGINE_ROOTS.items():
        if rel.startswith(root + "/"):
            return base
    if rel.startswith("backend/src/epc/modules/"):
        return "backend." + rel.split("/")[4]
    return "backend.core" if rel.startswith("backend/src/epc/core/") else "backend.app"


def package_of(path: Path) -> List[str]:
    rel = path.relative_to(REPO).as_posix()
    if rel.startswith("backend/src/"):
        return rel[len("backend/src/"):].rsplit("/", 1)[0].split("/")
    return rel.split("/src/", 1)[1].rsplit("/", 1)[0].split("/") if "/src/" in rel else []


def imported_modules(tree: ast.AST, pkg: List[str]) -> Iterable[str]:
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            yield from (a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            base = ".".join(pkg[: len(pkg) - n.level + 1]) if n.level else ""
            module = ".".join(x for x in (base, n.module or "") if x)
            yield module
            yield from (f"{module}.{a.name}" for a in n.names)


def string_refs(tree: ast.AST) -> Iterable[str]:
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            yield from NAME_REF.findall(n.value)


def python_files(root: Path) -> Iterable[Path]:
    return (f for f in root.rglob("*.py") if not ({"__pycache__", "tests", ".venv"} & set(f.parts)) and ".egg-info" not in str(f))


def scan() -> tuple:
    """(edges, third_party): edges[unit] = units it uses; third_party[unit] = external packages it imports."""
    edges: Dict[str, Set[str]] = defaultdict(set)
    third: Dict[str, Set[str]] = defaultdict(set)
    roots = [REPO / r for r in ENGINE_ROOTS.values()] + [REPO / "backend" / "src" / "epc"]
    for root in sorted(set(roots)):
        for f in python_files(root):
            unit = unit_of_file(f)
            try:
                tree = ast.parse(f.read_text(encoding="utf-8-sig"))
            except SyntaxError:
                continue
            for mod in list(imported_modules(tree, package_of(f))) + list(string_refs(tree)):
                target = unit_of_module(mod)
                if target and target != unit:
                    edges[unit].add(target)
                elif not target and mod.split(".")[0] not in STD | IGNORED_THIRD_PARTY | set(ENGINE_PKGS) and mod.split(".")[0]:
                    third[unit].add(mod.split(".")[0])
    return edges, third


def engine_units() -> List[str]:
    """Every engine package, whether or not anything uses it."""
    return sorted(ENGINE_PKGS.values())


def dependents(edges: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = defaultdict(set)
    for u, ts in edges.items():
        for t in ts:
            out[t].add(u)
    return out


def closure(start: str, graph: Dict[str, Set[str]]) -> Set[str]:
    seen: Set[str] = set()
    todo = [start]
    while todo:
        for nxt in graph.get(todo.pop(), ()):
            if nxt not in seen and nxt != start:
                seen.add(nxt)
                todo.append(nxt)
    return seen


IMPORT_TO_DIST = {"docx": "python-docx", "yaml": "pyyaml", "PIL": "pillow", "cv2": "opencv-python"}


def _dist_name(requirement: str) -> str:
    return re.split(r"[<>=~!\[; ]", requirement.strip())[0].lower().replace("_", "-")


def project_requirements(unit: str) -> tuple:
    """(required, optional) distribution names of the engine package, as written in its pyproject.toml."""
    import tomllib
    f = REPO / PYPROJECT[unit] / "pyproject.toml"
    project = tomllib.loads(f.read_text(encoding="utf-8")).get("project", {}) if f.exists() else {}
    required = {_dist_name(r) for r in project.get("dependencies", [])}
    optional = {_dist_name(r) for group in project.get("optional-dependencies", {}).values() for r in group}
    return required, optional


def declared_dependencies(unit: str) -> Set[str]:
    required, optional = project_requirements(unit)
    return required | optional


def plugins() -> Dict[str, dict]:
    out = {}
    for f in sorted((REPO / "claude" / "plugins").glob("*/plugin.json")):
        m = json.loads(f.read_text(encoding="utf-8"))
        out[m["id"]] = m
    return out


def cell(items: Iterable[str]) -> str:
    items = sorted(items)
    return ", ".join(f"`{i}`" for i in items) if items else "—"


def render() -> str:
    edges, third = scan()
    used_by = dependents(edges)
    units = engine_units()
    backend_units = sorted(u for u in set(edges) | set(used_by) if u.startswith("backend."))
    L = ["# Dependencias e impacto", "",
         "> Archivo generado por `python tools/build/impact_map.py` a partir del código (importaciones y referencias a módulos del motor). No se edita a mano: el gate "
         "avisa si quedó desactualizado.", "",
         "Cómo leerlo: **Usa** = de qué depende la unidad; **Lo usan** = quién se rompe o cambia si esta unidad cambia; **Impacto** = todo lo que alcanza, directa o indirectamente.", "",
         "## Motores", "", "| Unidad | Usa | Lo usan | Impacto si la modificas |", "|---|---|---|---|"]
    for u in units:
        L.append(f"| `{u}` | {cell(edges.get(u, ()))} | {cell(used_by.get(u, ()))} | {cell(closure(u, used_by))} |")
    L += ["", "## Módulos del backend", "", "| Módulo | Usa | Lo usan |", "|---|---|---|"]
    for u in backend_units:
        L.append(f"| `{u}` | {cell(edges.get(u, ()))} | {cell(used_by.get(u, ()))} |")
    L += ["", "## Paquetes externos por unidad del motor", "", "Lo declarado en `pyproject.toml` frente a lo que el código importa de verdad.", "",
          "| Unidad | Importa | Declarado | Falta declarar |", "|---|---|---|---|"]
    for u in units:
        imported = {IMPORT_TO_DIST.get(x, x).lower().replace("_", "-") for x in third.get(u, ())}
        declared = declared_dependencies(u)
        L.append(f"| `{u}` | {cell(imported)} | {cell(declared)} | {cell(imported - declared)} |")
    L += ["", "## Plugins", "", "| Plugin | Empaqueta (motor) | Requiere (plugins) | Lo requieren |", "|---|---|---|---|"]
    ps = plugins()
    required_by: Dict[str, Set[str]] = defaultdict(set)
    for pid, m in ps.items():
        for dep in m.get("requires", {}):
            required_by[dep].add(pid)
    for pid, m in ps.items():
        L.append(f"| `{pid}` | {cell(m.get('engine', []))} | {cell(m.get('requires', {}))} | {cell(required_by.get(pid, ()))} |")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = render()
    if a.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
            print("ERROR: docs/architecture/DEPENDENCIAS.md is out of date: run `python tools/build/impact_map.py` and commit it")
            return 1
        print("DEPENDENCIAS.md up to date")
        return 0
    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
