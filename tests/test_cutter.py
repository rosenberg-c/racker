import importlib.util
from collections import Counter
from pathlib import Path


_cutter_path = Path(__file__).resolve().parents[1] / "modular_units" / "cutter.py"
_cutter_spec = importlib.util.spec_from_file_location("mu_cutter", _cutter_path)
assert _cutter_spec is not None
_cutter_module = importlib.util.module_from_spec(_cutter_spec)
assert _cutter_spec.loader is not None
_cutter_spec.loader.exec_module(_cutter_module)

_select_path = (
    Path(__file__).resolve().parents[1] / "modular_units" / "cutter_select.py"
)
_select_spec = importlib.util.spec_from_file_location("mu_cutter_select", _select_path)
assert _select_spec is not None
_select_module = importlib.util.module_from_spec(_select_spec)
assert _select_spec.loader is not None
_select_spec.loader.exec_module(_select_module)

parse_lengths_csv = _cutter_module.parse_lengths_csv
parse_costs_csv = _cutter_module.parse_costs_csv
build_stock_materials = _cutter_module.build_stock_materials
StockMaterial = _cutter_module.StockMaterial
board_used_length = _cutter_module.board_used_length
calculate_cut_plan = _cutter_module.calculate_cut_plan
cut_operations_for_plan = _cutter_module.cut_operations_for_plan
material_cost_for_plan = _cutter_module.material_cost_for_plan
matches_prefix = _select_module.matches_prefix
matches_cutter_piece = _select_module.matches_cutter_piece
matches_instance_root = _select_module.matches_instance_root


def test_parse_lengths_csv():
    assert parse_lengths_csv("800, 1200;2000") == [800, 1200, 2000]
    assert parse_lengths_csv("  ") == []
    assert parse_lengths_csv("490, 392, 169") == [490, 392, 169]


def test_parse_costs_csv():
    assert parse_costs_csv("10, 12.5;20") == [10.0, 12.5, 20.0]
    assert parse_costs_csv(" ") == []


def test_build_stock_materials():
    materials = build_stock_materials([800, 1200], [10.0, 12.5])
    assert materials == [
        StockMaterial(length_mm=800, cost=10.0),
        StockMaterial(length_mm=1200, cost=12.5),
    ]


def test_board_used_length():
    assert board_used_length([], 4) == 0
    assert board_used_length([490], 4) == 490
    assert board_used_length([490, 392, 169], 4) == 1059


def test_material_cost_for_plan():
    boards = [(2000, [490, 490]), (1200, [392])]
    costs = {2000: 25.0, 1200: 15.0}
    assert material_cost_for_plan(boards, costs) == 40.0


def test_calculate_cut_plan_prefers_lower_cost():
    pieces = [400, 400]
    stock = [800, 1000]
    costs = [20.0, 1.0]

    materials = build_stock_materials(stock, costs)
    plan = calculate_cut_plan(pieces, materials, 0, 1, 0.0)
    assert plan is not None
    boards, total_stock, waste = plan
    assert total_stock == 1000
    assert waste == 200


def test_calculate_cut_plan_minimum_stock():
    pieces = [392] * 4 + [490] * 6 + [169] * 2
    stock = [800, 1200, 2000]
    kerf = 4

    materials = build_stock_materials(stock, [1.0, 1.0, 1.0])
    plan = calculate_cut_plan(pieces, materials, kerf)
    assert plan is not None

    boards, total_stock, waste = plan
    assert total_stock == 5200
    assert waste == 318

    flat_pieces = [piece for _board_len, board_pieces in boards for piece in board_pieces]
    assert Counter(flat_pieces) == Counter(pieces)


def test_calculate_cut_plan_invalid_piece():
    pieces = [2100]
    stock = [800, 1200, 2000]
    materials = build_stock_materials(stock, [1.0, 1.0, 1.0])
    plan = calculate_cut_plan(pieces, materials, 4)
    assert plan is None


def test_calculate_cut_plan_prefers_single_board():
    pieces = [100, 100, 100]
    stock = [250, 400]
    materials = build_stock_materials(stock, [1.0, 1.0])
    plan = calculate_cut_plan(pieces, materials, 0)

    assert plan is not None
    _boards, total_stock, waste = plan
    assert total_stock == 400
    assert waste == 100


def test_calculate_cut_plan_respects_kerf():
    pieces = [100, 100, 100]
    stock = [300, 400]
    materials = build_stock_materials(stock, [1.0, 1.0])
    plan = calculate_cut_plan(pieces, materials, 4)

    assert plan is not None
    _boards, total_stock, waste = plan
    assert total_stock == 400
    assert waste == 92


def test_calculate_cut_plan_multiple_boards():
    pieces = [300, 300, 300, 300]
    stock = [500, 700]
    materials = build_stock_materials(stock, [1.0, 1.0])
    plan = calculate_cut_plan(pieces, materials, 5)

    assert plan is not None
    _boards, total_stock, waste = plan
    assert total_stock == 1400
    assert waste == 190


def test_calculate_cut_plan_mixed_lengths():
    pieces = [250, 250, 250]
    stock = [300, 600]
    materials = build_stock_materials(stock, [1.0, 1.0])
    plan = calculate_cut_plan(pieces, materials, 0)

    assert plan is not None
    _boards, total_stock, waste = plan
    assert total_stock == 900
    assert waste == 150




def test_cut_operations_for_plan_with_stack():
    boards = [(1000, [400, 400]), (1000, [400])]
    assert cut_operations_for_plan(boards, 1) == 3
    assert cut_operations_for_plan(boards, 2) == 3


def test_cut_operations_for_plan_groups_identical_boards():
    boards = [(1000, [400, 400]), (1000, [400, 400])]
    assert cut_operations_for_plan(boards, 1) == 4
    assert cut_operations_for_plan(boards, 2) == 2


class _Dummy:
    def __init__(self, name, original=None, parent=None):
        self.name = name
        self.original = original
        self.parent = parent


class _Instance:
    def __init__(self, instance_object=None, parent=None):
        self.instance_object = instance_object
        self.parent = parent


def test_matches_prefix_uses_original_name():
    original = _Dummy("MU_Panel")
    eval_obj = _Dummy("PanelEval", original=original)
    assert matches_prefix(eval_obj)
    assert not matches_prefix(_Dummy("Other"))


def test_matches_cutter_piece_excludes_rails():
    assert matches_cutter_piece(_Dummy("MU_Panel"))
    assert not matches_cutter_piece(_Dummy("MU_Rail_Front_Left"))


def test_matches_instance_root_direct_instance():
    root = _Dummy("Root")
    inst = _Instance(instance_object=_Dummy("RootEval", original=root))
    assert matches_instance_root(inst, root)


def test_matches_instance_root_nested_parent_chain():
    root = _Dummy("Root")
    parent = _Dummy("ParentEval", original=root)
    child = _Dummy("ChildEval", parent=parent)
    inst = _Instance(parent=child)
    assert matches_instance_root(inst, root)


def test_matches_instance_root_mismatch():
    root = _Dummy("Root")
    other = _Dummy("Other")
    inst = _Instance(instance_object=other)
    assert not matches_instance_root(inst, root)
