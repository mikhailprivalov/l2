import datetime
import json
import os
from typing import List

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse

from api.extra_notification.sql_func import extra_notification_sql
from appconf.manager import SettingManager
from directions.models import Issledovaniya
from slog.models import Log
from clients.models import Card
from laboratory.utils import current_time, strfdatetime
from utils.data_verification import data_parse
from laboratory.settings import EXTRA_MASTER_RESEARCH_PK, EXTRA_SLAVE_RESEARCH_PK


@login_required
def search(request):
    request_data = json.loads(request.body)
    # status - 0 новые, 1-присвоенные номера от ЭпидЦентра, 2 - все
    status = int(request_data.get("status", 2))
    hospital = int(request_data.get("hospital", -1))
    date = request_data["date"]
    time_start = f'{date} {request_data.get("time_start", "00:00")}:00'
    time_end = f'{date} {request_data.get("time_end", "23:59")}:59:999999'
    datetime_start = datetime.datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
    datetime_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S:%f')

    if not request.user.doctorprofile.all_hospitals_users_control:
        hospital_id = request.user.doctorprofile.get_hospital_id() or -1
    else:
        hospital_id = -2

    result = extra_notification_sql(EXTRA_MASTER_RESEARCH_PK, EXTRA_SLAVE_RESEARCH_PK, datetime_start, datetime_end, hospital_id, status)

    return JsonResponse({})
