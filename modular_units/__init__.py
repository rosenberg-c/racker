from . import ui_text

bl_info = {
    "name": ui_text.ADDON_NAME,
    "author": "",
    "version": (0, 1, 239),
    "blender": (5, 0, 0),
    "location": "View3D > Add > Mesh",
    "description": ui_text.ADDON_DESCRIPTION,
    "category": ui_text.ADDON_CATEGORY,
}

ADDON_VERSION = ".".join(str(part) for part in bl_info["version"])
ui_text.PANEL_CATEGORY = f"{ui_text.PANEL_CATEGORY} v{ADDON_VERSION}"
PANEL_LABEL = ui_text.PANEL_LABEL_BASE

import bpy
from .cutter import parse_stock_materials_csv
from .cutter_ui import CUTTER_CLASSES, register_cutter_properties, unregister_cutter_properties
from .body_builder import build_body
from .faceplate_builder import build_faceplate
from .shelf_builder import build_shelf
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
    unit_margin: bpy.props.FloatProperty(
        name=ui_text.PROP_UNIT_MARGIN,
        default=4.0,
        min=0.0,
    )

    def execute(self, context):
        try:
            thickness = float(context.scene.mu_material_thickness)
        except (TypeError, ValueError):
            thickness = 18.0
        try:
            depth = float(context.scene.mu_material_depth)
        except (TypeError, ValueError):
            depth = 400.0
        return build_rack(
            context,
            self.units,
            self.rail_offset_front,
            self.rail_offset_back,
            self.front_rails,
            self.back_rails,
            context.scene.mu_material,
            thickness,
            depth_mm=depth,
            unit_margin_mm=self.unit_margin,
        )


class MU_MT_menu(bpy.types.Menu):
    bl_label = ui_text.MENU_LABEL
    bl_idname = "MU_MT_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator(MU_OT_add_rack.bl_idname, text=MU_OT_add_rack.bl_label)
        layout.operator(MU_OT_add_faceplate.bl_idname, text=MU_OT_add_faceplate.bl_label)
        layout.operator(MU_OT_add_body.bl_idname, text=MU_OT_add_body.bl_label)
        layout.operator(MU_OT_add_shelf.bl_idname, text=MU_OT_add_shelf.bl_label)


class MU_PT_panel(bpy.types.Panel):
    bl_label = PANEL_LABEL
    bl_idname = "MU_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = ui_text.PANEL_CATEGORY
    bl_parent_id = "MU_PT_rack_frame_parent"

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
        material_box.prop(context.scene, "mu_material_depth")
        material_box.prop(context.scene, "mu_unit_margin")
        note = material_box.row()
        note.scale_y = 0.8
        note.enabled = False
        note_split = note.split(factor=0.08)
        note_split.label(text="")
        note_split.label(text="Adds total clearance to rack height")
        layout.separator()
        op = layout.operator(MU_OT_add_rack.bl_idname, text=ui_text.PANEL_CREATE_LABEL)

        op.units = context.scene.mu_units
        op.rail_offset_front = context.scene.mu_rail_offset_front
        op.rail_offset_back = context.scene.mu_rail_offset_back
        op.front_rails = context.scene.mu_front_rails
        op.back_rails = context.scene.mu_back_rails
        op.material_thickness = float(context.scene.mu_material_thickness)
        op.unit_margin = context.scene.mu_unit_margin


class MU_OT_add_faceplate(bpy.types.Operator):
    bl_idname = "mesh.mu_add_faceplate"
    bl_label = "Add Faceplate"
    bl_options = {"REGISTER", "UNDO"}

    units: bpy.props.IntProperty(
        name=ui_text.PROP_UNITS,
        default=1,
        min=1,
    )
    thickness: bpy.props.FloatProperty(
        name=ui_text.PROP_FACEPLATE_THICKNESS,
        default=2.0,
        min=0.1,
    )
    apply_boolean: bpy.props.BoolProperty(
        name="Apply Hole Cut",
        default=False,
    )

    def execute(self, context):
        build_faceplate(
            context,
            self.units,
            width_mm=483.0,
            thickness_mm=self.thickness,
            apply_boolean=self.apply_boolean,
            keep_holes=not self.apply_boolean,
            material=None,
        )
        return {"FINISHED"}


class MU_OT_add_body(bpy.types.Operator):
    bl_idname = "mesh.mu_add_body"
    bl_label = "Add Body"
    bl_options = {"REGISTER", "UNDO"}

    units: bpy.props.IntProperty(
        name=ui_text.PROP_UNITS,
        default=1,
        min=1,
    )
    width: bpy.props.FloatProperty(
        name="Width (mm)",
        default=438.0,
        min=1.0,
    )
    depth: bpy.props.FloatProperty(
        name="Depth (mm)",
        default=200.0,
        min=1.0,
    )

    def execute(self, context):
        build_body(
            context,
            self.units,
            self.width,
            self.depth,
            material=None,
        )
        return {"FINISHED"}


class MU_OT_add_shelf(bpy.types.Operator):
    bl_idname = "mesh.mu_add_shelf"
    bl_label = "Add Shelf"
    bl_options = {"REGISTER", "UNDO"}

    units: bpy.props.IntProperty(
        name=ui_text.PROP_UNITS,
        default=1,
        min=1,
    )
    width: bpy.props.FloatProperty(
        name="Width (mm)",
        default=438.0,
        min=1.0,
    )
    depth: bpy.props.FloatProperty(
        name="Depth (mm)",
        default=200.0,
        min=1.0,
    )
    faceplate_thickness: bpy.props.FloatProperty(
        name=ui_text.PROP_FACEPLATE_THICKNESS,
        default=2.0,
        min=0.1,
    )

    def execute(self, context):
        build_shelf(
            context,
            self.units,
            self.width,
            self.depth,
            self.faceplate_thickness,
        )
        return {"FINISHED"}


class MU_PT_faceplate_panel(bpy.types.Panel):
    bl_label = "Faceplate"
    bl_idname = "MU_PT_faceplate_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = ui_text.PANEL_CATEGORY
    bl_parent_id = "MU_PT_rack_item_parent"

    @classmethod
    def poll(cls, context):
        return not context.scene.mu_create_shelf

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(context.scene, "mu_faceplate_units")
        box.prop(context.scene, "mu_faceplate_thickness")
        box.prop(context.scene, "mu_faceplate_apply_boolean")
        op = box.operator(MU_OT_add_faceplate.bl_idname, text="Create Faceplate")
        op.units = context.scene.mu_faceplate_units
        op.thickness = context.scene.mu_faceplate_thickness
        op.apply_boolean = context.scene.mu_faceplate_apply_boolean


class MU_PT_body_panel(bpy.types.Panel):
    bl_label = "Body"
    bl_idname = "MU_PT_body_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = ui_text.PANEL_CATEGORY
    bl_parent_id = "MU_PT_rack_item_parent"

    @classmethod
    def poll(cls, context):
        return not context.scene.mu_create_shelf

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(context.scene, "mu_body_units")
        box.prop(context.scene, "mu_body_width")
        box.prop(context.scene, "mu_body_depth")
        op = box.operator(MU_OT_add_body.bl_idname, text="Create Body")
        op.units = context.scene.mu_body_units
        op.width = context.scene.mu_body_width
        op.depth = context.scene.mu_body_depth


def _material_thickness_items(self, context):
    prefs_entry = context.preferences.addons.get("modular_units") if context else None
    prefs = prefs_entry.preferences if prefs_entry else None
    materials = list(getattr(prefs, "materials", [])) if prefs is not None else []
    if not materials:
        materials = parse_stock_materials_csv(ui_text.DEFAULT_STOCK_MATERIALS)
        thicknesses = sorted({material.thickness_mm for material in materials})
    else:
        thicknesses = sorted({material.thickness_mm for material in materials})
    if not thicknesses:
        thicknesses = [18.0]
    return [(str(value), f"{value} mm", "") for value in thicknesses]


def _material_depth_items(self, context):
    prefs_entry = context.preferences.addons.get("modular_units") if context else None
    prefs = prefs_entry.preferences if prefs_entry else None
    materials = list(getattr(prefs, "materials", [])) if prefs is not None else []
    if not materials:
        materials = parse_stock_materials_csv(ui_text.DEFAULT_STOCK_MATERIALS)
        depths = sorted({material.depth_mm for material in materials})
    else:
        depths = sorted({material.depth_mm for material in materials})
    if not depths:
        depths = [400.0]
    return [(str(value), f"{value} mm", "") for value in depths]


class MU_PT_rack_frame_parent(bpy.types.Panel):
    bl_label = "Rack Frame Building"
    bl_idname = "MU_PT_rack_frame_parent"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = ui_text.PANEL_CATEGORY

    def draw(self, context):
        pass


class MU_PT_rack_item_parent(bpy.types.Panel):
    bl_label = "Rack Item Building"
    bl_idname = "MU_PT_rack_item_parent"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = ui_text.PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "mu_create_shelf")
        if context.scene.mu_create_shelf:
            box = layout.box()
            box.prop(context.scene, "mu_faceplate_units")
            box.prop(context.scene, "mu_faceplate_thickness")
            box.prop(context.scene, "mu_body_width")
            box.prop(context.scene, "mu_body_depth")
            op = box.operator(MU_OT_add_shelf.bl_idname, text="Create Shelf")
            op.units = context.scene.mu_faceplate_units
            op.faceplate_thickness = context.scene.mu_faceplate_thickness
            op.width = context.scene.mu_body_width
            op.depth = context.scene.mu_body_depth


def _material_depth_for_thickness(context, thickness: float) -> float:
    prefs_entry = context.preferences.addons.get("modular_units") if context else None
    prefs = prefs_entry.preferences if prefs_entry else None
    materials = list(getattr(prefs, "materials", [])) if prefs is not None else []
    if not materials:
        materials = parse_stock_materials_csv(ui_text.DEFAULT_STOCK_MATERIALS)
    for material in materials:
        if abs(material.thickness_mm - thickness) < 1e-6:
            return material.depth_mm
    return 400.0


class MU_MaterialItem(bpy.types.PropertyGroup):
    length_mm: bpy.props.IntProperty(name="Length (mm)", default=800, min=1)
    cost: bpy.props.FloatProperty(name="Cost", default=0.0, min=0.0)
    thickness_mm: bpy.props.FloatProperty(
        name="Thickness (mm)", default=18.0, min=0.1
    )
    depth_mm: bpy.props.FloatProperty(name="Depth (mm)", default=400.0, min=1.0)


class MU_UL_materials(bpy.types.UIList):
    def draw_item(self, context, layout, _data, item, _icon, _active_data, _active_propname, _index):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            split = layout.split(factor=0.75)
            split.label(text=f"{item.thickness_mm} x {item.depth_mm} x {item.length_mm} mm")
            split.label(text=f"{item.cost:.2f}")
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text=str(item.length_mm))


class MU_OT_material_add(bpy.types.Operator):
    bl_idname = "mu.material_add"
    bl_label = "Add Material"

    def execute(self, context):
        prefs = context.preferences.addons["modular_units"].preferences
        item = prefs.materials.add()
        item.length_mm = 800
        item.cost = 0.0
        item.thickness_mm = 18.0
        item.depth_mm = 400.0
        prefs.materials_index = len(prefs.materials) - 1
        return {"FINISHED"}


class MU_OT_material_remove(bpy.types.Operator):
    bl_idname = "mu.material_remove"
    bl_label = "Remove Material"

    def execute(self, context):
        prefs = context.preferences.addons["modular_units"].preferences
        index = prefs.materials_index
        if 0 <= index < len(prefs.materials):
            prefs.materials.remove(index)
            prefs.materials_index = max(0, min(index, len(prefs.materials) - 1))
        return {"FINISHED"}


class MU_PT_materials_panel(bpy.types.Panel):
    bl_label = "Materials"
    bl_idname = "MU_PT_materials_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = ui_text.PANEL_CATEGORY
    bl_parent_id = "MU_PT_rack_frame_parent"

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences.addons.get("modular_units").preferences
        header = layout.row()
        header_split = header.split(factor=0.75)
        header_split.label(text="Thickness x Depth x Length")
        header_split.label(text="Cost")
        row = layout.row()
        row.template_list("MU_UL_materials", "", prefs, "materials", prefs, "materials_index")
        col = row.column(align=True)
        col.operator(MU_OT_material_add.bl_idname, text="", icon="ADD")
        col.operator(MU_OT_material_remove.bl_idname, text="", icon="REMOVE")

        toggle = layout.row()
        toggle.prop(
            prefs,
            "show_material_editor",
            text="Edit",
            toggle=True,
            icon="GREASEPENCIL",
        )

        if prefs.show_material_editor:
            if prefs.materials and 0 <= prefs.materials_index < len(prefs.materials):
                item = prefs.materials[prefs.materials_index]
                layout.prop(item, "length_mm")
                layout.prop(item, "cost")
                layout.prop(item, "thickness_mm")
                layout.prop(item, "depth_mm")



class MU_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = "modular_units"

    materials: bpy.props.CollectionProperty(type=MU_MaterialItem)
    materials_index: bpy.props.IntProperty(default=0, min=0)
    show_material_editor: bpy.props.BoolProperty(default=False)

    def draw(self, context):
        layout = self.layout
        layout.label(text=ui_text.PANEL_CUTTER_LABEL)
        layout.label(text="Materials are managed in the panel UI")


def menu_func(self, context):
    self.layout.menu(MU_MT_menu.bl_idname)


classes = (
    MU_MaterialItem,
    MU_UL_materials,
    MU_OT_material_add,
    MU_OT_material_remove,
    MU_PT_rack_frame_parent,
    MU_PT_rack_item_parent,
    MU_PT_materials_panel,
    MU_AddonPreferences,
    MU_OT_add_rack,
    MU_OT_add_faceplate,
    MU_OT_add_body,
    MU_OT_add_shelf,
    MU_MT_menu,
    MU_PT_panel,
    MU_PT_faceplate_panel,
    MU_PT_body_panel,
    *CUTTER_CLASSES,
)


def _ensure_default_materials(prefs):
    if prefs.materials:
        return
    materials = parse_stock_materials_csv(ui_text.DEFAULT_STOCK_MATERIALS)
    for material in materials:
        item = prefs.materials.add()
        item.length_mm = material.length_mm
        item.cost = material.cost
        item.thickness_mm = material.thickness_mm




def register():
    register_cutter_properties()
    for cls in classes:
        bpy.utils.register_class(cls)
    prefs_entry = bpy.context.preferences.addons.get("modular_units")
    if prefs_entry is not None:
        _ensure_default_materials(prefs_entry.preferences)
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
    bpy.types.Scene.mu_material_thickness = bpy.props.EnumProperty(
        name=ui_text.PROP_MATERIAL_THICKNESS,
        items=_material_thickness_items,
        default=0,
    )
    bpy.types.Scene.mu_material_depth = bpy.props.EnumProperty(
        name=ui_text.PROP_MATERIAL_DEPTH,
        items=_material_depth_items,
        default=0,
    )
    bpy.types.Scene.mu_unit_margin = bpy.props.FloatProperty(
        name=ui_text.PROP_UNIT_MARGIN,
        default=4.0,
        min=0.0,
    )
    bpy.types.Scene.mu_faceplate_units = bpy.props.IntProperty(
        name=ui_text.PROP_UNITS,
        default=1,
        min=1,
    )
    bpy.types.Scene.mu_faceplate_thickness = bpy.props.FloatProperty(
        name=ui_text.PROP_FACEPLATE_THICKNESS,
        default=2.0,
        min=0.1,
    )
    bpy.types.Scene.mu_faceplate_apply_boolean = bpy.props.BoolProperty(
        name="Apply Hole Cut",
        default=False,
    )
    bpy.types.Scene.mu_body_units = bpy.props.IntProperty(
        name=ui_text.PROP_UNITS,
        default=1,
        min=1,
    )
    bpy.types.Scene.mu_body_width = bpy.props.FloatProperty(
        name="Body Width (mm)",
        default=438.0,
        min=1.0,
    )
    bpy.types.Scene.mu_body_depth = bpy.props.FloatProperty(
        name="Body Depth (mm)",
        default=200.0,
        min=1.0,
    )
    bpy.types.Scene.mu_create_shelf = bpy.props.BoolProperty(
        name="Create Shelf",
        default=False,
    )
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    del bpy.types.Scene.mu_back_rails
    del bpy.types.Scene.mu_front_rails
    del bpy.types.Scene.mu_rail_offset_back
    del bpy.types.Scene.mu_rail_offset_front
    del bpy.types.Scene.mu_material
    del bpy.types.Scene.mu_units
    del bpy.types.Scene.mu_material_thickness
    del bpy.types.Scene.mu_material_depth
    del bpy.types.Scene.mu_unit_margin
    del bpy.types.Scene.mu_faceplate_units
    del bpy.types.Scene.mu_faceplate_thickness
    del bpy.types.Scene.mu_faceplate_apply_boolean
    del bpy.types.Scene.mu_body_units
    del bpy.types.Scene.mu_body_width
    del bpy.types.Scene.mu_body_depth
    del bpy.types.Scene.mu_create_shelf
    unregister_cutter_properties()


if __name__ == "__main__":
    register()
