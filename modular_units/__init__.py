from . import ui_text

bl_info = {
    "name": ui_text.ADDON_NAME,
    "author": "",
    "version": (0, 1, 134),
    "blender": (5, 0, 0),
    "location": "View3D > Add > Mesh",
    "description": ui_text.ADDON_DESCRIPTION,
    "category": ui_text.ADDON_CATEGORY,
}

ADDON_VERSION = ".".join(str(part) for part in bl_info["version"])
PANEL_LABEL = f"{ui_text.PANEL_LABEL_BASE} v{ADDON_VERSION}"

import bpy
from .cutter_ui import CUTTER_CLASSES, register_cutter_properties, unregister_cutter_properties
from .rack_builder import build_rack, mu_material_items


class MU_OT_add_rack(bpy.types.Operator):
    bl_idname = "mesh.mu_add_rack"
    bl_label = ui_text.OPERATOR_LABEL
    bl_options = {"REGISTER", "UNDO"}

    units: bpy.props.IntProperty(
        name=ui_text.PROP_UNITS,
        default=10,
        min=1,
    )
    rail_offset: bpy.props.FloatProperty(
        name=ui_text.PROP_RAIL_OFFSET,
        default=30.0,
        min=0.0,
    )
    rail_offset_front: bpy.props.FloatProperty(
        name=ui_text.PROP_RAIL_OFFSET_FRONT,
        default=30.0,
        min=0.0,
    )
    rail_offset_back: bpy.props.FloatProperty(
        name=ui_text.PROP_RAIL_OFFSET_BACK,
        default=30.0,
        min=0.0,
    )
    front_rails: bpy.props.BoolProperty(
        name=ui_text.PROP_FRONT_RAILS,
        default=True,
    )
    back_rails: bpy.props.BoolProperty(
        name=ui_text.PROP_BACK_RAILS,
        default=True,
    )
    material_thickness: bpy.props.FloatProperty(
        name=ui_text.PROP_MATERIAL_THICKNESS,
        default=18.0,
        min=1.0,
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
            self.material_thickness,
        )


class MU_MT_menu(bpy.types.Menu):
    bl_label = ui_text.MENU_LABEL
    bl_idname = "MU_MT_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator(MU_OT_add_rack.bl_idname, text=MU_OT_add_rack.bl_label)


class MU_PT_panel(bpy.types.Panel):
    bl_label = PANEL_LABEL
    bl_idname = "MU_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = ui_text.PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        layout.label(text=ui_text.PANEL_ADD_LABEL)
        basics_box = layout.box()
        basics_box.prop(context.scene, "mu_units")
        basics_box.prop(context.scene, "mu_material")
        layout.separator()
        front_box = layout.box()
        front_box.prop(context.scene, "mu_front_rails")
        front_box.prop(context.scene, "mu_rail_offset_front")
        layout.separator()
        back_box = layout.box()
        back_box.prop(context.scene, "mu_back_rails")
        back_box.prop(context.scene, "mu_rail_offset_back")
        layout.separator()
        material_box = layout.box()
        material_box.prop(context.scene, "mu_material_thickness")
        layout.separator()
        op = layout.operator(MU_OT_add_rack.bl_idname, text=ui_text.PANEL_CREATE_LABEL)

        op.units = context.scene.mu_units
        op.rail_offset_front = context.scene.mu_rail_offset_front
        op.rail_offset_back = context.scene.mu_rail_offset_back
        op.front_rails = context.scene.mu_front_rails
        op.back_rails = context.scene.mu_back_rails
        op.material_thickness = context.scene.mu_material_thickness


def menu_func(self, context):
    self.layout.menu(MU_MT_menu.bl_idname)


classes = (
    MU_OT_add_rack,
    MU_MT_menu,
    MU_PT_panel,
    *CUTTER_CLASSES,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_cutter_properties()
    bpy.types.Scene.mu_units = bpy.props.IntProperty(
        name=ui_text.PROP_UNITS,
        default=10,
        min=1,
    )
    bpy.types.Scene.mu_material = bpy.props.EnumProperty(
        name=ui_text.PROP_MATERIAL,
        items=mu_material_items,
        default=0,
    )
    bpy.types.Scene.mu_rail_offset_front = bpy.props.FloatProperty(
        name=ui_text.PROP_RAIL_OFFSET_FRONT,
        default=30.0,
        min=0.0,
    )
    bpy.types.Scene.mu_rail_offset_back = bpy.props.FloatProperty(
        name=ui_text.PROP_RAIL_OFFSET_BACK,
        default=30.0,
        min=0.0,
    )
    bpy.types.Scene.mu_front_rails = bpy.props.BoolProperty(
        name=ui_text.PROP_FRONT_RAILS,
        default=True,
    )
    bpy.types.Scene.mu_back_rails = bpy.props.BoolProperty(
        name=ui_text.PROP_BACK_RAILS,
        default=True,
    )
    bpy.types.Scene.mu_material_thickness = bpy.props.FloatProperty(
        name=ui_text.PROP_MATERIAL_THICKNESS,
        default=18.0,
        min=1.0,
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
    del bpy.types.Scene.mu_material_thickness
    unregister_cutter_properties()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
