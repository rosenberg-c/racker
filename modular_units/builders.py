import math

import bpy
import bmesh
import mathutils


def build_panel(name, dimensions, location, material, collection, context):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    bm = bmesh.new()
    _add_box(bm, dimensions, location, rotation_z=None)
    bm.to_mesh(mesh)
    bm.free()

    if material is not None:
        obj.data.materials.clear()
        obj.data.materials.append(material)
        mesh.materials.clear()
        mesh.materials.append(material)
        if obj.material_slots:
            obj.material_slots[0].material = material
        obj.active_material_index = 0
        obj.active_material = material
        mesh.update()

    _apply_uv_cube_project(context, obj)

    return obj


def build_rail(
    name,
    wood_dimensions,
    rack_dimensions,
    wood_location,
    rack_location,
    rotation_z,
    hole_centers,
    hole_radius,
    hole_depth,
    collection,
    context,
):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    bm = bmesh.new()
    _add_box(bm, wood_dimensions, wood_location, rotation_z=rotation_z)
    _add_box(bm, rack_dimensions, rack_location, rotation_z=rotation_z)
    bm.to_mesh(mesh)
    bm.free()

    if hole_centers:
        holes_obj = build_holes_object(
            f"{name}_Holes",
            hole_centers,
            hole_radius,
            hole_depth,
            rotation_z,
            collection,
        )
        _apply_boolean_difference(context, obj, holes_obj)
        bpy.data.objects.remove(holes_obj, do_unlink=True)

    return obj


def build_holes_object(
    name,
    hole_centers,
    hole_radius,
    hole_depth,
    rotation_z,
    collection,
):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    bm = bmesh.new()
    rotation = (0.0, math.radians(90.0), rotation_z)
    for center in hole_centers:
        _add_cylinder(bm, hole_radius, hole_depth, center, rotation)
    bm.to_mesh(mesh)
    bm.free()

    return obj


def _add_box(bm, dimensions, location, rotation_z=None):
    geom = bmesh.ops.create_cube(bm, size=1.0)
    verts = geom["verts"]
    bmesh.ops.scale(
        bm,
        verts=verts,
        vec=(dimensions[0], dimensions[1], dimensions[2]),
    )
    bmesh.ops.translate(bm, verts=verts, vec=location)
    if rotation_z:
        rot = mathutils.Euler((0.0, 0.0, rotation_z), "XYZ").to_matrix().to_4x4()
        bmesh.ops.rotate(bm, verts=verts, cent=location, matrix=rot)


def _add_cylinder(bm, radius, depth, location, rotation):
    geom = bmesh.ops.create_cone(
        bm,
        segments=32,
        radius1=radius,
        radius2=radius,
        depth=depth,
    )
    verts = geom["verts"]
    rot = mathutils.Euler(rotation, "XYZ").to_matrix().to_4x4()
    bmesh.ops.rotate(bm, verts=verts, cent=(0.0, 0.0, 0.0), matrix=rot)
    bmesh.ops.translate(bm, verts=verts, vec=location)


def _apply_uv_cube_project(context, obj):
    view_layer = context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = list(context.selected_objects)

    try:
        for selected in prev_selected:
            selected.select_set(False)
        obj.select_set(True)
        view_layer.objects.active = obj

        if obj.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.cube_project(cube_size=1.0)
        bpy.ops.object.mode_set(mode="OBJECT")
    finally:
        for selected in context.selected_objects:
            selected.select_set(False)
        for selected in prev_selected:
            selected.select_set(True)
        view_layer.objects.active = prev_active

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


def _apply_boolean_difference(context, target_obj, cutter_obj):
    modifier = target_obj.modifiers.new(name="MU_Holes", type="BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.object = cutter_obj
    view_layer = context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = list(context.selected_objects)

    try:
        for selected in prev_selected:
            selected.select_set(False)
        target_obj.select_set(True)
        view_layer.objects.active = target_obj
        if target_obj.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    finally:
        for selected in context.selected_objects:
            selected.select_set(False)
        for selected in prev_selected:
            selected.select_set(True)
        view_layer.objects.active = prev_active


def _rotate_uvs_for_axis_faces(mesh, axis, clockwise):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    uv_layer = bm.loops.layers.uv.verify()

    axis_index = {"X": 0, "Y": 1, "Z": 2}[axis]
    for face in bm.faces:
        normal = face.normal
        if axis_index == 0:
            match = abs(normal.x) >= abs(normal.y) and abs(normal.x) >= abs(normal.z)
        elif axis_index == 1:
            match = abs(normal.y) >= abs(normal.x) and abs(normal.y) >= abs(normal.z)
        else:
            match = abs(normal.z) >= abs(normal.x) and abs(normal.z) >= abs(normal.y)
        if not match:
            continue

        for loop in face.loops:
            u, v = loop[uv_layer].uv
            u -= 0.5
            v -= 0.5
            if clockwise:
                u, v = v, -u
            else:
                u, v = -v, u
            loop[uv_layer].uv = (u + 0.5, v + 0.5)

    bm.to_mesh(mesh)
    bm.free()


def _rotate_uvs_for_axis_faces_by_normal(
    mesh,
    axis,
    clockwise_for_positive,
    flip_u=False,
    flip_v=False,
):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    uv_layer = bm.loops.layers.uv.verify()

    axis_index = {"X": 0, "Y": 1, "Z": 2}[axis]
    for face in bm.faces:
        normal = face.normal
        if axis_index == 0:
            match = abs(normal.x) >= abs(normal.y) and abs(normal.x) >= abs(normal.z)
            sign = normal.x
        elif axis_index == 1:
            match = abs(normal.y) >= abs(normal.x) and abs(normal.y) >= abs(normal.z)
            sign = normal.y
        else:
            match = abs(normal.z) >= abs(normal.x) and abs(normal.z) >= abs(normal.y)
            sign = normal.z
        if not match:
            continue

        clockwise = clockwise_for_positive if sign >= 0.0 else not clockwise_for_positive
        for loop in face.loops:
            u, v = loop[uv_layer].uv
            u -= 0.5
            v -= 0.5
            if clockwise:
                u, v = v, -u
            else:
                u, v = -v, u
            if flip_u:
                u = -u
            if flip_v:
                v = -v
            loop[uv_layer].uv = (u + 0.5, v + 0.5)

    bm.to_mesh(mesh)
    bm.free()


def _remap_uvs_for_axis_faces(mesh, axis, u_axis, v_axis, flip_u=False, flip_v=False):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    uv_layer = bm.loops.layers.uv.verify()

    axis_index = {"X": 0, "Y": 1, "Z": 2}[axis]
    coord_index = {"X": 0, "Y": 1, "Z": 2}
    u_index = coord_index[u_axis]
    v_index = coord_index[v_axis]

    for face in bm.faces:
        normal = face.normal
        if axis_index == 0:
            match = abs(normal.x) >= abs(normal.y) and abs(normal.x) >= abs(normal.z)
        elif axis_index == 1:
            match = abs(normal.y) >= abs(normal.x) and abs(normal.y) >= abs(normal.z)
        else:
            match = abs(normal.z) >= abs(normal.x) and abs(normal.z) >= abs(normal.y)
        if not match:
            continue

        face_uvs = []
        for loop in face.loops:
            vec = loop.vert.co
            u = vec[u_index]
            v = vec[v_index]
            face_uvs.append((loop, u, v))

        min_u = min(value[1] for value in face_uvs)
        max_u = max(value[1] for value in face_uvs)
        min_v = min(value[2] for value in face_uvs)
        max_v = max(value[2] for value in face_uvs)
        span_u = max_u - min_u
        span_v = max_v - min_v

        for loop, u, v in face_uvs:
            if span_u != 0.0:
                u = (u - min_u) / span_u
            else:
                u = 0.0
            if span_v != 0.0:
                v = (v - min_v) / span_v
            else:
                v = 0.0
            if flip_u:
                u = 1.0 - u
            if flip_v:
                v = 1.0 - v
            loop[uv_layer].uv = (u, v)

    bm.to_mesh(mesh)
    bm.free()


def _swap_uvs_for_axis_faces(mesh, axis):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    uv_layer = bm.loops.layers.uv.verify()

    axis_index = {"X": 0, "Y": 1, "Z": 2}[axis]
    for face in bm.faces:
        normal = face.normal
        if axis_index == 0:
            match = abs(normal.x) >= abs(normal.y) and abs(normal.x) >= abs(normal.z)
        elif axis_index == 1:
            match = abs(normal.y) >= abs(normal.x) and abs(normal.y) >= abs(normal.z)
        else:
            match = abs(normal.z) >= abs(normal.x) and abs(normal.z) >= abs(normal.y)
        if not match:
            continue

        for loop in face.loops:
            u, v = loop[uv_layer].uv
            loop[uv_layer].uv = (v, u)

    bm.to_mesh(mesh)
    bm.free()
