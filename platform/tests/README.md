# tests

`golden/` holds reference input/output sets (Excel -> JSON -> SVG). Seeds: `hub/sld/tests/fixtures/{a1,a3}` and `hub/iram-titleblock/tests/fixtures`.
Run plugin unit tests from each plugin's `scripts/` folder: `python -m unittest discover -s . -p "test_*.py"`.
