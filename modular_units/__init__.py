bl_info = {
    "name": "Modular Units",
    "author": "",
    "version": (0, 1, 101),
    "blender": (3, 0, 0),
    "location": "View3D > Add > Mesh",
    "description": "Adds a simple 19-inch rack shell",
    "category": "Add Mesh",
}

import bpy
from .rack_builder import build_rack, mu_material_items


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
        return build_rack(
            context,
            self.units,
            self.rail_offset_front,
            self.rail_offset_back,
            self.front_rails,
            self.back_rails,
            context.scene.mu_material,
        )


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
