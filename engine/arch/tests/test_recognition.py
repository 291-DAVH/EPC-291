"""Architecture recognition: each reader gives the same flat, and the recognizers find in it the walls, the door and the window."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_arch import ArchError, Options, kinds, pdf_to_png, recognize   # noqa: E402
from epc_arch.sources import detect_kind   # noqa: E402
import helpers   # noqa: E402


def counts(result):
    return result.as_dict()["counts"]


class TestDxf(unittest.TestCase):
    def test_a_flat_in_metres_gives_its_walls_door_and_window(self):
        r = recognize(helpers.room_dxf(), "flat.dxf")
        a = r.architecture
        self.assertEqual(counts(r), {"walls": 6, "doors": 1, "windows": 1, "openings": 0})
        self.assertAlmostEqual(a.wall_thickness / a.units_per_metre, helpers.T, delta=0.02)
        self.assertIsNone(a.scale_hint)                                       # the units are known: no guess needed
        self.assertTrue(all(w.confidence >= 0.7 for w in a.walls))

    def test_the_door_knows_its_hinge_its_width_and_the_wall_it_opens(self):
        a = recognize(helpers.room_dxf(), "flat.dxf").architecture
        door = next(o for o in a.openings if o.kind == "door")
        self.assertAlmostEqual(door.width / a.units_per_metre, 0.9, delta=0.05)
        self.assertIn("arc", door.reason)
        self.assertTrue(door.wall.startswith("w"))
        self.assertIsNotNone(door.hinge)
        window = next(o for o in a.openings if o.kind == "window")
        self.assertAlmostEqual(window.width / a.units_per_metre, 1.2, delta=0.05)
        self.assertIn("2 lines", window.reason)

    def test_the_same_flat_in_millimetres_is_the_same_flat(self):
        r = recognize(helpers.room_dxf(unit=1000.0, insunits=4), "flat.dxf")
        self.assertEqual(counts(r), {"walls": 6, "doors": 1, "windows": 1, "openings": 0})
        self.assertAlmostEqual(r.architecture.wall_thickness / r.architecture.units_per_metre, helpers.T, delta=0.02)

    def test_without_units_it_still_finds_everything_and_guesses_the_scale_from_the_door(self):
        r = recognize(helpers.room_dxf(insunits=0), "flat.dxf")
        a = r.architecture
        self.assertEqual(counts(r), {"walls": 6, "doors": 1, "windows": 1, "openings": 0})
        self.assertIsNone(a.units_per_metre)
        self.assertIsNotNone(a.scale_hint)
        self.assertAlmostEqual(a.scale_hint["units_per_metre"], 3000 / helpers.W, delta=0.05 * 3000 / helpers.W)     # 6 m across 3000 units

    def test_a_gap_with_nothing_in_it_is_an_opening_and_a_named_block_makes_it_a_door(self):
        flat = helpers.room_dxf(door_arc_on=False)
        self.assertEqual(counts(recognize(flat, "f.dxf")), {"walls": 6, "doors": 0, "windows": 1, "openings": 1})

        def block(msp, k):
            blk = msp.doc.blocks.new("PUERTA_90")
            blk.add_line((0, 0), (0.9 * k, 0))
            msp.add_blockref("PUERTA_90", (helpers.DOOR[0] * k, helpers.T / 2 * k))
        r = recognize(helpers.room_dxf(door_arc_on=False, extra=[block]), "f.dxf")
        self.assertEqual(counts(r), {"walls": 6, "doors": 1, "windows": 1, "openings": 0})
        self.assertTrue(any("PUERTA_90" in o.reason for o in r.architecture.openings))

    def test_layers_named_as_walls_are_the_only_ones_walls_are_made_of(self):
        def furniture(msp, k):                                      # a cupboard 0.2 m thick that would pair up like a wall
            for y in (1.0, 1.0 + helpers.T):
                msp.add_line((1.0 * k, y * k), (2.5 * k, y * k), dxfattribs={"layer": "MOBILIARIO"})
        r = recognize(helpers.room_dxf(layer="MUROS", extra=[furniture]), "f.dxf")
        self.assertEqual(counts(r)["walls"], 6)

    def test_the_svg_has_one_group_per_kind_of_element_in_the_frame_of_the_plan(self):
        r = recognize(helpers.room_dxf(), "flat.dxf")
        root = ET.fromstring(r.svg)
        ns = "{http://www.w3.org/2000/svg}"
        groups = {g.get("id"): g for g in root.iter(f"{ns}g")}
        self.assertEqual(set(groups) & {"ARQ-FONDO", "ARQ-MUROS", "ARQ-PUERTAS", "ARQ-VENTANAS", "ARQ-HUECOS"}, {"ARQ-FONDO", "ARQ-MUROS", "ARQ-PUERTAS", "ARQ-VENTANAS", "ARQ-HUECOS"})
        self.assertEqual(len(list(groups["ARQ-MUROS"])), 6)
        self.assertEqual(len(list(groups["ARQ-PUERTAS"])), 1)
        self.assertEqual([float(v) for v in root.get("viewBox").split()], [0.0, 0.0, float(root.get("width")), float(root.get("height"))])
        no_bg = ET.fromstring(recognize(helpers.room_dxf(), "flat.dxf", Options(background=False)).svg)
        self.assertNotIn("ARQ-FONDO", {g.get("id") for g in no_bg.iter(f"{ns}g")})

    def test_a_flat_turned_to_any_angle_is_the_same_flat(self):
        for angle in (30.0, 90.0, 137.0):
            r = recognize(helpers.room_dxf(rotate=angle), "flat.dxf")
            self.assertEqual(counts(r), {"walls": 6, "doors": 1, "windows": 1, "openings": 0}, angle)

    def test_the_y_axis_is_flipped_so_the_plan_reads_like_the_drawing(self):
        a = recognize(helpers.room_dxf(), "flat.dxf").architecture
        door = next(o for o in a.openings if o.kind == "door")
        window = next(o for o in a.openings if o.kind == "window")
        self.assertGreater(door.at[1], window.at[1])                          # the door is in the bottom wall, the window in the top one: y grows downwards


class TestPdf(unittest.TestCase):
    def test_a_vector_pdf_gives_the_same_flat(self):
        r = recognize(helpers.room_pdf(), "flat.pdf")
        self.assertEqual(r.architecture.source, "pdf")
        self.assertEqual(counts(r), {"walls": 6, "doors": 1, "windows": 1, "openings": 0})

    def test_the_door_swing_drawn_as_a_curve_is_read_as_an_arc(self):
        r = recognize(helpers.room_pdf(), "flat.pdf")
        self.assertEqual(sum(1 for o in r.architecture.openings if o.kind == "door" and "arc" in o.reason), 1)
        without = recognize(helpers.room_pdf(arc=False), "flat.pdf")
        self.assertEqual(counts(without)["doors"], 0)

    def test_a_pdf_with_no_vector_drawing_falls_back_to_the_picture_of_its_page(self):
        r = recognize(helpers.make_pdf("0.5 w 10 10 m 100 10 l S"), "scan.pdf")
        self.assertEqual(r.architecture.source, "pdf-image")
        self.assertTrue(any("picture of the page" in w for w in r.architecture.warnings))

    def test_the_picture_of_a_page_is_made_in_one_place(self):
        png = pdf_to_png(helpers.room_pdf())
        self.assertTrue(png.startswith(b"\x89PNG"))
        self.assertIsNone(pdf_to_png(b"not a pdf"))


class TestImage(unittest.TestCase):
    def test_walls_drawn_as_thick_bands_are_found_with_their_door_and_window_gaps(self):
        r = recognize(helpers.room_png(), "flat.png")
        self.assertEqual(r.architecture.source, "image")
        c = counts(r)
        self.assertEqual(c["walls"], 6)
        self.assertEqual((c["windows"], c["openings"], c["doors"]), (1, 1, 0))             # an image has no door arcs: the door is an opening
        self.assertAlmostEqual(r.architecture.wall_thickness, 12.0, delta=2.0)
        self.assertTrue(any("horizontal and vertical" in w for w in r.architecture.warnings))

    def test_the_coordinates_are_those_of_the_picture(self):
        png = helpers.room_png()
        r = recognize(png, "flat.png")
        from PIL import Image
        import io
        self.assertEqual(tuple(r.architecture.size), Image.open(io.BytesIO(png)).size)
        xs = [p[0] for w in r.architecture.walls for p in (w.a, w.b)]
        self.assertGreater(min(xs), 90)
        self.assertLess(max(xs), 100 + helpers.W * 150 + 20)

    def test_a_blank_image_says_there_is_nothing_to_find(self):
        from PIL import Image
        import io
        out = io.BytesIO()
        Image.new("L", (400, 300), 255).save(out, format="PNG")
        r = recognize(out.getvalue(), "blank.png")
        self.assertEqual(counts(r)["walls"], 0)
        self.assertTrue(any("no walls" in w for w in r.architecture.warnings))


class TestSources(unittest.TestCase):
    def test_the_kind_comes_from_the_bytes(self):
        self.assertEqual(kinds(), ["dxf", "image", "pdf"])
        self.assertEqual(detect_kind(helpers.room_pdf()), "pdf")
        self.assertEqual(detect_kind(helpers.room_png()), "image")
        self.assertEqual(detect_kind(helpers.room_dxf(), "x.dxf"), "dxf")
        with self.assertRaises(ArchError):
            detect_kind(b"hello")

    def test_a_file_that_is_not_what_it_says_is_refused_with_a_reason(self):
        with self.assertRaises(ArchError):
            recognize(b"0\nSECTION\n2\nHEADER\n", "broken.dxf")
        with self.assertRaises(ArchError):
            recognize(b"%PDF-1.4 garbage", "broken.pdf")
        with self.assertRaises(ArchError):
            recognize(b"\x89PNG garbage", "broken.png")
        with self.assertRaises(ArchError):
            recognize(helpers.room_dxf(), "x.dxf", Options(kind="xml"))

    def test_the_engine_stands_alone(self):
        """Isolation: no other package of the platform is imported by this one."""
        src = HERE.parent / "src" / "epc_arch"
        for path in src.rglob("*.py"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith(("import epc_", "from epc_")):
                    self.assertTrue(line.split()[1].startswith("epc_arch"), f"{path.name}: {line}")


if __name__ == "__main__":
    unittest.main()
