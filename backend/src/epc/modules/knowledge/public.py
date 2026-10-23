"""Public interface of the knowledge module."""
from epc.modules.knowledge import service


def rules_stats() -> dict:
    """Counters of the loaded standards and rules (drafts included outside production)."""
    return service.stats()


__all__ = ["rules_stats"]
