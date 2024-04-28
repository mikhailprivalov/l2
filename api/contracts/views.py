from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import simplejson as json
from directory.models import Researches, Unit, LaboratoryMaterial, ResultVariants, MaterialVariants, SubGroupPadrazdeleniye, SubGroupDirectory
from laboratory.decorators import group_required
from podrazdeleniya.models import Podrazdeleniya
from researches.models import Tubes
from utils.response import status_response


@login_required
@group_required("Конструктор: Лабораторные исследования")
def update_order_research(request):
    request_data = json.loads(request.body)
    result = Researches.update_order(request_data["researchPk"], request_data["researchNearbyPk"], request_data["action"])
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
    return JsonResponse(result)


@login_required
@group_required("Конструктор: Лабораторные исследования")
def get_lab_ref_books(request):
    request_data = json.loads(request.body)
    units = Unit.get_units()
    materials = LaboratoryMaterial.get_materials()
    subgroups = SubGroupPadrazdeleniye.get_subgroup_podrazdeleniye(request_data["departmentId"])
    variants = ResultVariants.get_all()
    tubes = Tubes.get_all()
    result = {"units": units, "materials": materials, "subGroups": subgroups, "variants": variants, "tubes": tubes}
    return JsonResponse({"result": result})


@login_required
@group_required("Конструктор: Лабораторные исследования")
def get_comments_variants(request):
    result = MaterialVariants.get_all()
    return JsonResponse({"result": result})


@login_required
@group_required("Конструктор: Лабораторные исследования")
def get_lab_research_additional_data(request):
    request_data = json.loads(request.body)
    result = Researches.get_lab_additional_data(request_data["researchPk"])
    return JsonResponse({"result": result})


@login_required
def get_subgroups_department(request):
    request_data = json.loads(request.body)
    pk = request_data['department_pk']
    podrazdeleniye = Podrazdeleniya.objects.get(pk=pk)
    rows = SubGroupPadrazdeleniye.get_subgroup_podrazdeleniye(podrazdeleniye)
    return JsonResponse(rows, safe=False)


@login_required
def save_subgroups_department(request):
    request_data = json.loads(request.body)
    tb_data = request_data.get('tb_data', '')
    department_pk = int(request_data.get('department_pk', -1))
    if len(tb_data) < 1:
        return JsonResponse({'message': 'Ошибка в количестве'})
    result = SubGroupPadrazdeleniye.save_subgroups_department(department_pk, tb_data)
    if result:
        return JsonResponse({'ok': True, 'message': 'Сохранено'})
    return JsonResponse({'ok': False, 'message': 'ошибка'})


@login_required
def get_subgroups_all(request):
    rows = [
        {
            "id": subgroup.pk,
            "label": f"{subgroup.title}",
        }
        for subgroup in SubGroupDirectory.objects.all().order_by("title")
    ]
    return JsonResponse(rows, safe=False)
