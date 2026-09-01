import datetime
from typing import Iterator, Optional, Tuple


def normalize_work_day_status_id(work_time: dict) -> Optional[int]:
    type_id = work_time.get("typeId")
    if not type_id:
        return None
    return type_id


def iter_changed_work_time_cells(changed_time: dict) -> Iterator[Tuple[int, str, dict, Optional[int]]]:
    for employee_position_id, work_times in changed_time.items():
        position_id = int(employee_position_id)
        lunch_duration = work_times.get("lunchDuration")
        for date, work_time in work_times.items():
            if date == "lunchDuration":
                continue
            yield position_id, date, work_time, lunch_duration


def parse_schedule_start_end(date: str, work_time: dict) -> Tuple[Optional[str], Optional[str]]:
    start_time = work_time.get("startWorkTime") or None
    end_time = work_time.get("endWorkTime") or None
    start = f"{date} {start_time}" if start_time else None
    end = f"{date} {end_time}" if end_time else None
    if end_time == "00:00" and end:
        end_dt = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M") + datetime.timedelta(days=1)
        end = end_dt.strftime("%Y-%m-%d %H:%M")
    return start, end


def parse_fact_start_end_datetimes(date: str, work_time: dict) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    start_time = work_time.get("startWorkTime") or None
    end_time = work_time.get("endWorkTime") or None
    if not start_time or not end_time:
        return None, None
    start = datetime.datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
    end = datetime.datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
    if end_time == "00:00":
        end = end + datetime.timedelta(days=1)
    return start, end
