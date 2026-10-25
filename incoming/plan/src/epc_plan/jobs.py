"""Long operations run in the background: the caller starts a job and reads its status file; it never waits for the work."""
import json
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict

from epc_plan import core


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
