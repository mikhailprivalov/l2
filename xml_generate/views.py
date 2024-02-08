import json
import os
import uuid

from jinja2 import FileSystemLoader, Environment

from clients.models import HarmfulFactor
from directions.models import Issledovaniya, DirectionDocument
from laboratory.settings import BASE_DIR, CPP_TEMPLATE_XML_DIRECTORY, MEDIA_ROOT, CDA_TEMPLATE_XML_DIRECTORY
import shutil
from datetime import datetime


def gen_resul_cpp_file(iss: Issledovaniya, used_cpp_template_files, data):
    d = DirectionDocument.objects.filter(direction=iss.napravleniye, is_archive=False, file_type="cpp").first()
    if d:
        if d.file:
            d.file.delete()
        d.delete()
    tmp_dir = '/tmp/sample/'
    try:
        shutil.rmtree(tmp_dir)
    except:
        pass
    os.mkdir(tmp_dir)

    cpp_template_files = json.loads(used_cpp_template_files)
    file_loader = FileSystemLoader(os.path.join(BASE_DIR, 'xml_generate', CPP_TEMPLATE_XML_DIRECTORY))
    env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
    output_filename = f'{iss.napravleniye.pk}-{datetime.strftime(iss.napravleniye.last_confirmed_at, "%y%m%d%H%M%S%f")[:-3]}'
    patient_result = normilize_result_data(data.get("result"))
    patient_result["direction_number"] = iss.napravleniye_id
    data["result"] = patient_result
    for k, file_name in sorted(cpp_template_files.items()):
        template_file_name = f"{file_name.get('template')}"
        tm = env.get_template(template_file_name)
        msg = tm.render(data=data)

        if file_name.get('file_name'):
            xml_file_name = f"{file_name.get('file_name')}.xml"
        else:
            xml_file_name = file_name.get('template')
            xml_file_name = f"{xml_file_name}-{output_filename}.xml"

        with open(f'{tmp_dir}{xml_file_name}', 'w') as fp:
            fp.write(msg)
        data[file_name.get('template')] = xml_file_name

    zip_file_name = f"{iss.napravleniye.pk}-cpp"
    result = os.path.join(MEDIA_ROOT, 'directions', str(iss.doc_confirmation.hospital.code_tfoms), str(iss.napravleniye.pk), zip_file_name)
    shutil.make_archive(f"{result}", 'zip', tmp_dir)
    DirectionDocument.objects.create(direction=iss.napravleniye, last_confirmed_at=iss.napravleniye.last_confirmed_at, file_type="cpp", file=f"{result}.zip")
    iss.napravleniye.need_resend_cpp = True
    iss.napravleniye.save(update_fields=['need_resend_cpp'])
    shutil.rmtree(tmp_dir)


def normilize_result_data(results):
    dict_result = {}
    for i in results:
        if i.get("title") == "Дата осмотра":
            dict_result["Дата осмотра"] = i.get("value")

        elif i.get("title") == "Группы риска":
            tmp_json = json.loads(i["value"])
            dict_result["Группы риска"] = tmp_json["title"]

        elif i.get("title") == "Группы риска по SCORE":
            tmp_json = json.loads(i["value"])
            dict_result["Группы риска по SCORE"] = tmp_json["title"]

        elif i.get("title") == "Группа здоровья":
            tmp_json = json.loads(i["value"])
            dict_result["Группа здоровья"] = tmp_json["title"]

        elif i.get("title") == "Результат медицинского осмотра":
            tmp_json = json.loads(i["value"])
            dict_result["Результат медицинского осмотра"] = tmp_json["title"]

        elif i.get("title") == "Дата присвоения группы здоровья":
            dict_result["Дата присвоения группы здоровья"] = i.get("value")

        elif i.get("title") == "Номер справки":
            dict_result["Номер справки"] = i.get("value")

        elif i.get("title") == "Дата выдачи справки":
            dict_result["Дата выдачи справки"] = i.get("value")
        elif i.get("title") == "Вредные факторы":
            harmfull_factos = i.get("value").split(";")
            hf = HarmfulFactor.objects.filter(title__in=harmfull_factos)
            dict_result["Вредные факторы"] = [str(i.cpp_key) for i in hf]
        dict_result["uuid"] = str(uuid.uuid4())
    return dict_result


def gen_result_cda_files(template_file_name, data):
    file_loader = FileSystemLoader(os.path.join(BASE_DIR, 'xml_generate', CDA_TEMPLATE_XML_DIRECTORY))
    env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
    tm = env.get_template(template_file_name)
    return tm.render(data)
