#!/usr/bin/env python3
"""progress-report.py — ver .claude/hooks/README.md y workflow.py (WF-001). Ejecutar con --help."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwlib
import workflow

if __name__ == "__main__":
    fwlib.correr(lambda: workflow.cli_progress_report(sys.argv[1:]))
