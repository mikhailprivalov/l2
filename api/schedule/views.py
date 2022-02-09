from collections import defaultdict
from typing import List

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User

from api.schedule.sql_func import get_date_slots
from clients.models import Card, CardBase
import math
import datetime
from datetime import timedelta

from directory.models import Researches
from doctor_schedule.models import ScheduleResource, SlotFact, SlotPlan
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction

from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile
from utils.data_verification import data_parse
from laboratory.utils import localtime
from utils.dates import try_strptime
from utils.response import status_response


def delta_to_string(d):
    return None if d is None else ':'.join([x.rjust(2, '0') for x in str(d).split(':')[:2]])


@login_required
def days(request):
    day, resource_pk, display_days = data_parse(request.body, {'date': str, 'resource': int, 'displayDays': int}, {'displayDays': 7})
    rows = []

    start_time = None
    end_time = None
    display_days = min(display_days, 21)

    date_start = datetime.datetime.strptime(day, '%Y-%m-%d')
    for i in range(display_days):
        date = date_start + datetime.timedelta(days=i)
        date_end = date + datetime.timedelta(days=1)
        date_s = datetime.datetime.strftime(date, '%Y-%m-%d')
        date_data = {
            'date': date_s,
            'weekDay': date.weekday(),
            'month': date.month - 1,
            'slots': [],
        }
        resource = ScheduleResource.objects.filter(pk=resource_pk).first()
        if resource:
            slots = SlotPlan.objects.filter(resource=resource, datetime__gte=date, datetime__lt=date_end).order_by('datetime')
            for s in slots:
                slot_datetime = localtime(s.datetime)
                duration = s.duration_minutes

                current_slot_time = timedelta(hours=max(slot_datetime.hour, 0))
                hours_duration = int(math.ceil(duration / 60))
                current_slot_end_time = timedelta(hours=min(slot_datetime.hour + hours_duration, 24))

                if start_time is None or start_time > current_slot_time:
                    start_time = current_slot_time

                if end_time is None or end_time < current_slot_end_time:
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

    if end_time is not None and end_time >= timedelta(hours=24):
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


@login_required
def search_resource(request):
    rows = []
    q = request.GET.get('query') or ''
    departments = defaultdict(list)
    for r in ScheduleResource.objects.filter(executor__fio__istartswith=q)[:15]:
        departments[r.executor.podrazdeleniye_id].append({"id": r.pk, "label": str(r)})
    for dep_pk in departments:
        rows.append(
            {
                "id": f"dep-{dep_pk}",
                "label": Podrazdeleniya.objects.get(pk=dep_pk).get_title(),
                "children": departments[dep_pk],
            }
        )
    return JsonResponse({"rows": rows})


@login_required
def get_first_user_resource(request):
    resources = ScheduleResource.objects.filter(executor=request.user.doctorprofile)
    if resources.exists():
        options = []
        departments = defaultdict(list)
        for r in resources:
            departments[r.executor.podrazdeleniye_id].append({"id": r.pk, "label": str(r)})
        for dep_pk in departments:
            options.append(
                {
                    "id": f"dep-{dep_pk}",
                    "label": Podrazdeleniya.objects.get(pk=dep_pk).get_title(),
                    "children": departments[dep_pk],
                }
            )
        return JsonResponse({"pk": resources[0].pk, "title": str(resources[0]), "options": options})
    return JsonResponse({"pk": None, "title": None, "options": []})


@login_required
def create_slots(request):
    data = data_parse(request.body, {'slots': list, 'sources': list, 'duration': int, 'date': str, 'resource': int})
    slots: List[str] = data[0]
    print(slots)
    sources: List[str] = data[1]
    duration: int = data[2]
    date: str = data[3]
    date_start = f"{date} 00:00:00"
    date_end = f"{date} 23:59:59"
    date_slots = get_date_slots(date_start, date_end)
    remove_element = []
    for s in slots:
        start_end = s.split(" — ")
        a1 = try_strptime(f"{date} {start_end[0]}", formats=('%Y-%m-%d %H:%M',))
        a2 = try_strptime(f"{date} {start_end[1]}", formats=('%Y-%m-%d %H:%M',))
        for ds in date_slots:
            b1 = try_strptime(f"{date} {ds.start_slot}", formats=('%Y-%m-%d %H:%M',))
            b2 = try_strptime(f"{date} {ds.end_slot}", formats=('%Y-%m-%d %H:%M',))
            # проерка на не пересечение
            print(a1, a2, b1, b2)
            if not (a1 >= b2 or a2 <= b1):
                remove_element.append(s)
    for r in remove_element:
        slots.remove(r)
    resource: int = data[4]
    with transaction.atomic():
        for s in slots:
            time = s.split(' ')[0]
            datetime_str = f"{date} {time}"
            dt = try_strptime(datetime_str, formats=('%Y-%m-%d %H:%M',))
            end_date = dt + relativedelta(minutes=duration)
            print(dt, " - ", end_date)
            SlotPlan.objects.create(
                resource_id=resource,
                datetime=dt,
                datetime_end=end_date,
                duration_minutes=duration,
                available_systems=sources,
            )
    return status_response(True)
