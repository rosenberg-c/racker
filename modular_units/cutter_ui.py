from __future__ import annotations

from typing import List

import bpy

from . import ui_text
from .cutter import board_used_length, calculate_cut_plan, parse_lengths_csv


def _selected_lengths_mm(context) -> List[int]:
    lengths = []
    for obj in context.selected_objects:
        dims = getattr(obj, "dimensions", None)
        if dims is None:
            continue
        length_mm = max(dims) * 1000.0
        if length_mm > 0:
            lengths.append(int(round(length_mm)))
    return lengths


class MU_OT_cutter_calculate(bpy.types.Operator):
    bl_idname = "mu.cutter_calculate"
    bl_label = ui_text.BUTTON_CUTTER_CALCULATE
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        stock_lengths = parse_lengths_csv(context.scene.mu_cutter_stock_lengths)
        kerf_mm = int(round(context.scene.mu_cutter_kerf))
        pieces = _selected_lengths_mm(context)

        if not pieces:
            context.scene.mu_cutter_results = "No selected objects."
            self.report({"WARNING"}, "No selected objects")
            return {"CANCELLED"}

        if not stock_lengths:
            context.scene.mu_cutter_results = "No stock lengths provided."
            self.report({"WARNING"}, "No stock lengths provided")
            return {"CANCELLED"}

        plan = calculate_cut_plan(pieces, stock_lengths, kerf_mm)
        if plan is None:
            context.scene.mu_cutter_results = "No valid cut plan found."
            self.report({"WARNING"}, "No valid cut plan found")
            return {"CANCELLED"}

        boards, total_stock, waste = plan
        boards_sorted = sorted(boards, key=lambda entry: (-entry[0], -len(entry[1])))

        lines = [
            ui_text.PANEL_CUTTER_RESULTS_LABEL,
            f"Pieces: {len(pieces)}",
            f"Total stock: {total_stock} mm",
            f"Waste: {waste} mm",
            f"Kerf: {kerf_mm} mm",
            ui_text.INFO_CUTTER_LENGTH_SOURCE,
            "",
        ]

        for board_length, board_pieces in boards_sorted:
            used = board_used_length(board_pieces, kerf_mm)
            offcut = board_length - used
            pieces_text = ", ".join(str(piece) for piece in board_pieces)
            lines.append(
                f"{board_length}: {pieces_text} (used {used} mm, offcut {offcut} mm)"
            )

        context.scene.mu_cutter_results = "\n".join(lines)
        return {"FINISHED"}


class MU_PT_cutter_panel(bpy.types.Panel):
    bl_label = ui_text.PANEL_CUTTER_LABEL
    bl_idname = "MU_PT_cutter_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = ui_text.PANEL_CATEGORY

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "mu_cutter_stock_lengths")
        layout.prop(context.scene, "mu_cutter_kerf")
        layout.operator(MU_OT_cutter_calculate.bl_idname)

        if context.scene.mu_cutter_results:
            box = layout.box()
            for line in context.scene.mu_cutter_results.splitlines():
                box.label(text=line)


CUTTER_CLASSES = (
    MU_OT_cutter_calculate,
    MU_PT_cutter_panel,
)


def register_cutter_properties():
    bpy.types.Scene.mu_cutter_stock_lengths = bpy.props.StringProperty(
        name=ui_text.PROP_CUTTER_STOCK_LENGTHS,
        default=ui_text.DEFAULT_STOCK_LENGTHS,
    )
    bpy.types.Scene.mu_cutter_kerf = bpy.props.FloatProperty(
        name=ui_text.PROP_CUTTER_KERF,
        default=4.0,
        min=0.0,
    )
    bpy.types.Scene.mu_cutter_results = bpy.props.StringProperty(
        name=ui_text.PANEL_CUTTER_RESULTS_LABEL,
        default="",
    )


def unregister_cutter_properties():
    del bpy.types.Scene.mu_cutter_results
    del bpy.types.Scene.mu_cutter_kerf
    del bpy.types.Scene.mu_cutter_stock_lengths
