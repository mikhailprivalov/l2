import re
from typing import Union, Tuple

from refprocessor.common import ValueRange, Value, get_sign_by_string, POINT_STRICT, SIGN_GT, SIGN_GTE, SIGN_LT, SIGN_LTE, RANGE_REGEXP


class ResultRight:
    MODE_NUMBER_RANGE = 'number_range'
    MODE_CONSTANT = 'constant'
    MODE_ANY = 'any'

    RESULT_MODE_NORMAL = 'normal'
    RESULT_MODE_MAYBE = 'maybe'
    RESULT_MODE_NOT_NORMAL = 'not_normal'

    def __init__(self, orig_str: str):
        orig_str = orig_str.strip().lower()
        self.range = ValueRange(0, 0)

        if not orig_str:
            self.mode = ResultRight.MODE_ANY
            return

        orig_str = re.sub(' +', ' ', orig_str)

        simple_range = ResultRight.check_is_range(orig_str)

        if simple_range:
            self.mode = simple_range[0]
            self.range = ValueRange(simple_range[1], simple_range[2])
            return

        const_range = ResultRight.check_is_constant_with_sign(orig_str)

        if const_range:
            self.mode = const_range[0]
            self.range = ValueRange(const_range[1], const_range[2])
            return

        self.mode = ResultRight.MODE_CONSTANT
        self.const = orig_str

    def test(self, value: str) -> str:
        if self.mode == ResultRight.MODE_ANY:
            return ResultRight.RESULT_MODE_NORMAL

        value = value.strip().lower()

        if self.mode == ResultRight.MODE_CONSTANT:
            return ResultRight.RESULT_MODE_NORMAL if value == self.const else ResultRight.RESULT_MODE_MAYBE

        numbers = re.findall(r"-?\d*[.,]\d+|-?\d+", value)

        if numbers:
            for n in numbers:
                n = float(n.replace(',', '.'))
                if not self.range.in_range(n):
                    return ResultRight.RESULT_MODE_NOT_NORMAL
        elif value:
            return ResultRight.RESULT_MODE_MAYBE

        return ResultRight.RESULT_MODE_NORMAL

    @staticmethod
    def check_is_range(s: str) -> Union[bool, Tuple[str, Union[float, Value], Union[float, Value]]]:
        matched = re.match(RANGE_REGEXP, s)

        if matched:
            g = list(map(lambda x: x if not x else x.strip(), matched.groups()))

            mode = ResultRight.MODE_NUMBER_RANGE

            if g[4] == 'до':
                return mode, Value(g[1]), Value(float(g[5]), mode=POINT_STRICT)

            return mode, Value(g[1]), Value(g[5])
        return False

    @staticmethod
    def check_is_constant_with_sign(orig_str: str) -> Union[bool, Tuple[str, Value, Value]]:
        matched = re.match(r"^([\w<>≤≥&;=]+) ?(-?\d+[.,]\d+|-?\d+)$", orig_str)

        if matched:
            g = list(matched.groups())

            mode = ResultRight.MODE_NUMBER_RANGE

            sign_orig = g[0]
            sign = get_sign_by_string(sign_orig)
            if not sign:
                return False

            value = g[1]

            if sign == SIGN_GT:
                return mode, Value(value=value, mode=POINT_STRICT), Value(value=float('inf'))

            if sign == SIGN_GTE:
                return mode, Value(value=value), Value(value=float('inf'))

            if sign == SIGN_LT:
                return mode, Value(value=float('-inf')), Value(value=value, mode=POINT_STRICT)

            if sign == SIGN_LTE:
                return mode, Value(value=float('-inf')), Value(value=value)

        return False
