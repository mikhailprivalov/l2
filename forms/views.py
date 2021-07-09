# import os
import json

from django.http import HttpResponse
from django.utils.module_loading import import_string
import datetime

# from io import BytesIO
# from datetime import datetime
# from pdf2docx import Converter
# from docx import Document
# import fitz
# from pdf2docx import Page
# from appconf.manager import SettingManager
from forms.sql_func import get_covid_to_json
from laboratory.settings import COVID_RESEARCHES_PK


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
    response.write(
        f(
            request_data={
                **dict(request.GET.items()),
                "user": request.user,
                "hospital": request.user.doctorprofile.get_hospital(),
            }
        )
    )
    return response


# def docx(request):
#     response = HttpResponse(content_type='application/application/vnd.openxmlformats-officedocument.wordprocessingml.document')
#     t = request.GET.get("type")
#     f = import_string('forms.forms' + t[0:3] + '.form_' + t[4:6])
#     pdf = f(
#         request_data={
#             **dict(request.GET.items()),
#             "user": request.user,
#             "hospital": request.user.doctorprofile.get_hospital(),
#         }
#     )
#
#     buffer = BytesIO()
#     buffer.write(pdf)
#     buffer.seek(0)
#
#     today = datetime.now()
#     date_now1 = datetime.strftime(today, "%y%m%d%H%M%S%f")[:-3]
#     date_now_str = str(date_now1)
#     dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
#     docx_file = os.path.join(dir_param, date_now_str + '_dir.docx')
#     cv = MyConverter(buffer)
#     cv.convert(docx_file, start=0, end=None)
#     cv.close()
#     doc = Document(docx_file)
#     os.remove(docx_file)
#     buffer.close()
#
#     response['Content-Disposition'] = 'attachment; filename="form-' + t + '.docx"'
#     doc.save(response)
#
#     return response


# def save(form, filename: str):
#     with open(filename, 'wb') as f:
#         f.write(form.read())
#
#
# class MyConverter(Converter):
#     def __init__(self, buffer):
#         self.filename_pdf = 'xx.pdf'
#         self._fitz_doc = fitz.Document(stream=buffer, filename=self.filename_pdf)
#         self._pages = [Page(fitz_page) for fitz_page in self._fitz_doc]


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
    request_data = {**dict(request.GET.items())}
    date = request_data["date"]
    time_start = f'{date} {request_data.get("time_start", "00:00")}:00'
    time_end = f'{date} {request_data.get("time_end", "23:59")}:59:999999'
    datetime_start = datetime.datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S')
    datetime_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S:%f')
    result = get_covid_to_json(COVID_RESEARCHES_PK, datetime_start, datetime_end)
    data_return = []
    for i in result:
        result_value = i.value_result
        if result_value == 'отрицательно':
            result_value = 0
        if result_value == 'положительно':
            result_value = 1
        enp = ""
        if i.oms_number:
            enp = i.oms_number
        snils_number = ""
        if i.snils_number:
            snils_number = i.oms_number

        passport_serial, passport_number = "", ""
        if i.passport_serial and i.passport_number:
            passport_serial = i.passport_serial
            passport_number = i.passport_number

        data_return.append({
                "order": {
                    "number": i.number_direction,
                    "depart": "100000",
                    "laboratoryName": i.laboratoryname,
                    "laboratoryOgrn": i.laboratoryogrn,
                    "name": i.title_org_initiator,
                    "ogrn": i.ogrn_org_initiator,
                    "orderDate": i.get_tubes,
                    "serv": [
                        {
                            "code": i.fsli,
                            "name": i.title,
                            "testSystem": "",
                            "biomaterDate": i.get_tubes,
                            "readyDate": i.date_confirm,
                            "result": result_value,
                            "type": 1,
                        }
                    ],
                    "patient": {
                        "surname": i.pfam,
                        "name": i.pname,
                        "patronymic": i.twoname,
                        "gender": 2,
                        "birthday":  i.birthday,
                        "phone": "",
                        "email": "",

                        "documentType": "ПаспортгражданинаРФ",
                        "documentNumber": passport_number,
                        "documentSerNumber": passport_serial,

                        "snils": snils_number,
                        "oms": enp,
                        "address": {
                            "regAddress": {
                                "town": "",
                                "house": "",
                                "region": "",
                                "building": "",
                                "district": "",
                                "appartament": "",
                                "streetName": "",
                            },
                            "factAddress": {
                                "town": "",
                                "house": "",
                                "region": "",
                                "building": "",
                                "district": "",
                                "appartament": "",
                                "streetName": ""
                            }
                        }
                    }
                }
            })
    response['Content-Disposition'] = "attachment; filename=\"covid.json\""
    response.write(json.dumps(data_return, ensure_ascii=False))
    return response
