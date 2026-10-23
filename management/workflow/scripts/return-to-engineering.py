#!/usr/bin/env python3
"""return-to-engineering.py — ver .claude/hooks/README.md y workflow.py (WF-001). Ejecutar con --help."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fwlib
import workflow

if __name__ == "__main__":
    fwlib.correr(lambda: workflow.cli_return_to_engineering(sys.argv[1:]))
