from laboratory.decorators import group_required
import simplejson as json
from django.http import JsonResponse

from time_cards.models import Departments


@group_required("Штатное расписание - подразделения")
def load_department(request):
    staff_departments = Departments.get_all_departments()
    return JsonResponse({"staffDepartments": staff_departments})


@group_required("Штатное расписание - подразделения")
def update_department(request):
    data = json.loads(request.body)
    Departments.update_departmnet(data)
    staff_departments = Departments.get_all_departments()
    return JsonResponse({"staffDepartments": staff_departments})


@group_required("Штатное расписание - сотрудники")
def load_person(request):
    data = json.loads(request.body)
    pass


@group_required("Штатное расписание - сотрудники")
def load_department_persons(request):
    data = json.loads(request.body)
    pass


@group_required("Штатное расписание - сотрудники")
def update_perosn(request):
    data = json.loads(request.body)
    pass
