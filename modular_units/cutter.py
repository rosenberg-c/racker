from __future__ import annotations

from typing import Iterable, List, Optional, Tuple, Union


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


def parse_lengths_csv(value: str) -> List[int]:
    if not value:
        return []
    tokens = value.replace(";", ",").split(",")
    return _coerce_positive_ints(token.strip() for token in tokens if token.strip())


def board_used_length(pieces: List[int], kerf: int) -> int:
    if not pieces:
        return 0
    kerf_total = kerf * (len(pieces) - 1)
    return sum(pieces) + kerf_total


def calculate_cut_plan(
    pieces_mm: List[int],
    stock_lengths_mm: List[int],
    kerf_mm: int,
) -> Optional[Tuple[List[Tuple[int, List[int]]], int, int]]:
    pieces = sorted(_coerce_positive_ints(pieces_mm), reverse=True)
    stock_lengths = sorted(set(_coerce_positive_ints(stock_lengths_mm)))
    kerf = max(0, int(round(kerf_mm)))

    if not pieces or not stock_lengths:
        return None
    if max(pieces) > max(stock_lengths):
        return None

    best_plan = None
    best_total = None
    best_waste = None
    best_boards = None
    memo = {}

    def board_state(boards):
        return tuple(sorted((board["length"], board["used"]) for board in boards))

    def is_better(total_length, waste, board_count):
        if best_total is None:
            return True
        if total_length < best_total:
            return True
        if total_length == best_total and waste < best_waste:
            return True
        if total_length == best_total and waste == best_waste and board_count < best_boards:
            return True
        return False

    def dfs(index, boards, total_length):
        nonlocal best_plan, best_total, best_waste, best_boards

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
            if is_better(total_length, waste, board_count):
                best_total = total_length
                best_waste = waste
                best_boards = board_count
                best_plan = [
                    (board["length"], list(board["pieces"])) for board in boards
                ]
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
            if best_total is not None and total_length + stock > best_total:
                continue
            board = {"length": stock, "used": length, "pieces": [length]}
            boards.append(board)
            dfs(index + 1, boards, total_length + stock)
            boards.pop()

    dfs(0, [], 0)

    if best_plan is None or best_total is None or best_waste is None:
        return None

    return best_plan, best_total, best_waste
