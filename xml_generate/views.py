import json
import os
from jinja2 import FileSystemLoader, Environment
from directions.models import Issledovaniya, DirectionDocument
from laboratory.settings import BASE_DIR, CPP_TEMPLATE_XML_DIRECTORY, MEDIA_ROOT
import shutil
from datetime import datetime


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
    iss.napravleniye.need_resend_cpp = True
    iss.napravleniye.save(update_fields=['need_resend_cpp'])
    shutil.rmtree(tmp_dir)
