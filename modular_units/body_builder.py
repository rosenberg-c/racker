import bpy

from .builders import build_panel
from .config import RackConfig
from .geometry import unique_collection_name


def build_body(
    context,
    units,
    width_mm,
    depth_mm,
    material=None,
    collection=None,
):
    config = RackConfig()
    height_mm = units * config.unit_height
    mm_to_m = 0.001

    if collection is None:
        collection = _ensure_collection(
            context,
            f"MU_Body_{units}U_{_fmt(width_mm)}x{_fmt(depth_mm)}",
        )

    y_center = (depth_mm * 0.5) * mm_to_m
    obj = build_panel(
        "MU_Body",
        (width_mm * mm_to_m, depth_mm * mm_to_m, height_mm * mm_to_m),
        (0.0, y_center, height_mm * 0.5 * mm_to_m),
        material,
        collection,
        context,
    )

    return obj


def _ensure_collection(context, name):
    existing = {collection.name for collection in bpy.data.collections}
    resolved = unique_collection_name(name, existing)
    collection = bpy.data.collections.new(resolved)
    context.scene.collection.children.link(collection)
    return collection


def _fmt(value):
    if abs(value - round(value)) < 1e-6:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")
