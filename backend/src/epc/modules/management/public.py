"""Public interface of the management module."""
from pathlib import Path

from epc.modules.management import service


def project_summary(project_dir: Path) -> dict:
    """Card data of one project: progress, health, milestone, deliverable and input counters."""
    return service.summary(project_dir)


def publish_report(project_dir: Path, source_pdf: Path, title: str, kind: str, date_iso: str, summary: str) -> dict:
    """Publish a PDF report to the client's Reports list; returns the index entry (id INF-nnn)."""
    return service.publish_report(project_dir, source_pdf, title, kind, date_iso, summary)


__all__ = ["project_summary", "publish_report"]
