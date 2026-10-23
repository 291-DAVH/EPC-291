# tests

`golden/` holds reference input/output sets (Excel -> JSON -> SVG). Seeds: `engine/drawing/tests/fixtures/{sld,titleblock}`.
Engine unit tests live in `engine/<area>/tests`; run them all with `python tools/ci/run_gate.py`.
