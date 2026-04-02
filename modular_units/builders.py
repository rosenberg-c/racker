import math

import bpy
import bmesh
import mathutils


def build_panel(name, dimensions, location, material, collection):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    bm = bmesh.new()
    _add_box(bm, dimensions, location, rotation_z=None)
    bm.to_mesh(mesh)
    bm.free()

    if material is not None:
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)

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


def _apply_boolean_difference(context, target_obj, cutter_obj):
    modifier = target_obj.modifiers.new(name="MU_Holes", type="BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.object = cutter_obj
    with context.temp_override(object=target_obj, active_object=target_obj):
        bpy.ops.object.modifier_apply(modifier=modifier.name)
