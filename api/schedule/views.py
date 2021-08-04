import datetime
from doctor_schedule.models import ScheduleResource, SlotPlan
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from utils.data_verification import data_parse
from laboratory.utils import localtime


@login_required
def days(request):
    day = data_parse(request.body, {'date': str})[0]
    rows = []

    date_start = datetime.datetime.strptime(day, '%Y-%m-%d')
    for i in range(7):
        date = date_start + datetime.timedelta(days=i)
        date_end = date + datetime.timedelta(days=1)
        date_s = datetime.datetime.strftime(date, '%Y-%m-%d')
        date_data = {
            'date': date_s,
            'key': date_s,
            'slots': [],
        }
        resource = ScheduleResource.objects.filter(executor=request.user.doctorprofile).first()
        if resource:
            slots = SlotPlan.objects.filter(resource=resource, datetime__gte=date, datetime__lt=date_end).order_by('datetime')
            for s in slots:
                date_data['slots'].append({
                    'key': s.pk,
                    'date': datetime.datetime.strftime(localtime(s.datetime), '%Y-%m-%d %X'),
                })
        rows.append(date_data)
    return JsonResponse({'days': rows})
