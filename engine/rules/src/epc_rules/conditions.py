"""Condition and check evaluation shared by the rule engine."""
from typing import Any

OPS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}
_WORD = {"eq": "==", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">=", "in": "in", "not_in": "not_in"}

MISSING = object()


def compare(actual: Any, op: str, expected: Any) -> bool:
    try:
        return bool(OPS[op](actual, expected))
    except TypeError:
        return False


def match_when(when: dict, ctx: dict) -> bool:
    """True when every condition holds. A missing context field makes the condition fail."""
    for field, cond in (when or {}).items():
        actual = ctx.get(field, MISSING)
        if actual is MISSING:
            return False
        if isinstance(cond, dict):
            for word, expected in cond.items():
                if not compare(actual, _WORD[word], expected):
                    return False
        elif isinstance(cond, list):
            if actual not in cond:
                return False
        elif actual != cond:
            return False
    return True
