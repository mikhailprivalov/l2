import json
from typing import Union, Dict, Iterable, Any

from laboratory.settings import SYSTEM_AS_VI


def one_of_includes(check_value: Union[str, Iterable[str], Dict[str, Any]], values_to_check: Iterable[str]):
    return any(x in check_value for x in values_to_check)


def select_key_by_one_of_values_includes(value: str, values_to_check: Dict[str, Iterable]):
    for key in values_to_check:
        if one_of_includes(value, values_to_check[key]):
            return key
    return None


def replace_values_by_keys(value: str, to_replace: Dict[str, str]):
    for key in to_replace:
        value = value.replace(f"{{{{{key}}}}}", to_replace[key])
    return value


def non_selected_visible_type(orig, more_filters=None, for_treeselect=None):
    if not more_filters:
        more_filters = {}
    if for_treeselect:
        return list_non_selected_visible_type(orig.objects.filter(hide=False, **more_filters).values("pk", "title").order_by("pk"), for_treeselect)
    return list_non_selected_visible_type(orig.objects.filter(hide=False, **more_filters).values("pk", "title").order_by("pk"))


def list_non_selected_visible_type(orig, for_treeselect=None):
    if for_treeselect:
        return [{"id": i['pk'], "label": i['title']} for i in list(orig)]
    return [{"pk": -1, "title": "Не выбрано"}, *list(orig)]


def none_if_minus_1(v):
    if v == -1 or v == "-1":
        return None
    return v


def get_system_name():
    return 'VI' if SYSTEM_AS_VI else 'L2'


def values_from_structure_data(data):
    s = ''
    for v in data:
        if v['group_title']:
            s = f"{s} [{v['group_title']}]:"
        for field in v['fields']:
            if field['field_type'] in [24, 25, 26]:
                continue
            if field['value']:
                if field['title_field']:
                    s = f"{s} {field['title_field']}"
                s = f"{s} {field['value']};"
    return s.strip()


def values_as_structure_data(data):
    values = []
    from directions.models import ParaclinicResult

    for v in data:
        for field in v['fields']:
            s = ''
            if v['group_title']:
                s = f"[{v['group_title']}]"
            if field['title_field']:
                s = f"{s} {field['title_field']}".strip()

            if field['field_type'] in [24, 25, 26]:
                continue
            if field['value']:
                vv = field['value']
                t = field['field_type']
                is_table = t == 27

                values.append(
                    {
                        "title": s,
                        "value": json.loads(vv) if is_table else ParaclinicResult.JsonParser.from_static_json_to_string_value(vv, t),
                        "table": is_table,
                    }
                )
    return values


def shorten_fio(fio):
    fio_data = fio.split(" ")
    family = fio_data[0]
    name_short = fio_data[1][0]
    patronymic_short = None
    if len(fio_data) > 2 and len(fio_data[2]) > 0:
        patronymic_short = fio_data[2][0]
    if patronymic_short is None:
        return f"{family} {name_short}."
    return f"{family} {name_short}.{patronymic_short}."
