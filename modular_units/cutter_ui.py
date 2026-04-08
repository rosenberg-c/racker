from __future__ import annotations

import math
from typing import List

import bpy
from . import ui_text
from .cutter import (
    board_used_length,
    calculate_cut_plan,
    cut_operations_for_plan,
    parse_lengths_csv,
    stack_groups_for_plan,
)
from .cutter_select import matches_cutter_piece, matches_instance_root


def _object_length_mm(obj, depsgraph) -> int:
    eval_obj = obj.evaluated_get(depsgraph)
    if not matches_cutter_piece(eval_obj):
        return 0
    dims = getattr(eval_obj, "dimensions", None)
    if dims is None:
        return 0
    length_mm = dims.x * 1000.0
    return int(round(length_mm)) if length_mm > 0 else 0


def _instance_collection_lengths_mm(obj, depsgraph) -> List[int]:
    lengths = []
    for inst in depsgraph.object_instances:
        if not matches_instance_root(inst, obj):
            continue
        eval_obj = inst.object
        if eval_obj is None or eval_obj.type == "EMPTY":
            continue
        if not matches_cutter_piece(eval_obj):
            continue
        dims = getattr(eval_obj, "dimensions", None)
        if dims is None:
            continue
        scale_x = inst.matrix_world.to_scale().x
        length_mm = dims.x * scale_x * 1000.0
        if length_mm > 0:
            lengths.append(int(round(length_mm)))
    return lengths


def _selected_lengths_mm(context) -> List[int]:
    lengths = []
    depsgraph = context.evaluated_depsgraph_get()

    for obj in context.selected_objects:
        if obj.instance_collection is not None:
            lengths.extend(_instance_collection_lengths_mm(obj, depsgraph))
        length_mm = _object_length_mm(obj, depsgraph)
        if length_mm > 0:
            lengths.append(length_mm)

        for child in obj.children_recursive:
            child_length = _object_length_mm(child, depsgraph)
            if child_length > 0:
                lengths.append(child_length)

    return lengths


class MU_OT_cutter_calculate(bpy.types.Operator):
    bl_idname = "mu.cutter_calculate"
    bl_label = ui_text.BUTTON_CUTTER_CALCULATE
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        stock_lengths = parse_lengths_csv(context.scene.mu_cutter_stock_lengths)
        kerf_mm = int(round(context.scene.mu_cutter_kerf))
        max_stack = max(1, int(round(context.scene.mu_cutter_max_stack)))
        pieces = _selected_lengths_mm(context)

        if not pieces:
            context.scene.mu_cutter_results = "No selected objects."
            self.report({"WARNING"}, "No selected objects")
            return {"CANCELLED"}

        if not stock_lengths:
            context.scene.mu_cutter_results = "No stock lengths provided."
            self.report({"WARNING"}, "No stock lengths provided")
            return {"CANCELLED"}

        plan = calculate_cut_plan(pieces, stock_lengths, kerf_mm, max_stack)
        if plan is None:
            context.scene.mu_cutter_results = "No valid cut plan found."
            self.report({"WARNING"}, "No valid cut plan found")
            return {"CANCELLED"}

        boards, total_stock, waste = plan
        cut_ops = cut_operations_for_plan(boards, max_stack)
        boards_sorted = sorted(boards, key=lambda entry: (-entry[0], -len(entry[1])))
        stack_groups = stack_groups_for_plan(boards) if max_stack > 1 else []

        lines = [
            ui_text.PANEL_CUTTER_RESULTS_LABEL,
            f"Pieces: {len(pieces)}",
            f"Total stock: {total_stock} mm",
            f"Waste: {waste} mm",
            f"Kerf: {kerf_mm} mm",
            f"Cuts: {cut_ops} (stack {max_stack})",
            ui_text.INFO_CUTTER_LENGTH_SOURCE,
            "",
        ]

        if max_stack > 1:
            if stack_groups:
                lines.append("Stack groups:")
                for piece_list, count in stack_groups:
                    pieces_text = ", ".join(str(piece) for piece in piece_list)
                    batches = math.ceil(count / max_stack)
                    lines.append(
                        f"{count} boards: {pieces_text} (batch {max_stack} x {batches})"
                    )
                lines.append("")
            else:
                lines.append("Stack groups: none")
                lines.append("")

        for board_length, board_pieces in boards_sorted:
            used = board_used_length(board_pieces, kerf_mm)
            offcut = board_length - used
            pieces_text = ", ".join(str(piece) for piece in board_pieces)
            lines.append(
                f"{board_length}: {pieces_text} (used {used} mm, offcut {offcut} mm)"
            )

        context.scene.mu_cutter_results = "\n".join(lines)
        return {"FINISHED"}


class MU_OT_cutter_copy_results(bpy.types.Operator):
    bl_idname = "mu.cutter_copy_results"
    bl_label = ui_text.BUTTON_CUTTER_COPY

    def execute(self, context):
        results = context.scene.mu_cutter_results
        if not results:
            self.report({"WARNING"}, "No results to copy")
            return {"CANCELLED"}
        context.window_manager.clipboard = results
        self.report({"INFO"}, "Cutter results copied to clipboard")
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
        layout.prop(context.scene, "mu_cutter_max_stack")
        layout.operator(MU_OT_cutter_calculate.bl_idname)
        layout.operator(MU_OT_cutter_copy_results.bl_idname)

        if context.scene.mu_cutter_results:
            box = layout.box()
            for line in context.scene.mu_cutter_results.splitlines():
                box.label(text=line)


CUTTER_CLASSES = (
    MU_OT_cutter_calculate,
    MU_OT_cutter_copy_results,
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
    bpy.types.Scene.mu_cutter_max_stack = bpy.props.IntProperty(
        name=ui_text.PROP_CUTTER_MAX_STACK,
        default=1,
        min=1,
    )
    bpy.types.Scene.mu_cutter_results = bpy.props.StringProperty(
        name=ui_text.PANEL_CUTTER_RESULTS_LABEL,
        default="",
    )


def unregister_cutter_properties():
    del bpy.types.Scene.mu_cutter_results
    del bpy.types.Scene.mu_cutter_kerf
    del bpy.types.Scene.mu_cutter_max_stack
    del bpy.types.Scene.mu_cutter_stock_lengths
