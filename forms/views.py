# import os
import json
import os

from openpyxl import Workbook
from django.http import HttpResponse
from django.utils.module_loading import import_string
import datetime

from io import BytesIO
from pdf2docx import Converter
from docx import Document
from appconf.manager import SettingManager
from forms.sql_func import get_covid_to_json, get_extra_notification_data_for_pdf
from laboratory.settings import (
    COVID_RESEARCHES_PK,
    CENTRE_GIGIEN_EPIDEMIOLOGY,
    REGION,
    EXCLUDE_HOSP_SEND_EPGU,
    EXTRA_MASTER_RESEARCH_PK,
    EXTRA_SLAVE_RESEARCH_PK,
    DISABLED_AUTO_PRINT_DATE_IN_FORMS,
)
from utils.dates import normalize_date
from hospitals.models import Hospitals
from utils.xh import save_tmp_file


def pdf(request):
    """
    Get form's number (decimal type: 101.15 - where "101" is form's group and "15"-number itsels).
    Can't use 1,2,3,4,5,6,7,8,9 for number itsels - which stands after the point.
    Bacause in database field store in decimal format xxx.yy - two number after dot, and active status.
    Must use: 01,02,03-09,10,11,12-19,20,21,22-29,30,31.....
    :param request:
    :return:
    """
    response = HttpResponse(content_type='application/pdf')
    t = request.GET.get("type")
    response['Content-Disposition'] = 'inline; filename="form-' + t + '.pdf"'

    f = import_string('forms.forms' + t[0:3] + '.form_' + t[4:6])
    disable_date = False
    if 'form_' + t[4:6] in DISABLED_AUTO_PRINT_DATE_IN_FORMS:
        disable_date = True

    response.write(
        f(
            request_data={
                **dict(request.GET.items()),
                "user": request.user,
                "hospital": request.user.doctorprofile.get_hospital() if hasattr(request.user, "doctorprofile") else Hospitals.get_default_hospital(),
                "disable_date": disable_date,
            }
        )
    )
    return response


def docx(request):
    response = HttpResponse(content_type='application/application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    t = request.GET.get("type")
    f = import_string('forms.forms' + t[0:3] + '.form_' + t[4:6])
    pdf = f(
        request_data={
            **dict(request.GET.items()),
            "user": request.user,
            "hospital": request.user.doctorprofile.get_hospital(),
        }
    )

    buffer = BytesIO()
    buffer.write(pdf)
    buffer.seek(0)

    today = datetime.datetime.now()
    date_now1 = datetime.datetime.strftime(today, "%Y%m%d%H%M%S%f")[:-3]
    date_now_str = str(date_now1)
    dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
    docx_file = os.path.join(dir_param, date_now_str + '_dir.docx')
    file_dir = os.path.join(dir_param, date_now_str + '_dir.pdf')
    save_tmp_file(buffer, filename=file_dir)
    cv = Converter(file_dir)
    cv.convert(docx_file, start=0, end=None)
    cv.close()
    doc = Document(docx_file)
    os.remove(docx_file)
    buffer.close()

    response['Content-Disposition'] = 'attachment; filename="form-' + t + '.docx"'
    doc.save(response)

    return response


def xlsx(request):
    """Генерация XLSX"""

    response = HttpResponse(content_type='application/ms-excel')
    type_form = request.GET.get("type")
    response['Content-Disposition'] = 'attachment; filename="form-' + type_form + '.xlsx"'

    function = import_string('forms.xlsx.forms' + type_form[0:3] + '.form_' + type_form[4:6])
    xlsx_workbook: Workbook = function(
        request_data={
            **dict(request.GET.items()),
            "user": request.user,
            "hospital": request.user.doctorprofile.get_hospital() if hasattr(request.user, "doctorprofile") else Hospitals.get_default_hospital(),
        }
    )

    xlsx_workbook.save(response)
    return response


def extra_nofication(request):
    # Результат Экстренные извещения
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="extra_note.pdf"'

    f = import_string('forms.forms110.form_01')
    response.write(
        f(
            request_data={
                **dict(request.GET.items()),
            }
        )
    )
    return response


def covid_result(request):
    response = HttpResponse(content_type='application/json')
    if not request.user.doctorprofile.has_group('Заполнение экстренных извещений'):
        response.write(json.dumps({"error": "Access denied"}, ensure_ascii=False))
        return response

    request_data = {**dict(request.GET.items())}
    date = request_data["date"]
    time_start = f'{date} {request_data.get("time_start", "00:00")}:00'
    time_end = f'{date} {request_data.get("time_end", "23:59")}:59:999999'
    datetime_start = datetime.datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
    datetime_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S:%f')
    result = get_covid_to_json(COVID_RESEARCHES_PK, datetime_start, datetime_end)
    data_return = []
    count = 0
    for i in result:
        if i.hosp_id in EXCLUDE_HOSP_SEND_EPGU:
            continue
        if not i.value_result:
            continue
        result_value = i.value_result.lower()
        if result_value.find('отрицат') != -1:
            result_value = 0
        elif result_value.find('поло') != -1:
            result_value = 1
        enp = ""
        if i.oms_number:
            enp = i.oms_number
        snils_number = ""
        if i.snils_number:
            snils_number = i.snils_number

        passport_serial, passport_number = "", ""
        if i.passport_serial and i.passport_number:
            passport_serial = i.passport_serial
            passport_number = i.passport_number

        sex = None
        if i.psex == "ж":
            sex = 2
        elif i.psex == "м":
            sex = 1

        laboratory_ogrn = i.laboratoryogrn or ""
        laboratory_name = i.laboratoryname or ""
        get_tubes = i.get_tubes or i.date_confirm
        data_return.append(
            {
                "order": {
                    "number": str(i.number_direction),
                    "depart": CENTRE_GIGIEN_EPIDEMIOLOGY,
                    "laboratoryName": laboratory_name,
                    "laboratoryOgrn": laboratory_ogrn,
                    "name": i.title_org_initiator or laboratory_name,
                    "ogrn": i.ogrn_org_initiator or laboratory_ogrn,
                    "orderDate": get_tubes,
                    "serv": [
                        {
                            "code": i.fsli,
                            "name": i.title,
                            "testSystem": "",
                            "biomaterDate": get_tubes,
                            "readyDate": i.date_confirm,
                            "result": result_value,
                            "type": 1,
                        }
                    ],
                    "patient": {
                        "surname": i.pfam,
                        "name": i.pname,
                        "patronymic": i.twoname,
                        "gender": sex or "",
                        "birthday": i.birthday,
                        "phone": "",
                        "email": "",
                        "documentType": "Паспорт гражданина РФ",
                        "documentNumber": passport_number,
                        "documentSerNumber": passport_serial,
                        "snils": snils_number,
                        "oms": enp,
                        "address": {
                            "regAddress": {
                                "town": "",
                                "house": "",
                                "region": REGION,
                                "building": "",
                                "district": "",
                                "appartament": "",
                                "streetName": "",
                            },
                            "factAddress": {"town": "", "house": "", "region": REGION, "building": "", "district": "", "appartament": "", "streetName": ""},
                        },
                    },
                }
            }
        )
        count += 1
    response['Content-Disposition'] = f"attachment; filename=\"{date}-covid-{count}.json\""
    response.write(json.dumps(data_return, ensure_ascii=False))

    return response


def json_nofication(request):
    response = HttpResponse(content_type='application/json')
    if not request.user.doctorprofile.has_group('Заполнение экстренных извещений'):
        response.write(json.dumps({"error": "Access denied"}, ensure_ascii=False))
        return response

    request_data = {**dict(request.GET.items())}
    directions = [x for x in json.loads(request_data["pk"]) if x is not None]
    data_result = get_epid_data(directions, -1)
    response['Content-Disposition'] = "attachment; filename=\"json_nofication.json\""
    response.write(json.dumps(data_result, ensure_ascii=False))

    return response


def get_epid_data(directions, with_confirm):
    result = get_extra_notification_data_for_pdf(directions, EXTRA_MASTER_RESEARCH_PK, EXTRA_SLAVE_RESEARCH_PK, with_confirm)
    data = {}
    for i in result:
        if i.master_field == 1:
            master_value = normalize_date(i.master_value)
        else:
            master_value = i.master_value
        if data.get(i.slave_dir) is None:
            data[i.slave_dir] = {
                'master_dir': i.master_dir,
                'epid_title': i.epid_title,
                'epid_value': i.epid_value,
                'master_field_results': [{'master_field_title': i.master_field_title, 'master_value': master_value}],
            }
        else:
            temp_data = data.get(i.slave_dir)
            temp_data['master_field_results'].append({'master_field_title': i.master_field_title, 'master_value': master_value})

    return data


def generate_xml(request):
    return
