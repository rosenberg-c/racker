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

_rack_module = importlib.import_module("modular_units.rack_builder")
build_rack = _rack_module.build_rack
RackConfig = _rack_module.RackConfig


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
    )
    top.name = "MU_Top"

    side = build_panel(
        "MU_Side_Left",
        (0.018, 0.4, 0.48),
        (1.0, 0.0, 0.0),
        material,
        collection,
        bpy.context,
    )

    for obj in (top, side):
        _apply_uv_cube_project(bpy.context, obj)
        _rotate_uvs_for_axis_faces(obj.data, axis="X", clockwise=True)
        if obj.name in {"MU_Top", "MU_Bottom"}:
            _remap_uvs_for_axis_faces(
                obj.data,
                axis="Y",
                u_axis="Z",
                v_axis="X",
                flip_u=False,
                flip_v=False,
            )
        else:
            _rotate_uvs_for_axis_faces(obj.data, axis="Y", clockwise=True)

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
        _assert_uv_orientation_for_all_faces(top, (0.49, 0.4, 0.018))
    if len(side_centroids) == 6:
        _assert_uv_orientation_for_all_faces(side, (0.018, 0.4, 0.48))

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
    assert abs(top_obj.rotation_euler.y - (math.radians(90.0))) < 1e-6
    assert abs(top_obj.rotation_euler.z - 0.0) < 1e-6

    assert abs(bottom_obj.rotation_euler.x - 0.0) < 1e-6
    assert abs(bottom_obj.rotation_euler.y - (math.radians(90.0))) < 1e-6
    assert abs(bottom_obj.rotation_euler.z - 0.0) < 1e-6

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

    build_rack(
        bpy.context,
        units,
        30.0,
        30.0,
        True,
        True,
        "MU_CREATE_DEFAULT",
        thin_thickness,
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
    y_front_offset = config_thin.rail_rack_width * 0.5
    y_back_offset = config_thin.rail_rack_width * 0.5
    side_z_center_thin_m = side_z_center_thin * 0.001

    rail_front_left = bpy.data.objects.get("MU_Rail_Front_Left")
    rail_front_right = bpy.data.objects.get("MU_Rail_Front_Right")
    rail_back_left = bpy.data.objects.get("MU_Rail_Back_Left")
    rail_back_right = bpy.data.objects.get("MU_Rail_Back_Right")
    assert rail_front_left is not None
    assert rail_front_right is not None
    assert rail_back_left is not None
    assert rail_back_right is not None

    _assert_point(
        rail_front_left.location,
        ((left_x_face * 0.001), (front_y - y_front_offset) * 0.001, side_z_center_thin_m),
    )
    _assert_point(
        rail_front_right.location,
        ((right_x_face * 0.001), (front_y - y_front_offset) * 0.001, side_z_center_thin_m),
    )
    _assert_point(
        rail_back_left.location,
        ((left_x_face * 0.001), (back_y + y_back_offset) * 0.001, side_z_center_thin_m),
    )
    _assert_point(
        rail_back_right.location,
        ((right_x_face * 0.001), (back_y + y_back_offset) * 0.001, side_z_center_thin_m),
    )


if __name__ == "__main__":
    main()
def _assert_point(actual, expected, tolerance=1e-6):
    assert abs(actual[0] - expected[0]) < tolerance
    assert abs(actual[1] - expected[1]) < tolerance
    assert abs(actual[2] - expected[2]) < tolerance
