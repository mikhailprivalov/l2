from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required
import simplejson as json
from hospitals.models import Hospitals


@login_required
@group_required("Лечащий врач", "Врач-лаборант", "Оператор лечащего врача", "Заполнение мониторингов")
def hospital_fields(request):
    hospital_id = request.user.doctorprofile.hospital_id
    hosp_obj = Hospitals.objects.get(pk=hospital_id)

    return {
        "hosp_id": hospital_id,
        "title": hosp_obj.title,
        "short_title": hosp_obj.short_title,
        "code_tfoms": hosp_obj.code_tfoms,
        "oid": hosp_obj.oid,
        "address": hosp_obj.address,
        "phones": hosp_obj.phones,
        "ogrn": hosp_obj.ogrn,
        "www": hosp_obj.www,
        "license_data": hosp_obj.license_data,
        "current_manager": hosp_obj.current_manager,
    }
