import time

from education.models import LogUpdateMMIS
from education.sql_func import get_connection_params, get_enrollees_by_id, get_changes


def create_connection_string(settings_name: str):
    connection_params = get_connection_params(settings_name)[0]
    connection_string = (
        f"DRIVER={connection_params.driver}; SERVER={connection_params.ip_address}; DATABASE={connection_params.database}; Encrypt={connection_params.encrypt}; "
        f"UID={connection_params.login}; PWD={connection_params.password}"
    )
    return connection_string


def get_enrollees(connection_string: str, list_id: list):
    result = get_enrollees_by_id(connection_string, list_id)
    return result


def get_ids_changes_enrollees(connection_string: str):
    last_log = LogUpdateMMIS.objects.last()
    last_time_str = last_log.last_mmis_log_time.strftime('%Y-%m-%d %H:%M:%S')
    changes = get_changes(connection_string, last_time_str)
    lens_changes = len(changes)
    if lens_changes != 0:
        id_changed_enrollees = []
        count = 0
        for i in changes:
            if count == (lens_changes - 1):
                last_log.last_mmis_log_time = i.дата
                last_log.last_mmis_log_id = i.Код
                # last_log.save()
            if i.код_абитуриента != 0 and i.код_абитуриента not in id_changed_enrollees:
                id_changed_enrollees.append(i.код_абитуриента)
            count += 1
        return id_changed_enrollees
    return None


MAX_LOOP_TIME = 600


def process_update_enrollees():
    time_start = time.time()
    connection_string = create_connection_string('MMIS')
    while time.time() - time_start < MAX_LOOP_TIME:
        ids_changed_enrollees = get_ids_changes_enrollees(connection_string)
        if ids_changed_enrollees is None:
            print('Данных нет пока что')
        else:
            print('мы тута')
            enrolles_data = get_enrollees(connection_string, ids_changed_enrollees)
            print(enrolles_data)
        time.sleep(10)


def process_start_update_enrolles():
    print('Starting  process')  # noqa: F201
    while True:
        process_update_enrollees()
