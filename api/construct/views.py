from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import simplejson as json
from directory.models import Researches, Fractions, Unit, LaboratoryMaterial, SubGroup, ResultVariants
from laboratory.decorators import group_required
from podrazdeleniya.models import Podrazdeleniya
from utils.response import status_response


@login_required
@group_required("Конструктор: Лабораторные исследования")
def get_lab_departments(request):
    result = Podrazdeleniya.get_podrazdeleniya(Podrazdeleniya.LABORATORY)
    return JsonResponse({"result": result})


@login_required
@group_required("Конструктор: Лабораторные исследования")
def get_tubes(request):
    request_data = json.loads(request.body)
    result = Researches.get_tubes(request_data["department_id"])
    return JsonResponse({"result": result})


@login_required
@group_required("Конструктор: Лабораторные исследования")
def update_order_research(request):
    request_data = json.loads(request.body)
    result = Researches.update_order(request_data["researchPk"], request_data["researchNearbyPk"], request_data["action"])
    return status_response(result)


@login_required
@group_required("Конструктор: Лабораторные исследования")
def update_order_fraction(request):
    request_data = json.loads(request.body)
    result = Fractions.update_order(request_data["fractionPk"], request_data["fractionNearbyPk"], request_data["action"])
    return status_response(result)


@login_required
@group_required("Конструктор: Лабораторные исследования")
def change_visibility_research(request):
    request_data = json.loads(request.body)
    result = Researches.change_visibility(request_data["researchPk"])
    return status_response(result)


@login_required
@group_required("Конструктор: Лабораторные исследования")
def get_lab_research(request):
    request_data = json.loads(request.body)
    result = Researches.get_research(request_data["researchPk"])
    return JsonResponse({"result": result})


@login_required
@group_required("Конструктор: Лабораторные исследования")
def update_lab_research(request):
    request_data = json.loads(request.body)
    result = Researches.update_lab_research(request_data["research"])
    return status_response(result)


@login_required
@group_required("Конструктор: Лабораторные исследования")
def get_lab_ref_books(request):
    units = Unit.get_units()
    materials = LaboratoryMaterial.get_materials()
    subgroups = SubGroup.get_groups()
    variants = ResultVariants.get_all()
    print(variants)
    result = {"units": units, "materials": materials, "subGroups": subgroups, "variants": variants}
    print(result)
    return JsonResponse({"result": result})


@login_required
@group_required("Конструктор: Лабораторные исследования")
def get_fraction(request):
    request_data = json.loads(request.body)
    result = Fractions.get_fraction(request_data["fractionPk"])
    return JsonResponse({"result": result})
