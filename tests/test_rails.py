import importlib.util
import math
from pathlib import Path


_rails_path = Path(__file__).resolve().parents[1] / "modular_units" / "rails.py"
_spec = importlib.util.spec_from_file_location("mu_rails", _rails_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

rail_component_centers_mm = _module.rail_component_centers_mm
rail_hole_centers_mm = _module.rail_hole_centers_mm


class _Config:
    rail_wood_width = 30.0
    rail_thickness = 2.0
    rail_rack_width = 21.0


def test_rail_component_centers_no_rotation():
    wood_loc, rack_loc = rail_component_centers_mm(
        x_face=0.0,
        x_inward=1.0,
        y_face=0.0,
        y_inward=-1.0,
        side_z_center=100.0,
        config=_Config(),
    )
    assert wood_loc == (15.0, -1.0, 100.0)
    assert rack_loc == (1.0, -10.5, 100.0)


def test_rail_component_centers_rotation_z():
    wood_loc, rack_loc = rail_component_centers_mm(
        x_face=0.0,
        x_inward=1.0,
        y_face=0.0,
        y_inward=-1.0,
        side_z_center=100.0,
        config=_Config(),
        rotation_z=math.radians(90.0),
    )
    assert abs(wood_loc[0] - 1.0) < 1e-6
    assert abs(wood_loc[1] - 15.0) < 1e-6
    assert wood_loc[2] == 100.0
    assert abs(rack_loc[0] - 10.5) < 1e-6
    assert abs(rack_loc[1] - 1.0) < 1e-6
    assert rack_loc[2] == 100.0


def test_rail_hole_centers_mm():
    rack_loc = (1.0, -10.5, 100.0)
    hole_zs = (10.0, 20.0, 30.0)
    centers = rail_hole_centers_mm(rack_loc, hole_zs)
    assert centers == [
        (1.0, -10.5, 10.0),
        (1.0, -10.5, 20.0),
        (1.0, -10.5, 30.0),
    ]
