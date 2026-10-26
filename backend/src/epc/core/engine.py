"""Running an engine module (`python -m epc_drawing...`) as a child process: one place for the command, the capture and the way a failure is reported.

`set_runner` is the seam for tests: a function with the signature of `subprocess.run` replaces the real process (None restores it), as
`intake.analyzer.set_client_factory` does for the AI client.
"""
import os
import subprocess
import sys
from typing import Callable, Optional, Sequence

from epc.core.config import settings

_runner: Callable = subprocess.run


def set_runner(fn: Optional[Callable]) -> None:
    global _runner
    _runner = fn or subprocess.run


def run_module(module: str, args: Sequence, timeout: int) -> subprocess.CompletedProcess:
    """`python -m <module> <args>` with output captured as text. The caller decides what a non-zero exit code means."""
    env = dict(os.environ, EPC_LAYERS_JSON=str(settings.layers_file), EPC_SOLUTIONS_JSON=str(settings.solutions_file))       # the global catalogs the MASTER edits: DXF layers, standard solutions
    return _runner([sys.executable, "-m", module, *[str(a) for a in args]], capture_output=True, text=True, timeout=timeout, env=env)


def tail(res: subprocess.CompletedProcess, chars: int) -> str:
    """The end of what the process wrote (stderr, else stdout): where its error message is."""
    return (res.stderr or res.stdout).strip()[-chars:]
