import re
from typing import Tuple, Union, List

SIGN_GT = ">"
SIGN_GTE = ">="
SIGN_LT = "<"
SIGN_LTE = "<="

# Знаки больше
SIGNS_GT = (
    ">",
    "&gt;",
    "старше",
    "больше",
    "более",
)
# Знаки больше или равно
SIGNS_GTE = (
    ">=",
    "≥",
    "&ge;",
    "от",
    "с",
)

# Знаки меньше
SIGNS_LT = (
    "<",
    "&lt;",
    "младше",
    "меньше",
    "менее",
)
# Знаки меньше или равно
SIGNS_LTE = (
    "<=",
    "≤",
    "&le;",
    "до",
)

SIGNS_ORIG_TO_SIGN = (
    (SIGNS_GT, SIGN_GT),
    (SIGNS_GTE, SIGN_GTE),
    (SIGNS_LT, SIGN_LT),
    (SIGNS_LTE, SIGN_LTE),
)


class Age:
    MODE_STRICT = ")"
    MODE_NON_STRICT = "]"

    def __init__(self, value: Union[int, float, Tuple[Union[int, float], str]], mode=MODE_NON_STRICT):
        if isinstance(value, tuple):
            self.value = value[0]
            self.mode = value[1]
        else:
            self.value = value
            self.mode = mode

    def __eq__(self, other: 'Age'):
        return self.value == other.value and self.mode == other.mode

    def __str__(self):
        return f"{self.mode}{self.value}"


class AgeRange:
    RANGE_TEMPLATE = r"^(от )?(\d+)( )?([\w.]+)* ([-–] |до )(\d+)( )?([\w.]+)*$"

    def __init__(self, age_from: Union[Age, int, float, Tuple[Union[int, float], str]], age_to: Union[Age, int, float]):
        if isinstance(age_from, Age):
            self.age_from = age_from
        else:
            self.age_from = Age(age_from)

        if isinstance(age_to, Age):
            self.age_to = age_to
        else:
            self.age_to = Age(age_to)

    def in_range(self, age: int):
        if self.age_from.mode == Age.MODE_STRICT and age <= self.age_from.value:
            return False
        if self.age_from.mode == Age.MODE_NON_STRICT and age < self.age_from.value:
            return False

        if self.age_to.mode == Age.MODE_STRICT and age >= self.age_to.value:
            return False
        if self.age_to.mode == Age.MODE_NON_STRICT and age > self.age_to.value:
            return False

        return True

    def __eq__(self, other: 'AgeRange'):
        return self.age_from == other.age_from and self.age_to == other.age_to

    def __str__(self):
        return f"{self.age_from} – {self.age_to}"


class AgeRight:
    MODE_DAY = "day"
    MODE_MONTH = "month"
    MODE_YEAR = "year"
    MODE_UNKNOW = "unknow"

    DAY_ORIGS = (
        "дней",
        "день",
        "дня",
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
            self.age_range = AgeRange(0, float('inf'))
            self.mode = AgeRight.MODE_YEAR
            return

        constant_simple_year = AgeRight.check_is_constant_simple_year(orig_str)
        if constant_simple_year:
            self.age_range = AgeRange(constant_simple_year, constant_simple_year)
            self.mode = AgeRight.MODE_YEAR
            return

        simple_year_age = AgeRight.check_is_simple_year_range(orig_str)
        if simple_year_age:
            self.age_range = AgeRange(int(simple_year_age.group(1)), int(simple_year_age.group(2)))
            self.mode = AgeRight.MODE_YEAR
            return

        orig_str = re.sub(' +', ' ', orig_str)

        constant_age_with_mode = AgeRight.check_is_constant_age_with_mode(orig_str)
        if constant_age_with_mode:
            self.age_range = AgeRange(constant_age_with_mode[0], constant_age_with_mode[0])
            self.mode = constant_age_with_mode[1]
            return

        constant_age_with_sign = AgeRight.check_is_constant_age_with_sign_and_optional_mode(orig_str)
        if constant_age_with_sign:
            self.age_range = AgeRange(constant_age_with_sign[1], constant_age_with_sign[2])
            self.mode = constant_age_with_sign[0]
            return

        full_range = AgeRight.check_is_full_range(orig_str)
        if full_range:
            self.age_range = AgeRange(full_range[1], full_range[2])
            self.mode = full_range[0]
            return

        self.age_range = AgeRange(Age(0, Age.MODE_STRICT), Age(0, Age.MODE_STRICT))
        self.mode = AgeRight.MODE_UNKNOW

    def test(self, age: List[int]) -> bool:
        if self.mode == AgeRight.MODE_UNKNOW:
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

        return self.age_range.in_range(age_var)

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
        if mode != AgeRight.MODE_UNKNOW:
            return value, mode

        return False

    @staticmethod
    def check_is_constant_age_with_sign_and_optional_mode(orig_str: str) -> Union[bool, Tuple[str, Age, Age]]:
        matched = re.match(r"^([\w|<>+≤≥&;=]+) (\d+)( )?(\w+)?$", orig_str)

        if matched:
            g = list(matched.groups())
            if g[3]:
                mode = AgeRight.get_mode_by_string(g[3])
                if mode == AgeRight.MODE_UNKNOW:
                    return False
            else:
                mode = AgeRight.MODE_YEAR

            sign_orig = g[0]
            sign = AgeRight.get_sign_by_string(sign_orig)
            if not sign:
                return False

            value = int(g[1])

            if sign == SIGN_GT:
                return mode, Age(value=value, mode=Age.MODE_STRICT), Age(value=float('inf'))

            if sign == SIGN_GTE:
                return mode, Age(value=value), Age(value=float('inf'))

            if sign == SIGN_LT:
                return mode, Age(value=0), Age(value=value, mode=Age.MODE_STRICT)

            if sign == SIGN_LTE:
                return mode, Age(value=0), Age(value=value)

        return False

    @staticmethod
    def check_is_full_range(orig_str: str) -> Union[bool, Tuple[str, int, int]]:
        matched = re.match(AgeRange.RANGE_TEMPLATE, orig_str)

        if matched:
            g = list(matched.groups())
            if g[3] or g[7]:
                mode = AgeRight.get_mode_by_string(g[3] or g[7])
                if mode == AgeRight.MODE_UNKNOW:
                    return False
            else:
                mode = AgeRight.MODE_YEAR

            return mode, int(g[1]), int(g[5])

        return False

    @staticmethod
    def get_mode_by_string(s: str) -> Union[bool, str]:
        for mode_origs, mode in AgeRight.MODES_FROM_ORIGS:
            if s in mode_origs:
                return mode
        return AgeRight.MODE_UNKNOW

    @staticmethod
    def get_sign_by_string(s: str) -> Union[None, str]:
        for signs in SIGNS_ORIG_TO_SIGN:
            if s in signs[0]:
                return signs[1]
        return None
