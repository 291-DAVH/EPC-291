import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))

from epc_lighting import LightingError, run  # noqa: E402
import helpers  # noqa: E402


def refused(doc):
    with unittest.TestCase().assertRaises(LightingError) as ctx:
        run(doc)
    return str(ctx.exception)


class TestLoading(unittest.TestCase):
    def test_dict_str_and_bytes_give_the_same_result(self):
        doc = helpers.document()
        text = json.dumps(doc)
        self.assertEqual(run(doc).as_dict(), run(text).as_dict())
        self.assertEqual(run(doc).as_dict(), run(text.encode("utf-8")).as_dict())
        self.assertEqual(run(doc).as_dict(), run(b"\xef\xbb\xbf" + text.encode("utf-8")).as_dict())

    def test_empty_input_is_refused_with_its_reason(self):
        for empty in (b"", "", "   "):
            self.assertIn("empty", refused(empty))

    def test_invalid_json_says_where(self):
        self.assertIn("not valid JSON", refused(b"{not json"))

    def test_a_non_object_document_is_refused(self):
        self.assertIn("must be an object", refused(b"[1, 2]"))

    def test_binary_input_is_refused(self):
        self.assertIn("UTF-8", refused(b"\xff\xfe\x00"))

    def test_the_wrong_type_is_refused(self):
        self.assertIn("must be a JSON document", refused(42))

    def test_nothing_to_calculate_is_a_warning_not_an_error(self):
        result = run(helpers.document(rooms=[], luminaires=[]))
        self.assertEqual(result.as_dict()["counts"]["rooms"], 0)
        self.assertTrue(result.warnings)


class TestMessagesSayWhatToFix(unittest.TestCase):
    def test_wrong_schema_version(self):
        doc = helpers.document()
        doc["schema_version"] = "2.0"
        self.assertIn("schema_version: must be '1.0'", refused(doc))

    def test_missing_dimension_names_the_room_and_the_field(self):
        room = helpers.room_dict()
        del room["width_m"]
        msg = refused(helpers.document([room]))
        self.assertIn("rooms[0] ('R1')", msg)
        self.assertIn("'width_m' is required", msg)

    def test_negative_dimension(self):
        self.assertIn("must be greater than 0", refused(helpers.document([helpers.room_dict(height_m=-1)])))

    def test_a_text_where_a_number_goes(self):
        self.assertIn("must be a number", refused(helpers.document([helpers.room_dict(width_m="4")])))

    def test_a_boolean_is_not_a_number(self):
        self.assertIn("must be a number", refused(helpers.document([helpers.room_dict(width_m=True)])))

    def test_target_or_activity_is_needed_and_the_ids_are_listed(self):
        room = helpers.room_dict()
        del room["target_lux"]
        msg = refused(helpers.document([room]))
        self.assertIn("'target_lux' or 'activity' is required", msg)
        self.assertIn("education.classroom", msg)

    def test_unknown_activity(self):
        self.assertIn("'bakery' is not valid", refused(helpers.document([helpers.room_dict(activity="bakery")])))

    def test_unknown_luminaire_reference_lists_the_defined_ids(self):
        msg = refused(helpers.document([helpers.room_dict(luminaire="XX")]))
        self.assertIn("'XX' is not defined in 'luminaires'", msg)
        self.assertIn("'L1'", msg)

    def test_duplicate_ids(self):
        self.assertIn("appears more than once", refused(helpers.document([helpers.room_dict(), helpers.room_dict()])))
        self.assertIn("appears more than once", refused(helpers.document(luminaires=[helpers.DOWNLIGHT, helpers.DOWNLIGHT])))

    def test_unknown_method_and_system(self):
        self.assertIn("choose one of ['lumen', 'zonal']", refused(helpers.document([helpers.room_dict(method="point")])))
        self.assertIn("lighting_system", refused(helpers.document([helpers.room_dict(lighting_system="laser")])))

    def test_reflectance_out_of_range_and_unknown_material(self):
        self.assertIn("must be at most 1", refused(helpers.document([helpers.room_dict(reflectances={"ceiling": 1.5})])))
        self.assertIn("material 'gold' is not valid", refused(helpers.document([helpers.room_dict(reflectances={"walls": {"material": "gold"}})])))
        self.assertIn("unknown surface", refused(helpers.document([helpers.room_dict(reflectances={"roof": 0.5})])))

    def test_lamps_must_be_whole(self):
        self.assertIn("must be a whole number", refused(helpers.document(luminaires=[helpers.luminaire_dict(lamps=1.5)])))

    def test_cu_table_shape_errors(self):
        bad = {"axis_values": [1.0, 2.0], "reflectances": [[0.5, 0.5, 0.2]], "values": [[0.6]]}
        self.assertIn("needs one row per axis value", refused(helpers.document(luminaires=[helpers.luminaire_dict(cu_table=bad)])))
        bad = {"axis_values": [2.0, 1.0], "reflectances": [[0.5, 0.5, 0.2]], "values": [[0.6], [0.5]]}
        self.assertIn("strictly increasing", refused(helpers.document(luminaires=[helpers.luminaire_dict(cu_table=bad)])))
        bad = {"axis": "z", "axis_values": [1.0], "reflectances": [[0.5, 0.5, 0.2]], "values": [[0.6]]}
        self.assertIn("choose 'k'", refused(helpers.document(luminaires=[helpers.luminaire_dict(cu_table=bad)])))

    def test_photometry_shape_errors(self):
        bad = {"gamma_deg": [0, 30, 60], "intensity_cd_per_klm": [100, 90]}
        self.assertIn("needs one value per gamma angle", refused(helpers.document(luminaires=[helpers.luminaire_dict(photometry=bad)])))

    def test_suspension_mode_choices(self):
        self.assertIn("auto_min", refused(helpers.document([helpers.room_dict(suspension_mode="low")])))


class TestTableErrors(unittest.TestCase):
    def _lum(self, **kw):
        return helpers.document(luminaires=[helpers.luminaire_dict(**kw)])

    def test_nan_and_infinity_are_refused(self):
        text = json.dumps(helpers.document()).replace('"width_m": 4', '"width_m": NaN')
        self.assertIn("finite", refused(text))
        text = json.dumps(helpers.document()).replace('"width_m": 4', '"width_m": Infinity')
        self.assertIn("finite", refused(text))

    def test_cu_table_columns_units_and_rows(self):
        base = {"axis_values": [1.0], "reflectances": [[0.5, 0.5, 0.2]], "values": [[0.6]]}
        for change, message in (
            ({"reflectances": [[0.5, 0.5]]}, "must be a list with at least 3"),
            ({"reflectances": [[0.5, 0.5, 0.2, 0.1]]}, "[ceiling, walls, floor]"),
            ({"unit": "pct"}, "choose 'fraction' or 'percent'"),
            ({"values": [[0.6, 0.7]]}, "one value per reflectance column"),
            ({"axis_values": []}, "at least 1"),
        ):
            self.assertIn(message, refused(self._lum(cu_table={**base, **change})), change)
        self.assertIn("must be an object", refused(self._lum(cu_table=[1])))

    def test_percent_tables_are_scaled(self):
        table = {"axis_values": [1.0], "reflectances": [[0.5, 0.5, 0.2]], "values": [[60]], "unit": "percent"}
        cu = run(helpers.document([helpers.room_dict(coefficient_of_utilisation=None, reflectances={"ceiling": 0.5, "walls": 0.5, "floor": 0.2})], [helpers.luminaire_dict(cu_table=table)])).as_dict()["rooms"][0]["factors"]["cu"]
        self.assertAlmostEqual(cu["value"], 0.6, places=2)

    def test_photometry_c_planes(self):
        base = {"gamma_deg": [0, 90], "c_deg": [0, 180], "intensity_cd_per_klm": [[1, 1], [2, 2]]}
        self.assertIn("one row per C plane", refused(self._lum(photometry={**base, "intensity_cd_per_klm": [[1, 1]]})))
        self.assertIn("strictly increasing", refused(self._lum(photometry={**base, "c_deg": [180, 0]})))
        self.assertIn("must be an object", refused(self._lum(photometry=5)))
        ok = run(helpers.document([helpers.room_dict()], [helpers.luminaire_dict(photometry=base)]))
        self.assertTrue(ok.as_dict()["rooms"][0]["points"]["computed"])

    def test_bad_point_normals_and_lists(self):
        for points, message in (
            ([{"x_m": 1, "y_m": 1, "normal": [0, 0, 0]}], "cannot be [0, 0, 0]"),
            ([{"x_m": 1, "y_m": 1, "normal": "sideways"}], "'horizontal' or a vector"),
            ("P1", "must be a list of points"),
        ):
            self.assertIn(message, refused(helpers.document([helpers.room_dict(points=points)])), message)

    def test_list_fields_must_be_lists_and_items_objects(self):
        doc = helpers.document()
        doc["rooms"] = {"id": "R1"}
        self.assertIn("rooms: must be a list", refused(doc))
        doc["rooms"] = ["R1"]
        self.assertIn("must be an object", refused(doc))

    def test_ids_must_be_texts(self):
        self.assertIn("non-empty text", refused(helpers.document([helpers.room_dict(id="")])))


class TestDefaultsAndMaterials(unittest.TestCase):
    def test_missing_reflectances_use_the_article_defaults_with_low_confidence(self):
        refl = run(helpers.document()).as_dict()["rooms"][0]["reflectances"]
        self.assertEqual([refl[k]["value"] for k in ("ceiling", "walls", "floor")], [0.5, 0.3, 0.1])
        self.assertEqual(refl["ceiling"]["confidence"], 0.5)

    def test_a_material_resolves_to_the_midpoint_of_its_range(self):
        room = helpers.room_dict(reflectances={"walls": {"material": "white_paint"}, "floor": 0.2})
        refl = run(helpers.document([room])).as_dict()["rooms"][0]["reflectances"]
        self.assertAlmostEqual(refl["walls"]["value"], 0.775)
        self.assertEqual(refl["floor"]["confidence"], 1.0)

    def test_activity_gives_the_target_and_the_quality_limits(self):
        room = helpers.room_dict(activity="education.classroom")
        del room["target_lux"]
        target = run(helpers.document([room])).as_dict()["rooms"][0]["target"]
        self.assertEqual((target["value"], target["ugr_l_max"], target["ra_min"]), (300.0, 19, 80))

    def test_an_explicit_target_overrides_the_activity_and_says_so(self):
        target = run(helpers.document([helpers.room_dict(activity="education.reading_room")])).as_dict()["rooms"][0]["target"]
        self.assertEqual(target["value"], 300.0)
        self.assertIn("suggests 500", target["reason"])

    def test_environment_and_explicit_maintenance(self):
        dirty = run(helpers.document([helpers.room_dict(environment="dirty")])).as_dict()["rooms"][0]["factors"]["maintenance"]
        given = run(helpers.document([helpers.room_dict(maintenance_factor=0.7)])).as_dict()["rooms"][0]["factors"]["maintenance"]
        self.assertEqual((dirty["value"], given["value"]), (0.6, 0.7))


if __name__ == "__main__":
    unittest.main()
