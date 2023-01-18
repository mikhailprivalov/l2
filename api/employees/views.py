import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from laboratory.decorators import group_required
from employees.models import Department, Position, Employee, EmployeePosition
from utils.response import status_response

@login_required
def departments_list(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()

    only_active = request_data.get('onlyActive', True)
    return_total_rows = request_data.get('returnTotalRows', False)
    page = request_data.get('page', 1)
    per_page = request_data.get('perPage', 30)
    sort_column = request_data.get('sortColumn')
    sort_direction = request_data.get('sortDirection')
    q_filter = request_data.get('filter')

    import time
    time.sleep(5)

    rows, pages = Department.get_json_list(hospital_id, only_active, page, per_page, sort_column, sort_direction, q_filter, return_total_rows=return_total_rows)
    return JsonResponse({
        "rows": rows,
        "pages": pages,
    })


@login_required
@group_required("Конструктор: Настройка организации")
def departments_add(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    name = request_data.get('name')

    try:
        department = Department.add(hospital_id, name, request.user.doctorprofile)
    except ValueError as e:
        return status_response(False, message=str(e))
    else:
        return status_response(True, data={"value": department})


@login_required
@group_required("Конструктор: Настройка организации")
def departments_edit(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    department_id = request_data.get('id')
    name = request_data.get('name')
    is_active = request_data.get('isActive')

    try:
        department = Department.edit(hospital_id, department_id, name, is_active, request.user.doctorprofile)
    except ValueError as e:
        return status_response(False, message=str(e))
    else:
        return status_response(True, data={"value": department})


@login_required
def departments_treeselect(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    count = request_data.get('count', 10)
    filter = request_data.get('filter')

    rows = Department.get_json_list(hospital_id, per_page=count, filter=filter)
    return JsonResponse([{"id": x["id"], "label": x["name"]} for x in rows], safe=False)


@login_required
def departments_get(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    department_id = request_data.get('id')

    department = Department.get_json_by_id(hospital_id, department_id)
    return JsonResponse(department)


@login_required
def positions_list(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()

    only_active = request_data.get('onlyActive', True)
    page = request_data.get('page', 1)
    per_page = request_data.get('perPage', 30)
    sort_column = request_data.get('sortColumn')
    sort_direction = request_data.get('sortDirection')
    q_filter = request_data.get('filter')

    rows = Position.get_json_list(hospital_id, only_active, page, per_page, sort_column, sort_direction, q_filter)
    return JsonResponse(rows, safe=False)


@login_required
@group_required("Конструктор: Настройка организации")
def positions_add(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    name = request_data.get('name')

    try:
        position = Position.add(hospital_id, name, request.user.doctorprofile)
    except ValueError as e:
        return status_response(False, message=str(e))
    else:
        return status_response(True, data={"value": position})


@login_required
@group_required("Конструктор: Настройка организации")
def positions_edit(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    position_id = request_data.get('id')
    name = request_data.get('name')
    is_active = request_data.get('isActive')

    try:
        position = Position.edit(hospital_id, position_id, name, is_active, request.user.doctorprofile)
    except ValueError as e:
        return status_response(False, message=str(e))
    else:
        return status_response(True, data={"value": position})


@login_required
def positions_treeselect(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    count = request_data.get('count', 10)
    filter = request_data.get('filter')

    rows = Position.get_json_list(hospital_id, per_page=count, filter=filter)
    return JsonResponse([{"id": x["id"], "label": x["name"]} for x in rows], safe=False)


@login_required
def positions_get(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    position_id = request_data.get('id')

    position = Position.get_json_by_id(hospital_id, position_id)
    return JsonResponse(position)


@login_required
def employees_list(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()

    only_active = request_data.get('onlyActive', True)
    page = request_data.get('page', 1)
    per_page = request_data.get('perPage', 30)
    sort_column = request_data.get('sortColumn')
    sort_direction = request_data.get('sortDirection')
    q_filter = request_data.get('filter')

    rows = Employee.get_json_list(hospital_id, only_active, page, per_page, sort_column, sort_direction, q_filter)
    return JsonResponse(rows, safe=False)


@login_required
@group_required("Конструктор: Настройка организации")
def employees_add(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    family = request_data.get('family')
    name = request_data.get('name')
    patronymic = request_data.get('patronymic')

    try:
        employee = Employee.add(hospital_id, family, name, patronymic, request.user.doctorprofile)
    except ValueError as e:
        return status_response(False, message=str(e))
    else:
        return status_response(True, data={"value": employee})


@login_required
@group_required("Конструктор: Настройка организации")
def employees_edit(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    employee_id = request_data.get('id')
    family = request_data.get('family')
    name = request_data.get('name')
    patronymic = request_data.get('patronymic')
    is_active = request_data.get('isActive')

    try:
        employee = Employee.edit(hospital_id, employee_id, family, name, patronymic, is_active, request.user.doctorprofile)
    except ValueError as e:
        return status_response(False, message=str(e))
    else:
        return status_response(True, data={"value": employee})


@login_required
def employees_treeselect(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    count = request_data.get('count', 10)
    filter = request_data.get('filter')

    rows = Employee.get_json_list(hospital_id, per_page=count, filter=filter)
    return JsonResponse([{"id": x["id"], "label": x["name"]} for x in rows], safe=False)


@login_required
def employees_get(request):
    request_data = json.loads(request.body)
    hospital_id = request.user.doctorprofile.get_hospital_id()
    employee_id = request_data.get('id')

    employee = Employee.get_json_by_id(hospital_id, employee_id)
    return JsonResponse(employee)
