import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models.functions import Coalesce
from django.db.models import Value, Q

from api.models import Application
from hospitals.models import Hospitals
from laboratory.decorators import group_required
from laboratory.utils import strdatetime
from slog.models import Log
from users.models import DoctorProfile


@login_required
@group_required("Просмотр журнала")
def get_types(request):
    result = [{"id": -1, "label": "Все виды действий"}]

    categories = {}

    for type_id, label in Log.TYPES:
        if ":" not in label:
            result.append({"id": type_id, "label": label})
            continue

        parts = label.split(":", 1)
        category = parts[0].strip()
        item_name = parts[1].strip()

        if " в " in category:
            main_parts = category.split(" в ", 1)
            main_category = main_parts[0].strip()
            sub_category = "в " + main_parts[1].strip()

            if main_category not in categories:
                categories[main_category] = {"_direct": []}

            if sub_category not in categories[main_category]:
                categories[main_category][sub_category] = []

            categories[main_category][sub_category].append({"id": type_id, "label": item_name})
        else:
            if category not in categories:
                categories[category] = {"_direct": []}

            categories[category]["_direct"].append({"id": type_id, "label": item_name, "full_label": label})

    category_id = -2

    for category, content in sorted(categories.items()):
        direct_items = content["_direct"]
        subcategories = {k: v for k, v in content.items() if k != "_direct"}

        if not subcategories and len(direct_items) == 1:
            result.append({"id": direct_items[0]["id"], "label": direct_items[0]["full_label"]})
            continue

        category_item = {"id": category_id, "label": category, "children": []}
        category_id -= 1

        for item in direct_items:
            category_item["children"].append({"id": item["id"], "label": item["label"]})

        for subcat_name, items in sorted(subcategories.items()):
            if len(items) == 1 and not direct_items and len(subcategories) == 1:
                category_item["children"].append({"id": items[0]["id"], "label": f"{subcat_name}: {items[0]['label']}"})
            else:
                subcat_item = {"id": category_id, "label": subcat_name, "children": items}
                category_id -= 1
                category_item["children"].append(subcat_item)

        result.append(category_item)

    return JsonResponse({"types": result})


@login_required
@group_required("Просмотр журнала")
def get_orgs(request):
    rows = Hospitals.objects.all()

    if not request.user.is_superuser and not request.user.is_staff:
        rows = rows.filter(id=request.user.doctorprofile.get_hospital_id())

    rows = rows.annotate(sort_field=Coalesce("short_title", "title", default=Value(""))).order_by("sort_field")

    result = [{"id": o.id, "label": o.safe_short_title} for o in rows]

    return JsonResponse(
        {
            "orgs": [
                *([{"id": -1, "label": "Все организации"}] if len(result) > 1 else []),
                *result,
            ],
        }
    )


def get_user_label(user: DoctorProfile, has_many_orgs: bool):
    if not user.user.is_active:
        parts = ["(неактивен)"]
    else:
        parts = []

    if has_many_orgs or not user.hospital:
        parts.append(user.get_fio(dots=False, with_space=False))
        hospital_title = user.hospital.safe_short_title if user.hospital else "без организации"
        parts.append(f"({hospital_title})")
    else:
        parts.append(user.get_full_fio())

    return " ".join(parts)


@login_required
@group_required("Просмотр журнала")
def get_users(request):
    user_org_id = request.user.doctorprofile.get_hospital_id()
    has_access_to_all_orgs = request.user.is_superuser or request.user.is_staff

    data = json.loads(request.body)
    request_org_id = data.get("orgId")
    if request_org_id:
        request_org_id = int(request_org_id)

    is_default_org = has_access_to_all_orgs and Hospitals.get_default_hospital().pk == user_org_id

    if not has_access_to_all_orgs:
        request_org_id = user_org_id

    for_all_orgs = request_org_id and request_org_id == -1

    if for_all_orgs or has_access_to_all_orgs:
        if for_all_orgs:
            rows = DoctorProfile.objects.all()
        else:
            if is_default_org:
                rows = DoctorProfile.objects.filter(Q(hospital_id=request_org_id) | Q(hospital_id=None))
            else:
                rows = DoctorProfile.objects.filter(hospital_id=request_org_id)
    else:
        rows = DoctorProfile.objects.filter(hospital_id=user_org_id)

    has_many_orgs = rows.order_by("hospital_id").distinct("hospital_id").filter(hospital_id__isnull=False).count() > 1
    rows = rows.order_by("fio")

    result = [{"id": o.user.id, "label": get_user_label(o, has_many_orgs)} for o in rows]

    return JsonResponse(
        {
            "users": [
                *([{"id": -1, "label": "Все пользователи"}] if len(result) > 1 or has_access_to_all_orgs else []),
                *([{"id": -2, "label": "Система"}] if has_access_to_all_orgs else []),
                *result,
            ],
        }
    )


@login_required
@group_required("Просмотр журнала")
def get_logs(request):
    user_org_id = request.user.doctorprofile.get_hospital_id()
    has_access_to_all_orgs = request.user.is_superuser or request.user.is_staff

    data = json.loads(request.body)
    request_org_id = data.get("orgId")
    if request_org_id is not None:
        request_org_id = int(request_org_id)

    user_id = data.get("userId")
    if user_id is not None:
        user_id = int(user_id)

    type_id = data.get("typeId")
    if type_id is not None:
        type_id = int(type_id)

    after_id = data.get("afterId")
    if after_id is not None:
        after_id = int(after_id)

    last_id = data.get("lastId")
    if last_id is not None:
        last_id = int(last_id)

    application_id = data.get("applicationId")
    if application_id is not None:
        application_id = int(application_id)

    size = 40

    key = data.get("key")

    is_default_org = has_access_to_all_orgs and Hospitals.get_default_hospital().pk == user_org_id

    if not has_access_to_all_orgs:
        request_org_id = user_org_id

    for_all_orgs = request_org_id is not None and request_org_id == -1
    more_than_one_hospital = list(Hospitals.objects.filter(hide=False).values_list("pk", flat=True)[:2])
    show_org_title = for_all_orgs or (has_access_to_all_orgs and len(more_than_one_hospital) > 1)

    base_query = Log.objects.select_related("user__user", "user__hospital", "application")

    if for_all_orgs or has_access_to_all_orgs:
        if for_all_orgs:
            rows = base_query
        else:
            if is_default_org:
                rows = base_query.filter(Q(user__hospital_id=request_org_id) | Q(user__hospital_id=None))
            else:
                rows = base_query.filter(user__hospital_id=request_org_id)
    else:
        rows = base_query.filter(user__hospital_id=user_org_id)

    if not has_access_to_all_orgs:
        rows = rows.filter(Q(application__isnull=True) | Q(application__hospitals__id=user_org_id))

    if user_id is not None:
        if user_id >= 0:
            rows = rows.filter(user_id=user_id)
        elif user_id == -2:
            rows = rows.filter(user_id=None)

    if type_id is not None and type_id >= 0:
        rows = rows.filter(type=type_id)

    if key:
        rows = rows.filter(key__contains=key)

    if application_id is not None and application_id >= 0:
        rows = rows.filter(application_id=application_id)

    if after_id is not None:
        rows = rows.filter(pk__gt=after_id)

    if last_id is not None:
        rows = rows.filter(pk__lt=last_id)

    rows = rows.order_by("-pk")[:size]

    result = []
    for row in rows:
        tmp_object = {
            "id": row.pk,
            "user": {
                "id": row.user_id,
                "fio": row.user.get_fio() if row.user else "Система",
                "username": row.user.user.username if row.user and row.user.user else None,
            },
            "org": {
                "id": row.user.hospital_id if row.user and row.user.hospital else None,
                "title": (row.user.hospital.safe_short_title if row.user and row.user.hospital else "Система") if show_org_title else None,
            },
            "application": (
                {
                    "id": row.application_id,
                    "label": row.application.name if row.application else None,
                }
                if row.application
                else None
            ),
            "key": row.key,
            "body": row.body,
            "type": row.get_type_display(),
            "time": strdatetime(row.time),
        }
        result.append(tmp_object)

    return JsonResponse({"logs": result})


@login_required
@group_required("Просмотр журнала")
def get_applications(request):
    has_access_to_all_orgs = request.user.is_superuser or request.user.is_staff
    rows = Application.objects.filter(active=True)

    if not has_access_to_all_orgs:
        rows = rows.filter(hospitals__id=request.user.doctorprofile.get_hospital_id())

    rows = rows.order_by("name")

    return JsonResponse(
        {
            "applications": [
                {"id": -1, "label": "Все приложения"},
                *[{"id": a.id, "label": a.name} for a in rows],
            ],
        }
    )
