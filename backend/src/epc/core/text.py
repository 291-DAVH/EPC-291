"""Text helpers shared by modules."""
import re
from typing import Optional


def slugify(text: Optional[str], max_len: Optional[int] = None, default: str = "") -> str:
    """Lowercase letters and digits joined by single dashes, cut to `max_len` (if given); `default` when nothing is left."""
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:max_len] or default
