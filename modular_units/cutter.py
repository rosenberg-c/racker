from __future__ import annotations

from typing import Iterable, List, Optional, Tuple, Union
import time
import math


def _coerce_positive_ints(values: Iterable[Union[float, int, str]]) -> List[int]:
    result = []
    for value in values:
        if value is None:
            continue
        try:
            number = int(round(float(value)))
        except (TypeError, ValueError):
            continue
        if number > 0:
            result.append(number)
    return result


def _coerce_positive_floats(values: Iterable[Union[float, int, str]]) -> List[float]:
    result = []
    for value in values:
        if value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if number > 0:
            result.append(number)
    return result


def parse_lengths_csv(value: str) -> List[int]:
    if not value:
        return []
    tokens = value.replace(";", ",").split(",")
    return _coerce_positive_ints(token.strip() for token in tokens if token.strip())


def parse_costs_csv(value: str) -> List[float]:
    if not value:
        return []
    tokens = value.replace(";", ",").split(",")
    return _coerce_positive_floats(token.strip() for token in tokens if token.strip())


def board_used_length(pieces: List[int], kerf: int) -> int:
    if not pieces:
        return 0
    kerf_total = kerf * (len(pieces) - 1)
    return sum(pieces) + kerf_total


def material_cost_for_plan(
    boards: List[Tuple[int, List[int]]],
    costs_by_length: dict[int, float],
) -> float:
    total = 0.0
    for board_length, _pieces in boards:
        total += costs_by_length.get(board_length, 0.0)
    return total


def greedy_cut_plan(
    pieces: List[int],
    stock_lengths: List[int],
    kerf: int,
    costs_by_length: Optional[dict[int, float]],
) -> Optional[List[Tuple[int, List[int]]]]:
    boards = []
    for length in pieces:
        best_index = None
        best_remaining = None
        for index, board in enumerate(boards):
            add_length = length if not board["pieces"] else length + kerf
            if board["used"] + add_length > board["length"]:
                continue
            remaining = board["length"] - (board["used"] + add_length)
            if best_remaining is None or remaining < best_remaining:
                best_remaining = remaining
                best_index = index

        if best_index is not None:
            board = boards[best_index]
            add_length = length if not board["pieces"] else length + kerf
            board["used"] += add_length
            board["pieces"].append(length)
            continue

        candidates = [stock for stock in stock_lengths if stock >= length]
        if not candidates:
            return None
        if costs_by_length is None:
            stock = min(candidates)
        else:
            stock = min(
                candidates,
                key=lambda value: (costs_by_length.get(value, 0.0), value),
            )
        boards.append({"length": stock, "used": length, "pieces": [length]})

    return [(board["length"], list(board["pieces"])) for board in boards]


def cut_operations_for_plan(
    boards: List[Tuple[int, List[int]]],
    max_stack: int,
) -> int:
    stack = max(1, int(max_stack))
    groups = stack_groups_for_plan(boards)
    return sum(math.ceil(count / stack) * len(key) for key, count in groups)


def stack_groups_for_plan(
    boards: List[Tuple[int, List[int]]],
) -> List[Tuple[Tuple[int, ...], int]]:
    groups = {}
    for _board_length, pieces in boards:
        key = tuple(sorted(pieces))
        groups[key] = groups.get(key, 0) + 1
    return sorted(groups.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))


def calculate_cut_plan(
    pieces_mm: List[int],
    stock_lengths_mm: List[int],
    kerf_mm: int,
    max_stack: int = 1,
    stock_costs: Optional[List[float]] = None,
    cut_cost: float = 0.0,
    timeout_seconds: float = 2.0,
    return_meta: bool = False,
) -> Optional[
    Union[
        Tuple[List[Tuple[int, List[int]]], int, int],
        Tuple[List[Tuple[int, List[int]]], int, int, dict[str, bool]],
    ]
]:
    pieces = sorted(_coerce_positive_ints(pieces_mm), reverse=True)
    stock_lengths = sorted(set(_coerce_positive_ints(stock_lengths_mm)))
    costs_by_length = None
    if stock_costs is not None:
        costs = _coerce_positive_floats(stock_costs)
        if len(costs) == len(stock_lengths_mm):
            costs_by_length = {
                length: cost for length, cost in zip(stock_lengths_mm, costs)
            }
    kerf = max(0, int(round(kerf_mm)))
    stack = max(1, int(max_stack))

    if not pieces or not stock_lengths:
        return None
    if max(pieces) > max(stock_lengths):
        return None

    best_plan = None
    best_total = None
    best_waste = None
    best_cuts = None
    best_boards = None
    best_cost = None
    min_board_cost = None
    max_stock_length = max(stock_lengths) if stock_lengths else 0
    if costs_by_length is not None:
        min_board_cost = min(costs_by_length.values()) if costs_by_length else None
    timed_out = False
    start_time = time.monotonic()
    memo = {}

    def board_state(boards):
        return tuple(sorted((board["length"], board["used"]) for board in boards))

    def is_better(total_length, waste, cut_ops, board_count, total_cost):
        if best_total is None:
            return True
        if costs_by_length is not None:
            if total_cost < best_cost:
                return True
            if total_cost == best_cost and total_length < best_total:
                return True
            if total_cost == best_cost and total_length == best_total and waste < best_waste:
                return True
            if (
                total_cost == best_cost
                and total_length == best_total
                and waste == best_waste
                and cut_ops < best_cuts
            ):
                return True
            if (
                total_cost == best_cost
                and total_length == best_total
                and waste == best_waste
                and cut_ops == best_cuts
                and board_count < best_boards
            ):
                return True
            return False
        if total_length < best_total:
            return True
        if total_length == best_total and waste < best_waste:
            return True
        if total_length == best_total and waste == best_waste and cut_ops < best_cuts:
            return True
        if (
            total_length == best_total
            and waste == best_waste
            and cut_ops == best_cuts
            and board_count < best_boards
        ):
            return True
        return False

    def dfs(index, boards, total_length):
        nonlocal best_plan, best_total, best_waste, best_cuts, best_boards, best_cost
        nonlocal timed_out

        if timeout_seconds is not None:
            if time.monotonic() - start_time > timeout_seconds:
                timed_out = True
                return

        if costs_by_length is not None and best_cost is not None and min_board_cost:
            remaining_pieces = pieces[index:]
            if remaining_pieces:
                remaining_length = sum(remaining_pieces) + kerf * (len(remaining_pieces) - 1)
                min_boards_needed = math.ceil(remaining_length / max_stock_length)
            else:
                min_boards_needed = 0
            current_cost = material_cost_for_plan(
                [(board["length"], board["pieces"]) for board in boards],
                costs_by_length,
            )
            lower_bound = current_cost + (min_boards_needed * min_board_cost)
            if lower_bound >= best_cost:
                return

        if costs_by_length is None:
            if best_total is not None and total_length > best_total:
                return

            state_key = (index, board_state(boards))
            prev_best = memo.get(state_key)
            if prev_best is not None and total_length >= prev_best:
                return
            memo[state_key] = total_length

        if index >= len(pieces):
            waste = sum(board["length"] - board["used"] for board in boards)
            board_count = len(boards)
            plan = [(board["length"], list(board["pieces"])) for board in boards]
            cut_ops = cut_operations_for_plan(plan, stack)
            total_cost = 0.0
            if costs_by_length is not None:
                total_cost = material_cost_for_plan(plan, costs_by_length)
                total_cost += cut_ops * float(cut_cost)
            if is_better(total_length, waste, cut_ops, board_count, total_cost):
                best_total = total_length
                best_waste = waste
                best_cuts = cut_ops
                best_boards = board_count
                best_cost = total_cost
                best_plan = plan
            return

        length = pieces[index]

        for board in boards:
            add_length = length if not board["pieces"] else length + kerf
            if board["used"] + add_length <= board["length"]:
                board["used"] += add_length
                board["pieces"].append(length)
                dfs(index + 1, boards, total_length)
                board["pieces"].pop()
                board["used"] -= add_length

        for stock in stock_lengths:
            if stock < length:
                continue
            if costs_by_length is None:
                if best_total is not None and total_length + stock > best_total:
                    continue
            board = {"length": stock, "used": length, "pieces": [length]}
            boards.append(board)
            dfs(index + 1, boards, total_length + stock)
            boards.pop()

    dfs(0, [], 0)

    if best_plan is None or best_total is None or best_waste is None:
        fallback = greedy_cut_plan(pieces, stock_lengths, kerf, costs_by_length)
        if fallback is None:
            return None
        best_plan = fallback
        best_total = sum(board[0] for board in best_plan)
        best_waste = sum(
            board[0] - board_used_length(board[1], kerf) for board in best_plan
        )
        timed_out = True

    if return_meta:
        return best_plan, best_total, best_waste, {
            "timed_out": timed_out,
            "used_greedy": best_plan is not None and best_cost is None and timed_out,
        }

    return best_plan, best_total, best_waste
