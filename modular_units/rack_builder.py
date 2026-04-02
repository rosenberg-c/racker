import math

import bpy

from .builders import build_panel, build_rail
from .config import RackConfig
from .geometry import (
    collection_name,
    rail_face_y_from_config,
    rail_hole_zs_from_config,
    rail_length_from_config,
    rail_x_faces_from_config,
    total_height_from_config,
    unique_collection_name,
)
from .rails import rail_component_centers_mm, rail_hole_centers_mm


DEFAULT_MATERIAL_NAME = "material.shelf.pine.800x400x18"


def mu_material_items(self, context):
    items = [("MU_CREATE_DEFAULT", "Create default material", "")]
    for material in bpy.data.materials:
        if material.library is not None:
            continue
        if material.asset_data is None:
            continue
        items.append((material.name, material.name, ""))
    return items


def build_rack(
    context,
    units,
    rail_offset_front,
    rail_offset_back,
    front_rails,
    back_rails,
    material_selection,
):
    config = RackConfig()
    mm_to_m = 0.001
    total_height = total_height_from_config(units, config)
    side_z = total_height
    rail_length = rail_length_from_config(units, config)

    def to_m(values):
        return tuple(value * mm_to_m for value in values)

    def ensure_collection(name):
        existing = {collection.name for collection in bpy.data.collections}
        resolved = unique_collection_name(name, existing)
        collection = bpy.data.collections.new(resolved)
        context.scene.collection.children.link(collection)
        return collection

    def ensure_material(name):
        material = bpy.data.materials.get(name)
        if material is None:
            material = bpy.data.materials.new(name=name)
        return material

    def add_box(name, dimensions, location, material, collection):
        return build_panel(
            name,
            to_m(dimensions),
            to_m(location),
            material,
            collection,
            context,
        )

    def add_rail(name_prefix, x_face, x_inward, y_face, y_inward, rotation=None):
        rotation_z = rotation[2] if rotation is not None else 0.0
        wood_loc, rack_loc = rail_component_centers_mm(
            x_face,
            x_inward,
            y_face,
            y_inward,
            side_z_center,
            config,
            rotation_z=rotation_z,
        )

        hole_radius = config.hole_diameter * 0.5
        hole_depth = config.rail_thickness * 1.5
        hole_centers = [
            to_m(center)
            for center in rail_hole_centers_mm(
                rack_loc,
                rail_hole_zs_from_config(units, config),
            )
        ]

        build_rail(
            name_prefix,
            to_m((config.rail_wood_width, config.rail_thickness, rail_length)),
            to_m((config.rail_thickness, config.rail_rack_width, rail_length)),
            to_m(wood_loc),
            to_m(rack_loc),
            rotation_z,
            hole_centers,
            hole_radius * mm_to_m,
            hole_depth * mm_to_m,
            collection,
            context,
        )

    top_z = total_height - (config.top_bottom_z * 0.5)
    bottom_z = config.top_bottom_z * 0.5
    side_z_center = total_height * 0.5
    side_x_offset = (config.top_bottom_x * 0.5) - (config.side_x * 0.5) + 18.0
    inside_x_face_left, inside_x_face_right = rail_x_faces_from_config(config, 0.0)
    inside_y_face_front, inside_y_face_back = rail_face_y_from_config(
        config,
        rail_offset_front,
        rail_offset_back,
    )

    if material_selection == "MU_CREATE_DEFAULT":
        material = ensure_material(DEFAULT_MATERIAL_NAME)
    else:
        material = bpy.data.materials.get(material_selection)
        if material is None:
            material = ensure_material(DEFAULT_MATERIAL_NAME)

    collection = ensure_collection(collection_name(units, front_rails, back_rails))

    add_box(
        "MU_Top",
        (config.top_bottom_x, config.top_bottom_y, config.top_bottom_z),
        (0.0, 0.0, top_z),
        material,
        collection,
    )
    add_box(
        "MU_Bottom",
        (config.top_bottom_x, config.top_bottom_y, config.top_bottom_z),
        (0.0, 0.0, bottom_z),
        material,
        collection,
    )
    add_box(
        "MU_Side_Left",
        (config.side_x, config.side_y, side_z),
        (-side_x_offset, 0.0, side_z_center),
        material,
        collection,
    )
    add_box(
        "MU_Side_Right",
        (config.side_x, config.side_y, side_z),
        (side_x_offset, 0.0, side_z_center),
        material,
        collection,
    )

    if front_rails:
        add_rail(
            "MU_Rail_Front_Left",
            inside_x_face_left - config.rail_outset,
            1.0,
            inside_y_face_front,
            -1.0,
            rotation=(0.0, 0.0, math.radians(90.0)),
        )
        add_rail(
            "MU_Rail_Front_Right",
            inside_x_face_right + config.rail_outset,
            -1.0,
            inside_y_face_front,
            -1.0,
            rotation=(0.0, 0.0, math.radians(-90.0)),
        )
    if back_rails:
        add_rail(
            "MU_Rail_Back_Left",
            inside_x_face_left - config.rail_outset,
            1.0,
            inside_y_face_back,
            1.0,
            rotation=(0.0, 0.0, math.radians(-90.0)),
        )
        add_rail(
            "MU_Rail_Back_Right",
            inside_x_face_right + config.rail_outset,
            -1.0,
            inside_y_face_back,
            1.0,
            rotation=(0.0, 0.0, math.radians(90.0)),
        )

    return {"FINISHED"}
