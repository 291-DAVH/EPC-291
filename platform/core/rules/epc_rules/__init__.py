"""EPC rules engine (stdlib only)."""
from .conditions import compare, match_when
from .ruleset import Finding, Report, RuleSet

__all__ = ["RuleSet", "Finding", "Report", "compare", "match_when"]
__version__ = "0.1.0"
