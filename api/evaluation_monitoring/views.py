import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .sql_func import sql_load
from hospitals.models import Hospitals
from directions.models import MonitoringResult, Issledovaniya, Napravleniya, CuratorGrade
from directory.models import ParaclinicInputField, Researches
from users.models import DoctorProfile
from laboratory.settings import EVALUATION_MONITORING_QUARTERLY_DIRECTIONS, EVALUATION_MONITORING_YEAR_DIRECTIONS



@login_required
def hospitals(request):
    return JsonResponse({"results": list(Hospitals.objects.values('pk', 'title'))})


@login_required
def load(request):
    request_data = json.loads(request.body)
    hospital_pk = int(request_data['hospital'])
    quarter = int(request_data['quarter']) if request_data['quarter'] != -1 else None
    type_period = 'PERIOD_QURTER' if quarter != -1 else 'PERIOD_YEAR'
    year = int(request_data['year'])
    sql_result = sql_load(
        hospital_pk=hospital_pk,
        research_pk=EVALUATION_MONITORING_QUARTERLY_DIRECTIONS if request_data['quarter'] != -1 else EVALUATION_MONITORING_YEAR_DIRECTIONS,
        type_period=type_period,
        quarter=quarter,
        year=year,
    )
    results = []
    group_object = {
        'title': '',
        'fields': [],
        'grader': {
            'grade': '',
            'comment': '',
            'grader': '',
        },
    }
    for i in sql_result:
        grade = json.loads(i.curator_grade) if i.curator_grade is not None else {'grade': None, 'comment': None}
        if group_object['title'] == '':
            group_object['title'] = i.group_title
            group_object['grade'] = {
                'grade': grade['grade'],
                'comment': grade['comment'],
                'grader': i.curator_fio,
            }
        elif group_object['title'] != i.group_title:
            results.append(group_object)
            group_object = {
                'title': i.group_title,
                'fields': [],
                'grade': {
                    'grade': grade['grade'],
                    'comment':  grade['comment'],
                    'grader': i.curator_fio,
                }
            }
        group_object['fields'].append({
            'result_id': i.id,
            'field_id': i.field_id,
            'value_aggregate': int(i.value_aggregate) if i.value_aggregate is not None else None,
            'value_text': i.value_text if i.value_aggregate is None else None,
        })

    return JsonResponse({'rows': results})


@login_required
def add_result(request):
    doctor = DoctorProfile.objects.get(user=request.user)
    request_data = json.loads(request.body)
    result = MonitoringResult.objects.get(pk=int(request_data['result_id']))
    grade_value = request_data['grade']
    comment = request_data['comment']
    grade = CuratorGrade.objects.filter(monitoring_field_id=result.id)

    if len(grade) == 0:
        grade = CuratorGrade(
            monitoring_field=result,
            curator=doctor,
            grade_values={
                'grade': grade_value,
                'comment': comment,
            },
        )
        grade.save()
    else:
        grade = grade[0]
        grade.curator = doctor
        grade.grade_values = {
            'grade': grade_value,
            'comment': comment,
        }
        grade.save()

    return JsonResponse(
        {
            'ok': True,
            'message': 'Ok',
            'value': '',
            'slaveConfirm': '',
        }
    )


