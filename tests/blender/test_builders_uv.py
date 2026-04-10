import importlib
import importlib.util
import math
from pathlib import Path
import sys

try:
    import bpy
except ModuleNotFoundError:
    try:
        import pytest
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("bpy is required to run this test") from exc
    pytest.skip("bpy is required to run this test", allow_module_level=True)

_builders_path = Path(__file__).resolve().parents[2] / "modular_units" / "builders.py"
_spec = importlib.util.spec_from_file_location("mu_builders", _builders_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
build_panel = _module.build_panel
_apply_uv_cube_project = _module._apply_uv_cube_project
_rotate_uvs_for_axis_faces = _module._rotate_uvs_for_axis_faces
_remap_uvs_for_axis_faces = _module._remap_uvs_for_axis_faces

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

def _reload_modular_units():
    for name in list(sys.modules):
        if name == "modular_units" or name.startswith("modular_units."):
            del sys.modules[name]


_reload_modular_units()
_rack_module = importlib.import_module("modular_units.rack_builder")
build_rack = _rack_module.build_rack
RackConfig = _rack_module.RackConfig
_geometry_module = importlib.import_module("modular_units.geometry")
collection_name = _geometry_module.collection_name
rail_hole_zs_from_config = _geometry_module.rail_hole_zs_from_config
_faceplate_module = importlib.import_module("modular_units.faceplate_builder")
build_faceplate = _faceplate_module.build_faceplate
_body_module = importlib.import_module("modular_units.body_builder")
build_body = _body_module.build_body
_shelf_module = importlib.import_module("modular_units.shelf_builder")
build_shelf = _shelf_module.build_shelf
_rails_module = importlib.import_module("modular_units.rails")
rail_component_centers_mm = _rails_module.rail_component_centers_mm
_geometry_module = importlib.import_module("modular_units.geometry")
rail_length_from_config = _geometry_module.rail_length_from_config


def _corr(a, b):
    mean_a = sum(a) / len(a)
    mean_b = sum(b) / len(b)
    num = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    den_a = math.sqrt(sum((x - mean_a) ** 2 for x in a))
    den_b = math.sqrt(sum((y - mean_b) ** 2 for y in b))
    if den_a == 0.0 or den_b == 0.0:
        return 0.0
    return num / (den_a * den_b)


def _axis_from_normal(normal):
    ax = abs(normal.x)
    ay = abs(normal.y)
    az = abs(normal.z)
    if ax >= ay and ax >= az:
        return "X"
    if ay >= az:
        return "Y"
    return "Z"


def _axis_from_world_normal(normal, matrix_world):
    world_normal = (matrix_world.to_3x3() @ normal).normalized()
    return _axis_from_normal(world_normal)


def _expected_grain_axis(dimensions, face_axis):
    dims = {"X": dimensions[0], "Y": dimensions[1], "Z": dimensions[2]}
    plane_axes = [axis for axis in ("X", "Y", "Z") if axis != face_axis]
    return max(plane_axes, key=lambda axis: dims[axis])


def _axis_corr(values, axis_values):
    return abs(_corr(values, axis_values))


def _assert_uv_orientation_for_all_faces(
    obj,
    dimensions,
    tolerance=0.9,
    include_axes=("X", "Y", "Z"),
):
    mesh = obj.data
    uv_layer = mesh.uv_layers.active
    assert uv_layer is not None

    for face in mesh.polygons:
        face_axis = _axis_from_normal(face.normal)
        if face_axis not in include_axes:
            continue
        expected_axis = _expected_grain_axis(dimensions, face_axis)

        us = []
        xs = []
        ys = []
        zs = []
        for loop_index in face.loop_indices:
            u, _v = uv_layer.data[loop_index].uv
            vert_index = mesh.loops[loop_index].vertex_index
            vert = mesh.vertices[vert_index].co
            us.append(u)
            xs.append(vert.x)
            ys.append(vert.y)
            zs.append(vert.z)

        corrs = {
            "X": _axis_corr(us, xs),
            "Y": _axis_corr(us, ys),
            "Z": _axis_corr(us, zs),
        }
        spans = {
            "X": max(xs) - min(xs),
            "Y": max(ys) - min(ys),
            "Z": max(zs) - min(zs),
        }
        assert corrs[expected_axis] >= tolerance, (
            f"face_axis={face_axis} expected_u={expected_axis} corrs={corrs} spans={spans}"
        )


def _assert_uv_u_orientation_for_axis_faces(
    obj,
    face_axis,
    expected_axis,
    tolerance=0.9,
    use_world=False,
):
    mesh = obj.data
    uv_layer = mesh.uv_layers.active
    assert uv_layer is not None

    for face in mesh.polygons:
        if use_world:
            axis = _axis_from_world_normal(face.normal, obj.matrix_world)
        else:
            axis = _axis_from_normal(face.normal)
        if axis != face_axis:
            continue

        us = []
        xs = []
        ys = []
        zs = []
        for loop_index in face.loop_indices:
            u, _v = uv_layer.data[loop_index].uv
            vert_index = mesh.loops[loop_index].vertex_index
            vert = mesh.vertices[vert_index].co
            if use_world:
                vert = obj.matrix_world @ vert
            us.append(u)
            xs.append(vert.x)
            ys.append(vert.y)
            zs.append(vert.z)

        corrs = {
            "X": _axis_corr(us, xs),
            "Y": _axis_corr(us, ys),
            "Z": _axis_corr(us, zs),
        }
        spans = {
            "X": max(xs) - min(xs),
            "Y": max(ys) - min(ys),
            "Z": max(zs) - min(zs),
        }
        assert corrs[expected_axis] >= tolerance, (
            f"face_axis={face_axis} expected_u={expected_axis} corrs={corrs} spans={spans}"
        )


def _unique_uv_centroids(mesh, tolerance=1e-4):
    uv_layer = mesh.uv_layers.active
    assert uv_layer is not None

    centroids = []
    for face in mesh.polygons:
        us = []
        vs = []
        for loop_index in face.loop_indices:
            u, v = uv_layer.data[loop_index].uv
            us.append(u)
            vs.append(v)
        centroid = (sum(us) / len(us), sum(vs) / len(vs))
        centroids.append(centroid)

    unique = []
    for centroid in centroids:
        if not any(
            abs(centroid[0] - existing[0]) < tolerance
            and abs(centroid[1] - existing[1]) < tolerance
            for existing in unique
        ):
            unique.append(centroid)

    return unique


def _assert_point(actual, expected, tolerance=1e-6):
    assert abs(actual[0] - expected[0]) < tolerance, (
        f"actual={actual} expected={expected} axis=x"
    )
    assert abs(actual[1] - expected[1]) < tolerance, (
        f"actual={actual} expected={expected} axis=y"
    )
    assert abs(actual[2] - expected[2]) < tolerance, (
        f"actual={actual} expected={expected} axis=z"
    )


def _mesh_bounds_center(obj):
    mesh = obj.data
    assert mesh.vertices
    min_x = float("inf")
    min_y = float("inf")
    min_z = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")
    max_z = float("-inf")
    for vert in mesh.vertices:
        world = obj.matrix_world @ vert.co
        min_x = min(min_x, world.x)
        min_y = min(min_y, world.y)
        min_z = min(min_z, world.z)
        max_x = max(max_x, world.x)
        max_y = max(max_y, world.y)
        max_z = max(max_z, world.z)
    return ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, (min_z + max_z) * 0.5)


def _mesh_bounds(obj):
    mesh = obj.data
    assert mesh.vertices
    min_x = float("inf")
    min_y = float("inf")
    min_z = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")
    max_z = float("-inf")
    for vert in mesh.vertices:
        world = obj.matrix_world @ vert.co
        min_x = min(min_x, world.x)
        min_y = min(min_y, world.y)
        min_z = min(min_z, world.z)
        max_x = max(max_x, world.x)
        max_y = max(max_y, world.y)
        max_z = max(max_z, world.z)
    return (min_x, min_y, min_z), (max_x, max_y, max_z)


def _mesh_has_vertex_z(obj, target_z, tolerance=1e-5):
    mesh = obj.data
    assert mesh.vertices
    for vert in mesh.vertices:
        world = obj.matrix_world @ vert.co
        if abs(world.z - target_z) < tolerance:
            return True
    return False


def _bounds_from_center(center, dimensions, rotation_z):
    half_x = dimensions[0] * 0.5
    half_y = dimensions[1] * 0.5
    half_z = dimensions[2] * 0.5
    rotation = abs(rotation_z or 0.0) % (math.pi * 2.0)
    if abs(rotation - math.radians(90.0)) < 1e-6 or abs(
        rotation - math.radians(270.0)
    ) < 1e-6:
        half_x, half_y = half_y, half_x
    min_point = (center[0] - half_x, center[1] - half_y, center[2] - half_z)
    max_point = (center[0] + half_x, center[1] + half_y, center[2] + half_z)
    return min_point, max_point


def _combined_bounds_center(wood_center, rack_center, wood_dims, rack_dims, rotation_z):
    wood_min, wood_max = _bounds_from_center(wood_center, wood_dims, rotation_z)
    rack_min, rack_max = _bounds_from_center(rack_center, rack_dims, rotation_z)
    min_x = min(wood_min[0], rack_min[0])
    min_y = min(wood_min[1], rack_min[1])
    min_z = min(wood_min[2], rack_min[2])
    max_x = max(wood_max[0], rack_max[0])
    max_y = max(wood_max[1], rack_max[1])
    max_z = max(wood_max[2], rack_max[2])
    return ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, (min_z + max_z) * 0.5)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    collection = bpy.context.scene.collection
    material = bpy.data.materials.new(name="MU_Test_Material")

    top = build_panel(
        "MU_Test_Panel",
        (0.49, 0.4, 0.018),
        (0.0, 0.0, 0.0),
        material,
        collection,
        bpy.context,
        uv_rotation=(0.0, math.radians(90.0), 0.0),
        top_bottom_uv_mode="standard",
    )
    top.name = "MU_Top"

    side = build_panel(
        "MU_Side_Left",
        (0.48, 0.4, 0.018),
        (1.0, 0.0, 0.0),
        material,
        collection,
        bpy.context,
        uv_rotation=(0.0, math.radians(90.0), 0.0),
    )

    for obj in (top, side):
        assert obj.data.materials
        assert obj.data.materials[0] == material
        assert obj.active_material == material
        assert obj.data.uv_layers

    top_centroids = _unique_uv_centroids(top.data)
    side_centroids = _unique_uv_centroids(side.data)

    assert len(top_centroids) in (1, 6)
    assert len(side_centroids) in (1, 6)

    if len(top_centroids) == 6:
        _assert_uv_orientation_for_all_faces(
            top,
            (0.49, 0.4, 0.018),
            include_axes=("Y", "Z"),
        )
        _assert_uv_u_orientation_for_axis_faces(top, "Z", "X")
        _assert_uv_u_orientation_for_axis_faces(top, "Y", "X")
        _assert_uv_u_orientation_for_axis_faces(
            top,
            "Y",
            "X",
            use_world=True,
        )
    if len(side_centroids) == 6:
        _assert_uv_orientation_for_all_faces(
            side,
            (0.48, 0.4, 0.018),
            include_axes=("Y", "Z"),
        )
        _assert_uv_u_orientation_for_axis_faces(side, "Z", "X")
        _assert_uv_u_orientation_for_axis_faces(
            side,
            "Y",
            "X",
            use_world=True,
        )

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    config = RackConfig()
    units = 10
    total_height = (config.top_bottom_z * 2.0) + (units * config.unit_height)
    top_z = total_height - (config.top_bottom_z * 0.5)
    bottom_z = config.top_bottom_z * 0.5

    build_rack(
        bpy.context,
        units,
        30.0,
        30.0,
        True,
        True,
        "MU_CREATE_DEFAULT",
        18.0,
        depth_mm=400.0,
        unit_margin_mm=0.0,
    )

    top_obj = bpy.data.objects.get("MU_Top")
    bottom_obj = bpy.data.objects.get("MU_Bottom")
    assert top_obj is not None
    assert bottom_obj is not None

    assert abs(top_obj.location.x - 0.0) < 1e-6
    assert abs(top_obj.location.y - 0.0) < 1e-6
    assert abs(top_obj.location.z - (top_z * 0.001)) < 1e-6

    assert abs(bottom_obj.location.x - 0.0) < 1e-6
    assert abs(bottom_obj.location.y - 0.0) < 1e-6
    assert abs(bottom_obj.location.z - (bottom_z * 0.001)) < 1e-6

    assert abs(top_obj.rotation_euler.x - 0.0) < 1e-6
    assert abs(top_obj.rotation_euler.y - 0.0) < 1e-6
    assert abs(top_obj.rotation_euler.z - 0.0) < 1e-6

    assert abs(bottom_obj.rotation_euler.x - 0.0) < 1e-6
    assert abs(bottom_obj.rotation_euler.y - 0.0) < 1e-6
    assert abs(bottom_obj.rotation_euler.z - 0.0) < 1e-6

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    unit_margin = 4.0
    total_height_margin = total_height + unit_margin
    top_z_margin = total_height_margin - (config.top_bottom_z * 0.5)
    bottom_z_margin = config.top_bottom_z * 0.5
    expected_collection_base = collection_name(
        units,
        18.0,
        400.0,
        True,
        True,
        unit_margin,
    )

    build_rack(
        bpy.context,
        units,
        30.0,
        30.0,
        True,
        True,
        "MU_CREATE_DEFAULT",
        18.0,
        depth_mm=400.0,
        unit_margin_mm=unit_margin,
    )

    top_obj = bpy.data.objects.get("MU_Top")
    bottom_obj = bpy.data.objects.get("MU_Bottom")
    rail_front_left = bpy.data.objects.get("MU_Rail_Front_Left")
    assert top_obj is not None
    assert bottom_obj is not None
    assert rail_front_left is not None
    assert abs(top_obj.location.z - (top_z_margin * 0.001)) < 1e-6
    assert abs(bottom_obj.location.z - (bottom_z_margin * 0.001)) < 1e-6
    rail_center = _mesh_bounds_center(rail_front_left)
    expected_rail_center_z = (total_height * 0.5) * 0.001
    assert abs(rail_center[2] - expected_rail_center_z) < 1e-6
    collections = [collection.name for collection in bpy.data.collections]
    assert any(
        name == expected_collection_base or name.startswith(f"{expected_collection_base}.")
        for name in collections
    )
    hole_zs = rail_hole_zs_from_config(units, config)
    for hole_z in hole_zs:
        assert _mesh_has_vertex_z(rail_front_left, hole_z * 0.001)
    boolean_modifiers = [
        modifier
        for modifier in rail_front_left.modifiers
        if modifier.type == "BOOLEAN"
    ]
    assert boolean_modifiers

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    thin_thickness = 12.0
    config_thin = RackConfig(
        top_bottom_z=thin_thickness,
        side_x=thin_thickness,
    )
    total_height_thin = (config_thin.top_bottom_z * 2.0) + (units * config_thin.unit_height)
    side_z_center_thin = total_height_thin * 0.5
    side_x_offset_thin = (
        (config_thin.top_bottom_x * 0.5)
        - (config_thin.side_x * 0.5)
        + config_thin.side_x
    )
    rail_length_thin = rail_length_from_config(units, config_thin)

    build_rack(
        bpy.context,
        units,
        30.0,
        30.0,
        True,
        True,
        "MU_CREATE_DEFAULT",
        thin_thickness,
        depth_mm=400.0,
        unit_margin_mm=0.0,
    )

    side_left = bpy.data.objects.get("MU_Side_Left")
    side_right = bpy.data.objects.get("MU_Side_Right")
    assert side_left is not None
    assert side_right is not None

    assert abs(side_left.location.x - (-side_x_offset_thin * 0.001)) < 1e-6
    assert abs(side_left.location.y - 0.0) < 1e-6
    assert abs(side_left.location.z - (side_z_center_thin * 0.001)) < 1e-6

    assert abs(side_right.location.x - (side_x_offset_thin * 0.001)) < 1e-6
    assert abs(side_right.location.y - 0.0) < 1e-6
    assert abs(side_right.location.z - (side_z_center_thin * 0.001)) < 1e-6

    inside_left_thin = (
        -((config_thin.top_bottom_x * 0.5) - config_thin.side_x)
        - (config_thin.side_x - 18.0)
    )
    inside_right_thin = (
        ((config_thin.top_bottom_x * 0.5) - config_thin.side_x)
        + (config_thin.side_x - 18.0)
    )
    left_x_face = inside_left_thin - config_thin.rail_outset
    right_x_face = inside_right_thin + config_thin.rail_outset
    front_y = -(config_thin.top_bottom_y * 0.5) + 30.0
    back_y = (config_thin.top_bottom_y * 0.5) - 30.0

    rail_front_left = bpy.data.objects.get("MU_Rail_Front_Left")
    rail_front_right = bpy.data.objects.get("MU_Rail_Front_Right")
    rail_back_left = bpy.data.objects.get("MU_Rail_Back_Left")
    rail_back_right = bpy.data.objects.get("MU_Rail_Back_Right")
    assert rail_front_left is not None
    assert rail_front_right is not None
    assert rail_back_left is not None
    assert rail_back_right is not None

    wood_dimensions = (
        config_thin.rail_wood_width,
        config_thin.rail_thickness,
        rail_length_thin,
    )
    rack_dimensions = (
        config_thin.rail_thickness,
        config_thin.rail_rack_width,
        rail_length_thin,
    )

    def _expected_bounds_center(x_face, x_inward, y_face, y_inward, rotation_z):
        wood_center, rack_center = rail_component_centers_mm(
            x_face,
            x_inward,
            y_face,
            y_inward,
            side_z_center_thin,
            config_thin,
            rotation_z=rotation_z,
        )
        return _combined_bounds_center(
            wood_center,
            rack_center,
            wood_dimensions,
            rack_dimensions,
            rotation_z,
        )

    rail_expectations = [
        (rail_front_left, left_x_face, 1.0, front_y, -1.0, math.radians(90.0)),
        (rail_front_right, right_x_face, -1.0, front_y, -1.0, math.radians(-90.0)),
        (rail_back_left, left_x_face, 1.0, back_y, 1.0, math.radians(-90.0)),
        (rail_back_right, right_x_face, -1.0, back_y, 1.0, math.radians(90.0)),
    ]

    for rail_obj, x_face, x_inward, y_face, y_inward, rotation_z in rail_expectations:
        _assert_point(
            _mesh_bounds_center(rail_obj),
            tuple(
                value * 0.001
                for value in _expected_bounds_center(
                    x_face,
                    x_inward,
                    y_face,
                    y_inward,
                    rotation_z,
                )
            ),
        )

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    faceplate_units = 2
    build_faceplate(bpy.context, faceplate_units)
    faceplate_collection = bpy.data.collections.get(f"MU_Faceplate_{faceplate_units}U")
    assert faceplate_collection is not None
    faceplate = bpy.data.objects.get("MU_Faceplate")
    holes = bpy.data.objects.get("MU_Faceplate_Holes")
    assert faceplate is not None
    assert holes is not None
    assert faceplate.name in faceplate_collection.objects
    assert holes.name in faceplate_collection.objects
    modifiers = [modifier for modifier in faceplate.modifiers if modifier.type == "BOOLEAN"]
    assert modifiers
    assert modifiers[0].object == holes

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    build_body(bpy.context, 1, 438.0, 200.0)
    body = bpy.data.objects.get("MU_Body")
    assert body is not None

    build_shelf(bpy.context, 1, 438.0, 200.0, 2.0)
    shelf = bpy.data.objects.get("MU_Shelf")
    assert shelf is not None
    min_bounds, max_bounds = _mesh_bounds(shelf)
    assert abs(min_bounds[0] - (-0.2415)) < 1e-6
    assert abs(max_bounds[0] - 0.2415) < 1e-6
    assert abs(min_bounds[1] - (-0.002)) < 1e-6
    assert abs(max_bounds[1] - 0.2) < 1e-6
    assert abs(min_bounds[2] - 0.0) < 1e-6
    assert abs(max_bounds[2] - 0.04445) < 1e-6


if __name__ == "__main__":
    main()
