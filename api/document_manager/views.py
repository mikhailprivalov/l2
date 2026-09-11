import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from document_management.models import DocumentFieldGroups, Documents, GroupDocuments, TypeDocuments
from laboratory.decorators import group_required
from utils.response import status_response


def _request_data(request):
    if not request.body:
        return {}
    return json.loads(request.body)


def _load_save_request(request):
    content_type = (request.content_type or "").lower()
    if content_type.startswith("multipart/form-data"):
        form_raw = request.POST.get("form")
        if form_raw is None:
            form_file = request.FILES.get("form")
            if form_file is not None:
                form_raw = form_file.read().decode("utf-8")
        if not form_raw:
            form_raw = "{}"
        files = {key: value for key, value in request.FILES.items() if key != "form"}
        return json.loads(form_raw), files
    if not request.body:
        return {}, {}
    return json.loads(request.body), {}


def _save_from_request(request, with_confirm=None):
    rb, request_files = _load_save_request(request)
    request_data = rb.get("data") or {}
    confirm = rb.get("with_confirm", False) if with_confirm is None else with_confirm
    return Documents.save_paraclinic_result(
        request_data.get("pk"),
        request_data.get("research"),
        confirm,
        rb.get("visibility_state") or {},
        request.user.doctorprofile,
        request_files,
    )


@login_required
@group_required("Конструктор: ДОУ", "ДОУ: просмотр документов")
def groups_list(request):
    return JsonResponse({"result": GroupDocuments.get_list()})


@login_required
@group_required("Конструктор: ДОУ")
def groups_update(request):
    data = _request_data(request)
    result = GroupDocuments.save_group(data.get("id", -1), data.get("title", ""))
    if result.get("ok"):
        return status_response(True, data=result)
    return status_response(False, result.get("message"))


@login_required
@group_required("Конструктор: ДОУ", "ДОУ: просмотр документов")
def types_list(request):
    data = _request_data(request)
    return JsonResponse({"result": TypeDocuments.get_list(data.get("groupId"))})


@login_required
@group_required("Конструктор: ДОУ")
def types_update(request):
    data = _request_data(request)
    result = TypeDocuments.save_type(
        data.get("id", -1),
        data.get("title", ""),
        data.get("groupId"),
        data.get("code", ""),
        data.get("layoutTemplateId"),
    )
    if result.get("ok"):
        return status_response(True, data=result)
    return status_response(False, result.get("message"))


@login_required
@group_required("Конструктор: ДОУ")
def structure_details(request):
    data = _request_data(request)
    result = DocumentFieldGroups.get_structure(data.get("id"))
    if result.get("ok"):
        return JsonResponse(result)
    return status_response(False, result.get("message"))


@login_required
@group_required("Конструктор: ДОУ")
def structure_update(request):
    data = _request_data(request)
    result = DocumentFieldGroups.save_structure(data.get("id"), data.get("groups"))
    if result.get("ok"):
        return status_response(True, data=result)
    return status_response(False, result.get("message"))


@login_required
@group_required("ДОУ: просмотр документов")
def documents_list(request):
    data = _request_data(request)
    return JsonResponse(
        {"result": Documents.get_list(data.get("typeId"), data.get("groupId"), data.get("filter"), request.user.doctorprofile)}
    )


@login_required
@group_required("ДОУ: просмотр документов")
def documents_create(request):
    data = _request_data(request)
    result = Documents.create_document(data.get("typeId"), request.user.doctorprofile)
    if result.get("ok"):
        return status_response(True, data=result)
    return status_response(False, result.get("message"))


@login_required
@group_required("ДОУ: просмотр документов")
def documents_details(request):
    data = _request_data(request)
    result = Documents.get_details(data.get("id"))
    if result.get("ok"):
        return JsonResponse(result)
    return status_response(False, result.get("message"))


@login_required
@group_required("ДОУ: просмотр документов")
def documents_save(request):
    result = _save_from_request(request)
    if result.get("ok"):
        return status_response(True, data=result)
    return status_response(False, result.get("message"))


@login_required
@group_required("ДОУ: просмотр документов")
def documents_confirm(request):
    result = _save_from_request(request, with_confirm=True)
    if result.get("ok"):
        return status_response(True, data=result)
    return status_response(False, result.get("message"))


@login_required
@group_required("ДОУ: просмотр документов")
def documents_confirm_reset(request):
    data = _request_data(request)
    result = Documents.confirm_reset(data.get("id"))
    if result.get("ok"):
        return status_response(True, data=result)
    return status_response(False, result.get("message"))
