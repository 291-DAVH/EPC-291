"""Footprints and clash detection between disciplines (epc_plan.footprint, epc_plan.clash). Pure: no backend, no network."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from epc_plan import clash, footprint   # noqa: E402


def sheet(level="L0", discipline="electrica_BT", nodes=(), lines=(), scale=True):
    """A drawing where 10 view units are 1 m."""
    plan = {"id": "T", "level": level, "origin": [0, 0], **({"scale": {"p1": [0, 0], "p2": [100, 0], "distance_m": 10}} if scale else {})}
    return {"schema_version": "1.0", "plan": plan, "discipline": discipline, "nodes": list(nodes), "lines": list(lines)}


def tray(i, a, b, **attrs):
    return {"id": i, "kind": "BN", "points": [a, b], **({"attrs": attrs} if attrs else {})}


def pipe(i, a, b, **attrs):
    return {"id": i, "kind": "CC", "points": [a, b], **({"attrs": attrs} if attrs else {})}


def items(*docs):
    return [it for name, d in docs for it in footprint.footprints(d, name)]


class TestFootprint(unittest.TestCase):
    def test_a_drawing_without_scale_occupies_nothing_measurable(self):
        self.assertEqual(footprint.footprints(sheet(lines=[tray("l1", [0, 0], [100, 0])], scale=False), "L0"), [])

    def test_the_defaults_of_the_kind_give_its_size_and_the_person_can_override_them(self):
        f = footprint.footprints(sheet(lines=[tray("l1", [0, 0], [100, 0]), tray("l2", [0, 50], [100, 50], z_m=3.0, ancho_m=0.6)]), "L0")
        self.assertEqual((f[0]["width_m"], f[0]["z0"], f[0]["z1"]), (0.3, 2.55, 2.65))
        self.assertEqual((f[1]["width_m"], f[1]["z0"], f[1]["z1"]), (0.6, 2.95, 3.05))
        self.assertEqual(f[0]["points"], [[0.0, 0.0], [10.0, 0.0]])

    def test_the_floor_of_each_level_is_a_storey_higher(self):
        up = footprint.footprints(sheet(level="L1", lines=[tray("l1", [0, 0], [100, 0])]), "L1")
        self.assertAlmostEqual(up[0]["z0"], 3.0 + 2.55)
        down = footprint.footprints(sheet(level="L-1", lines=[tray("l1", [0, 0], [100, 0])]), "L-1")
        self.assertAlmostEqual(down[0]["z0"], -3.0 + 2.55)

    def test_a_shaft_rises_from_its_elevation(self):
        f = footprint.footprints(sheet(nodes=[{"id": "n1", "kind": "PL", "x": 0, "y": 0}]), "L0")
        self.assertEqual((f[0]["z0"], f[0]["z1"]), (0.0, 3.0))


class TestClash(unittest.TestCase):
    def test_bodies_at_different_heights_do_not_clash(self):
        e = sheet(lines=[tray("l1", [0, 0], [100, 0])])
        s = sheet(discipline="sanitaria_cloacas", lines=[pipe("l1", [50, -50], [50, 50])])
        self.assertEqual(clash.detect(items(("E", e), ("S", s))), [])

    def test_bodies_that_cross_at_the_same_height_are_a_hard_clash(self):
        e = sheet(lines=[tray("l1", [0, 0], [100, 0])])
        s = sheet(discipline="sanitaria_cloacas", lines=[pipe("l1", [50, -50], [50, 50], z_m=2.6)])
        found = clash.detect(items(("E", e), ("S", s)))
        self.assertEqual([(c["type"], c["severity"]) for c in found], [("hard", "error")])
        self.assertEqual(found[0]["point_m"], [5.0, 0.0])
        self.assertEqual({found[0]["a"]["discipline"], found[0]["b"]["discipline"]}, {"electrica_BT", "sanitaria_cloacas"})

    def test_the_architecture_is_the_plan_the_others_are_drawn_over_and_clashes_with_nobody(self):
        wall = {"id": "l1", "kind": "MU", "points": [[50, -50], [50, 50]]}
        e = sheet(lines=[tray("l1", [0, 0], [100, 0])])
        self.assertEqual(clash.detect(items(("E", e), ("A", sheet(discipline="arquitectura", lines=[wall])))), [])

    def test_two_elements_of_the_same_discipline_never_clash(self):
        e = sheet(lines=[tray("l1", [0, 0], [100, 0]), tray("l2", [50, -50], [50, 50])])
        self.assertEqual(clash.detect(items(("E", e))), [])

    def test_closer_than_the_separation_of_the_rules_is_a_clearance_clash(self):
        e = sheet(lines=[tray("l1", [0, 0], [100, 0])])
        s = sheet(discipline="sanitaria_cloacas", lines=[pipe("l1", [0, 25], [100, 25], z_m=2.6)])        # 2.5 m apart in plan... too far
        self.assertEqual(clash.detect(items(("E", e), ("S", s))), [])
        near = sheet(discipline="sanitaria_cloacas", lines=[pipe("l1", [0, 3], [100, 3], z_m=2.6)])         # 0.3 m centre to centre: bodies 0.095 m apart
        found = clash.detect(items(("E", e), ("S", near)))
        self.assertEqual([c["type"] for c in found], ["clearance"])
        self.assertEqual(found[0]["clearance_m"], 0.3)
        self.assertGreater(found[0]["gap_m"], 0)

    def test_the_free_space_of_an_equipment_is_kept_clear(self):
        board = {"id": "n1", "kind": "TB", "x": 0, "y": 0}
        e = sheet(nodes=[board])
        s = sheet(discipline="sanitaria_cloacas", nodes=[{"id": "n1", "kind": "BR", "x": 0, "y": 80, "attrs": {"z_m": 1.5, "alto_m": 1.0, "ancho_m": 0.4}}])      # 8 m away
        self.assertEqual(clash.detect(items(("E", e), ("S", s))), [])
        close = sheet(discipline="sanitaria_cloacas", nodes=[{"id": "n1", "kind": "BR", "x": 0, "y": 12, "attrs": {"z_m": 1.5, "alto_m": 1.0, "ancho_m": 0.4}}])    # 1.2 m: inside the 1 m of free space + body
        found = clash.detect(items(("E", e), ("S", close)))
        self.assertEqual([c["type"] for c in found], ["maintenance"])

    def test_a_shaft_clashes_with_what_crosses_it_on_the_next_level(self):
        e = sheet(nodes=[{"id": "n1", "kind": "PL", "x": 0, "y": 0}])
        s = sheet(level="L1", discipline="sanitaria_cloacas", lines=[pipe("l1", [-50, 0], [50, 0], z_m=-0.05)])          # passes through the slab, where the shaft still is
        found = clash.detect(items(("E", e), ("S", s)))
        self.assertEqual([c["type"] for c in found], ["hard"])
        self.assertEqual({found[0]["a"]["sheet"], found[0]["b"]["sheet"]}, {"E", "S"})

    def test_the_id_of_a_clash_depends_only_on_the_pair(self):
        e = sheet(lines=[tray("l1", [0, 0], [100, 0])])
        s = sheet(discipline="sanitaria_cloacas", lines=[pipe("l1", [50, -50], [50, 50], z_m=2.6)])
        moved = sheet(discipline="sanitaria_cloacas", lines=[pipe("l1", [60, -50], [60, 50], z_m=2.6)])
        a = clash.detect(items(("E", e), ("S", s)))[0]["id"]
        b = clash.detect(items(("S", moved), ("E", e)))[0]["id"]
        self.assertEqual(a, b)

    def test_rules_of_a_later_level_replace_or_remove_earlier_ones(self):
        base = clash.default_rules()
        pair = {"a": "electrica_BT", "b": "sanitaria_cloacas", "clearance_m": 0.6}
        merged = clash.merge_rules(base, [pair])
        self.assertEqual([r["clearance_m"] for r in merged if r["a"] == "electrica_BT"], [0.6])
        self.assertEqual([r for r in clash.merge_rules(merged, [{**pair, "disabled": True}]) if r["a"] == "electrica_BT"], [])

    def test_a_rule_can_say_to_ignore_a_pair_of_kinds(self):
        e = sheet(lines=[tray("l1", [0, 0], [100, 0])])
        s = sheet(discipline="sanitaria_cloacas", lines=[pipe("l1", [50, -50], [50, 50], z_m=2.6)])
        rules = clash.merge_rules(clash.default_rules(), [{"a": "electrica_BT", "b": "sanitaria_cloacas", "kinds_a": ["BN"], "kinds_b": ["CC"], "ignore": True}])
        self.assertEqual(clash.detect(items(("E", e), ("S", s)), rules), [])


if __name__ == "__main__":
    unittest.main()
