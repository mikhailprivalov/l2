from clients.models import Card
import math
import datetime
from datetime import timedelta
from doctor_schedule.models import ScheduleResource, SlotFact, SlotPlan
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from utils.data_verification import data_parse
from laboratory.utils import localtime


def delta_to_string(d):
    return None if not d else ':'.join([x.rjust(2, '0') for x in str(d).split(':')[:2]])


@login_required
def days(request):
    day = data_parse(request.body, {'date': str})[0]
    rows = []

    start_time = None
    end_time = None

    date_start = datetime.datetime.strptime(day, '%Y-%m-%d')
    for i in range(7):
        date = date_start + datetime.timedelta(days=i)
        date_end = date + datetime.timedelta(days=1)
        date_s = datetime.datetime.strftime(date, '%Y-%m-%d')
        date_data = {
            'date': date_s,
            'weekDay': date.weekday(),
            'month': date.month - 1,
            'slots': [],
        }
        resource = ScheduleResource.objects.filter(executor=request.user.doctorprofile).first()
        if resource:
            slots = SlotPlan.objects.filter(resource=resource, datetime__gte=date, datetime__lt=date_end).order_by('datetime')
            for s in slots:
                slot_datetime = localtime(s.datetime)
                duration = s.duration_minutes

                current_slot_time = timedelta(hours=max(slot_datetime.hour, 0))
                hours_duration = int(math.ceil(duration / 60))
                current_slot_end_time = timedelta(hours=min(slot_datetime.hour + hours_duration, 24))

                if not start_time or start_time > current_slot_time:
                    start_time = current_slot_time

                if not end_time or end_time < current_slot_end_time:
                    end_time = current_slot_end_time

                slot_fact = SlotFact.objects.filter(plan=s).order_by('-pk').first()

                status = 'empty'

                patient = None
                service = None
                direction = None

                if slot_fact:
                    status = {
                        0: 'reserved',
                        1: 'cancelled',
                        2: 'succes',
                    }[slot_fact.status]

                    if slot_fact.patient:
                        card: Card = slot_fact.patient
                        patient = {
                            'cardId': card.pk,
                            'base': card.base_id,
                            'number': card.number_with_type(),
                            'fio': card.individual.fio(full=True),
                            'birthday': card.individual.bd(),
                        }

                    if slot_fact.service:
                        service = {
                            'id': slot_fact.service_id,
                            'title': slot_fact.service.get_title(),
                        }

                    if slot_fact.direction:
                        direction = {
                            'id': slot_fact.direction_id,
                        }

                date_data['slots'].append({
                    'id': s.pk,
                    'date': datetime.datetime.strftime(slot_datetime, '%Y-%m-%d'),
                    'time': datetime.datetime.strftime(slot_datetime, '%X'),
                    'hour': delta_to_string(current_slot_time),
                    'hourValue': slot_datetime.hour,
                    'minute': slot_datetime.minute,
                    'duration': duration,
                    'status': status,
                    'patient': patient,
                    'service': service,
                    'direction': direction,
                })
        rows.append(date_data)

    if end_time and end_time >= timedelta(hours=24):
        end_time = timedelta(hours=23)

    start_calendar_time = delta_to_string(start_time)
    end_calendar_time = delta_to_string(end_time)

    return JsonResponse({
        'days': rows,
        'startTime': start_calendar_time,
        'endTime': end_calendar_time,
    })
