import re
from typing import Tuple, Union, List

from refprocessor.common import RANGE_REGEXP, SIGN_GT, SIGN_GTE, SIGN_LT, SIGN_LTE, get_sign_by_string, ValueRange, \
    POINT_STRICT, Value, RANGE_IN


class AgeRight:
    MODE_DAY = "day"
    MODE_MONTH = "month"
    MODE_YEAR = "year"
    MODE_UNKNOWN = "unknow"

    DAY_ORIGS = (
        "дней",
        "день",
        "дня",
        "дн",
        "дн.",
        "д",
        "д.",
    )

    MONTH_ORIGS = (
        "месяц",
        "месяцев",
        "месяца",
        "мес",
        "мес.",
        "м",
        "м.",
    )

    YEAR_ORIGS = (
        "год",
        "года",
        "лет",
        "г",
        "г.",
        "л",
        "л.",
    )

    MODES_FROM_ORIGS = (
        (DAY_ORIGS, MODE_DAY),
        (MONTH_ORIGS, MODE_MONTH),
        (YEAR_ORIGS, MODE_YEAR),
    )

    def __init__(self, orig_str: str):
        orig_str = orig_str.strip().lower()
        if AgeRight.check_is_all(orig_str):
            self.age_range = ValueRange(0, float('inf'))
            self.mode = AgeRight.MODE_YEAR
            return

        if "един" in orig_str:
            orig_str = "0-2"
        if "отсутств" in orig_str:
            orig_str = "0-0"

        constant_simple_year = AgeRight.check_is_constant_simple_year(orig_str)
        if constant_simple_year:
            self.age_range = ValueRange(constant_simple_year, constant_simple_year)
            self.mode = AgeRight.MODE_YEAR
            return

        simple_year_age = AgeRight.check_is_simple_year_range(orig_str)
        if simple_year_age:
            self.age_range = ValueRange(int(simple_year_age.group(1)), int(simple_year_age.group(2)))
            self.mode = AgeRight.MODE_YEAR
            return

        orig_str = re.sub(' +', ' ', orig_str)

        constant_age_with_mode = AgeRight.check_is_constant_age_with_mode(orig_str)
        if constant_age_with_mode:
            self.age_range = ValueRange(constant_age_with_mode[0], constant_age_with_mode[0])
            self.mode = constant_age_with_mode[1]
            return

        constant_age_with_sign = AgeRight.check_is_constant_age_with_sign_and_optional_mode(orig_str)
        if constant_age_with_sign:
            self.age_range = ValueRange(constant_age_with_sign[1], constant_age_with_sign[2])
            self.mode = constant_age_with_sign[0]
            return

        full_range = AgeRight.check_is_full_range(orig_str)
        if full_range:
            self.age_range = ValueRange(full_range[1], full_range[2])
            self.mode = full_range[0]
            return

        self.age_range = ValueRange(Value(0, POINT_STRICT), Value(0, POINT_STRICT))
        self.mode = AgeRight.MODE_UNKNOWN

    def test(self, age: List[int]) -> bool:
        if self.mode == AgeRight.MODE_UNKNOWN:
            return False

        if self.mode == AgeRight.MODE_DAY:
            if age[1] > 0 or age[2] > 0:
                return False
            age_var = age[0]
        elif self.mode == AgeRight.MODE_MONTH:
            if age[2] > 0:
                return False
            age_var = age[1]
        else:
            age_var = age[2]

        return self.age_range.in_range(age_var) == RANGE_IN

    @staticmethod
    def check_is_all(orig_str: str) -> bool:
        return orig_str in ["все", ""]

    @staticmethod
    def check_is_simple_year_range(orig_str: str):
        orig_str = orig_str.replace(" ", "")
        return re.match(r"^(\d+)-(\d+)$", orig_str)

    @staticmethod
    def check_is_constant_simple_year(orig_str: str) -> Union[bool, int]:
        orig_str = orig_str.replace(" ", "")
        if not orig_str.isdigit():
            return False
        return int(orig_str)

    @staticmethod
    def check_is_constant_age_with_mode(orig_str: str) -> Union[bool, Tuple[int, str]]:
        matched = re.match(r"^(\d+) ([\w.]+)$", orig_str)
        if not matched:
            return False
        value = int(matched.group(1))
        mode_orig = matched.group(2).lower()

        mode = AgeRight.get_mode_by_string(mode_orig)
        if mode != AgeRight.MODE_UNKNOWN:
            return value, mode

        return False

    @staticmethod
    def check_is_constant_age_with_sign_and_optional_mode(orig_str: str) -> Union[bool, Tuple[str, Value, Value]]:
        matched = re.match(r"^([\w<>≤≥&;=]+) (\d+)( )?(\w+)?$", orig_str)

        if matched:
            g = list(matched.groups())
            if g[3]:
                mode = AgeRight.get_mode_by_string(g[3])
                if mode == AgeRight.MODE_UNKNOWN:
                    return False
            else:
                mode = AgeRight.MODE_YEAR

            sign_orig = g[0]
            sign = get_sign_by_string(sign_orig)
            if not sign:
                return False

            value = int(g[1])

            if sign == SIGN_GT:
                return mode, Value(value=value, mode=POINT_STRICT), Value(value=float('inf'))

            if sign == SIGN_GTE:
                return mode, Value(value=value), Value(value=float('inf'))

            if sign == SIGN_LT:
                return mode, Value(value=0), Value(value=value, mode=POINT_STRICT)

            if sign == SIGN_LTE:
                return mode, Value(value=0), Value(value=value)

        return False

    @staticmethod
    def check_is_full_range(orig_str: str) -> Union[bool, Tuple[str, Union[int, Value], Union[int, Value]]]:
        matched = re.match(RANGE_REGEXP, orig_str)

        if matched:
            g = list(map(lambda x: x if not x else x.strip(), matched.groups()))
            if g[3] or g[7]:
                mode = AgeRight.get_mode_by_string(g[3] or g[7])
                if mode == AgeRight.MODE_UNKNOWN:
                    return False
            else:
                mode = AgeRight.MODE_YEAR

            if g[4] == 'до':
                return mode, int(g[1]), Value(int(g[5]), mode=POINT_STRICT)

            return mode, int(g[1]), int(g[5])

        return False

    @staticmethod
    def get_mode_by_string(s: str) -> Union[bool, str]:
        for mode_origs, mode in AgeRight.MODES_FROM_ORIGS:
            if s in mode_origs:
                return mode
        return AgeRight.MODE_UNKNOWN
