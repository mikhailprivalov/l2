import os
import docx as my_docx
from django.http import HttpResponse
from django.utils.module_loading import import_string
from io import BytesIO
from datetime import datetime
from pdf2docx import Converter

from appconf.manager import SettingManager


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
    doc = None
    if pdf:
        buffer = BytesIO()
        buffer.write(pdf)
        buffer.seek(0)

        today = datetime.now()
        date_now1 = datetime.strftime(today, "%y%m%d%H%M%S%f")[:-3]
        date_now_str = str(date_now1)
        dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
        file_dir = os.path.join(dir_param, date_now_str + '_dir.pdf')

        save(buffer, filename=file_dir)
        docx_file = os.path.join(dir_param, date_now_str + '_dir.docx')
        cv = Converter(file_dir)
        cv.convert(docx_file, start=0, end=None)
        cv.close()
        os.remove(file_dir)
        doc = my_docx.Document(docx_file)
        os.remove(docx_file)
        buffer.close()

    response['Content-Disposition'] = 'attachment; filename="form-' + t + '.docx"'
    if doc:
        doc.save(response)

    return response


def save(form, filename: str):
    with open(filename, 'wb') as f:
        f.write(form.read())
