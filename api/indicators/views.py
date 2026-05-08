import datetime
import json
import re

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from api.indicators.sql_func import indicator_sql
from directory.models import ParaclinicInputField, ParaclinicInputGroups
from directions.models import Issledovaniya, ParaclinicResultIndicator
from external_system.models import CuratorCdaFields, CdaFields
from utils.dates import normalize_dots_date


def _parse_input_templates(field: ParaclinicInputField):
    values = []
    if field.input_templates and field.input_templates != "[]":
        values = json.loads(field.input_templates)
    if field.required:
        return ['- Не выбрано'] + values
    return values


def _normalize_formula_for_curator(formula: str, curator_field_pk: int):
    if not formula:
        return ""
    return re.sub(rf"\{{{curator_field_pk}\}}", "[_curator_value_]", formula)


def _replace_js_operators(expr: str):
    expr = expr.replace("&&", " and ").replace("||", " or ")
    expr = re.sub(r"(?<![=!])!(?!=)", " not ", expr)
    return expr


def _split_ternary(formula: str):
    depth = 0
    quote = None
    q_pos = -1
    c_pos = -1
    for i, ch in enumerate(formula):
        if quote:
            if ch == quote and (i == 0 or formula[i - 1] != "\\"):
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
        elif ch == "?" and depth == 0 and q_pos == -1:
            q_pos = i
        elif ch == ":" and depth == 0 and q_pos != -1:
            c_pos = i
            break
    if q_pos != -1 and c_pos != -1:
        return formula[:q_pos], formula[q_pos + 1:c_pos], formula[c_pos + 1:]
    return None


def _safe_eval_expr(expr: str):
    is_empty = lambda v: not v
    is_filled = lambda v: not is_empty(v)
    return eval(
        expr,
        {"__builtins__": {}},
        {
            "isEmpty": is_empty,
            "isFilled": is_filled,
        },
    )


def _calculate_curator_score(formula: str, curator_value):
    if not formula:
        return ""
    return "1"


@require_POST
def search_indicator(request):
    request_data = json.loads(request.body)
    status = int(request_data.get("status", 2))
    hospital = int(request_data.get("hospital", -1))
    date_period = request_data["datePeriod"]
    time_start = f'{normalize_dots_date(date_period[0])} {request_data.get("time_start", "00:00")}:00'
    time_end = f'{normalize_dots_date(date_period[1])} {request_data.get("time_end", "23:59")}:59:999999'
    datetime_start = datetime.datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
    datetime_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S:%f')

    user_hospital = request.user.doctorprofile.get_hospital_id() or -1

    if user_hospital != hospital and "Заполнение экстренных извещений" not in [str(x) for x in request.user.groups.all()]:
        hospital = -1

    if hospital == -1:
        return JsonResponse(
            {
                'result': [],
            }
        )

    doctorprofile = request.user.doctorprofile
    indicators = CuratorCdaFields.objects.filter(curator=doctorprofile).values_list("indicator_id", flat=True)
    cda_pks = CdaFields.objects.filter(pk__in=indicators).values_list("pk", flat=True)
    groups_obj = ParaclinicInputGroups.objects.filter(cda_option__in=cda_pks)
    fields = list(ParaclinicInputField.objects.filter(group__in=groups_obj))
    fields_obj = [f.pk for f in fields]
    field_to_group = {f.pk: f.group_id for f in fields}
    group_to_curator_field = {}
    group_to_score_field = {}
    for field in fields:
        if field.field_type in [10, 18] and field.group_id not in group_to_curator_field:
            group_to_curator_field[field.group_id] = field
        if field.field_type == 3 and field.group_id not in group_to_score_field:
            group_to_score_field[field.group_id] = field

    result_extra = indicator_sql(tuple(fields_obj), datetime_start, datetime_end)

    result = []
    prev_direction, prev_group = None, None
    step = 0
    current_result = {}
    for i in result_extra:
        if step == 0:
            group_id = field_to_group.get(i.field_id)
            current_result = {
                "direction": i.direction_id,
                "issledovaniye": i.issledovaniye_id,
                'hospital': i.hospital_title,
                'indicatorTitle': i.group_title,
                'groupId': group_id,
            }

        if (prev_direction != i.direction_id or prev_group != i.group_title) and step != 0:
            result.append(current_result.copy())
            group_id = field_to_group.get(i.field_id)
            current_result = {
                "direction": i.direction_id,
                "issledovaniye": i.issledovaniye_id,
                'hospital': i.hospital_title,
                'indicatorTitle': i.group_title,
                'groupId': group_id,
            }
        if "значение" in i.field_title.lower():
            current_result['hospitalValue'] = i.result_value
        if "балл" in i.field_title.lower():
            current_result['score'] = i.result_value
        step += 1
        prev_direction = i.direction_id
        prev_group = i.group_title
    if current_result:
        result.append(current_result.copy())

    issledovaniye_ids = [r["issledovaniye"] for r in result]
    curator_field_ids = [
        group_to_curator_field[r["groupId"]].pk
        for r in result
        if r.get("groupId") in group_to_curator_field
    ]
    score_field_ids = [
        group_to_score_field[r["groupId"]].pk
        for r in result
        if r.get("groupId") in group_to_score_field
    ]
    all_field_ids = list(set(curator_field_ids + score_field_ids))

    saved_values = {}
    if issledovaniye_ids and all_field_ids:
        saved_values = {
            (x.issledovaniye_id, x.field_id): x.value
            for x in ParaclinicResultIndicator.objects.filter(
                issledovaniye_id__in=issledovaniye_ids,
                field_id__in=all_field_ids,
            )
        }

    for row in result:
        curator_field = group_to_curator_field.get(row.get("groupId"))
        score_field = group_to_score_field.get(row.get("groupId"))
        if not curator_field:
            row["curatorFieldPk"] = None
            row["curatorFieldType"] = None
            row["curatorVariants"] = []
            row["curatorValue"] = ""
            row["curatorScoreFieldPk"] = score_field.pk if score_field else None
            row["curatorScoreFormula"] = ""
            row["curatorScore"] = saved_values.get((row["issledovaniye"], score_field.pk), "") if score_field else ""
            row.pop("groupId", None)
            continue

        variants = _parse_input_templates(curator_field)
        default_value = variants[0] if curator_field.field_type == 10 and variants else ""
        value = saved_values.get((row["issledovaniye"], curator_field.pk), default_value)
        formula = _normalize_formula_for_curator(score_field.default_value, curator_field.pk) if score_field else ""
        row["curatorFieldPk"] = curator_field.pk
        row["curatorFieldType"] = curator_field.field_type
        row["curatorVariants"] = variants if curator_field.field_type == 10 else []
        row["curatorValue"] = value
        row["curatorScoreFieldPk"] = score_field.pk if score_field else None
        row["curatorScoreFormula"] = formula
        row["curatorScore"] = saved_values.get((row["issledovaniye"], score_field.pk), "") if score_field else ""
        row.pop("groupId", None)

    return JsonResponse({'rows': result})


@require_POST
def save_indicator_value(request):
    request_data = json.loads(request.body)
    iss_pk = int(request_data.get("issledovaniye", 0))
    field_pk = int(request_data.get("fieldPk", 0))
    value = request_data.get("value", "")
    score_field_pk = int(request_data.get("scoreFieldPk", 0))
    score_formula = request_data.get("scoreFormula", "")
    if not iss_pk or not field_pk:
        return JsonResponse({"ok": False, "message": "issledovaniye and fieldPk are required"}, status=400)

    issledovaniye = Issledovaniya.objects.get(pk=iss_pk)
    field = ParaclinicInputField.objects.get(pk=field_pk)
    ParaclinicResultIndicator.objects.update_or_create(
        issledovaniye=issledovaniye,
        field=field,
        defaults={
            "value": value,
            "doctor_profile": request.user.doctorprofile,
        },
    )
    score_value = ""
    if score_field_pk and score_formula:
        score_field = ParaclinicInputField.objects.get(pk=score_field_pk)
        score_value = _calculate_curator_score(score_formula, value)
        ParaclinicResultIndicator.objects.update_or_create(
            issledovaniye=issledovaniye,
            field=score_field,
            defaults={
                "value": score_value,
                "doctor_profile": request.user.doctorprofile,
            },
        )
    return JsonResponse({"ok": True, "curatorScore": score_value})
