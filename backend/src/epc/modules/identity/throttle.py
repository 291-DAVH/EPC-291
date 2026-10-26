"""Limit of attempts per key (e-mail, address) in a time window."""

import threading
import time
from typing import Dict, List

from epc.core.errors import TooManyRequests


_fails: Dict[str, List[float]] = {}


_fails_lock = threading.Lock()


def _throttle(key: str, limit: int, add: bool = False) -> None:
    now = time.time()
    with _fails_lock:
        hits = [t for t in _fails.get(key, []) if now - t < 900]
        if add:
            hits.append(now)
        _fails[key] = hits
        if len(hits) >= limit and not add:
            raise TooManyRequests({"errors": {"login": "too many attempts, try again in a few minutes"}})


def reset_throttle() -> None:
    with _fails_lock:
        _fails.clear()
