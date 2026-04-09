import math

import bpy
import bmesh
import mathutils

from .builders import build_panel, _apply_boolean_difference
from .config import RackConfig


def build_faceplate(
    context,
    units,
    width_mm=483.0,
    thickness_mm=2.0,
    hole_diameter_mm=7.1,
    material=None,
    collection=None,
):
    config = RackConfig()
    height_mm = units * config.unit_height
    mm_to_m = 0.001

    if collection is None:
        collection = context.scene.collection

    y_center = -(thickness_mm * 0.5) * mm_to_m
    obj = build_panel(
        "MU_Faceplate",
        (width_mm * mm_to_m, thickness_mm * mm_to_m, height_mm * mm_to_m),
        (0.0, y_center, height_mm * 0.5 * mm_to_m),
        material,
        collection,
        context,
    )

    hole_radius = hole_diameter_mm * 0.5
    hole_depth = thickness_mm * 2.0

    hole_zs = faceplate_hole_zs_mm(units, config.unit_height, config.hole_offsets)
    hole_offset_x = 232.5
    hole_centers = []
    for hole_z in hole_zs:
        hole_centers.append((hole_offset_x * mm_to_m, y_center, hole_z * mm_to_m))
        hole_centers.append((-hole_offset_x * mm_to_m, y_center, hole_z * mm_to_m))

    holes_obj = _build_holes_object_y(
        "MU_Faceplate_Holes",
        hole_centers,
        hole_radius * mm_to_m,
        hole_depth * mm_to_m,
        collection,
    )
    _apply_boolean_difference(context, obj, holes_obj)
    bpy.data.objects.remove(holes_obj, do_unlink=True)

    return obj


def faceplate_hole_zs_mm(units, unit_height, hole_offsets):
    top_offset = hole_offsets[0]
    total_height = units * unit_height
    return [total_height - top_offset, top_offset]


def _build_holes_object_y(
    name,
    hole_centers,
    hole_radius,
    hole_depth,
    collection,
):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    bm = bmesh.new()
    rotation = (math.radians(90.0), 0.0, 0.0)
    for center in hole_centers:
        _add_cylinder(bm, hole_radius, hole_depth, center, rotation)
    bm.to_mesh(mesh)
    bm.free()

    return obj


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
