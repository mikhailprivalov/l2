import datetime
import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

from api.extra_notification.sql_func import extra_notification_sql
from directions.models import Napravleniya, Issledovaniya, ParaclinicResult
from directory.models import ParaclinicInputGroups, ParaclinicInputField
from laboratory.decorators import group_required
from laboratory.settings import EXTRA_MASTER_RESEARCH_PK, EXTRA_SLAVE_RESEARCH_PK
from laboratory.utils import strdate


@login_required
def search(request):
    request_data = json.loads(request.body)
    # status - 0 новые, 1-присвоенные номера от ЭпидЦентра, 2 - все
    status = int(request_data.get("status", 2))
    hospital = int(request_data.get("hospital", -1))
    date = request_data["date"]
    time_start = f'{date} {request_data.get("time_start", "00:00")}:00'
    time_end = f'{date} {request_data.get("time_end", "23:59")}:59:999999'
    datetime_start = datetime.datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
    datetime_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S:%f')

    user_hospital = request.user.doctorprofile.get_hospital_id() or -1

    if user_hospital != hospital and "Заполнение экстренных извещений" not in [str(x) for x in request.user.groups.all()]:
        hospital = -1

    if hospital == -1:
        return JsonResponse(
            {
                'result': [],
            }
        )

    result_extra = extra_notification_sql(EXTRA_MASTER_RESEARCH_PK, EXTRA_SLAVE_RESEARCH_PK, datetime_start, datetime_end, hospital, status)
    result = []
    for i in result_extra:
        title = i.title
        if i.short_title:
            title = i.short_title
        patient = f'{i.pfam} {i.pname} {i.twoname}'
        result.append(
            {
                'hospital': title,
                'mainDirection': i.dir_id,
                'mainConfirm': i.d_confirm,
                'slaveDir': i.r_dir_id,
                'slaveConfirm': i.rd_confirm,
                'patient': patient,
                'born': i.birthday,
                'value': i.num_value,
                'issPk': i.r_iss_id,
            }
        )

    return JsonResponse({'rows': result})


@login_required
@group_required('Заполнение экстренных извещений')
def save(request):
    request_data = json.loads(request.body)
    pk = int(request_data.get("pk", -1))
    value = str(request_data.get("value", '')).strip()
    with_confirm = bool(request_data.get("withConfirm", True))

    direction = Napravleniya.objects.filter(pk=pk).first()

    if not direction:
        return JsonResponse({'ok': False, 'message': 'Документ не найден'})

    if not value and with_confirm:
        return JsonResponse({'ok': False, 'message': 'Некорректное значение'})

    iss = Issledovaniya.objects.filter(napravleniye=direction, time_confirmation__isnull=True).filter(
        Q(research__podrazdeleniye=request.user.doctorprofile.podrazdeleniye)
        | Q(research__is_doc_refferal=True)
        | Q(research__is_treatment=True)
        | Q(research__is_gistology=True)
        | Q(research__is_stom=True)
        | Q(research__is_gistology=True)
        | Q(research__is_form=True)
    )

    confirmed_at = None
    ok = False
    message = 'Неизвестная ошибка'
    with transaction.atomic():
        for i in iss:
            ParaclinicResult.objects.filter(issledovaniye=i).delete()

            for g in ParaclinicInputGroups.objects.filter(research=i.research):
                for f in ParaclinicInputField.objects.filter(group=g):
                    f_result = ParaclinicResult(issledovaniye=i, field=f, value="")
                    f_result.value = value
                    f_result.field_type = f.field_type
                    f_result.save()

            i.doc_save = request.user.doctorprofile
            i.time_save = timezone.now()

            if with_confirm:
                i.doc_confirmation = request.user.doctorprofile
                i.time_confirmation = timezone.now()

            if i.napravleniye:
                i.napravleniye.qr_check_token = None
                i.napravleniye.save(update_fields=['qr_check_token'])
            i.save()
            if i.napravleniye:
                i.napravleniye.sync_confirmed_fields()
            confirmed_at = strdate(i.time_confirmation)
            ok = True
            message = None

    return JsonResponse(
        {
            'ok': ok,
            'message': message,
            'value': value,
            'slaveConfirm': confirmed_at,
        }
    )
