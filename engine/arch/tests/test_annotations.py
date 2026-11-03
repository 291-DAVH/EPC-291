"""What a plan carries that is not the building (grid axes, dimensions, labels) is set apart in layers of its own and does not disturb the walls, doors and windows."""
import sys
import tempfile
import unittest
from pathlib import Path

import ezdxf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_arch import recognize                                             # noqa: E402
import helpers                                                             # noqa: E402


def _flat_with_notes(notes: bool = True) -> bytes:
    """The flat of the helpers, and around it: an axis of dashes with its bubble, a dimension line with its ticks and figure, a tag with its box and leader."""
    doc = ezdxf.new("R2010")
    doc.units = 6
    msp = doc.modelspace()
    for a, b in helpers.room_lines() + helpers.window_lines() + [helpers.door_leaf()]:
        msp.add_line(a, b)
    (cx, cy), r, a0, a1 = helpers.door_arc()
    msp.add_arc((cx, cy), r, a0, a1)
    if notes:
        for k in range(8):                                                   # an axis of dashes under the flat, with a bubble at its end
            msp.add_line((0.2 + k * 0.8, -1.0), (0.7 + k * 0.8, -1.0))
        msp.add_arc((-0.6, -1.0), 0.3, 0, 360)
        msp.add_text("A", dxfattribs={"insert": (-0.7, -1.1), "height": 0.2})
        msp.add_line((0.0, -2.0), (6.0, -2.0))                               # a dimension line: ticks across it at each end and in the middle, and the figure
        for x in (0.0, 3.0, 6.0):
            msp.add_line((x - 0.06, -2.06), (x + 0.06, -1.94))
        msp.add_text("3,00", dxfattribs={"insert": (1.2, -1.9), "height": 0.2})
        for a, b in (((7.0, 1.5), (7.9, 1.5)), ((7.9, 1.5), (7.9, 1.85)), ((7.9, 1.85), (7.0, 1.85)), ((7.0, 1.85), (7.0, 1.5)), ((7.0, 1.67), (6.3, 2.2))):      # a tag with its leader
            msp.add_line(a, b)
        msp.add_text("V-01", dxfattribs={"insert": (7.1, 1.6), "height": 0.15})
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "t.dxf"
        doc.saveas(str(path))
        return path.read_bytes()


class TestAnnotations(unittest.TestCase):
    def test_axes_dimensions_and_labels_are_set_apart(self):
        a = recognize(_flat_with_notes(), "flat.dxf").architecture
        found = {k: m.count() for k, m in a.annotations.items()}
        self.assertGreaterEqual(found["axes"], 9)                              # eight dashes, the bubble and its letter
        self.assertGreaterEqual(found["dimensions"], 5)                        # the line, three ticks and the figure
        self.assertGreaterEqual(found["labels"], 6)                            # four sides of the box, the leader and the text

    def test_the_building_is_read_as_if_they_were_not_there(self):
        clean = recognize(_flat_with_notes(notes=False), "flat.dxf").as_dict()
        noted = recognize(_flat_with_notes(), "flat.dxf").as_dict()
        self.assertEqual(noted["counts"], clean["counts"])
        self.assertEqual(noted["counts"], {"walls": 6, "doors": 1, "windows": 1, "openings": 0})
        self.assertEqual(len(noted["rooms"]), len(clean["rooms"]))

    def test_a_plan_with_no_notes_has_none(self):
        a = recognize(helpers.room_dxf(), "flat.dxf").architecture
        self.assertEqual(sum(m.count() for m in a.annotations.values()), 0)

    def test_the_svg_has_a_layer_for_each_kind_so_that_they_can_be_hidden(self):
        svg = recognize(_flat_with_notes(), "flat.dxf").svg
        for gid in ("ARQ-EJES", "ARQ-COTAS", "ARQ-ETIQUETAS"):
            self.assertIn(f'<g id="{gid}"', svg)
        self.assertIn(">V-01<", svg)
        self.assertNotIn("ARQ-EJES", recognize(helpers.room_dxf(), "flat.dxf").svg)

    def test_the_faint_background_does_not_repeat_what_has_its_own_layer(self):
        svg = recognize(_flat_with_notes(), "flat.dxf").svg
        background = svg.split('<g id="ARQ-FONDO"')[1].split("</g>")[0]
        self.assertLess(background.count("<line"), 40)                         # the flat's own strokes only: the 8 dashes, the dimension and the tag are in their layers

    def test_the_result_counts_them(self):
        d = recognize(_flat_with_notes(), "flat.dxf").as_dict()
        self.assertEqual(set(d["annotation_counts"]), {"axes", "dimensions", "labels"})
        self.assertGreater(d["annotation_counts"]["axes"], 0)


if __name__ == "__main__":
    unittest.main()
