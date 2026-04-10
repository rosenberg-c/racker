import importlib.util
from pathlib import Path


_geometry_path = Path(__file__).resolve().parents[1] / "modular_units" / "geometry.py"
_spec = importlib.util.spec_from_file_location("mu_geometry", _geometry_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

collection_name = _module.collection_name
unique_collection_name = _module.unique_collection_name
rail_face_y_mm = _module.rail_face_y_mm
rail_face_y_from_config = _module.rail_face_y_from_config
rail_hole_zs_mm = _module.rail_hole_zs_mm
faceplate_hole_zs_mm = _module.faceplate_hole_zs_mm
rail_hole_zs_from_config = _module.rail_hole_zs_from_config
rail_x_faces_mm = _module.rail_x_faces_mm
rail_x_faces_from_config = _module.rail_x_faces_from_config
rail_length_mm = _module.rail_length_mm
rail_length_from_config = _module.rail_length_from_config
total_height_mm = _module.total_height_mm
total_height_from_config = _module.total_height_from_config


class _Config:
    top_bottom_x = 490.0
    top_bottom_y = 400.0
    top_bottom_z = 18.0
    side_x = 18.0
    unit_height = 44.45
    hole_offsets = (6.35, 22.225, 38.1)


def test_collection_name():
    assert collection_name(10, 18.0, 400.0, False, False) == "MU_10U_18x400.c0"
    assert collection_name(10, 18.0, 400.0, True, False) == "MU_10U_18x400.c0.front"
    assert collection_name(10, 18.0, 400.0, False, True) == "MU_10U_18x400.c0.back"
    assert collection_name(10, 18.0, 400.0, True, True) == "MU_10U_18x400.c0.front-back"


def test_collection_name_with_clearance():
    assert (
        collection_name(10, 18.0, 400.0, False, False, 4.0)
        == "MU_10U_18x400.c4"
    )


def test_collection_name_with_decimal_clearance():
    assert (
        collection_name(10, 18.0, 400.0, False, False, 0.5)
        == "MU_10U_18x400.c0.5"
    )


def test_collection_name_with_clearance_and_rails():
    assert (
        collection_name(10, 18.0, 400.0, True, True, 4.0)
        == "MU_10U_18x400.c4.front-back"
    )


def test_unique_collection_name():
    existing = {"MU_10", "MU_10.2", "MU_10.3"}
    assert unique_collection_name("MU_10", existing) == "MU_10.4"
    assert unique_collection_name("MU_11", existing) == "MU_11"


def test_total_height_mm():
    assert total_height_mm(10, 18.0, 44.45) == 18.0 * 2.0 + 10 * 44.45


def test_total_height_from_config():
    assert total_height_from_config(10, _Config()) == 18.0 * 2.0 + 10 * 44.45


def test_rail_length_mm_min_u():
    total = total_height_mm(1, 18.0, 44.45)
    assert rail_length_mm(total, 18.0) == 44.45


def test_rail_length_from_config():
    assert rail_length_from_config(1, _Config()) == 44.45


def test_rail_face_y_mm():
    front, back = rail_face_y_mm(400.0, 30.0, 30.0)
    assert front == -200.0 + 30.0
    assert back == 200.0 - 30.0


def test_rail_face_y_from_config():
    front, back = rail_face_y_from_config(_Config(), 30.0, 30.0)
    assert front == -200.0 + 30.0
    assert back == 200.0 - 30.0


def test_rail_face_y_mm_asymmetric():
    front, back = rail_face_y_mm(400.0, 10.0, 50.0)
    assert front == -200.0 + 10.0
    assert back == 200.0 - 50.0


def test_rail_x_faces_mm():
    left, right = rail_x_faces_mm(487.0, 18.0, 18.0)
    assert left == -225.5 - 18.0
    assert right == 225.5 + 18.0


def test_rail_x_faces_from_config():
    left, right = rail_x_faces_from_config(_Config(), 18.0)
    assert left == -227.0 - 18.0
    assert right == 227.0 + 18.0


def test_rail_hole_zs_mm_count():
    hole_offsets = (6.35, 22.225, 38.1)
    positions = rail_hole_zs_mm(2, 18.0, 44.45, hole_offsets)
    assert len(positions) == 6


def test_rail_hole_zs_from_config_count():
    positions = rail_hole_zs_from_config(2, _Config())
    assert len(positions) == 6


def test_rail_hole_zs_mm_count_multi_u():
    hole_offsets = (6.35, 22.225, 38.1)
    positions = rail_hole_zs_mm(4, 18.0, 44.45, hole_offsets)
    assert len(positions) == 12


def test_rail_hole_spacing_per_u():
    hole_offsets = (6.35, 22.225, 38.1)
    positions = sorted(rail_hole_zs_mm(1, 18.0, 44.45, hole_offsets))
    assert len(positions) == 3
    spacing1 = positions[1] - positions[0]
    spacing2 = positions[2] - positions[1]
    assert abs(spacing1 - 15.875) < 1e-6
    assert abs(spacing2 - 15.875) < 1e-6


def test_rail_hole_zs_mm_bounds():
    hole_offsets = (6.35, 22.225, 38.1)
    positions = rail_hole_zs_mm(1, 18.0, 44.45, hole_offsets)
    assert min(positions) >= 18.0
    assert max(positions) <= 18.0 + 44.45


def test_faceplate_hole_zs_mm():
    hole_offsets = (6.35, 22.225, 38.1)
    positions = faceplate_hole_zs_mm(1, 44.45, hole_offsets)
    assert positions == [44.45 - 6.35, 6.35]


def test_faceplate_hole_zs_matches_rail_ends():
    hole_offsets = (6.35, 22.225, 38.1)
    rail_positions = rail_hole_zs_mm(1, 0.0, 44.45, hole_offsets)
    faceplate_positions = sorted(faceplate_hole_zs_mm(1, 44.45, hole_offsets))
    assert abs(faceplate_positions[0] - min(rail_positions)) < 1e-6
    assert abs(faceplate_positions[1] - max(rail_positions)) < 1e-6
