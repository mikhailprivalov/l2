import time

from education.models import LogUpdateMMIS
from education.sql_func import get_connection_params, get_enrollees_by_id, get_changes, get_grade_entrance_exams, get_application_by_id, get_achievements_by_id
from education.views import update_education_individual, change_encoding_cp1251
from hospitals.models import Hospitals
from laboratory.settings import TIME_ZONE, MMIS_CONNECT_WITH_PYODBC
from pymssql import OperationalError
from pyodbc import InterfaceError
import pytz_deprecation_shim as pytz


def create_connection_string():
    connection_params = get_connection_params()[0]
    if MMIS_CONNECT_WITH_PYODBC:
        connection_string = (
            f"DRIVER={connection_params.driver}; SERVER={connection_params.ip_address},{connection_params.port}; DATABASE={connection_params.database}; Encrypt={connection_params.encrypt}; "
            f"UID={connection_params.login}; PWD={connection_params.password}"
        )
    else:
        connection_string = {
            "server": connection_params.ip_address,
            "port": connection_params.port,
            "user": connection_params.login,
            "password": connection_params.password,
            "database": connection_params.database,
        }
    return connection_string


def get_enrollees(connection_string, list_id: list):
    list_id_str = ", ".join(map(str, list_id))
    enrollees_person_data = None
    enrollees_grades = None
    enrollees_application_data = None
    enrollees_achievements = None
    try:
        enrollees_person_data = get_enrollees_by_id(connection_string, list_id_str)
        enrollees_grades = get_grade_entrance_exams(connection_string, list_id_str)
        enrollees_application_data = get_application_by_id(connection_string, list_id_str)
        enrollees_achievements = get_achievements_by_id(connection_string, list_id_str)
    except (OperationalError, InterfaceError):
        print('Database connection error')  # noqa: F201
    return (
        enrollees_person_data,
        enrollees_grades,
        enrollees_application_data,
        enrollees_achievements,
    )


def get_ids_changes_enrollees(connection_string: str):
    last_log: LogUpdateMMIS = LogUpdateMMIS.objects.last()
    last_time_str = last_log.last_mmis_log_time.astimezone(pytz.timezone(TIME_ZONE)).strftime('%Y-%m-%d %H:%M:%S')
    id_changed_enrollees = []
    try:
        changes_log = get_changes(connection_string, last_time_str)
    except (OperationalError, InterfaceError):
        print('Database connection error')  # noqa: F201
    else:
        curren_log = None
        for curren_log in changes_log:
            if curren_log.код_абитуриента not in id_changed_enrollees:
                id_changed_enrollees.append(curren_log.код_абитуриента)
        if curren_log:
            last_log.last_mmis_log_time = curren_log.дата.astimezone(pytz.timezone(TIME_ZONE))
            last_log.last_mmis_log_id = curren_log.Код
    return id_changed_enrollees, last_log


MAX_LOOP_TIME = 600


def process_update_enrollees():
    time_start = time.time()
    connection_string = create_connection_string()
    user_obj_hospital = Hospitals.objects.get(is_default=True)
    while time.time() - time_start < MAX_LOOP_TIME:
        ids_changed_enrollees, current_last_log = get_ids_changes_enrollees(connection_string)
        if not ids_changed_enrollees:
            pass
        else:
            enrollees_person_data, enrollees_grade, enrollees_application, enrollees_achievements = get_enrollees(connection_string, ids_changed_enrollees)
            enrollees_grade_data = {}
            for grade in enrollees_grade:
                if not enrollees_grade_data.get(grade.ID):
                    enrollees_grade_data[grade.ID] = [
                        {"Оценка": grade.Оценка, "Код_Испытания": grade.Код_Испытания, "Код": grade.Код, "Код_Заявления": grade.Код_Заявления, "Код_Дисциплины": grade.Код_Дисциплины}
                    ]
                else:
                    tmp_data = enrollees_grade_data[grade.ID]
                    tmp_data.append(
                        {"Оценка": grade.Оценка, "Код_Испытания": grade.Код_Испытания, "Код": grade.Код, "Код_Заявления": grade.Код_Заявления, "Код_Дисциплины": grade.Код_Дисциплины}
                    )
                    enrollees_grade_data[grade.ID] = tmp_data.copy()
            enrollees_application_data = {}
            for application in enrollees_application:
                if not enrollees_application_data.get(application.ID):
                    enrollees_application_data[application.ID] = [
                        {
                            "Код_Заявления": application.Код_Заявления,
                            "Основания": change_encoding_cp1251(application.Основания),
                            "Код_Специальности": application.Код_Специальности,
                            "НомерЛД": change_encoding_cp1251(application.НомерЛД),
                            "Шифр": change_encoding_cp1251(application.Шифр),
                            "Факультет": application.Факультет,
                            "Оригинал": application.Оригинал,
                            "Дата_Подачи": application.Дата_Подачи,
                            "Зачислен": application.Зачислен,
                            "ОтказалсяОтЗачисления": application.ОтказалсяОтЗачисления,
                            "КодФормы": application.КодФормы,
                            "Проверено": application.Проверено,
                        }
                    ]
                else:
                    tmp_data = enrollees_application_data.get(application.ID, [])
                    tmp_data.append(
                        {
                            "Код_Заявления": application.Код_Заявления,
                            "Основания": change_encoding_cp1251(application.Основания),
                            "Код_Специальности": application.Код_Специальности,
                            "НомерЛД": change_encoding_cp1251(application.НомерЛД),
                            "Шифр": change_encoding_cp1251(application.Шифр),
                            "Факультет": application.Факультет,
                            "Оригинал": application.Оригинал,
                            "Дата_Подачи": application.Дата_Подачи,
                            "Зачислен": application.Зачислен,
                            "ОтказалсяОтЗачисления": application.ОтказалсяОтЗачисления,
                            "КодФормы": application.КодФормы,
                            "Проверено": application.Проверено,
                        }
                    )
                    enrollees_application_data[application.ID] = tmp_data.copy()
            enrollees_achievements_data = {}
            for achievement in enrollees_achievements:
                if not enrollees_achievements_data.get(achievement.ID):
                    enrollees_achievements_data[achievement.ID] = [
                        {
                            "КодИД": achievement.КодИД,
                            "ДатаИД": achievement.ДатаИД,
                            "БаллИД": achievement.БаллИД,
                            "Код": achievement.Код,
                            "СерияИД": achievement.СерияИД,
                            "НомерИД": achievement.НомерИД,
                            "ОрганизацияИД": change_encoding_cp1251(achievement.ОрганизацияИД),
                            "Код_Заявления": achievement.Код_Заявления,
                        }
                    ]
                else:
                    tmp_data = enrollees_achievements_data.get(achievement.ID, [])
                    tmp_data.append(
                        {
                            "КодИД": achievement.КодИД,
                            "ДатаИД": achievement.ДатаИД,
                            "БаллИД": achievement.БаллИД,
                            "Код": achievement.Код,
                            "СерияИД": achievement.СерияИД,
                            "НомерИД": achievement.НомерИД,
                            "ОрганизацияИД": change_encoding_cp1251(achievement.ОрганизацияИД),
                            "Код_Заявления": achievement.Код_Заявления,
                        }
                    )
                    enrollees_achievements_data[achievement.ID] = tmp_data.copy()
            for person_data in enrollees_person_data:
                update_education_individual(
                    person_data,
                    user_obj_hospital,
                    enrollees_application_data.get(person_data.ID, []),
                    enrollees_grade_data.get(person_data.ID, []),
                    enrollees_achievements_data.get(person_data.ID, []),
                )
            if enrollees_person_data:
                current_last_log.save()
        time.sleep(10)


def process_start_update_enrollees():
    while True:
        process_update_enrollees()
