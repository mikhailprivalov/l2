from laboratory.decorators import group_required
import simplejson as json
from django.http import JsonResponse
import time_cards.models as staff_models

@group_required("Штатное расписание")
def staf_load_department(request):
    staff_departments = staff_models.Departments.get_all_departments()
    return JsonResponse({"staffDepartments": staff_departments})


@group_required("Штатное расписание")
def staff_update_department(request):
    data = json.loads(request.body)
    staff_models.Departments.update_departmnet(data)
    staff_departments = staff_models.Departments.get_all_departments()
    return JsonResponse({"staffDepartments": staff_departments})


@group_required("Штатное расписание")
def staff_load_department_employees(request):
    data = json.loads(request.body)
    department_pk = int(data.get("pk", -1))
    result = []
    if department_pk > -1:
        result = staff_models.Employees.get_all_employees_by_department(department_pk)
    return JsonResponse({"departmentEmployees": result})


@group_required("Штатное расписание")
def staff_load_employee(request):
    data = json.loads(request.body)
    employee_pk = int(data.get("employeePk", -1))
    employee = {}
    if employee_pk > -1:
        employee = staff_models.Employees.get_employee(employee_pk)
    return JsonResponse({"employee": employee})


@group_required("Штатное расписание")
def staff_update_employee(request):
    data = json.loads(request.body)
    employee_pk = int(data.get("employeePk", -1))
    if employee_pk > -1:
        staff_models.Employees.update_employee(data)
    employee = staff_models.Employees.get_employee(employee_pk)
    return JsonResponse({"employee": employee})


@group_required("Штатное расписание")
def staff_load_posts(request):
    posts = staff_models.Posts.get_posts()
    return JsonResponse({"posts": posts})


@group_required("Штатное расписание")
def staff_update_post(request):
    data = json.loads(request.body)
    post_pk = int(data.get("postPk", -1))
    post = {}
    if post_pk > -1:
        post = staff_models.Posts.update_post(data)
    return JsonResponse({"post": post})


@group_required("Штатное расписание")
def staff_load_post(request):
    data = json.loads(request.body)
    post_pk = int(data.get("postPk", -1))
    post = {}
    if post_pk > -1:
        post = staff_models.Posts.get_post(post_pk)
    return JsonResponse({"post": post})


@group_required("Табель подразделение")
def staff_result_tabel(request):
    data = json.loads(request.body)
    doc = request.user.doctorprofile
    staff_models.TabelDocuments.create_tabel_document()


@group_required("Табель проверка")
def staff_change_status_tabel():
    pass
