from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import simplejson as json
from directory.models import Researches, Unit, LaboratoryMaterial, ResultVariants, MaterialVariants, SubGroupPadrazdeleniye, SubGroupDirectory, ComplexService
from laboratory.decorators import group_required
from podrazdeleniya.models import Podrazdeleniya
from researches.models import Tubes
from slog.models import Log
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
    Log.log(
        request_data["researchPk"],
        220000,
        request.user.doctorprofile,
        {"research_pk": request_data["researchPk"], "action": request_data["action"]},
    )
    return status_response(result)


@login_required
@group_required("Конструктор: Лабораторные исследования")
def change_visibility_research(request):
    request_data = json.loads(request.body)
    result = Researches.change_visibility(request_data["researchPk"], True)
    Log.log(
        request_data["researchPk"],
        220001,
        request.user.doctorprofile,
        {"research_pk": request_data["researchPk"], "hide": result["hide"]},
    )
    return status_response(result["ok"])


@login_required
@group_required("Конструктор: Лабораторные исследования")
def get_lab_research(request):
    request_data = json.loads(request.body)
    result = Researches.get_lab_research(request_data["researchPk"])
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


@login_required
@group_required("Конструктор: Комплексные услуги")
def get_complexes(request):
    services = Researches.get_complex_services()
    return JsonResponse({"result": services})


@login_required
@group_required("Конструктор: Комплексные услуги")
def check_complex_hidden(request):
    request_data = json.loads(request.body)
    complex_id = request_data.get("complexId")
    service = Researches.objects.get(pk=complex_id)
    return JsonResponse({"result": service.hide})


@login_required
@group_required("Конструктор: Комплексные услуги")
def get_services_in_complex(request):
    request_data = json.loads(request.body)
    complex_id = request_data.get("complexId")
    services = ComplexService.get_services_in_complex(complex_id)
    return JsonResponse({"result": services})


@login_required
@group_required("Конструктор: Комплексные услуги")
def add_service_in_complex(request):
    request_data = json.loads(request.body)
    complex_id = request_data.get("complexId")
    service_id = request_data.get("serviceId")
    result = ComplexService.add_service(complex_id, service_id)
    Log.log(result["result"], 210003, request.user.doctorprofile, {"complex_id": complex_id, "service_id": service_id})
    return status_response(result["ok"])


@login_required
@group_required("Конструктор: Комплексные услуги")
def change_complex_hidden(request):
    request_data = json.loads(request.body)
    complex_id = request_data.get("complexId")
    result = ComplexService.change_hidden_complex(complex_id)
    Log.log(complex_id, 210002, request.user.doctorprofile, {"complex_pk": complex_id, "hide": result["hide"]})
    return status_response(result["ok"])


@login_required
@group_required("Конструктор: Комплексные услуги")
def update_complex(request):
    request_data = json.loads(request.body)
    complex_id = request_data.get("complexId")
    complex_title = request_data.get("complexTitle")
    result = ComplexService.update_complex(complex_id, complex_title)
    if complex_id:
        Log.log(complex_id, 210001, request.user.doctorprofile, {"complex_pk": complex_id, "old_title": result["old_title"], "new_title": complex_title})
    else:
        Log.log(result["id"], 210000, request.user.doctorprofile, {"complex_pk": result["id"], "new_title": complex_title})
    return JsonResponse({"ok": result["ok"], "id": result["id"]})


@login_required
@group_required("Конструктор: Комплексные услуги")
def change_service_hidden(request):
    request_data = json.loads(request.body)
    complex_id = request_data.get("complexId")
    service_id = request_data.get("serviceId")
    result = ComplexService.change_service_hidden(complex_id, service_id)
    Log.log(service_id, 210004, request.user.doctorprofile, {"complex_id": complex_id, "service_id": service_id, "hide": result["hide"]})
    return status_response(result["ok"])
