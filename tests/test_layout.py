import importlib.util
import math
from pathlib import Path


_config_path = Path(__file__).resolve().parents[1] / "modular_units" / "config.py"
_geometry_path = Path(__file__).resolve().parents[1] / "modular_units" / "geometry.py"
_rails_path = Path(__file__).resolve().parents[1] / "modular_units" / "rails.py"

_config_spec = importlib.util.spec_from_file_location("mu_config", _config_path)
_config_module = importlib.util.module_from_spec(_config_spec)
_config_spec.loader.exec_module(_config_module)

_geometry_spec = importlib.util.spec_from_file_location("mu_geometry", _geometry_path)
_geometry_module = importlib.util.module_from_spec(_geometry_spec)
_geometry_spec.loader.exec_module(_geometry_module)

_rails_spec = importlib.util.spec_from_file_location("mu_rails", _rails_path)
_rails_module = importlib.util.module_from_spec(_rails_spec)
_rails_spec.loader.exec_module(_rails_module)

RackConfig = _config_module.RackConfig
rail_face_y_from_config = _geometry_module.rail_face_y_from_config
rail_hole_zs_from_config = _geometry_module.rail_hole_zs_from_config
rail_x_faces_from_config = _geometry_module.rail_x_faces_from_config
total_height_from_config = _geometry_module.total_height_from_config
rail_component_centers_mm = _rails_module.rail_component_centers_mm
rail_hole_centers_mm = _rails_module.rail_hole_centers_mm


def test_panel_centers_default_config():
    config = RackConfig()
    units = 10
    total_height = total_height_from_config(units, config)
    side_z_center = total_height * 0.5
    top_z = total_height - (config.top_bottom_z * 0.5)
    bottom_z = config.top_bottom_z * 0.5
    side_x_offset = (config.top_bottom_x * 0.5) - (config.side_x * 0.5) + 18.0

    assert total_height == 480.5
    assert top_z == 471.5
    assert bottom_z == 9.0
    assert side_z_center == 240.25
    assert side_x_offset == 254.0


def test_rail_centers_front_back_default_config():
    config = RackConfig()
    units = 10
    total_height = total_height_from_config(units, config)
    side_z_center = total_height * 0.5
    inside_x_left, inside_x_right = rail_x_faces_from_config(config, 0.0)
    front_y, back_y = rail_face_y_from_config(config, 30.0, 30.0)

    front_left = rail_component_centers_mm(
        inside_x_left - config.rail_outset,
        1.0,
        front_y,
        -1.0,
        side_z_center,
        config,
        rotation_z=math.radians(90.0),
    )
    front_right = rail_component_centers_mm(
        inside_x_right + config.rail_outset,
        -1.0,
        front_y,
        -1.0,
        side_z_center,
        config,
        rotation_z=math.radians(-90.0),
    )
    back_left = rail_component_centers_mm(
        inside_x_left - config.rail_outset,
        1.0,
        back_y,
        1.0,
        side_z_center,
        config,
        rotation_z=math.radians(-90.0),
    )
    back_right = rail_component_centers_mm(
        inside_x_right + config.rail_outset,
        -1.0,
        back_y,
        1.0,
        side_z_center,
        config,
        rotation_z=math.radians(90.0),
    )

    rail_centers = [
        (front_left, ((-244.0, -155.0, 240.25), (-234.5, -169.0, 240.25))),
        (front_right, ((244.0, -155.0, 240.25), (234.5, -169.0, 240.25))),
        (back_left, ((-244.0, 155.0, 240.25), (-234.5, 169.0, 240.25))),
        (back_right, ((244.0, 155.0, 240.25), (234.5, 169.0, 240.25))),
    ]
    for (wood_center, rack_center), (expected_wood, expected_rack) in rail_centers:
        _assert_point(wood_center, expected_wood)
        _assert_point(rack_center, expected_rack)


def test_rail_hole_centers_default_config():
    config = RackConfig()
    units = 1
    total_height = total_height_from_config(units, config)
    side_z_center = total_height * 0.5
    inside_x_left, _inside_x_right = rail_x_faces_from_config(config, 0.0)
    front_y, _back_y = rail_face_y_from_config(config, 30.0, 30.0)

    _wood_loc, rack_loc = rail_component_centers_mm(
        inside_x_left - config.rail_outset,
        1.0,
        front_y,
        -1.0,
        side_z_center,
        config,
        rotation_z=math.radians(90.0),
    )
    hole_centers = rail_hole_centers_mm(
        rack_loc,
        rail_hole_zs_from_config(units, config),
    )
    expected_hole_zs = (56.1, 40.225, 24.35)
    for hole_center, expected_z in zip(hole_centers, expected_hole_zs):
        _assert_point(hole_center, (rack_loc[0], rack_loc[1], expected_z))


def _assert_point(point, expected, tolerance=1e-6):
    assert abs(point[0] - expected[0]) < tolerance
    assert abs(point[1] - expected[1]) < tolerance
    assert abs(point[2] - expected[2]) < tolerance
