from typing import Any, List


def transpose(orig: List[List[Any]]) -> List[List[Any]]:
    """
    Транспонирование списка списков
    """
    max_len = max([len(x) for x in orig])
    for row in orig:
        row.extend([None] * (max_len - len(row)))
    return list(map(list, zip(*orig)))
