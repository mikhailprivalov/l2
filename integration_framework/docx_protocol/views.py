import json

from django.http import HttpResponse, JsonResponse
from directions.models import Napravleniya
from rest_framework.decorators import api_view

from users.models import DoctorProfile

from .utils import build_paraclinic_protocol_html, fetch_paraclinic_form_data


def _get_paraclinic_form_user(user_n3_id_for_html):
    doctor = DoctorProfile.objects.filter(n3_id=user_n3_id_for_html).first()
    return doctor.user if doctor else None


def _resolve_direction_pk(pk, year=None):
    try:
        pk_value = int(pk)
    except (TypeError, ValueError):
        return None

    if Napravleniya.objects.filter(pk=pk_value).exists():
        return pk_value

    queryset = Napravleniya.objects.filter(register_number=pk_value)
    if year is not None:
        queryset = queryset.filter(register_number_year=year)
    direction = queryset.order_by("-register_number_year", "-pk").first()
    return direction.pk if direction else None


def _prepare_paraclinic_form_params(request_data):
    form_params = {
        key: value
        for key, value in request_data.items()
        if key not in ("iss_pk", "user_n3_id_for_html")
    }
    resolved_pk = _resolve_direction_pk(form_params.get("pk"), form_params.get("year"))
    if resolved_pk:
        form_params["pk"] = resolved_pk
    if "force" not in form_params:
        form_params["force"] = True
    if "searchMode" not in form_params:
        form_params["searchMode"] = "direction"
    return form_params, resolved_pk


@api_view(["POST"])
def paraclinic_protocol_html(request):
    request_data = json.loads(request.body)
    pk = request_data.get("pk")
    if not pk:
        return JsonResponse({"ok": False, "message": "Не указан pk направления"}, status=400)

    form_params, resolved_pk = _prepare_paraclinic_form_params(request_data)
    if not resolved_pk:
        return JsonResponse({"ok": False, "message": "Направление не найдено"}, status=400)

    user_n3_id_for_html = request_data.get("user_n3_id_for_html")
    if not user_n3_id_for_html:
        return JsonResponse({"ok": False, "message": "Не указан user_n3_id_for_html"}, status=400)

    user = _get_paraclinic_form_user(user_n3_id_for_html)
    if not user:
        return JsonResponse({"ok": False, "message": "Служебный пользователь для параклиники не найден"}, status=500)

    form_data, error = fetch_paraclinic_form_data(user, form_params)
    if error == "Направление не найдено" and not form_params.get("force"):
        form_params["force"] = True
        form_data, error = fetch_paraclinic_form_data(user, form_params)
    if error:
        return JsonResponse({"ok": False, "message": error}, status=400)

    html_content, error = build_paraclinic_protocol_html(form_data)
    if error:
        return JsonResponse({"ok": False, "message": error}, status=400)

    return HttpResponse(html_content, content_type="text/html; charset=utf-8")
