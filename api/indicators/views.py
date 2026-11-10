import datetime
import json
import re

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from api.indicators.journal import aggregate_approval_rows
from api.indicators.sql_func import approval_journal_sql, indicator_sql
from directory.models import ParaclinicInputField, ParaclinicInputGroups
from directions.models import Issledovaniya, ParaclinicResult, ParaclinicResultIndicator
from document_management.models import DocumentApprovalSign, Documents, TypeDocuments, TypeDocumentsSchema
from external_system.models import CuratorCdaFields, CdaFields
from hospitals.models import Hospitals
from laboratory.decorators import group_required
from utils.dates import normalize_dots_date

APPROVAL_JOURNAL_GROUP = "Журнал утверждения"


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


@require_POST
def search_indicator(request):
    request_data = json.loads(request.body)
    hospital = int(request_data.get("hospital", -1))
    filter_by_date = bool(request_data.get("filterByDate", True))
    date_period = request_data.get("datePeriod") or ["", ""]
    datetime_start = None
    datetime_end = None
    if filter_by_date:
        if date_period[0]:
            time_start = f'{normalize_dots_date(date_period[0])} {request_data.get("time_start", "00:00")}:00'
            datetime_start = datetime.datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
        if len(date_period) > 1 and date_period[1]:
            time_end = f'{normalize_dots_date(date_period[1])} {request_data.get("time_end", "23:59")}:59:999999'
            datetime_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S:%f')
    has_start = datetime_start is not None
    has_end = datetime_end is not None
    if not has_start:
        datetime_start = datetime.datetime(1970, 1, 1)
    if not has_end:
        datetime_end = datetime.datetime(2100, 1, 1)

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

    result_extra = indicator_sql(tuple(fields_obj), datetime_start, datetime_end, filter_by_date, has_start, has_end)

    def _indicator_row(row):
        group_id = field_to_group.get(row.field_id)
        return {
            "direction": row.document_id or row.direction_id,
            "documentId": row.document_id,
            "issledovaniye": row.issledovaniye_id,
            "hospital": row.hospital_title,
            "confirmDate": row.d_confirm or "",
            "indicatorTitle": row.group_title,
            "groupId": group_id,
        }

    result = []
    prev_key = None
    step = 0
    current_result = {}
    for i in result_extra:
        row_key = (i.document_id, i.direction_id, i.group_title)
        if step == 0:
            current_result = _indicator_row(i)

        if prev_key != row_key and step != 0:
            result.append(current_result.copy())
            current_result = _indicator_row(i)
        if "значение" in i.field_title.lower():
            current_result['hospitalValue'] = i.result_value
        if "балл" in i.field_title.lower():
            current_result['score'] = i.result_value
        step += 1
        prev_key = row_key
    if current_result:
        result.append(current_result.copy())

    issledovaniye_ids = [r["issledovaniye"] for r in result]
    curator_field_ids = [group_to_curator_field[r["groupId"]].pk for r in result if r.get("groupId") in group_to_curator_field]
    score_field_ids = [group_to_score_field[r["groupId"]].pk for r in result if r.get("groupId") in group_to_score_field]
    all_field_ids = list(set(curator_field_ids + score_field_ids))

    saved_records = {}
    if issledovaniye_ids and all_field_ids:
        saved_records = {
            (x.issledovaniye_id, x.field_id): x
            for x in ParaclinicResultIndicator.objects.filter(
                issledovaniye_id__in=issledovaniye_ids,
                field_id__in=all_field_ids,
            )
        }
    saved_values = {key: record.value for key, record in saved_records.items()}

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
            row["curatorApproved"] = False
            row["curatorComment"] = ""
            row.pop("groupId", None)
            continue

        curator_record = saved_records.get((row["issledovaniye"], curator_field.pk))
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
        row["curatorApproved"] = curator_record.approved if curator_record else False
        row["curatorComment"] = curator_record.comment if curator_record else ""
        row.pop("groupId", None)

    return JsonResponse({'rows': result})


@require_POST
def save_indicator_value(request):
    request_data = json.loads(request.body)
    iss_pk = int(request_data.get("issledovaniye", 0))
    field_pk = int(request_data.get("fieldPk", 0))
    value = request_data.get("value", "")
    score_field_pk = int(request_data.get("scoreFieldPk", 0))
    curator_score_value = request_data.get("curatorScore", "")
    approved = bool(request_data.get("approved", False))
    comment = request_data.get("comment", "")
    if not iss_pk or not field_pk:
        return JsonResponse({"ok": False, "message": "issledovaniye and fieldPk are required"}, status=400)

    ParaclinicResultIndicator.objects.update_or_create(
        issledovaniye_id=iss_pk,
        field_id=field_pk,
        defaults={
            "value": value,
            "approved": approved,
            "comment": comment,
            "doctor_profile": request.user.doctorprofile,
        },
    )
    if score_field_pk:
        ParaclinicResultIndicator.objects.update_or_create(
            issledovaniye_id=iss_pk,
            field_id=score_field_pk,
            defaults={
                "value": curator_score_value,
                "doctor_profile": request.user.doctorprofile,
            },
        )
    return JsonResponse({"ok": True, "curatorScore": curator_score_value})


def _body(request):
    if not request.body:
        return {}
    return json.loads(request.body)


def _period_bounds(data):
    filter_by_date = bool(data.get("filterByDate", True))
    date_period = data.get("datePeriod") or ["", ""]
    datetime_start = datetime.datetime(1970, 1, 1)
    datetime_end = datetime.datetime(2100, 1, 1)
    if filter_by_date and date_period and date_period[0]:
        datetime_start = datetime.datetime.strptime(f"{normalize_dots_date(str(date_period[0]))} 00:00:00", "%Y-%m-%d %H:%M:%S")
    if filter_by_date and len(date_period) > 1 and date_period[1]:
        datetime_end = datetime.datetime.strptime(f"{normalize_dots_date(str(date_period[1]))} 23:59:59:999999", "%Y-%m-%d %H:%M:%S:%f")
    return filter_by_date, datetime_start, datetime_end


def _hospital_filter(data):
    try:
        hospital_id = int(data.get("hospitalId", -1))
    except (TypeError, ValueError):
        hospital_id = -1
    if hospital_id > 0:
        return hospital_id, True
    return 0, False


def _format_date(value):
    if not value:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime("%d.%m.%Y")


def _child_payload(document):
    type_title = document.type_document.title if document.type_document_id and document.type_document else "Документ"
    return {"id": document.pk, "title": f"{type_title} №{document.pk}"}


def _sign_payload(sign):
    fio = sign.doctor.get_fio() if sign.doctor_id and sign.doctor else ""
    return {"signedAt": _format_date(sign.signed_at), "fio": fio}


def _journal_sql(date_start, date_end, filter_by_date, hospital_id, filter_hospital, document_id=None, document_ids=None):
    use_document_ids = document_ids is not None
    return approval_journal_sql(
        date_start,
        date_end,
        filter_by_date,
        hospital_id,
        filter_hospital,
        document_id,
        document_ids or [0],
        use_document_ids,
    )


def _journal_rows(aggregated):
    document_ids = [row["documentId"] for row in aggregated]
    children = {}
    signs = {}
    if document_ids:
        for document in Documents.objects.filter(parent_document_id__in=document_ids).select_related("type_document").order_by("pk"):
            children.setdefault(document.parent_document_id, []).append(_child_payload(document))
        for sign in DocumentApprovalSign.objects.filter(document_id__in=document_ids).select_related("doctor"):
            signs[sign.document_id] = _sign_payload(sign)
    result = []
    for row in aggregated:
        result.append(
            {
                "documentId": row["documentId"],
                "hospital": row["hospital"],
                "confirmDate": _format_date(row["confirmAt"]),
                "approved": row["approved"],
                "linkedDocuments": children.get(row["documentId"], []),
                "sign": signs.get(row["documentId"]),
            }
        )
    return result


def _document_state(document_id):
    raw_rows = _journal_sql(datetime.datetime(1970, 1, 1), datetime.datetime(2100, 1, 1), False, 0, False, document_id=document_id)
    rows = aggregate_approval_rows(raw_rows)
    return rows[0] if rows else None


def _hospital_options():
    return [{"id": row.pk, "label": row.short_title or row.title} for row in Hospitals.objects.filter(hide=False).order_by("short_title", "title", "pk")]


def _copy_curator_indicator_values(source_id, iss, child):
    saved = {}
    records = ParaclinicResultIndicator.objects.filter(issledovaniye__document_id=source_id).select_related("field").order_by("pk")
    for record in records:
        if record.field_id:
            saved[record.field_id] = record
    if not saved:
        return
    body = dict(child.body_values) if isinstance(child.body_values, dict) else {}
    for record in saved.values():
        value = "" if record.value is None else record.value
        ParaclinicResult.objects.update_or_create(
            issledovaniye=iss,
            field=record.field,
            defaults={"value": value, "field_type": record.field.field_type},
        )
        body[str(record.field_id)] = value
    child.body_values = body
    child.save(update_fields=["body_values"])


def _ensure_curator_copy(document_id, doctor):
    if not document_id or not _document_state(document_id):
        return {"ok": False, "message": "Документ не найден"}
    with transaction.atomic():
        source = Documents.objects.select_for_update().filter(pk=document_id).first()
        if not source:
            return {"ok": False, "message": "Документ не найден"}
        existing = Documents.objects.filter(parent_document_id=source.pk).select_related("type_document").order_by("pk").first()
        if existing:
            if not existing.approval_journal_copy:
                Documents.objects.filter(pk=existing.pk).update(approval_journal_copy=True)
            return {"ok": True, "document": _child_payload(existing)}
        if not source.type_document_id:
            return {"ok": False, "message": "У документа нет вида"}
        type_doc = TypeDocuments.objects.select_related("monitoring", "layout_template").filter(pk=source.type_document_id).first()
        research = type_doc.form_research() if type_doc else None
        if not type_doc or not research:
            return {"ok": False, "message": "Нельзя создать документ этого вида"}
        schema = TypeDocumentsSchema.objects.filter(type_document=type_doc).order_by("-created_at", "-pk").first()
        if schema is None:
            schema = TypeDocumentsSchema.get_or_create_for_type(type_doc)
        child = Documents.objects.create(
            type_document=type_doc,
            who_create=doctor,
            body_values={},
            schema=schema,
            parent_document=source,
            approval_journal_copy=True,
        )
        iss = Issledovaniya.objects.create(
            document=child,
            research=research,
            creator=doctor,
            doc_save=doctor,
            time_save=timezone.now(),
        )
        _copy_curator_indicator_values(source.pk, iss, child)
    child = Documents.objects.select_related("type_document").get(pk=child.pk)
    type_title = type_doc.title or "Документ"
    Documents.log_action(
        child.pk,
        Documents.LOG_CREATE,
        doctor,
        {
            "title": f"{type_title} №{child.pk}",
            "typeId": type_doc.pk,
            "typeTitle": type_doc.title or "",
            "parentDocumentId": source.pk,
        },
    )
    return {"ok": True, "document": _child_payload(child)}


def _refresh_curator_copy(source_id, child_id, doctor):
    if not source_id or not _document_state(source_id):
        return {"ok": False, "message": "Документ не найден"}
    try:
        child_id = int(child_id or 0)
    except (TypeError, ValueError):
        child_id = 0
    if not child_id:
        return {"ok": False, "message": "Связный документ не найден"}
    with transaction.atomic():
        child = Documents.objects.select_for_update().filter(pk=child_id, parent_document_id=source_id).first()
        if not child:
            return {"ok": False, "message": "Связный документ не найден"}
        if not child.approval_journal_copy:
            child.approval_journal_copy = True
            child.save(update_fields=["approval_journal_copy"])
        iss = child.get_issledovaniye()
        _copy_curator_indicator_values(source_id, iss, child)
        iss.doc_save = doctor
        iss.time_save = timezone.now()
        iss.save(update_fields=["doc_save", "time_save"])
    child = Documents.objects.select_related("type_document").get(pk=child.pk)
    return {"ok": True, "document": _child_payload(child)}


def _doctor(request):
    return getattr(request.user, "doctorprofile", None)


@login_required
@group_required(APPROVAL_JOURNAL_GROUP)
@require_POST
def approval_journal(request):
    try:
        data = _body(request)
        filter_by_date, datetime_start, datetime_end = _period_bounds(data)
        hospital_id, filter_hospital = _hospital_filter(data)
        matched = _journal_sql(datetime_start, datetime_end, filter_by_date, 0, False)
        document_ids = list({row.document_id for row in matched})
        aggregated = []
        if document_ids:
            full_rows = _journal_sql(datetime.datetime(1970, 1, 1), datetime.datetime(2100, 1, 1), False, 0, False, document_ids=document_ids)
            aggregated = aggregate_approval_rows(full_rows)
            if filter_hospital:
                aggregated = [row for row in aggregated if row["hospitalId"] == hospital_id]
        rows = _journal_rows(aggregated)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "message": "Некорректный период"}, status=400)
    return JsonResponse({"ok": True, "rows": rows, "hospitals": _hospital_options()})


@login_required
@group_required(APPROVAL_JOURNAL_GROUP)
@require_POST
def approval_journal_link(request):
    doctor = _doctor(request)
    if not doctor:
        return JsonResponse({"ok": False, "message": "Профиль врача не найден"})
    data = _body(request)
    try:
        document_id = int(data.get("documentId") or 0)
    except (TypeError, ValueError):
        document_id = 0
    result = _ensure_curator_copy(document_id, doctor)
    if not result.get("ok"):
        return JsonResponse({"ok": False, "message": result.get("message") or "Документ не создан"})
    return JsonResponse({"ok": True, "document": result["document"]})


@login_required
@group_required(APPROVAL_JOURNAL_GROUP)
@require_POST
def approval_journal_link_open(request):
    doctor = _doctor(request)
    if not doctor:
        return JsonResponse({"ok": False, "message": "Профиль врача не найден"})
    data = _body(request)
    try:
        document_id = int(data.get("documentId") or 0)
    except (TypeError, ValueError):
        document_id = 0
    result = _refresh_curator_copy(document_id, data.get("linkedDocumentId"), doctor)
    if not result.get("ok"):
        return JsonResponse({"ok": False, "message": result.get("message") or "Не удалось обновить документ"})
    return JsonResponse({"ok": True, "document": result["document"]})


@login_required
@group_required(APPROVAL_JOURNAL_GROUP)
@require_POST
def approval_journal_sign(request):
    doctor = _doctor(request)
    if not doctor:
        return JsonResponse({"ok": False, "message": "Профиль врача не найден"})
    data = _body(request)
    try:
        document_id = int(data.get("documentId") or 0)
    except (TypeError, ValueError):
        document_id = 0
    state = _document_state(document_id) if document_id else None
    if not state:
        return JsonResponse({"ok": False, "message": "Документ не найден"})
    if not state["approved"]:
        return JsonResponse({"ok": False, "message": "Документ не утвержден"})
    copy = _ensure_curator_copy(document_id, doctor)
    if not copy.get("ok"):
        return JsonResponse({"ok": False, "message": copy.get("message") or "Документ не создан"})
    try:
        sign, _created = DocumentApprovalSign.objects.get_or_create(document_id=document_id, defaults={"doctor": doctor})
    except IntegrityError:
        sign = DocumentApprovalSign.objects.select_related("doctor").get(document_id=document_id)
    else:
        sign = DocumentApprovalSign.objects.select_related("doctor").get(pk=sign.pk)
    return JsonResponse({"ok": True, "sign": _sign_payload(sign), "document": copy["document"]})


@login_required
@group_required(APPROVAL_JOURNAL_GROUP)
@require_POST
def approval_journal_sign_reset(request):
    data = _body(request)
    try:
        document_id = int(data.get("documentId") or 0)
    except (TypeError, ValueError):
        document_id = 0
    state = _document_state(document_id) if document_id else None
    if not state:
        return JsonResponse({"ok": False, "message": "Документ не найден"})
    DocumentApprovalSign.objects.filter(document_id=document_id).delete()
    return JsonResponse({"ok": True})
