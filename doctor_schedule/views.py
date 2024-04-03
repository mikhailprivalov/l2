import datetime
from dateutil.relativedelta import relativedelta
from doctor_schedule.models import ScheduleResource

from laboratory.utils import current_time
from doctor_schedule.sql_func import get_resource_by_research_hospital, get_slot_plan_by_hosp_resource, get_hospital_resource_by_research, get_slot_fact
from doctor_schedule.sql_func import get_date_slots_for_many_resource
from laboratory.settings import FORWARD_DAYS_SCHEDULE
from plans.models import PlanHospitalization
from utils.dates import try_strptime


def get_hospital_resource():
    hospital_resource = get_resource_by_research_hospital()
    hospital_resource_pk = [i.scheduleresource_id for i in hospital_resource]
    resource_researches = {}
    for i in hospital_resource:
        if not resource_researches.get(i.scheduleresource_id, None):
            resource_researches[i.scheduleresource_id] = {"researches_id": i.researches_id, "title": i.schedule_title or i.title, "short_title": i.short_title}

    d1 = current_time(only_date=True)
    d2 = d1 + relativedelta(days=FORWARD_DAYS_SCHEDULE)
    date_start = datetime.datetime.combine(d1, datetime.time.min)
    date_end = datetime.datetime.combine(d2, datetime.time.max)
    slot_plan_for_hospital = get_slot_plan_by_hosp_resource(date_start, date_end, tuple(hospital_resource_pk))
    resource_has_slot = set([sl.resource_id for sl in slot_plan_for_hospital])
    final_hosp_researches_has_slot = []
    for rslot in resource_has_slot:
        if resource_researches.get(rslot):
            temp_data = resource_researches.get(rslot)
            temp_data["resource_id"] = rslot
            final_hosp_researches_has_slot.append(temp_data.copy())

    return final_hosp_researches_has_slot


def get_available_hospital_plans(research_pk, resource_id=None, date_start=None, date_end=None):
    if date_start and date_end:
        d1 = try_strptime(f"{date_start}", formats=('%Y-%m-%d',))
        d2 = try_strptime(f"{date_end}", formats=('%Y-%m-%d',))
    else:
        d1 = current_time(only_date=True) + relativedelta(days=1)
        d2 = d1 + relativedelta(days=FORWARD_DAYS_SCHEDULE)

    if resource_id is None:
        resource_id = tuple(ScheduleResource.objects.filter(service__in=[research_pk]).values_list('pk', flat=True))
    elif isinstance(resource_id, tuple):
        resource_id = resource_id
    elif isinstance(resource_id, list):
        resource_id = tuple(resource_id)
    else:
        resource_id = tuple([resource_id])

    if not resource_id:
        return {}, {}

    counts = {}

    start_date = datetime.datetime.combine(d1, datetime.time.min)
    end_date = datetime.datetime.combine(d2, datetime.time.max)
    result_slot = get_slot_plan_by_hosp_resource(start_date, end_date, resource_id)
    date_slots = {}
    for rslots in result_slot:
        if not date_slots.get(rslots.date_char, None):
            date_slots[rslots.date_char] = [rslots.datetime]
        else:
            temp_date_slots = date_slots.get(rslots.date_char, None)
            temp_date_slots.append(rslots.datetime)
            date_slots[rslots.date_char] = temp_date_slots.copy()
    date_available_status = {}

    date_i = start_date - datetime.timedelta(days=1)  # ЦИТО можно записать на сегодня
    while date_i < end_date:
        date_s = date_i.strftime("%Y-%m-%d")
        date_available_status[date_s] = False
        date_i += datetime.timedelta(days=1)

    for current_date, slots_in_date in date_slots.items():
        d1 = try_strptime(current_date, formats=('%Y-%m-%d',))
        start_date = datetime.datetime.combine(d1, datetime.time.min)
        end_date = datetime.datetime.combine(d1, datetime.time.max)
        current_plan_count = (
            PlanHospitalization.objects.filter(exec_at__range=(start_date, end_date), work_status__in=[0, 1, 3], action=0, research_id=research_pk).order_by("exec_at").count()
        )
        counts[current_date] = {
            "available": len(slots_in_date),
            "used": current_plan_count,
        }
        date_available_status[current_date] = counts[current_date]["available"] > counts[current_date]["used"]

    return date_available_status, counts


def check_available_hospital_slot_before_save(research_pk, resource_id, date):
    if not research_pk or not date:
        return False
    d = try_strptime(f"{date}", formats=('%Y-%m-%d',))
    start_date = datetime.datetime.combine(d, datetime.time.min)
    end_date = datetime.datetime.combine(d, datetime.time.max)
    if resource_id is None:
        resource_id = tuple(ScheduleResource.objects.filter(service__in=[research_pk]).values_list('pk', flat=True))
    elif isinstance(resource_id, tuple):
        resource_id = resource_id
    elif isinstance(resource_id, list):
        resource_id = tuple(resource_id)
    else:
        resource_id = tuple([resource_id])

    if not resource_id:
        return False

    result_slot = get_slot_plan_by_hosp_resource(start_date, end_date, resource_id)
    date_slots = [i.hhmm_char for i in result_slot]
    current_plan_count = PlanHospitalization.objects.filter(exec_at__range=(start_date, end_date), work_status=0, action=0, research_id=research_pk).order_by("exec_at").count()
    return len(date_slots) > current_plan_count


def get_available_hospital_resource_slot(research_pk, date_start, date_end, allow_cito=False):
    d1 = try_strptime(f"{date_start}", formats=('%Y-%m-%d',))
    d2 = try_strptime(f"{date_end}", formats=('%Y-%m-%d',))
    start_date = datetime.datetime.combine(d1, datetime.time.min)
    end_date = datetime.datetime.combine(d2, datetime.time.max)
    result = {"dates": {}}

    if end_date < datetime.datetime.combine(try_strptime(current_time().strftime("%Y-%m-%d"), formats=('%Y-%m-%d',)), datetime.time.max):
        return result

    resource_hosp = get_hospital_resource_by_research(research_pk)
    structure_resource = {rh.scheduleresource_id: rh.resource_title for rh in resource_hosp}

    resource_tuple = tuple(structure_resource.keys())
    slot_plans = get_date_slots_for_many_resource(start_date, end_date, resource_tuple)
    slot_plan_pks = tuple([slplan.slot_id for slplan in slot_plans])
    slot_plan_busy_slot_fact = get_slot_fact(slot_plan_pks)
    slot_plan_busy_slot_fact = [i.plan_id for i in slot_plan_busy_slot_fact]
    data = result["dates"]
    dates = set([slotplan.date_char for slotplan in slot_plans])
    for d in dates:
        data[d] = []

    temp_data_slot_resource = {}
    for slotplan in slot_plans:
        if slotplan.slot_id in slot_plan_busy_slot_fact:
            continue
        if not temp_data_slot_resource.get(slotplan.resource_id):
            temp_data_slot_resource[slotplan.resource_id] = {slotplan.date_char: [{"pk": slotplan.slot_id, "title": f"{slotplan.start_slot} - {slotplan.end_slot}"}]}
        else:
            temp_slot_resource_date = temp_data_slot_resource.get(slotplan.resource_id, None)
            if not temp_slot_resource_date.get(slotplan.date_char):
                temp_slot_resource_date[slotplan.date_char] = [{"pk": slotplan.slot_id, "title": f"{slotplan.start_slot} - {slotplan.end_slot}"}]
            else:
                temp_slot_resource_data = temp_slot_resource_date.get(slotplan.date_char)
                temp_slot_resource_data.append({"pk": slotplan.slot_id, "title": f"{slotplan.start_slot} - {slotplan.end_slot}"})
                temp_slot_resource_date[slotplan.date_char] = temp_slot_resource_data.copy()
            temp_data_slot_resource[slotplan.resource_id] = temp_slot_resource_date.copy()

    for k, v in temp_data_slot_resource.items():
        for date, slots in v.items():
            temp_data = data.get(date)
            schedule_resource_obj = ScheduleResource.objects.filter(pk=k).first()
            rmis_location = None
            if schedule_resource_obj:
                rmis_location = schedule_resource_obj.executor.rmis_location
            temp_data.append({"resourcePk": k, "rmis_location": rmis_location, "resourceTitle": structure_resource.get(k, ""), "slots": slots})
            data[date] = temp_data.copy()

    if allow_cito:
        dates = []
        date_i = start_date
        while date_i < end_date:
            date = date_i.strftime("%Y-%m-%d")
            if date not in data:
                data[date] = []
            has_resources = {x['resourcePk']: x for x in data[date]}
            for rpk in resource_tuple:
                if rpk in has_resources:
                    has_resources[rpk]['slots'].append({"pk": -10, "title": "CITO"})
                    continue
                temp_data = {"resourcePk": rpk, "resourceTitle": structure_resource.get(rpk, ""), "slots": [{"pk": -10, "title": "CITO"}]}
                data[date].append(temp_data)

            date_i += datetime.timedelta(days=1)
    return result


def get_available_slots_of_dates(research_pk, date_start, date_end, allow_cito=False):
    d1 = try_strptime(f"{date_start}", formats=('%Y-%m-%d',))
    d2 = try_strptime(f"{date_end}", formats=('%Y-%m-%d',))
    current_date = try_strptime(current_time().strftime("%Y-%m-%d"), formats=('%Y-%m-%d',))
    start_date = datetime.datetime.combine(d1, datetime.time.min)
    end_date = datetime.datetime.combine(d2, datetime.time.max)

    if end_date < datetime.datetime.combine(current_date, datetime.time.max):
        return {}

    if start_date < datetime.datetime.combine(current_date, datetime.time.min):
        start_date = datetime.datetime.combine(current_date, datetime.time.min) + datetime.timedelta(days=1)

    if allow_cito:
        data = {}
        date_i = start_date - datetime.timedelta(days=1)  # ЦИТО можно записать на сегодня
        while date_i < end_date:
            date_s = date_i.strftime("%Y-%m-%d")
            data[date_s] = True
            date_i += datetime.timedelta(days=1)
        return data

    resource_hosp = get_hospital_resource_by_research(research_pk)
    structure_resource = {rh.scheduleresource_id: rh.resource_title for rh in resource_hosp}

    resource_tuple = tuple(structure_resource.keys())
    slot_plans = get_date_slots_for_many_resource(start_date, end_date, resource_tuple)
    slot_plan_pks = tuple([slplan.slot_id for slplan in slot_plans])
    slot_plan_busy_slot_fact = get_slot_fact(slot_plan_pks)
    slot_plan_busy_slot_fact = [i.plan_id for i in slot_plan_busy_slot_fact]
    data = {}

    for slotplan in slot_plans:
        if slotplan.slot_id in slot_plan_busy_slot_fact or slotplan.date_char in data:
            continue
        data[slotplan.date_char] = True

    return data
