import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from document_management.models import DocumentFieldGroups, GroupDocuments, TypeDocuments
from laboratory.decorators import group_required
from utils.response import status_response


def _request_data(request):
    if not request.body:
        return {}
    return json.loads(request.body)


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
    result = TypeDocuments.save_type(data.get("id", -1), data.get("title", ""), data.get("groupId"), data.get("code", ""))
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
