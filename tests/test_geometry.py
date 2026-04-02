import importlib.util
from pathlib import Path


_geometry_path = Path(__file__).resolve().parents[1] / "modular_units" / "geometry.py"
_spec = importlib.util.spec_from_file_location("mu_geometry", _geometry_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

collection_name = _module.collection_name
rail_face_y_mm = _module.rail_face_y_mm
rail_hole_zs_mm = _module.rail_hole_zs_mm
total_height_mm = _module.total_height_mm


def test_collection_name():
    assert collection_name(10, False, False) == "MU_10"
    assert collection_name(10, True, False) == "MU_10.front"
    assert collection_name(10, False, True) == "MU_10.back"
    assert collection_name(10, True, True) == "MU_10.front-back"


def test_total_height_mm():
    assert total_height_mm(10, 18.0, 44.45) == 18.0 * 2.0 + 10 * 44.45


def test_rail_face_y_mm():
    front, back = rail_face_y_mm(400.0, 30.0, 30.0)
    assert front == -200.0 + 30.0
    assert back == 200.0 - 30.0


def test_rail_hole_zs_mm_count():
    hole_offsets = (6.35, 22.225, 38.1)
    positions = rail_hole_zs_mm(2, 18.0, 44.45, hole_offsets)
    assert len(positions) == 6


def test_rail_hole_zs_mm_bounds():
    hole_offsets = (6.35, 22.225, 38.1)
    positions = rail_hole_zs_mm(1, 18.0, 44.45, hole_offsets)
    assert min(positions) >= 18.0
    assert max(positions) <= 18.0 + 44.45
