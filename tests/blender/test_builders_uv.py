import math

try:
    import bpy
except ModuleNotFoundError:
    try:
        import pytest
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError("bpy is required to run this test") from exc
    pytest.skip("bpy is required to run this test", allow_module_level=True)

from modular_units.builders import build_panel


def _corr(a, b):
    mean_a = sum(a) / len(a)
    mean_b = sum(b) / len(b)
    num = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    den_a = math.sqrt(sum((x - mean_a) ** 2 for x in a))
    den_b = math.sqrt(sum((y - mean_b) ** 2 for y in b))
    if den_a == 0.0 or den_b == 0.0:
        return 0.0
    return num / (den_a * den_b)


def _assert_uv_orientation_for_x_faces(obj):
    mesh = obj.data
    uv_layer = mesh.uv_layers.active
    assert uv_layer is not None

    x_faces = [face for face in mesh.polygons if abs(face.normal.x) > 0.9]
    assert x_faces

    for face in x_faces:
        uvs = []
        ys = []
        zs = []
        for loop_index in face.loop_indices:
            u, v = uv_layer.data[loop_index].uv
            vert_index = mesh.loops[loop_index].vertex_index
            vert = mesh.vertices[vert_index].co
            uvs.append((u, v))
            ys.append(vert.y)
            zs.append(vert.z)

        us = [uv[0] for uv in uvs]
        vs = [uv[1] for uv in uvs]

        corr_u_y = abs(_corr(us, ys))
        corr_u_z = abs(_corr(us, zs))
        corr_v_y = abs(_corr(vs, ys))
        corr_v_z = abs(_corr(vs, zs))

        assert corr_u_z >= corr_u_y
        assert corr_v_y >= corr_v_z


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    collection = bpy.context.scene.collection
    material = bpy.data.materials.new(name="MU_Test_Material")

    obj = build_panel(
        "MU_Test_Panel",
        (0.49, 0.4, 0.018),
        (0.0, 0.0, 0.0),
        material,
        collection,
        bpy.context,
    )

    assert obj.data.materials
    assert obj.data.materials[0] == material
    assert obj.active_material == material
    assert obj.data.uv_layers

    _assert_uv_orientation_for_x_faces(obj)


if __name__ == "__main__":
    main()
