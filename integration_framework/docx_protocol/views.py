import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse

from directions.models import Issledovaniya, Napravleniya

from .utils import get_docx_protocol_bytes, get_docx_protocol_xml_from_form


def _get_direction_and_iss(request_data):
    pk = request_data.get("pk")
    iss_pk = request_data.get("iss_pk")

    if not pk:
        return None, None, JsonResponse({"ok": False, "message": "Не указан pk направления"}, status=400)

    direction = Napravleniya.objects.filter(pk=pk).first()
    if not direction:
        return None, None, JsonResponse({"ok": False, "message": "Направление не найдено"}, status=404)

    iss_qs = Issledovaniya.objects.filter(napravleniye=direction)
    if iss_pk:
        iss_qs = iss_qs.filter(pk=iss_pk)
    iss = iss_qs.first()
    if not iss:
        return None, None, JsonResponse({"ok": False, "message": "Исследование не найдено"}, status=404)

    return direction, iss, None


@login_required
def protocol_docx(request):
    request_data = json.loads(request.body)
    direction, iss, error_response = _get_direction_and_iss(request_data)
    if error_response:
        return error_response

    docx_bytes, error = get_docx_protocol_bytes(direction, iss)
    if error:
        return JsonResponse({"ok": False, "message": error}, status=400)

    response = HttpResponse(
        docx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="protocol-{direction.pk}.docx"'
    return response


@login_required
def protocol_docx_xml(request):
    request_data = json.loads(request.body)
    pk = request_data.get("pk") or request_data.get("direction")
    form_type = request_data.get("type", "113.01")

    if not pk:
        return JsonResponse({"ok": False, "message": "Не указан pk направления"}, status=400)

    form_params = {key: value for key, value in request_data.items() if key not in ("pk", "type", "iss_pk")}
    form_params["direction"] = pk

    xml_content, error = get_docx_protocol_xml_from_form(form_type, form_params, request.user)
    if error:
        return JsonResponse({"ok": False, "message": error}, status=400)

    response = HttpResponse(xml_content, content_type="application/xml; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="protocol-{pk}.xml"'
    return response
