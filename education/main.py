import time

from education.models import LogUpdateMMIS
from education.sql_func import get_connection_params, get_enrollees_by_id, get_changes, get_grade_entrance_exams
from education.views import save_education_individual
from laboratory.settings import EDUCATION_BASE_TITLE, TIME_ZONE
import pytz_deprecation_shim as pytz

from users.models import DoctorProfile


def create_connection_string(settings_name: str):
    connection_params = get_connection_params(settings_name)[0]
    connection_string = (
        f"DRIVER={connection_params.driver}; SERVER={connection_params.ip_address}; DATABASE={connection_params.database}; Encrypt={connection_params.encrypt}; "
        f"UID={connection_params.login}; PWD={connection_params.password}"
    )
    return connection_string


def get_enrollees(connection_string: str, list_id: list):
    list_id_str = ", ".join(map(str, list_id))
    enrollees_person_data = get_enrollees_by_id(connection_string, list_id_str)
    enrollees_grades = get_grade_entrance_exams(connection_string, list_id_str)
    return (
        enrollees_person_data,
        enrollees_grades,
    )


def get_ids_changes_enrollees(connection_string: str):
    last_log = LogUpdateMMIS.objects.last()
    last_time_str = last_log.last_mmis_log_time.astimezone(pytz.timezone(TIME_ZONE)).strftime('%Y-%m-%d %H:%M:%S')
    changes_log = get_changes(connection_string, last_time_str)
    curren_log = None
    id_changed_enrollees = []
    for curren_log in changes_log:
        if curren_log.код_абитуриента not in id_changed_enrollees:
            id_changed_enrollees.append(curren_log.код_абитуриента)
    if curren_log:
        last_log.last_mmis_log_time = curren_log.дата.astimezone(pytz.timezone(TIME_ZONE))
        last_log.last_mmis_log_id = curren_log.Код
        last_log.save()
    return id_changed_enrollees


MAX_LOOP_TIME = 600


def process_update_enrollees():
    time_start = time.time()
    connection_string = create_connection_string(EDUCATION_BASE_TITLE)
    user_obj_hospital = DoctorProfile.objects.get(pk=1).hospital
    while time.time() - time_start < MAX_LOOP_TIME:
        ids_changed_enrollees = get_ids_changes_enrollees(connection_string)
        if not ids_changed_enrollees:
            pass
        else:
            enrollees_person_data, enrollees_grade = get_enrollees(connection_string, ids_changed_enrollees)
            enrollees_grade_data = {
                i.ID:
                    {
                        "grade": i.Оценка,
                        "test_code": i.Код_Испытания,
                        "discipline": i.Дисциплина
                    }
                for i in enrollees_grade
            }
            for i in enrollees_person_data:
                save_education_individual(i, enrollees_grade_data.get(i.ID), user_obj_hospital)
        time.sleep(10)


def process_start_update_enrolles():
    while True:
        process_update_enrollees()
