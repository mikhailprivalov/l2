from typing import Tuple, Union, List

from appconf.manager import SettingManager
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

    def get_active_ref(self, raw_ref=True, single=False):
        if raw_ref:
            if single:
                show_only_needed_ref = SettingManager.get("show_only_needed_ref", default='True', default_type='b')
                if not show_only_needed_ref or not self.raw_ref:
                    return None

                show_full_needed_ref = SettingManager.get("show_full_needed_ref", default='False', default_type='b')
                if show_full_needed_ref:
                    return {self.key: self.raw_ref}

                return {'Все': self.raw_ref}
            return self.raw_ref
        if isinstance(self.ref, ResultRight):
            return self.ref
        return ValueRange((0, ")"), (0, ")"))

    def calc(self, value):
        if isinstance(self.ref, ResultRight):
            return self.ref.test(value)
        return ResultRight.RESULT_MODE_NORMAL, RANGE_IN
