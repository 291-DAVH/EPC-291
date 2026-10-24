"""Public interface of the reporting module."""
from pathlib import Path

from epc.modules.reporting import service


def generated_reports(project_dir: Path) -> list:
    """Management reports generated for the project (PM² D11 to D15) with their publication state."""
    return service.overview(project_dir)["reports"]


__all__ = ["generated_reports"]
