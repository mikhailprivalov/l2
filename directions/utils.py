from sys import stdout
from dateutil.relativedelta import relativedelta
import simplejson as json

from brokers_queue.rmq.publisher import broker_publish_msg
from directions.sql_func import get_directions_for_send_ecp_by_researches, get_directions_for_send_ecp_by_dirs, get_directions_for_send_rmq_by_dirs, get_directions_for_send_rmq_by_researches
from laboratory.settings import REMD_ONLY_RESEARCH, RMQ_RESEARCH_SEND
from laboratory.utils import current_time
from api.dicom import check_server_port
from appconf.manager import SettingManager
from directions.models import Napravleniya, DirectionParamsResult
from l2vi.integration import send_gistology_direction_to_ecp
import time


def gistology_result_send(dirs=''):
    base = SettingManager.get_api_ecp_base_url()
    if base != 'empty':
        available = check_server_port(base.split(":")[1].replace("//", ""), int(base.split(":")[2]))
        if not available:
            stdout.write("error Cервер отправки в ЕЦП не доступен")
    current_time_ecp_upload = SettingManager.rmis_upload_minutes_interval()
    date_start = current_time(only_date=False) + relativedelta(hours=-200)
    date_start = date_start.strftime('%Y%m%d %H:%M:%S')

    date_end = current_time(only_date=False) + relativedelta(minutes=-current_time_ecp_upload)
    date_end = date_end.strftime('%Y%m%d %H:%M:%S')
    if len(dirs) > 0:
        dirs = dirs.split(",")
        dirs = [int(i) for i in dirs]
        d_qs = get_directions_for_send_ecp_by_dirs(tuple(REMD_ONLY_RESEARCH), tuple(dirs))
    else:
        d_qs = get_directions_for_send_ecp_by_researches(tuple(REMD_ONLY_RESEARCH), date_start, date_end)
    directions = [i.napravleniye_id for i in d_qs]
    dir_params = DirectionParamsResult.objects.filter(napravleniye_id__in=directions)
    result_params = {}
    for i in dir_params:
        if i.title == "Маркировка материала":
            try:
                marking_biopsy = json.loads(i.value)
                marking_biopsy_local_id = marking_biopsy['rows'][0][1]
                marking_biopsy_local_id = marking_biopsy_local_id.split("/")
            except:
                marking_biopsy_local_id = []
            if len(marking_biopsy_local_id) < 2:
                continue
            result_params[i.napravleniye_id] = marking_biopsy_local_id[1]
    directions_iss = [
        {
            "directionId": d.napravleniye_id,
            "issId": d.iss_id,
            "dateRmis": d.rmis_direction_date,
            "rmis_number": d.rmis_number,
            "markBiopsy": result_params.get(d.napravleniye_id),
            "rmis_login": d.rmis_login,
            "rmis_password": d.rmis_password,
        }
        for d in d_qs
        if result_params.get(d.napravleniye_id) and d.rmis_login
    ]
    stdout.write(f"{directions_iss}")
    res = send_gistology_direction_to_ecp(directions_iss)
    stdout.write(f"{res}\n")
    count = 0
    result_send = {}
    for i in res.get('result'):
        result_send[i.get('directionId')] = i.get('success')

    for n in Napravleniya.objects.filter(pk__in=directions):
        if not result_send.get(n.pk):
            msg = f"{n.pk}- Не успех"
            stdout.write(msg)
            continue
        elif result_send.get(n.pk):
            n.result_rmis_send = True
            n.save()
            count += 1
            msg = f"{n.pk}- Ууспех"
            stdout.write(msg)
        else:
            msg = f"{n.pk}- Не успех"
            stdout.write(msg)

    stdout.write(f"{count}\n")
    return True


def direction_result_send_rmq(dirs=''):
    current_time_ecp_upload = SettingManager.rmis_upload_minutes_interval()
    date_start = current_time(only_date=False) + relativedelta(hours=-100)
    date_start = date_start.strftime('%Y%m%d %H:%M:%S')
    date_end = current_time(only_date=False) + relativedelta(minutes=-current_time_ecp_upload)
    date_end = date_end.strftime('%Y%m%d %H:%M:%S')
    if len(dirs) > 0:
        dirs = dirs.split(",")
        dirs = [int(i) for i in dirs]
        d_qs = get_directions_for_send_rmq_by_dirs(tuple(RMQ_RESEARCH_SEND), tuple(dirs))
    else:
        d_qs = get_directions_for_send_rmq_by_researches(tuple(RMQ_RESEARCH_SEND), date_start, date_end)
    directions_id = [i.napravleniye_id for i in d_qs]
    directions_obj = Napravleniya.objects.filter(pk__in=directions_id)
    for i in directions_obj:
        broker_publish_msg(i.pk)
        i.need_resend_ecp = True
        i.save()

    return True


def process_direction_send_rmq_start():
    stdout.write("Starting send direction to rmq")
    while True:
        result = direction_result_send_rmq()
        if result:
            time.sleep(600)


def process_gistology_result_upload_start():
    stdout.write("Starting send gistology result")
    while True:
        result = gistology_result_send()
        if result:
            time.sleep(600)
