import os
from jinja2 import FileSystemLoader, Environment
from laboratory.settings import BASE_DIR
import shutil


def gen_resul_cpp():
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


def gen_resul_cpp2():
    str_addr = "templates/cpp/"
    result_file_name= "cpp_result.xml"
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
    str_addr = f"{BASE_DIR}/xml_generate/{str_addr}"
    file_loader = FileSystemLoader(str_addr)
    env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
    tm = env.get_template(result_file_name)
    msg = tm.render(data=data)
    print(msg)
    tmp_dir = '/tmp/sample'
    os.mkdir(tmp_dir)
    with open(f'{tmp_dir}/result11.xml', 'w') as fp:
        fp.write(msg)
    with open(f'{tmp_dir}/result22.xml', 'w') as fp:
        fp.write(msg)

    output_filename = '/tmp/my-zip'
    shutil.make_archive(output_filename, 'zip', tmp_dir)
