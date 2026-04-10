import bpy

from .body_builder import build_body
from .faceplate_builder import build_faceplate
from .geometry import unique_collection_name


def build_shelf(
    context,
    units,
    width_mm,
    depth_mm,
    faceplate_thickness_mm,
):
    if faceplate_thickness_mm <= 0:
        faceplate_thickness_mm = 2.0
    collection = _ensure_collection(
        context,
        f"MU_Shelf_{units}U_{_fmt(width_mm)}x{_fmt(depth_mm)}",
    )

    body = build_body(
        context,
        units,
        width_mm,
        depth_mm,
        material=None,
        collection=collection,
    )
    faceplate_width_mm = 483.0
    faceplate = build_faceplate(
        context,
        units,
        width_mm=faceplate_width_mm,
        thickness_mm=faceplate_thickness_mm,
        material=None,
        collection=collection,
        apply_boolean=True,
        keep_holes=False,
    )

    _apply_boolean_difference(
        context,
        body,
        _build_body_cutter(
            context,
            units,
            width_mm,
            depth_mm,
            faceplate_thickness_mm,
            collection,
        ),
    )
    _apply_boolean_difference(
        context,
        faceplate,
        _build_faceplate_cutter(
            context,
            units,
            width_mm,
            faceplate_thickness_mm,
            collection,
        ),
    )
    _apply_boolean_union(context, body, faceplate)
    bpy.data.objects.remove(faceplate, do_unlink=True)

    body.name = "MU_Shelf"
    return body


def _apply_boolean_difference(context, target_obj, cutter_obj):
    modifier = target_obj.modifiers.new(name="MU_Shelf_Cut", type="BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.object = cutter_obj
    modifier.solver = "EXACT"
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
    bpy.data.objects.remove(cutter_obj, do_unlink=True)


def _apply_boolean_union(context, target_obj, union_obj):
    modifier = target_obj.modifiers.new(name="MU_Shelf_Union", type="BOOLEAN")
    modifier.operation = "UNION"
    modifier.object = union_obj
    modifier.solver = "EXACT"
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


def _ensure_collection(context, name):
    existing = {collection.name for collection in bpy.data.collections}
    resolved = unique_collection_name(name, existing)
    collection = bpy.data.collections.new(resolved)
    context.scene.collection.children.link(collection)
    return collection


def _build_body_cutter(context, units, width_mm, depth_mm, thickness_mm, collection):
    mm_to_m = 0.001
    height_mm = units * 44.45
    inner_width = max(0.0, width_mm - (thickness_mm * 2.0))
    inner_height = max(0.0, height_mm - thickness_mm)
    inner_depth = depth_mm

    x = 0.0
    y = (inner_depth * 0.5) * mm_to_m
    z = (thickness_mm + (inner_height * 0.5)) * mm_to_m

    return _build_box(
        context,
        "MU_Shelf_Body_Cutter",
        (inner_width * mm_to_m, inner_depth * mm_to_m, inner_height * mm_to_m),
        (x, y, z),
        collection,
    )


def _build_faceplate_cutter(context, units, body_width_mm, thickness_mm, collection):
    mm_to_m = 0.001
    height_mm = units * 44.45
    inner_width = max(0.0, body_width_mm - (thickness_mm * 2.0))
    inner_height = max(0.0, height_mm - thickness_mm)

    x = 0.0
    y = -(thickness_mm * 0.5) * mm_to_m
    z = (thickness_mm + (inner_height * 0.5)) * mm_to_m

    return _build_box(
        context,
        "MU_Shelf_Faceplate_Cutter",
        (inner_width * mm_to_m, thickness_mm * mm_to_m, inner_height * mm_to_m),
        (x, y, z),
        collection,
    )


def _build_box(context, name, dimensions, location, collection):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)

    import bmesh

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=bm.verts, vec=dimensions)
    bmesh.ops.translate(bm, verts=bm.verts, vec=location)
    bm.to_mesh(mesh)
    bm.free()

    return obj


def _fmt(value):
    if abs(value - round(value)) < 1e-6:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")
