import importlib.util
import math
from pathlib import Path

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

        if max(us) - min(us) < 1e-6:
            continue

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


def _assert_uv_face_centroids(mesh, expected_count=1, tolerance=1e-4):
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

    assert len(unique) == expected_count, (
        f"unique_centroids={len(unique)} centroids={centroids}"
    )


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
        assert obj.data.materials
        assert obj.data.materials[0] == material
        assert obj.active_material == material
        assert obj.data.uv_layers

    _assert_uv_face_centroids(top.data)
    _assert_uv_face_centroids(side.data)


if __name__ == "__main__":
    main()
