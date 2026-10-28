"""Running an engine module (`python -m epc_drawing...`) as a child process: one place for the command, the capture and the way a failure is reported.

`set_runner` is the seam for tests: a function with the signature of `subprocess.run` replaces the real process (None restores it), as
`intake.analyzer.set_client_factory` does for the AI client.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional, Sequence

from epc.core.config import settings

_runner: Callable = subprocess.run


def set_runner(fn: Optional[Callable]) -> None:
    global _runner
    _runner = fn or subprocess.run


def _catalog_env(catalogs: Optional[dict]) -> dict:
    """The environment variables that tell the engine which catalog files apply (several separated as paths are; the later wins)."""
    files = catalogs or {"layers": [settings.layers_file], "solutions": [settings.solutions_file]}
    return {"EPC_LAYERS_JSON": os.pathsep.join(map(str, files["layers"])), "EPC_SOLUTIONS_JSON": os.pathsep.join(map(str, files["solutions"]))}


def run_module(module: str, args: Sequence, timeout: int, catalogs: Optional[dict] = None) -> subprocess.CompletedProcess:
    """`python -m <module> <args>` with output captured as text. The caller decides what a non-zero exit code means.
    `catalogs` ({"layers": [files], "solutions": [files]}, in order of authority: global, company, project) says which catalogs of drawing the engine applies; without it, the global ones."""
    env = dict(os.environ, **_catalog_env(catalogs))
    return _runner([sys.executable, "-m", module, *[str(a) for a in args]], capture_output=True, text=True, timeout=timeout, env=env)


def tail(res: subprocess.CompletedProcess, chars: int) -> str:
    """The end of what the process wrote (stderr, else stdout): where its error message is."""
    return (res.stderr or res.stdout).strip()[-chars:]


def render_report_pdf(doc: dict, dst: Path, timeout: int = 180) -> None:
    """A structured report (see `epc_drawing.export.report_pdf`: title, key/value blocks, headings, paragraphs, bullets, tables) as an A4 PDF. Raises RuntimeError with the end of the engine's message."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "report.json"
        src.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        res = run_module("epc_drawing.export.report_pdf", [src, dst], timeout=timeout)
    if res.returncode != 0:
        raise RuntimeError(f"could not render the report: {tail(res, 300)}")
