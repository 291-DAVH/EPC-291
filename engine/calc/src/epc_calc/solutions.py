"""Standard solutions: which devices make up a circuit, written as data the MASTER edits.

The document (`data/standard-solutions.json`) says, for a kind of circuit, the chain of symbols that builds it: "a lighting circuit takes a differential and a breaker", "a star-delta motor takes a breaker,
three contactors and an overload relay". It does not draw anything and it does not make symbols (the symbol library does): it names the symbols and what goes in their slots; the diagrams lay them out.

Sources, the later one winning solution by solution (a file may carry only the solutions it changes; `null` removes one):
  1. the default document that travels with this package;
  2. the global file the MASTER edits: the path in the environment variable EPC_SOLUTIONS_JSON;
  3. files passed to `load` (later: the company's and the project's own).

A solution: {"name": {...}, "enabled": true, "priority": 10, "when": {...}, "chain": [item...], "disp": "text with {placeholders}"}.
  when     all of: topology [..], kind [..], phase [..], type [..], has_children, motor, in_a {gt, ge, lt, le}, text_contains [..] (description and notes); empty = any circuit.
  chain    items {"symbol", "short", "poles", "label", "slots", "if", "count"}: `poles` is how many conductors the device interrupts (a number, or a map by phase 1F/3F/3F+N and "*") and `label` the text the
           single-line shows for it; `slots` fill the symbol's text (placeholders such as {in_a:g}, {icu_ka:g}, {rcd_ma:g}, {tag}); `if` is a condition on the item; `count` repeats it (a number or arithmetic on the facts).
The solution with the highest priority that matches wins (file order breaks ties). Add-ons are appended to the chain of whatever solution won when their own `when` matches.
"""
import ast
import copy
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ENV_VAR = "EPC_SOLUTIONS_JSON"
DEFAULT_FILE = Path(__file__).resolve().parent / "data" / "standard-solutions.json"
PHASES = ("1F", "3F", "3F+N")
CONDITIONS = ("topology", "kind", "phase", "type", "has_children", "motor", "in_a", "text_contains")
RANGES = ("gt", "ge", "lt", "le")
ITEM_KEYS = ("symbol", "short", "poles", "label", "slots", "if", "count")
SAMPLE = {"tag": "C-01", "in_a": 16, "ib_a": 12.0, "icu_ka": 10, "rcd_ma": 30, "phase": "3F", "phase_n": 3, "poles_label": "3P"}


# ---------------------------------------------------------------- loading
def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def defaults() -> dict:
    """The document that travels with the package, without any override."""
    return _read(DEFAULT_FILE)


PARTS = ("solutions", "add_ons", "groups")


def _merge(base: dict, extra: dict) -> None:
    for part in PARTS:
        for id_, entry in (extra.get(part) or {}).items():
            if entry is None:
                base.setdefault(part, {}).pop(id_, None)
            else:
                base.setdefault(part, {})[id_] = entry


def _files(*extra: Any) -> List[Path]:
    """The override files in order of authority: those the environment names (several are separated as paths are), then `extra` (each a path or a list of paths)."""
    named = [x for x in (os.environ.get(ENV_VAR) or "").split(os.pathsep) if x]
    flat = [y for x in extra for y in (x if isinstance(x, (list, tuple)) else [x]) if y]
    return [Path(x) for x in [*named, *flat]]


def load(*extra: Any) -> dict:
    """The document in force: the default one with, in order, the files of the environment (the global one, the company's, the project's) and `extra` (those that exist) on top of it."""
    doc = defaults()
    for p in _files(*extra):
        if p.is_file():
            _merge(doc, _read(p))
    return doc


def resolve_doc(doc: Optional[dict]) -> dict:
    return doc if doc is not None else load()


def override_of(doc: dict, base: Optional[dict] = None) -> dict:
    """What a document changes with respect to a base (the default document when none is given): id -> its entry, or null for what was removed. It is what a file at that level stores."""
    base = defaults() if base is None else base
    out: dict = {part: {} for part in PARTS}
    for part in PARTS:
        mine, theirs = doc.get(part, {}), base.get(part, {})
        out[part] = {**{i: e for i, e in mine.items() if theirs.get(i) != e}, **{i: None for i in theirs if i not in mine}}
    return {k: v for k, v in out.items() if v}


# ---------------------------------------------------------------- facts and conditions
def facts(tag: str, description: str, notes: str, topology: str, kind: str, phase: str, circuit_type: str, in_a: float, ib_a: float, icu_ka: float, rcd_ma: float,
          has_children: bool, motor: bool) -> dict:
    """What the conditions and the placeholders know about one circuit."""
    ph = phase if phase in PHASES else "3F"
    return {"tag": tag, "in_a": in_a, "ib_a": ib_a, "icu_ka": icu_ka, "rcd_ma": rcd_ma, "phase": ph, "phase_n": 1 if ph == "1F" else 3, "topology": topology, "kind": kind,
            "type": circuit_type, "has_children": bool(has_children), "motor": bool(motor), "text": f"{description} {notes}".lower()}


def _in_range(value: float, limits: dict) -> bool:
    return all((value > v if k == "gt" else value >= v if k == "ge" else value < v if k == "lt" else value <= v) for k, v in limits.items())


def matches(when: dict, f: dict) -> bool:
    """True when every condition holds for the facts of the circuit."""
    for key, want in (when or {}).items():
        if key in ("topology", "kind", "phase", "type"):
            ok = f[key] in want
        elif key in ("has_children", "motor"):
            ok = f[key] == want
        elif key == "in_a":
            ok = _in_range(f["in_a"], want)
        else:                                                                    # text_contains
            ok = any(str(w).lower() in f["text"] for w in want)
        if not ok:
            return False
    return True


# ---------------------------------------------------------------- arithmetic on the facts (no code runs: only numbers, + - * / // % and a few functions)
_FUNCTIONS = {"ceil": math.ceil, "floor": math.floor, "max": max, "min": min, "round": round}


_BINARY = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b, ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b, ast.FloorDiv: lambda a, b: a // b, ast.Mod: lambda a, b: a % b}
_ALLOWED = "only numbers, the facts of the circuit, + - * / // % and ceil, floor, max, min, round are allowed"


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _calc_leaf(node: ast.AST, f: dict) -> float:
    if isinstance(node, ast.Constant) and _is_number(node.value):
        return node.value
    if isinstance(node, ast.Name) and _is_number(f.get(node.id)):
        return f[node.id]
    raise ValueError(_ALLOWED)


def _calc_call(node: ast.Call, f: dict) -> float:
    if isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS and not node.keywords:
        return _FUNCTIONS[node.func.id](*[_calc(a, f) for a in node.args])
    raise ValueError(_ALLOWED)


def _calc(node: ast.AST, f: dict) -> float:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return -_calc(node.operand, f) if isinstance(node.op, ast.USub) else _calc(node.operand, f)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        return _BINARY[type(node.op)](_calc(node.left, f), _calc(node.right, f))
    if isinstance(node, ast.Call):
        return _calc_call(node, f)
    return _calc_leaf(node, f)


def expression(value: Any, f: dict) -> float:
    """A number as written in the document: a number, or arithmetic on the facts (`ceil(ib_a / 20)`)."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return _calc(ast.parse(str(value), mode="eval").body, f)


# ---------------------------------------------------------------- resolving a circuit
def _by_phase(value: Any, phase: str) -> Any:
    return value if not isinstance(value, dict) else value.get(phase, value.get("*"))


def _slots(templates: Dict[str, str], f: dict) -> Dict[str, str]:
    return {slot: str(text).format_map(f) for slot, text in templates.items()}


def _items(items: Iterable[dict], f: dict) -> List[dict]:
    out: List[dict] = []
    for it in items:
        if not matches(it.get("if", {}), f):
            continue
        entry = {"symbol": it["symbol"], "short": it.get("short", it["symbol"]), "poles": _by_phase(it.get("poles"), f["phase"]), "label": _by_phase(it.get("label"), f["phase"]),
                 "slots": _slots(it.get("slots", {}), f)}
        out += [dict(entry) for _ in range(int(expression(it.get("count", 1), f)))]
    return out


def _winner(doc: dict, f: dict) -> tuple:
    """(id, solution) of the enabled solution that matches with the highest priority (file order breaks ties)."""
    enabled = [(i, s) for i, s in doc.get("solutions", {}).items() if s.get("enabled", True) and matches(s.get("when", {}), f)]
    if not enabled:
        raise ValueError(f"no standard solution matches circuit {f['tag']}: the document needs one with an empty 'when' as the last resort")
    return max(enumerate(enabled), key=lambda p: (p[1][1].get("priority", 0), -p[0]))[1]


def resolve(f: dict, doc: Optional[dict] = None) -> dict:
    """The solution of a circuit: {"solution": id, "chain": [{"symbol", "short", "poles", "label", "slots"}], "disp": text}. Raises ValueError when no solution matches."""
    doc = resolve_doc(doc)
    sid, sol = _winner(doc, f)
    chain = _items(sol["chain"], f)
    added = [a for a in doc.get("add_ons", {}).values() if a.get("enabled", True) and matches(a.get("when", {}), f)]
    for add in added:
        chain += _items(add["chain"], f)
    label = next((c["label"] for c in chain if c["label"]), "")
    text = sol["disp"] if sol.get("disp") and not added else " > ".join(c["short"] for c in chain) + " ({in_a:g} A)"
    return {"solution": sid, "chain": chain, "disp": text.format_map({**f, "poles_label": label})}


# ---------------------------------------------------------------- checking a document
_TEXT_LISTS = ("topology", "kind", "phase", "type", "text_contains")


def _is_text_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def _is_limits(value: Any) -> bool:
    return isinstance(value, dict) and bool(value) and set(value) <= set(RANGES) and all(_is_number(v) for v in value.values())


_CHECKS = {**{k: (_is_text_list, "a list of texts") for k in _TEXT_LISTS}, "has_children": (lambda v: isinstance(v, bool), "true or false"),
           "motor": (lambda v: isinstance(v, bool), "true or false"), "in_a": (_is_limits, "limits from gt, ge, lt, le")}


def _condition_problem(where: str, key: str, want: Any) -> Optional[str]:
    if key not in _CHECKS:
        return f"{where}.{key}: unknown condition (one of {', '.join(CONDITIONS)})"
    check, message = _CHECKS[key]
    return None if check(want) else f"{where}.{key}: {message}"


def _condition_errors(where: str, when: Any) -> Iterable[str]:
    if not isinstance(when, dict):
        yield f"{where}: an object of conditions"
        return
    yield from (m for m in (_condition_problem(where, k, v) for k, v in when.items()) if m)


def _item_errors(where: str, it: Any, known: Optional[set]) -> Iterable[str]:
    if not isinstance(it, dict) or set(it) - set(ITEM_KEYS):
        yield f"{where}: an object with {', '.join(ITEM_KEYS)}"
        return
    if not it.get("symbol") or (known is not None and it["symbol"] not in known):
        yield f"{where}.symbol: a symbol of the library"
    yield from _condition_errors(f"{where}.if", it.get("if", {}))
    try:
        expression(it.get("count", 1), {**SAMPLE})
        for text in (it.get("slots") or {}).values():
            str(text).format_map(SAMPLE)
    except (ValueError, KeyError, SyntaxError, IndexError, ZeroDivisionError) as e:
        yield f"{where}: {e}"


GROUP_KEYS = ("name", "enabled", "when", "by", "max_circuits", "max_ib_a", "tag", "description")


def _group_limit_errors(where: str, rule: dict) -> Iterable[str]:
    if not isinstance(rule.get("by", []), list) or any(k not in ("type", "phase", "kind", "topology") for k in rule.get("by", [])):
        yield f"{where}.by: a list of type, phase, kind, topology"
    if not isinstance(rule.get("max_circuits", 6), int) or rule.get("max_circuits", 6) < 1:
        yield f"{where}.max_circuits: a whole number from 1"
    if not _is_number(rule.get("max_ib_a", 40)) or rule.get("max_ib_a", 40) <= 0:
        yield f"{where}.max_ib_a: a number above 0"


def _group_text_errors(where: str, rule: dict) -> Iterable[str]:
    if not rule.get("tag"):
        yield f"{where}.tag: required, with {{n}} for the number of the group"
    try:
        str(rule.get("tag", "")).format(n=1)
        for text in (rule.get("description") or {}).values():
            str(text).format(n=1, type="", phase="")
    except (KeyError, IndexError, ValueError) as e:
        yield f"{where}: {e}"


def _group_errors(where: str, rule: Any) -> Iterable[str]:
    """What a rule of automatic groups may contain."""
    if not isinstance(rule, dict) or set(rule) - set(GROUP_KEYS):
        yield f"{where}: an object with {', '.join(GROUP_KEYS)}"
        return
    yield from _condition_errors(f"{where}.when", rule.get("when", {}))
    yield from _group_limit_errors(where, rule)
    yield from _group_text_errors(where, rule)


def _entry_errors(where: str, entry: Any, known: Optional[set], needs_priority: bool) -> Iterable[str]:
    if not isinstance(entry, dict):
        yield f"{where}: an object"
        return
    yield from _condition_errors(f"{where}.when", entry.get("when", {}))
    if needs_priority and not isinstance(entry.get("priority", 0), int):
        yield f"{where}.priority: a whole number"
    chain = entry.get("chain")
    if not isinstance(chain, list) or not chain:
        yield f"{where}.chain: at least one symbol"
        return
    for n, it in enumerate(chain):
        yield from _item_errors(f"{where}.chain[{n}]", it, known)


def validate(doc: dict, known_symbols: Optional[Iterable[str]] = None) -> Dict[str, str]:
    """{path: message} for what a document may not contain; empty when valid. `known_symbols` (the library's ids) makes an unknown symbol an error."""
    known = set(known_symbols) if known_symbols is not None else None
    errors: Dict[str, str] = {}
    for part, needs in (("solutions", True), ("add_ons", False)):
        for id_, entry in (doc.get(part) or {}).items():
            for msg in _entry_errors(f"{part}.{id_}", entry, known, needs):
                errors[msg.split(":")[0]] = msg.split(": ", 1)[1]
    for id_, rule in (doc.get("groups") or {}).items():
        for msg in _group_errors(f"groups.{id_}", rule):
            errors[msg.split(":")[0]] = msg.split(": ", 1)[1]
    last_resort = any(s.get("enabled", True) and not s.get("when") for s in (doc.get("solutions") or {}).values() if isinstance(s, dict))
    if not last_resort:
        errors["solutions"] = "needs an enabled solution with an empty 'when' (the last resort for any circuit)"
    return errors


def dump(doc: dict, path: os.PathLike) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({"schema_version": "1.0", **doc}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def copy_doc(doc: dict) -> dict:
    return copy.deepcopy(doc)
