"""A sheet is not a plan: its frame and title block are left out, each plan of it is read on its own with the floor its title names, and the floors share one frame."""
import sys
import tempfile
import unittest
from pathlib import Path

import ezdxf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_arch import Options, recognize                                    # noqa: E402
from epc_arch.pipeline import recognize_sheet                              # noqa: E402
from epc_arch.recognizers.levels import named                              # noqa: E402
from epc_arch.model import Text                                            # noqa: E402
import helpers                                                             # noqa: E402


def _flat(msp, ox: float, oy: float) -> None:
    for a, b in helpers.room_lines() + helpers.window_lines() + [helpers.door_leaf()]:
        msp.add_line((ox + a[0], oy + a[1]), (ox + b[0], oy + b[1]))
    (cx, cy), r, a0, a1 = helpers.door_arc()
    msp.add_arc((ox + cx, oy + cy), r, a0, a1)


def _frame(msp, x0: float, y0: float, x1: float, y1: float, block_x: float) -> None:
    """The border of the sheet, and the title block: a column on the right with its rows."""
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)), ((block_x, y0), (block_x, y1))):
        msp.add_line(a, b)
    for k in range(1, 8):
        y = y0 + k * (y1 - y0) / 8
        msp.add_line((block_x, y), (x1, y))


def _sheet(titles=("PLANTA BAJA", "PLANTA ALTA"), frame: bool = True, second: bool = True) -> bytes:
    """Two flats side by side (the same plan on two floors), their titles under them, a section-like strip, a frame and a title block, in metres."""
    doc = ezdxf.new("R2010")
    doc.units = 6
    msp = doc.modelspace()
    _flat(msp, 0.0, 0.0)
    msp.add_text(titles[0], dxfattribs={"insert": (0.5, -1.2), "height": 0.4})
    if second:
        _flat(msp, 9.0, 0.0)
        msp.add_text(titles[1], dxfattribs={"insert": (9.5, -1.2), "height": 0.4})
    for k in range(5):                                                       # a section: stacked long bands, no rooms, no doors
        msp.add_line((0.0, -6.0 - 0.6 * k), (14.0, -6.0 - 0.6 * k))
    if frame:
        _frame(msp, -3.0, -9.0, 28.0, 7.0, 21.0)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sheet.dxf"
        doc.saveas(str(path))
        return path.read_bytes()


class TestSheet(unittest.TestCase):
    def test_each_plan_of_a_sheet_is_a_level_named_by_its_title(self):
        s = recognize_sheet(_sheet(), "sheet.dxf")
        self.assertEqual([(r.architecture.level.name, r.architecture.level.index, r.architecture.level.source) for r in s.levels],
                         [("PLANTA BAJA", 0, "text"), ("PLANTA ALTA", 1, "text")])
        for r in s.levels:
            c = r.as_dict()["counts"]
            self.assertEqual((c["walls"], c["doors"], c["windows"]), (6, 1, 1))

    def test_the_frame_and_the_title_block_are_not_read(self):
        s = recognize_sheet(_sheet(), "sheet.dxf")
        a = s.levels[0].architecture
        self.assertLess(max(a.size) / a.units_per_metre, 8.0)                 # the frame is 31 m wide; one flat is 6 m
        self.assertEqual(sum(len(r.architecture.walls) for r in s.levels), 12)

    def test_the_floors_share_one_frame_so_a_point_has_the_same_coordinates_on_each(self):
        lo, hi = [r.architecture for r in recognize_sheet(_sheet(), "sheet.dxf").levels]
        self.assertEqual(lo.size, hi.size)
        self.assertEqual(lo.reference, hi.reference)
        key = lambda a: sorted((round(w.a[0], 1), round(w.a[1], 1), round(w.b[0], 1), round(w.b[1], 1)) for w in a.walls)      # noqa: E731
        self.assertEqual(key(lo), key(hi))                                    # the same flat on both floors lies on itself
        self.assertEqual(sorted(round(o.at[0], 1) for o in lo.openings), sorted(round(o.at[0], 1) for o in hi.openings))

    def test_the_svg_of_each_floor_is_framed_the_same_so_they_overlay(self):
        a, b = recognize_sheet(_sheet(), "sheet.dxf").levels
        view = lambda svg: svg.split('viewBox="')[1].split('"')[0]            # noqa: E731
        self.assertEqual(view(a.svg), view(b.svg))
        self.assertIn("PLANTA ALTA", b.svg)

    def test_plans_titled_by_floor_are_split_even_with_no_frame(self):
        s = recognize_sheet(_sheet(frame=False), "sheet.dxf")
        self.assertEqual([r.architecture.level.index for r in s.levels], [0, 1])

    def test_two_views_that_name_no_floor_and_have_no_frame_are_not_taken_for_a_sheet(self):
        self.assertEqual(len(recognize_sheet(_sheet(titles=("A", "B"), frame=False), "sheet.dxf").levels), 1)

    def test_a_floor_that_is_not_named_is_numbered_in_reading_order_and_says_so(self):
        s = recognize_sheet(_sheet(titles=("DETALLE", "ESCALA 1:50")), "sheet.dxf")
        self.assertEqual([r.architecture.level.source for r in s.levels], ["order", "order"])
        self.assertTrue(all(any("reading order" in w for w in r.architecture.warnings) for r in s.levels))

    def test_a_single_plan_inside_a_frame_is_still_one_plan_without_the_frame(self):
        s = recognize_sheet(_sheet(second=False), "sheet.dxf")
        self.assertEqual(len(s.levels), 1)
        self.assertEqual(s.levels[0].as_dict()["counts"]["walls"], 6)

    def test_recognize_gives_the_lowest_floor_of_a_sheet(self):
        r = recognize(_sheet(), "sheet.dxf", Options())
        self.assertEqual(r.architecture.level.name, "PLANTA BAJA")
        self.assertTrue(any("2 plans" in w for w in r.architecture.warnings))

    def test_a_plan_without_a_sheet_around_it_is_read_as_before(self):
        s = recognize_sheet(helpers.room_dxf(), "flat.dxf")
        self.assertEqual(len(s.levels), 1)
        self.assertIsNone(s.levels[0].architecture.level)
        self.assertIsNone(s.levels[0].architecture.reference)


class TestLevels(unittest.TestCase):
    box = (0.0, 0.0, 10.0, 10.0)

    def level(self, *values):
        return named([Text(v, (1.0, 11.0)) for v in values], self.box)

    def test_titles_say_the_floor(self):
        cases = {"1 PLANTA BAJA": 0, "PLANTA ALTA": 1, "Planta 2": 2, "PLANTA -1": -1, "SUBSUELO": -1, "Primer piso": 1, "Ground floor": 0, "NIVEL +3": 3, "PB": 0}
        for text, index in cases.items():
            self.assertEqual(self.level(text).index, index, text)

    def test_what_is_not_a_title_does_not_name_a_floor(self):
        self.assertIsNone(self.level("PB-01", "TERRAZA", "COCINA", "ESC. 1:100"))

    def test_the_most_specific_title_wins_over_a_bare_abbreviation(self):
        self.assertEqual(self.level("PB", "1 PLANTA BAJA").name, "PLANTA BAJA")

    def test_a_roof_is_named_but_has_no_floor_number(self):
        lv = self.level("3 PLANTA DE AZOTEA")
        self.assertEqual((lv.name, lv.index), ("PLANTA DE AZOTEA", None))


if __name__ == "__main__":
    unittest.main()
