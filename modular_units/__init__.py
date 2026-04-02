bl_info = {
    "name": "Modular Units",
    "author": "",
    "version": (0, 1, 55),
    "blender": (3, 0, 0),
    "location": "View3D > Add > Mesh",
    "description": "Adds a simple 19-inch rack shell",
    "category": "Add Mesh",
}

import bpy
import math
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


class MU_OT_add_rack(bpy.types.Operator):
    bl_idname = "mesh.mu_add_rack"
    bl_label = "Add Modular Units Rack"
    bl_options = {"REGISTER", "UNDO"}

    units: bpy.props.IntProperty(
        name="Units (U)",
        default=10,
        min=1,
    )
    rail_offset: bpy.props.FloatProperty(
        name="Rail Offset (mm)",
        default=30.0,
        min=0.0,
    )
    rail_offset_front: bpy.props.FloatProperty(
        name="Front Rail Offset (mm)",
        default=30.0,
        min=0.0,
    )
    rail_offset_back: bpy.props.FloatProperty(
        name="Back Rail Offset (mm)",
        default=30.0,
        min=0.0,
    )
    front_rails: bpy.props.BoolProperty(
        name="Front Rails",
        default=True,
    )
    back_rails: bpy.props.BoolProperty(
        name="Back Rails",
        default=True,
    )

    def execute(self, context):
        config = RackConfig()
        mm_to_m = 0.001
        total_height = total_height_from_config(self.units, config)
        side_z = total_height
        rail_length = rail_length_from_config(self.units, config)

        def to_m(values):
            return tuple(value * mm_to_m for value in values)

        def ensure_collection(name):
            existing = {collection.name for collection in bpy.data.collections}
            resolved = unique_collection_name(name, existing)
            collection = bpy.data.collections.new(resolved)
            context.scene.collection.children.link(collection)
            return collection

        def move_to_collection(obj, collection):
            if obj.name not in collection.objects:
                collection.objects.link(obj)
            for existing in list(obj.users_collection):
                if existing != collection:
                    existing.objects.unlink(obj)

        def ensure_material(name):
            material = bpy.data.materials.get(name)
            if material is None:
                material = bpy.data.materials.new(name=name)
            return material

        def add_box(name, dimensions, location, material, collection):
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                enter_editmode=False,
                align="WORLD",
                location=to_m(location),
            )
            obj = context.active_object
            obj.name = name
            obj.dimensions = to_m(dimensions)
            move_to_collection(obj, collection)
            if material is not None:
                if obj.data.materials:
                    obj.data.materials[0] = material
                else:
                    obj.data.materials.append(material)
            return obj

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

            wood = add_box(
                f"{name_prefix}_Wood",
                (config.rail_wood_width, config.rail_thickness, rail_length),
                wood_loc,
                None,
                collection,
            )
            rack = add_box(
                f"{name_prefix}_Rack",
                (config.rail_thickness, config.rail_rack_width, rail_length),
                rack_loc,
                None,
                collection,
            )
            if rotation is not None:
                wood.rotation_euler = rotation
                rack.rotation_euler = rotation

            for obj in (wood, rack):
                obj.select_set(True)
            context.view_layer.objects.active = wood
            bpy.ops.object.join()
            rail = context.active_object
            rail.name = name_prefix

            holes = []
            hole_index = 1
            for hole_center in rail_hole_centers_mm(
                rack_loc,
                rail_hole_zs_from_config(self.units, config),
            ):
                bpy.ops.mesh.primitive_cylinder_add(
                    radius=hole_radius * mm_to_m,
                    depth=hole_depth * mm_to_m,
                    enter_editmode=False,
                    align="WORLD",
                    location=to_m(hole_center),
                    rotation=(0.0, math.radians(90.0), rotation_z),
                )
                hole_obj = context.active_object
                hole_obj.name = f"{name_prefix}_Hole_{hole_index}"
                move_to_collection(hole_obj, collection)
                holes.append(hole_obj)
                hole_index += 1

            if holes:
                for obj in holes:
                    obj.select_set(True)
                context.view_layer.objects.active = holes[0]
                bpy.ops.object.join()
                holes_obj = context.active_object
                holes_obj.name = f"{name_prefix}_Holes"
                modifier = rail.modifiers.new(name="MU_Holes", type="BOOLEAN")
                modifier.operation = "DIFFERENCE"
                modifier.object = holes_obj
                context.view_layer.objects.active = rail
                bpy.ops.object.modifier_apply(modifier=modifier.name)
                bpy.data.objects.remove(holes_obj, do_unlink=True)

        top_z = total_height - (config.top_bottom_z * 0.5)
        bottom_z = config.top_bottom_z * 0.5
        side_z_center = total_height * 0.5
        side_x_offset = (config.top_bottom_x * 0.5) - (config.side_x * 0.5) + 18.0
        inside_x_face_left, inside_x_face_right = rail_x_faces_from_config(config, 0.0)
        inside_y_face_front, inside_y_face_back = rail_face_y_from_config(
            config,
            self.rail_offset_front,
            self.rail_offset_back,
        )

        selection = context.scene.mu_material
        if selection == "MU_CREATE_DEFAULT":
            material = ensure_material(DEFAULT_MATERIAL_NAME)
        else:
            material = bpy.data.materials.get(selection)
            if material is None:
                material = ensure_material(DEFAULT_MATERIAL_NAME)

        collection = ensure_collection(
            collection_name(self.units, self.front_rails, self.back_rails)
        )

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

        if self.front_rails:
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
        if self.back_rails:
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


class MU_MT_menu(bpy.types.Menu):
    bl_label = "Modular Units"
    bl_idname = "MU_MT_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator(MU_OT_add_rack.bl_idname, text=MU_OT_add_rack.bl_label)


class MU_PT_panel(bpy.types.Panel):
    bl_label = "Modular Units"
    bl_idname = "MU_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Modular Units"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Add Rack")
        layout.prop(context.scene, "mu_units")
        layout.prop(context.scene, "mu_material")
        layout.prop(context.scene, "mu_rail_offset_front")
        layout.prop(context.scene, "mu_rail_offset_back")
        layout.prop(context.scene, "mu_front_rails")
        layout.prop(context.scene, "mu_back_rails")
        op = layout.operator(MU_OT_add_rack.bl_idname, text="Create Rack")
        op.units = context.scene.mu_units
        op.rail_offset_front = context.scene.mu_rail_offset_front
        op.rail_offset_back = context.scene.mu_rail_offset_back
        op.front_rails = context.scene.mu_front_rails
        op.back_rails = context.scene.mu_back_rails


def menu_func(self, context):
    self.layout.menu(MU_MT_menu.bl_idname)


classes = (
    MU_OT_add_rack,
    MU_MT_menu,
    MU_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mu_units = bpy.props.IntProperty(
        name="Units (U)",
        default=10,
        min=1,
    )
    bpy.types.Scene.mu_material = bpy.props.EnumProperty(
        name="Material",
        items=mu_material_items,
        default=0,
    )
    bpy.types.Scene.mu_rail_offset_front = bpy.props.FloatProperty(
        name="Front Rail Offset (mm)",
        default=30.0,
        min=0.0,
    )
    bpy.types.Scene.mu_rail_offset_back = bpy.props.FloatProperty(
        name="Back Rail Offset (mm)",
        default=30.0,
        min=0.0,
    )
    bpy.types.Scene.mu_front_rails = bpy.props.BoolProperty(
        name="Front Rails",
        default=True,
    )
    bpy.types.Scene.mu_back_rails = bpy.props.BoolProperty(
        name="Back Rails",
        default=True,
    )
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    del bpy.types.Scene.mu_back_rails
    del bpy.types.Scene.mu_front_rails
    del bpy.types.Scene.mu_rail_offset_back
    del bpy.types.Scene.mu_rail_offset_front
    del bpy.types.Scene.mu_material
    del bpy.types.Scene.mu_units
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
