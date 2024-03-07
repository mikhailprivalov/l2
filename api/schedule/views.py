from collections import defaultdict
from typing import List

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from api.schedule.utils import can_access_user_to_modify_resource

from clients.models import Card, CardBase
import math
import datetime
from datetime import timedelta

from directory.models import Researches
from doctor_schedule.models import ScheduleResource, SlotFact, SlotPlan, SlotFactCancel, SlotFactDirection
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction

from doctor_schedule.sql_func import get_date_slots
from doctor_schedule.views import get_available_hospital_plans, get_available_hospital_resource_slot, check_available_hospital_slot_before_save, get_available_slots_of_dates
from laboratory.decorators import group_required
from plans.models import PlanHospitalization
from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile
from utils.auth import has_group
from utils.data_verification import data_parse
from laboratory.utils import localtime
from utils.dates import try_strptime
from utils.response import status_response


def delta_to_string(d):
    return None if d is None else ':'.join([x.rjust(2, '0') for x in str(d).split(':')[:2]])


COMMON_SCHEDULE_GROUPS = [
    'Лечащий врач',
    'Оператор лечащего врача',
    'Врач консультаций',
    'Врач стационара',
    'Врач параклиники',
    'Управление расписанием',
    'Создание и редактирование пользователей',
]
ADMIN_SCHEDULE_GROUPS = ['Управление расписанием', 'Создание и редактирование пользователей']


@login_required
@group_required(*COMMON_SCHEDULE_GROUPS)
def days(request):
    day, resource_pk, display_days = data_parse(request.body, {'date': str, 'resource': int, 'displayDays': int}, {'displayDays': 7})
    rows = []

    start_time = None
    end_time = None
    display_days = min(display_days, 21)

    date_start = datetime.datetime.strptime(day, '%Y-%m-%d')
    resource = ScheduleResource.objects.filter(pk=resource_pk).first()
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

                status = 'disabled' if s.disabled else 'empty'

                patient = None
                service = None
                direction = None
                is_cito = s.is_cito

                if slot_fact:
                    status = {
                        0: 'reserved',
                        1: 'cancelled',
                        2: 'success',
                    }[slot_fact.status]

                    if slot_fact.is_cito:
                        is_cito = True

                    if slot_fact.patient:
                        card: Card = slot_fact.patient
                        patient = {
                            'cardId': card.pk,
                            'base': card.base_id,
                            'number': card.number_with_type(),
                            'fio': card.individual.fio(full=True),
                            'fioShort': card.individual.fio(dots=True, short=True),
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
                        'factId': slot_fact.pk if slot_fact else None,
                        'date': datetime.datetime.strftime(slot_datetime, '%Y-%m-%d'),
                        'time': datetime.datetime.strftime(slot_datetime, '%H:%M'),
                        'timeEnd': datetime.datetime.strftime(slot_datetime + timedelta(minutes=duration), '%H:%M'),
                        'hour': delta_to_string(current_slot_time),
                        'hourValue': slot_datetime.hour,
                        'minute': slot_datetime.minute,
                        'duration': duration,
                        'status': status,
                        'patient': patient,
                        'service': service,
                        'direction': direction,
                        'cito': is_cito,
                    }
                )
        rows.append(date_data)

    if end_time is not None and end_time >= timedelta(hours=24):
        end_time = timedelta(hours=23)

    start_calendar_time = delta_to_string(start_time)
    end_calendar_time = delta_to_string(end_time)

    services = []

    if resource:
        services = [{'id': x['pk'], 'label': x['short_title'] or x['title']} for x in resource.service.all().values('pk', 'title', 'short_title').order_by('short_title', 'title')]

    return JsonResponse(
        {
            'days': rows,
            'startTime': start_calendar_time,
            'endTime': end_calendar_time,
            'services': services,
        }
    )


@login_required
@group_required(*COMMON_SCHEDULE_GROUPS)
def details(request):
    pk = data_parse(request.body, {'id': int})[0]

    s: SlotPlan = SlotPlan.objects.filter(pk=pk).first()

    if s:
        slot_datetime = localtime(s.datetime)
        duration = s.duration_minutes

        current_slot_time = timedelta(hours=max(slot_datetime.hour, 0))

        slot_fact = SlotFact.objects.filter(plan=s).order_by('-pk').first()

        disabled = s.disabled
        status = 'disabled' if disabled else 'empty'

        card_pk = None
        service = {
            'id': None,
        }
        direction = None
        base = CardBase.objects.filter(internal_type=True)[0]

        fin_source = None
        fact_id = None

        if slot_fact:
            fact_id = slot_fact.pk

            status = {
                0: 'reserved',
                1: 'cancelled',
                2: 'success',
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

            fin_source = slot_fact.fin_source_id

        return status_response(
            True,
            data={
                'data': {
                    'id': s.pk,
                    'factId': fact_id,
                    'date': datetime.datetime.strftime(slot_datetime, '%Y-%m-%d'),
                    'time': datetime.datetime.strftime(slot_datetime, '%X'),
                    'hour': delta_to_string(current_slot_time),
                    'hourValue': slot_datetime.hour,
                    'minute': slot_datetime.minute,
                    'duration': duration,
                    'status': status,
                    'cardId': card_pk,
                    'baseId': base.pk,
                    'finSources': base.get_fin_sources(),
                    'finSourceId': fin_source,
                    'service': service,
                    'direction': direction,
                    'disabled': disabled,
                },
            },
        )

    return status_response(False)


@login_required
@group_required(*COMMON_SCHEDULE_GROUPS)
def save(request):
    data = data_parse(
        request.body,
        {'id': int, 'cardId': int, 'status': str, 'planId': int, 'serviceId': int, 'date': str, 'resource': str, 'disabled': bool, 'finSourceId': int},
        {'planId': None, 'cardId': None, 'serviceId': None, 'status': 'reserved', 'date': None, 'resource': None, 'disabled': False, 'finSourceId': None},
    )
    pk: int = data[0]
    card_pk: int = data[1]
    status: str = data[2]
    plan_id: int = data[3]
    service_id: int = data[4]
    date: str = data[5]
    resource: int = data[6]
    disabled: bool = data[7]
    fin_source: bool = data[8]

    is_cito = False

    if card_pk and has_group(request.user, 'Цито-запись в расписании') and pk == -10 and date and resource:
        d = try_strptime(f"{date}", formats=('%Y-%m-%d',))
        start_date = datetime.datetime.combine(d, datetime.time.min)
        end_date = datetime.datetime.combine(d, datetime.time.max)
        slots = SlotPlan.objects.filter(datetime__range=(start_date, end_date))
        free_slot: SlotPlan = slots.filter(slotfact__isnull=True).order_by('datetime').first()
        if not free_slot:
            last_any_slot: SlotPlan = slots.order_by('-datetime').first()
            if last_any_slot:
                next_time = last_any_slot.datetime + datetime.timedelta(minutes=last_any_slot.duration_minutes)
                duration = last_any_slot.duration_minutes
            else:
                next_time = try_strptime(f"{date} 08:00", formats=('%Y-%m-%d %H:%M',))
                duration = 3
            end_time = next_time + datetime.timedelta(minutes=duration)
            new_slot_plan = SlotPlan.objects.create(
                resource_id=resource,
                datetime=next_time,
                datetime_end=end_time,
                duration_minutes=duration,
                available_systems=[SlotPlan.LOCAL],
                disabled=False,
                is_cito=True,
            )
            pk = new_slot_plan.pk
        else:
            pk = free_slot.pk
        is_cito = True

    s: SlotPlan = SlotPlan.objects.filter(pk=pk).first()
    if s:
        save_slot = save_slot_fact(s, card_pk, status, service_id, is_cito, fin_source, plan_id, disabled)
        return status_response(save_slot)

    return status_response(False, 'Слот не найден')


@login_required
@group_required("Отмена записи")
def cancel(request):
    data = data_parse(
        request.body,
        {'id': int, 'cardId': int, 'status': str, 'planId': int, 'serviceId': int, 'date': str, 'resource': str, 'disabled': bool, 'finSourceId': int},
        {'planId': None, 'cardId': None, 'serviceId': None, 'status': 'reserved', 'date': None, 'resource': None, 'disabled': False, 'finSourceId': None},
    )
    pk: int = data[0]
    card_pk: int = data[1]
    service_id: int = data[4]

    s: SlotPlan = SlotPlan.objects.filter(pk=pk).first()
    if s:
        save_slot = SlotFactCancel.cancel_slot(pk, card_pk, service_id, request.user.doctorprofile)
        return status_response(
            save_slot,
        )

    return status_response(False, 'Не получилось отменить')


def save_slot_fact(s, card_pk, status, service_id, is_cito, fin_source, plan_id, disabled, direction_id=None):
        if card_pk:
            status = {
                'reserved': 0,
                'cancelled': 1,
                'success': 2,
            }.get(status, 0)
            slot_fact: SlotFact = SlotFact.objects.filter(plan=s).order_by('-pk').first()

            if not slot_fact:
                slot_fact = SlotFact.objects.create(plan=s, status=status)

            s.disabled = False
            slot_fact.patient_id = card_pk
            slot_fact.status = status
            slot_fact.service_id = service_id
            slot_fact.is_cito = is_cito
            slot_fact.fin_source_id = fin_source
            slot_fact.save()
            if direction_id:
                slot_fact_direction: SlotFactDirection = SlotFactDirection(slot_fact_id=slot_fact.pk, direction_id=direction_id)
                slot_fact_direction.save()
            if plan_id:
                ph: PlanHospitalization = PlanHospitalization.objects.get(pk=plan_id)
                ph.slot_fact = slot_fact
                ph.work_status = 3
                ph.exec_at = s.datetime
                ph.save()
        else:
            s.disabled = disabled
            s.save(update_fields=['disabled'])
        return True


@login_required
@group_required(*ADMIN_SCHEDULE_GROUPS)
def save_resource(request):
    data = data_parse(request.body, {'pk': int, 'resource_researches': list, 'res_pk': int, 'res_title': str})
    user_pk = data[0]
    resource_researches = data[1]
    res_pk = data[2]
    res_title = data[3]

    user = User.objects.get(pk=user_pk)
    executor = DoctorProfile.objects.get(user=user)
    researches = Researches.objects.filter(pk__in=resource_researches)
    if res_pk == -1:
        doc_resource = ScheduleResource(executor=executor, department=executor.podrazdeleniye, speciality=executor.specialities, title=res_title)
        doc_resource.save()
    else:
        doc_resource = ScheduleResource.objects.get(pk=res_pk)
        doc_resource.title = res_title
        doc_resource.service.clear()
    for r in researches:
        doc_resource.service.add(r)
    doc_resource.save()
    return JsonResponse({"message": "Ресурс создан", "ok": True})


@login_required
@group_required(*COMMON_SCHEDULE_GROUPS)
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
@group_required(*COMMON_SCHEDULE_GROUPS)
def get_first_user_resource(request):
    access_to_all = has_group(request.user, *ADMIN_SCHEDULE_GROUPS) and request.GET.get('onlyMe') != '1'
    if access_to_all:
        resources = ScheduleResource.objects.all()
    else:
        resources = ScheduleResource.objects.filter(executor=request.user.doctorprofile)
    resources = resources.filter(hide=False, service__isnull=False).distinct()

    first_current_user_pk = None

    if resources.exists():
        options = []
        departments = defaultdict(list)
        for r in resources:
            departments[r.executor.podrazdeleniye_id].append({"id": r.pk, "label": str(r)})
            if r.executor_id == request.user.doctorprofile.pk:
                first_current_user_pk = r.pk
        for dep_pk in departments:
            options.append(
                {
                    "id": f"dep-{dep_pk}",
                    "label": Podrazdeleniya.objects.get(pk=dep_pk).get_title(),
                    "children": departments[dep_pk],
                }
            )
        return JsonResponse({"pk": first_current_user_pk if first_current_user_pk is not None else resources[0].pk, "title": str(resources[0]), "options": options})
    return JsonResponse({"pk": None, "title": None, "options": []})


@login_required
def create_slots(request):
    data = data_parse(request.body, {'slots': list, 'sources': list, 'duration': int, 'date': str, 'resource': int})
    slots: List[str] = data[0]
    sources: List[str] = data[1]
    duration: int = data[2]
    date: str = data[3]
    resource: int = data[4]
    date_start = f"{date} 00:00:00"
    date_end = f"{date} 23:59:59"

    has_rights = can_edit_resource(request, resource)
    if not has_rights:
        return status_response(False, 'У вас недостаточно прав')

    date_slots = get_date_slots(date_start, date_end, resource)
    remove_element = []
    for s in slots:
        start_end = s.split(" — ")
        a1 = try_strptime(f"{date} {start_end[0]}", formats=('%Y-%m-%d %H:%M',))
        a2 = try_strptime(f"{date} {start_end[1]}", formats=('%Y-%m-%d %H:%M',))
        for ds in date_slots:
            b1 = try_strptime(f"{date} {ds.start_slot}", formats=('%Y-%m-%d %H:%M',))
            b2 = try_strptime(f"{date} {ds.end_slot}", formats=('%Y-%m-%d %H:%M',))
            # проерка на не пересечение
            if not (a1 >= b2 or a2 <= b1):
                remove_element.append(s)
    for r in remove_element:
        slots.remove(r)

    with transaction.atomic():
        for s in slots:
            time = s.split(' ')[0]
            datetime_str = f"{date} {time}"
            dt = try_strptime(datetime_str, formats=('%Y-%m-%d %H:%M',))
            end_date = dt + relativedelta(minutes=duration)
            SlotPlan.objects.create(
                resource_id=resource,
                datetime=dt,
                datetime_end=end_date,
                duration_minutes=duration,
                available_systems=sources,
            )

    return status_response(True)


@login_required
def available_slots(request):
    data = data_parse(request.body, {'research_pk': int, 'date_start': str, 'date_end': str})
    research_pk: int = data[0]
    date_start: str = data[1]
    date_end: str = data[2]
    result = get_available_hospital_resource_slot(research_pk, date_start, date_end, allow_cito=has_group(request.user, 'Цито-запись в расписании'))
    return JsonResponse({"result": result})


@login_required
def available_hospitalization_plan(request):
    data = data_parse(
        request.body,
        {'research_pk': int, 'resource_id': int, 'date_start': str, 'date_end': str},
        {
            'research_pk': None,
            'resource_id': None,
            'date_start': None,
            'date_end': None,
        },
    )
    research_pk = data[0]
    resource_id = data[1]
    date_start = data[2]
    date_end = data[3]

    is_cito = has_group(request.user, 'Цито-запись в расписании')

    result, counts = get_available_hospital_plans(research_pk, resource_id, date_start, date_end)
    return JsonResponse({"data": result, "counts": counts, "cito": is_cito})


@login_required
def check_hosp_slot_before_save(request):
    data = data_parse(
        request.body,
        {'research_pk': int, 'resource_id': int, 'date': str},
        {
            'research_pk': None,
            'resource_id': None,
            'date': None,
        },
    )
    research_pk = data[0]
    resource_id = data[1]
    date = data[2]
    result = check_available_hospital_slot_before_save(research_pk, resource_id, date)
    return JsonResponse({"result": result})


@login_required
def available_slots_of_dates(request):
    data = data_parse(request.body, {'research_pk': int, 'date_start': str, 'date_end': str})
    research_pk = data[0]
    date_start = data[1]
    date_end = data[2]
    result = get_available_slots_of_dates(research_pk, date_start, date_end, allow_cito=has_group(request.user, 'Цито-запись в расписании'))
    return JsonResponse({"data": result})


@login_required
def schedule_access(request):
    resource_pk = data_parse(request.body, {'resourcePk': int}, {'resourcePk': None})[0]
    return status_response(can_edit_resource(request, resource_pk))


def can_edit_resource(request, resource_pk):
    if has_group(request.user, *ADMIN_SCHEDULE_GROUPS):
        return True
    return can_access_user_to_modify_resource(request.user.doctorprofile, resource_pk=resource_pk)


@login_required
def delete_day_slots(request):
    data = data_parse(request.body, {'date': str, 'resource': int})
    date: str = data[0]
    resource: int = data[1]
    date_start = f"{date} 00:00:00"
    date_end = f"{date} 23:59:59"
    result = SlotPlan.delete_slot_plan(resource, date_start, date_end)
    return status_response(result)


@login_required
def copy_day_slots(request):
    data = data_parse(request.body, {'date': str, 'resource': int, 'countDaysToCopy': int})
    date: str = data[0]
    resource: int = data[1]
    count_days_to_copy: int = data[2]
    date_start = f"{date} 00:00:00"
    date_end = f"{date} 23:59:59"
    result = SlotPlan.copy_day_slots_plan(resource, date_start, date_end, count_days_to_copy)

    return status_response(result)
