bl_info = {
    "name": "Modular Units",
    "author": "",
    "version": (0, 1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Add > Mesh",
    "description": "Adds a simple cube for testing",
    "category": "Add Mesh",
}

import bpy


class MU_OT_add_cube(bpy.types.Operator):
    bl_idname = "mesh.mu_add_cube"
    bl_label = "Add Modular Units Cube"
    bl_options = {"REGISTER", "UNDO"}

    size: bpy.props.FloatProperty(
        name="Size",
        default=1.0,
        min=0.01,
    )
    location: bpy.props.FloatVectorProperty(
        name="Location",
        default=(0.0, 0.0, 0.0),
        size=3,
        subtype="TRANSLATION",
    )

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add(
            size=self.size,
            enter_editmode=False,
            align="WORLD",
            location=self.location,
        )
        return {"FINISHED"}


class MU_MT_menu(bpy.types.Menu):
    bl_label = "Modular Units"
    bl_idname = "MU_MT_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator(MU_OT_add_cube.bl_idname, text=MU_OT_add_cube.bl_label)


class MU_PT_panel(bpy.types.Panel):
    bl_label = "Modular Units"
    bl_idname = "MU_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Modular Units"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Add Cube")
        layout.operator(MU_OT_add_cube.bl_idname, text="Create Cube")


def menu_func(self, context):
    self.layout.menu(MU_MT_menu.bl_idname)


classes = (
    MU_OT_add_cube,
    MU_MT_menu,
    MU_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
