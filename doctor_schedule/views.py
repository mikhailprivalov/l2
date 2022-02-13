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
            resource_researches[i.scheduleresource_id] = {"researches_id": i.researches_id, "title": i.title, "short_title": i.short_title}

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
        d2 = d1 + relativedelta(days=30)

    if resource_id is None:
        resource_id = tuple(ScheduleResource.objects.filter(service__in=[research_pk]).values_list('pk', flat=True))
    elif isinstance(resource_id, tuple):
        resource_id = resource_id
    elif isinstance(resource_id, list):
        resource_id = tuple(resource_id)
    else:
        resource_id = tuple([resource_id])

    if not resource_id:
        return {}

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

    date_counts = {}
    for current_date, slots_in_date in date_slots.items():
        d1 = try_strptime(current_date, formats=('%Y-%m-%d',))
        start_date = datetime.datetime.combine(d1, datetime.time.min)
        end_date = datetime.datetime.combine(d1, datetime.time.max)
        current_plan_count = PlanHospitalization.objects.filter(exec_at__range=(start_date, end_date), work_status=0, action=0, research_id=research_pk).order_by("exec_at").count()
        date_counts[current_date] = len(slots_in_date) > current_plan_count

    return date_counts


def get_available_hospital_resource_slot(research_pk, date_start, date_end):
    d1 = try_strptime(f"{date_start}", formats=('%Y-%m-%d',))
    d2 = try_strptime(f"{date_end}", formats=('%Y-%m-%d',))
    start_date = datetime.datetime.combine(d1, datetime.time.min)
    end_date = datetime.datetime.combine(d2, datetime.time.max)

    resource_hosp = get_hospital_resource_by_research(research_pk)
    structure_resource = {rh.scheduleresource_id: rh.resource_title for rh in resource_hosp}

    resource_tuple = tuple(structure_resource.keys())
    slot_plans = get_date_slots_for_many_resource(start_date, end_date, resource_tuple)
    slot_plan_pks = tuple([slplan.slot_id for slplan in slot_plans])
    slot_plan_busy_slot_fact = get_slot_fact(slot_plan_pks)
    result = {"dates": {}}
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
            temp_data.append({"resourcePk": k, "resourceTitle": structure_resource.get(k, ""), "slots": slots})
            data[date] = temp_data.copy()
    return result
