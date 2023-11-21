from api.directions.sql_func import get_lab_podr
from appconf.manager import SettingManager
from laboratory.settings import QRCODE_OFFSET_SIZE, LEFT_QRCODE_OFFSET_SIZE
from utils.flowable import QrCodeSite
import uuid
import os.path
from io import BytesIO
from pdfrw import PdfReader, PdfWriter
from django.core.cache import cache
import hashlib


def fix(s: str):
    return s.replace('<br>', '<br/>')


SQUARE_BRACKETS_WEIGHTS = {'[': -1, ']': 1}


def check_valid_square_brackets(v: str):
    count = 0
    for s in v:
        if s in SQUARE_BRACKETS_WEIGHTS:
            count += SQUARE_BRACKETS_WEIGHTS[s]
            if count > 0:
                return False
    return count == 0


def check_number_is_valid(s):
    s = str(s)
    if s.isdigit():
        return True
    return check_float_is_valid(s)


def check_float_is_valid(val):
    try:
        float(val)
        return True
    except ValueError:
        return False


def get_hospitals_podrazdeleniya(hospital):
    from podrazdeleniya.models import Podrazdeleniya
    podrazdeleniya = Podrazdeleniya.objects.values('pk', 'short_title', 'title').filter(p_type=7, hide=False, hospital_id=hospital).order_by('title')
    return [{"id": x["pk"], "label": x['short_title'] or x['title']} for x in podrazdeleniya]


def get_all_hospitals():
    from hospitals.models import Hospitals
    hospitals_data = Hospitals.objects.values('pk', 'short_title', 'title').all().exclude(hide=True).order_by('title')
    return [{"id": x["pk"], "label": x['short_title'] or x['title']} for x in hospitals_data]


def short_fio_dots(fio):
    fio_list = fio.split(' ')
    f = fio_list[0]
    n = fio_list[1][0:1] + '.'
    p = fio_list[2][0:1] + '.' if len(fio_list) > 2 else ''
    npf = n + ' ' + p + ' ' + f

    return npf


def check_type_research(pk):
    from directions.models import Issledovaniya
    is_obj = Issledovaniya.objects.filter(napravleniye_id=pk)
    lab_podr = get_lab_podr()
    lab_podr = [i[0] for i in lab_podr]
    for k in is_obj:
        research = k.research
        if research.is_form or research.is_stom or research.is_doc_refferal or research.is_gistology or research.is_extract:
            return "is_refferal"
        if research.is_paraclinic:
            return "is_paraclinic"
        if research.podrazdeleniye and research.podrazdeleniye.pk in lab_podr:
            return "is_lab"
    return "error"


def save_tmp_file(form, filename: str):
    with open(filename, 'wb') as f:
        f.write(form.read())


def translation_number_from_decimal(current_num):
    data = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "А", "Б", "В", "Г", "Д", "Е", "Ж", "К", "Л", "М", "Н", "П", "Р", "С", "Т", "Ф", "Х", "Ц", "Ч", "Ш", "Э"]
    s = ''
    base = len(data)
    while current_num > 0:
        symbol = data[current_num % base]
        s = symbol + s
        current_num = current_num // base
    return s


def show_qr_lk_address(fwb, leftnone=False):
    lk_address = SettingManager.get("lk_address", default='', default_type='s')
    if lk_address:
        if leftnone:
            qr_code_param = LEFT_QRCODE_OFFSET_SIZE
        else:
            qr_code_param = QRCODE_OFFSET_SIZE
        fwb.append(QrCodeSite(lk_address, qr_code_param))
    return fwb


def replace_values(key):
    replace_data = {"code": "Код МКБ10", "title": "", "id": ""}
    return replace_data.get(key, "")


def simple_join_two_pdf_files(inputs):
    pdf_all = BytesIO()
    writer = PdfWriter()
    dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
    for inpfn in inputs:
        writer.addpages(PdfReader(os.path.join(dir_param, inpfn)).pages)
    writer.write(pdf_all)
    pdf_out = pdf_all.getvalue()
    pdf_all.close()

    for i in inputs:
        os.remove(os.path.join(dir_param, i))
    return pdf_out


def simple_save_pdf_file(fc):
    fc_buf = BytesIO()
    fc_buf.write(fc)
    fc_buf.seek(0)
    dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
    name = str(uuid.uuid4()) + '_buffer.pdf'
    file_buffer1 = os.path.join(dir_param, name)
    save_tmp_file(fc_buf, filename=file_buffer1)
    return name


def correspondence_set_file_hash(title_name):
    k = hashlib.sha1(title_name.encode('utf-8')).hexdigest()
    cache.set(k, title_name, 60 * 1)
    return k


def correspondence_get_file_hash(k):
    return cache.get(k)
