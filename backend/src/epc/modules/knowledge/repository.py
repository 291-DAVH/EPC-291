"""Access to the rules engine (engine/rules). Drafts are included only outside production."""
from epc_rules import RuleSet

from epc.core.config import settings


def ruleset() -> RuleSet:
    drafts = settings.dev_knowledge if settings.env != "production" else None
    return RuleSet.load("AR", "electrical", env=settings.env, root=settings.engine, include_drafts_from=drafts)
