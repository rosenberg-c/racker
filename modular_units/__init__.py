bl_info = {
    "name": "Modular Units",
    "author": "",
    "version": (0, 1, 32),
    "blender": (3, 0, 0),
    "location": "View3D > Add > Mesh",
    "description": "Adds a simple 19-inch rack shell",
    "category": "Add Mesh",
}

import bpy
import math
import mathutils


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
        mm_to_m = 0.001
        top_bottom_x = 487.0
        top_bottom_y = 400.0
        top_bottom_z = 18.0
        side_x = 18.0
        side_y = 400.0
        unit_height = 44.45
        rail_thickness = 2.0
        rail_wood_width = 30.0
        rail_rack_width = 21.0
        rail_outset = 18.0

        total_height = (top_bottom_z * 2.0) + (self.units * unit_height)
        side_z = total_height
        rail_length = total_height - (top_bottom_z * 2.0)

        def to_m(values):
            return tuple(value * mm_to_m for value in values)

        def ensure_material(name):
            material = bpy.data.materials.get(name)
            if material is None:
                material = bpy.data.materials.new(name=name)
            return material

        def add_box(name, dimensions, location, material):
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                enter_editmode=False,
                align="WORLD",
                location=to_m(location),
            )
            obj = context.active_object
            obj.name = name
            obj.dimensions = to_m(dimensions)
            if material is not None:
                if obj.data.materials:
                    obj.data.materials[0] = material
                else:
                    obj.data.materials.append(material)
            return obj

        def add_rail(name_prefix, x_face, x_inward, y_face, y_inward, rotation=None):
            wood_center_x = x_face + (rail_wood_width * 0.5 * x_inward)
            rack_center_x = x_face + (rail_thickness * 0.5 * x_inward)

            wood_center_y = y_face + (rail_thickness * 0.5 * y_inward)
            rack_center_y = y_face + (rail_rack_width * 0.5 * y_inward)

            pivot = (x_face, y_face, side_z_center)
            wood_loc = (wood_center_x, wood_center_y, side_z_center)
            rack_loc = (rack_center_x, rack_center_y, side_z_center)
            rot = None
            if rotation is not None:
                rot = mathutils.Euler(rotation, "XYZ").to_matrix()
                pivot_vec = mathutils.Vector(pivot)
                wood_loc = tuple(pivot_vec + rot @ (mathutils.Vector(wood_loc) - pivot_vec))
                rack_loc = tuple(pivot_vec + rot @ (mathutils.Vector(rack_loc) - pivot_vec))

            wood = add_box(
                f"{name_prefix}_Wood",
                (rail_wood_width, rail_thickness, rail_length),
                wood_loc,
                None,
            )
            rack = add_box(
                f"{name_prefix}_Rack",
                (rail_thickness, rail_rack_width, rail_length),
                rack_loc,
                None,
            )
            if rotation is not None:
                wood.rotation_euler = rotation
                rack.rotation_euler = rotation

        top_z = total_height - (top_bottom_z * 0.5)
        bottom_z = top_bottom_z * 0.5
        side_z_center = total_height * 0.5
        side_x_offset = (top_bottom_x * 0.5) - (side_x * 0.5) + 18.0
        inside_x_face_left = -((top_bottom_x * 0.5) - side_x)
        inside_x_face_right = (top_bottom_x * 0.5) - side_x
        inside_y_face_front = -(top_bottom_y * 0.5) + self.rail_offset_front
        inside_y_face_back = (top_bottom_y * 0.5) - self.rail_offset_back

        selection = context.scene.mu_material
        if selection == "MU_CREATE_DEFAULT":
            material = ensure_material(DEFAULT_MATERIAL_NAME)
        else:
            material = bpy.data.materials.get(selection)
            if material is None:
                material = ensure_material(DEFAULT_MATERIAL_NAME)

        add_box(
            "MU_Top",
            (top_bottom_x, top_bottom_y, top_bottom_z),
            (0.0, 0.0, top_z),
            material,
        )
        add_box(
            "MU_Bottom",
            (top_bottom_x, top_bottom_y, top_bottom_z),
            (0.0, 0.0, bottom_z),
            material,
        )
        add_box(
            "MU_Side_Left",
            (side_x, side_y, side_z),
            (-side_x_offset, 0.0, side_z_center),
            material,
        )
        add_box(
            "MU_Side_Right",
            (side_x, side_y, side_z),
            (side_x_offset, 0.0, side_z_center),
            material,
        )

        if self.front_rails:
            add_rail(
                "MU_Rail_Front_Left",
                inside_x_face_left - rail_outset,
                1.0,
                inside_y_face_front,
                -1.0,
                rotation=(0.0, 0.0, math.radians(90.0)),
            )
            add_rail(
                "MU_Rail_Front_Right",
                inside_x_face_right + rail_outset,
                -1.0,
                inside_y_face_front,
                -1.0,
                rotation=(0.0, 0.0, math.radians(-90.0)),
            )
        if self.back_rails:
            add_rail(
                "MU_Rail_Back_Left",
                inside_x_face_left - rail_outset,
                1.0,
                inside_y_face_back,
                1.0,
                rotation=(0.0, 0.0, math.radians(-90.0)),
            )
            add_rail(
                "MU_Rail_Back_Right",
                inside_x_face_right + rail_outset,
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
