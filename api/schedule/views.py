from django.contrib.auth.models import User

from clients.models import Card, CardBase
import math
import datetime
from datetime import timedelta

from directory.models import Researches
from doctor_schedule.models import ScheduleResource, SlotFact, SlotPlan
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from users.models import DoctorProfile
from utils.data_verification import data_parse
from laboratory.utils import localtime
from utils.response import status_response


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

                date_data['slots'].append(
                    {
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
                    }
                )
        rows.append(date_data)

    if end_time and end_time >= timedelta(hours=24):
        end_time = timedelta(hours=23)

    start_calendar_time = delta_to_string(start_time)
    end_calendar_time = delta_to_string(end_time)

    return JsonResponse(
        {
            'days': rows,
            'startTime': start_calendar_time,
            'endTime': end_calendar_time,
        }
    )


@login_required
def details(request):
    pk = data_parse(request.body, {'id': int})[0]

    s: SlotPlan = SlotPlan.objects.filter(pk=pk).first()

    if s:
        slot_datetime = localtime(s.datetime)
        duration = s.duration_minutes

        current_slot_time = timedelta(hours=max(slot_datetime.hour, 0))

        slot_fact = SlotFact.objects.filter(plan=s).order_by('-pk').first()

        status = 'empty'

        card_pk = None
        service = None
        direction = None
        base_pk = CardBase.objects.filter(internal_type=True)[0].pk

        if slot_fact:
            status = {
                0: 'reserved',
                1: 'cancelled',
                2: 'succes',
            }[slot_fact.status]

            if slot_fact.patient:
                card: Card = slot_fact.patient

                card_pk = card.pk

            if slot_fact.service:
                service = {
                    'id': slot_fact.service_id,
                    'title': slot_fact.service.get_title(),
                }

            if slot_fact.direction:
                direction = {
                    'id': slot_fact.direction_id,
                }

        return status_response(
            True,
            data={
                'data': {
                    'id': s.pk,
                    'date': datetime.datetime.strftime(slot_datetime, '%Y-%m-%d'),
                    'time': datetime.datetime.strftime(slot_datetime, '%X'),
                    'hour': delta_to_string(current_slot_time),
                    'hourValue': slot_datetime.hour,
                    'minute': slot_datetime.minute,
                    'duration': duration,
                    'status': status,
                    'cardId': card_pk,
                    'baseId': base_pk,
                    'service': service,
                    'direction': direction,
                },
            },
        )

    return status_response(False)


@login_required
def save(request):
    data = data_parse(request.body, {'id': int, 'cardId': int, 'status': str})

    pk: int = data[0]
    card_pk: int = data[1]
    status: str = data[2]

    s: SlotPlan = SlotPlan.objects.filter(pk=pk).first()

    if s:
        status = {
            'reserved': 0,
            'cancelled': 1,
            'succes': 2,
        }.get(status, 0)
        slot_fact: SlotFact = SlotFact.objects.filter(plan=s).order_by('-pk').first()

        if not slot_fact:
            slot_fact = SlotFact.objects.create(plan=s, status=status)

        slot_fact.patient_id = card_pk
        slot_fact.status = status

        slot_fact.save(update_fields=['patient', 'status'])

        return status_response(True)

    return status_response(False, 'Слот не найден')


@login_required
def save_resource(request):
    data = data_parse(request.body, {'pk': int, 'resource_researches': list, 'res_pk': int})
    print(data)
    user = User.objects.get(pk=data[0])
    executor = DoctorProfile.objects.get(user=user)
    researches = Researches.objects.filter(pk__in=data[1])
    if data[2] == -1:
        doc_resource = ScheduleResource(executor=executor, department=executor.podrazdeleniye, speciality=executor.specialities)
        doc_resource.save()
    else:
        doc_resource = ScheduleResource.objects.get(pk=data[2])
        doc_resource.service.clear()
    for r in researches:
        doc_resource.service.add(r)
    return JsonResponse({"message": "dfdf", "ok": True})

