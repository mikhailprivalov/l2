import json
import os

from django.core.files.base import ContentFile
from jinja2 import FileSystemLoader, Environment

from directions.models import Issledovaniya, DirectionDocument
from laboratory.settings import BASE_DIR, CPP_TEMPLATE_XML_DIRECTORY, MEDIA_ROOT
import shutil
from datetime import datetime


def gen_result_cpp():
    data = {
        "PMOUUID": "121212",
        "EmployeeUUID": "1212",
        "PositionUUID": "1212",
        "SubdivisionUUID": "1212",
        "ContractUUID": "12121",
        "PMONumber": "1212",
        "PMODate": "01.10.2023",
        "PMORestrictions": "нет",
        "PMOResult": "допущен",
        "RiskGroup": "Группа1",
        "PMORecommendations": "Группа2",
        "DateGroupHealthDateGroupHealth": "01.12.2023",
        "GroupHealth": "Группа23",
        "FactorUUID": ["UUID-1111", "UUID-2222", "UUID-33333", "UUID-4444"],
        "CertificateDate": "10.12.2023",
    }

    file_loader = FileSystemLoader(os.path.join(BASE_DIR, 'xml_generate', 'templates'))
    env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
    tm = env.get_template('cpp_result.xml')
    msg = tm.render(data=data)
    print(msg)
    with open('/tmp/result11.xml', 'w') as fp:
        fp.write(msg)


def gen_resul_cpp_file_1(iss: Issledovaniya, used_cpp_template_files, data):
    print(data)
    # print(used_cpp_template_files)
    cpp_template_files = json.loads(used_cpp_template_files)
    tmp_dir = '/tmp/sample'
    # for k, file_name in sorted(cpp_template_files.items()):
    #     result_file_name = f"{file_name}.xml"
    data = {
        "PMOUUID": "121212",
        "EmployeeUUID": "1212",
        "ContractUUID": "12121",
        "PMONumber": "1212",
        "PMODate": "01.10.2023",
        "PMORestrictions": "нет",
        "PMOResult": "допущен",
        "RiskGroup": "Группа1",
        "PMORecommendations": "Группа2",
        "DateGroupHealthDateGroupHealth": "01.12.2023",
        "GroupHealth": "Группа23",
        "FactorUUID": ["UUID-1111", "UUID-2222", "UUID-33333", "UUID-4444"],
        "CertificateDate": "10.12.2023",
    }
    # str_addr = f"{BASE_DIR}/xml_generate/{CPP_TEMPLATE_XML}"
    # file_loader = FileSystemLoader(str_addr)
    # env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
    # tm = env.get_template(result_file_name)
    # msg = tm.render(data=data)
    # os.mkdir(tmp_dir)
    # with open(f'{tmp_dir}/{result_file_name}', 'w') as fp:
    #     fp.write(msg)
    os.mkdir(tmp_dir)
    output_filename = f'{iss.napravleniye.pk}-{iss.napravleniye.last_confirmed_at}'
    shutil.make_archive(output_filename, 'zip', tmp_dir)
    f = open(f"{tmp_dir}/{output_filename}.zip")
    file = ContentFile(f.read())
    d = DirectionDocument.objects.create(direction=iss.napravleniye, last_confirmed_at=iss.napravleniye.last_confirmed_at, file_type="cpp")
    d.file.save(f"{tmp_dir}/{output_filename}.zip", file)
    f.close()
    shutil.rmtree(tmp_dir)


def gen_resul_cpp_file_2(iss: Issledovaniya, used_cpp_template_files, data):
    print(data)
    d = DirectionDocument.objects.filter(direction=iss.napravleniye, is_archive=False, file_type="cpp").first()
    d.file.delete()
    d.delete()
    tmp_dir = '/tmp/sample/'

    try:
        shutil.rmtree(tmp_dir)
    except:
        pass
    os.mkdir(tmp_dir)

    # tmp_dir = '/tmp/sample'
    data = {
        "PMOUUID": "121212",
        "EmployeeUUID": "1212",
        "PositionUUID": "1212",
        "SubdivisionUUID": "1212",
        "ContractUUID": "12121",
        "PMONumber": "1212",
        "PMODate": "01.10.2023",
        "PMORestrictions": "нет",
        "PMOResult": "допущен",
        "RiskGroup": "Группа1",
        "PMORecommendations": "Группа2",
        "DateGroupHealthDateGroupHealth": "01.12.2023",
        "GroupHealth": "Группа23",
        "FactorUUID": ["UUID-1111", "UUID-2222", "UUID-33333", "UUID-4444"],
        "CertificateDate": "10.12.2023",
    }

    file_loader = FileSystemLoader(os.path.join(BASE_DIR, 'xml_generate', 'templates', 'cpp'))
    env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
    tm = env.get_template('cpp_result.xml')
    msg = tm.render(data=data)
    print(msg)
    output_filename = f'{iss.napravleniye.pk}-{datetime.strftime(iss.napravleniye.last_confirmed_at, "%y%m%d%H%M%S%f")[:-3]}'
    # with open('/tmp/result11.xml', 'w') as fp:
    with open(f'{tmp_dir}{output_filename}.xml', 'w') as fp:
        fp.write(msg)
    with open(f'{tmp_dir}{output_filename}_2.xml', 'w') as fp:
        fp.write(msg)
        # str_addr = f"{BASE_DIR}/xml_generate/{CPP_TEMPLATE_XML_DIRECTORY}"
        # file_loader = FileSystemLoader(str_addr)
        # env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
        # tm = env.get_template(result_file_name)
        # msg = tm.render(data=data)
        # os.mkdir(tmp_dir)
        # with open(f'{tmp_dir}/{result_file_name}', 'w') as fp:
        #     fp.write(msg)

    result = os.path.join(MEDIA_ROOT, 'directions', str(iss.doc_confirmation.hospital.code_tfoms), str(iss.napravleniye.pk), "Выгрузка")
    shutil.make_archive(f"{result}", 'zip', tmp_dir)
    DirectionDocument.objects.create(direction=iss.napravleniye, last_confirmed_at=iss.napravleniye.last_confirmed_at, file_type="cpp", file=f"{result}.zip")
    shutil.rmtree(tmp_dir)


def gen_resul_cpp_file(iss: Issledovaniya, used_cpp_template_files, data):
    d = DirectionDocument.objects.filter(direction=iss.napravleniye, is_archive=False, file_type="cpp").first()
    d.file.delete()
    d.delete()
    tmp_dir = '/tmp/sample/'

    try:
        shutil.rmtree(tmp_dir)
    except:
        pass
    os.mkdir(tmp_dir)

    data = {
        "PMOUUID": "121212",
        "EmployeeUUID": "1212",
        "PositionUUID": "1212",
        "SubdivisionUUID": "1212",
        "ContractUUID": "12121",
        "PMONumber": "1212",
        "PMODate": "01.10.2023",
        "PMORestrictions": "нет",
        "PMOResult": "допущен",
        "RiskGroup": "Группа1",
        "PMORecommendations": "Группа2",
        "DateGroupHealthDateGroupHealth": "01.12.2023",
        "GroupHealth": "Группа23",
        "FactorUUID": ["UUID-1111", "UUID-2222", "UUID-33333", "UUID-4444"],
        "CertificateDate": "10.12.2023",
    }
    cpp_template_files = json.loads(used_cpp_template_files)
    file_loader = FileSystemLoader(os.path.join(BASE_DIR, 'xml_generate', CPP_TEMPLATE_XML_DIRECTORY))
    env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
    output_filename = f'{iss.napravleniye.pk}-{datetime.strftime(iss.napravleniye.last_confirmed_at, "%y%m%d%H%M%S%f")[:-3]}'
    for k, file_name in sorted(cpp_template_files.items()):
        template_file_name = f"{file_name.get('template')}.xml"
        tm = env.get_template(template_file_name)
        msg = tm.render(data=data)
        print(msg)

    # with open('/tmp/result11.xml', 'w') as fp:
        if file_name.get('file_name'):
            xml_file_name = file_name.get('file_name')
        else:
            xml_file_name = file_name.get('template')
        with open(f'{tmp_dir}{xml_file_name}-{output_filename}.xml', 'w') as fp:
            fp.write(msg)
        with open(f'{tmp_dir}{xml_file_name}-{output_filename}_2.xml', 'w') as fp:
            fp.write(msg)

    zip_file_name = f"{iss.napravleniye.pk}-cpp"
    result = os.path.join(MEDIA_ROOT, 'directions', str(iss.doc_confirmation.hospital.code_tfoms), str(iss.napravleniye.pk), zip_file_name)
    shutil.make_archive(f"{result}", 'zip', tmp_dir)
    DirectionDocument.objects.create(direction=iss.napravleniye, last_confirmed_at=iss.napravleniye.last_confirmed_at, file_type="cpp", file=f"{result}.zip")
    shutil.rmtree(tmp_dir)
