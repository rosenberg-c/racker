import importlib.util
from collections import Counter
from pathlib import Path


_cutter_path = Path(__file__).resolve().parents[1] / "modular_units" / "cutter.py"
_cutter_spec = importlib.util.spec_from_file_location("mu_cutter", _cutter_path)
assert _cutter_spec is not None
_cutter_module = importlib.util.module_from_spec(_cutter_spec)
assert _cutter_spec.loader is not None
_cutter_spec.loader.exec_module(_cutter_module)

parse_lengths_csv = _cutter_module.parse_lengths_csv
board_used_length = _cutter_module.board_used_length
calculate_cut_plan = _cutter_module.calculate_cut_plan


def test_parse_lengths_csv():
    assert parse_lengths_csv("800, 1200;2000") == [800, 1200, 2000]
    assert parse_lengths_csv("  ") == []
    assert parse_lengths_csv("490, 392, 169") == [490, 392, 169]


def test_board_used_length():
    assert board_used_length([], 4) == 0
    assert board_used_length([490], 4) == 490
    assert board_used_length([490, 392, 169], 4) == 1059


def test_calculate_cut_plan_minimum_stock():
    pieces = [392] * 4 + [490] * 6 + [169] * 2
    stock = [800, 1200, 2000]
    kerf = 4

    plan = calculate_cut_plan(pieces, stock, kerf)
    assert plan is not None

    boards, total_stock, waste = plan
    assert total_stock == 5200
    assert waste == 318

    flat_pieces = [piece for _board_len, board_pieces in boards for piece in board_pieces]
    assert Counter(flat_pieces) == Counter(pieces)


def test_calculate_cut_plan_invalid_piece():
    pieces = [2100]
    stock = [800, 1200, 2000]
    plan = calculate_cut_plan(pieces, stock, 4)
    assert plan is None


def test_calculate_cut_plan_prefers_single_board():
    pieces = [100, 100, 100]
    stock = [250, 400]
    plan = calculate_cut_plan(pieces, stock, 0)

    assert plan is not None
    _boards, total_stock, waste = plan
    assert total_stock == 400
    assert waste == 100


def test_calculate_cut_plan_respects_kerf():
    pieces = [100, 100, 100]
    stock = [300, 400]
    plan = calculate_cut_plan(pieces, stock, 4)

    assert plan is not None
    _boards, total_stock, waste = plan
    assert total_stock == 400
    assert waste == 92


def test_calculate_cut_plan_multiple_boards():
    pieces = [300, 300, 300, 300]
    stock = [500, 700]
    plan = calculate_cut_plan(pieces, stock, 5)

    assert plan is not None
    _boards, total_stock, waste = plan
    assert total_stock == 1400
    assert waste == 190


def test_calculate_cut_plan_mixed_lengths():
    pieces = [250, 250, 250]
    stock = [300, 600]
    plan = calculate_cut_plan(pieces, stock, 0)

    assert plan is not None
    _boards, total_stock, waste = plan
    assert total_stock == 900
    assert waste == 150
