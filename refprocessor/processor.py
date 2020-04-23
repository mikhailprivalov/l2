from typing import Tuple, Union, List

from refprocessor.age_parser import AgeRight
from refprocessor.common import ValueRange, RANGE_IN
from refprocessor.result_parser import ResultRight


class RefProcessor:
    def __init__(self, ref: dict, age: List[int]):
        actual_key, actual_ref, actual_raw_ref = RefProcessor.get_actual_ref(ref, age)
        self.key = actual_key
        self.ref = actual_ref
        self.raw_ref = actual_raw_ref

    @staticmethod
    def get_actual_ref(ref: dict, age: List[int]) -> Union[Tuple[str, ResultRight, str], Tuple[None, None, None]]:
        for k in ref:
            age_rights = AgeRight(k)
            if age_rights.test(age):
                return k, ResultRight(ref[k]), ref[k]

        return None, None, None

    def get_active_ref(self, raw_ref=True):
        if raw_ref:
            return self.raw_ref
        if isinstance(self.ref, ResultRight):
            return self.ref
        return ValueRange((0, ")"), (0, ")"))

    def calc(self, value):
        if isinstance(self.ref, ResultRight):
            return self.ref.test(value)
        return ResultRight.RESULT_MODE_NORMAL, RANGE_IN
