import socket
from functools import reduce

from orthanc_rest_client import Orthanc

from directions.models import Issledovaniya
from laboratory.settings import DICOM_SEARCH_TAGS, DICOM_SERVER, DICOM_PORT, DICOM_ADDRESS


def sum(x, y):
    return int(x) + int(y)


def check_sum_ean13(num):
    evensum = reduce(sum, num[-2::-2])
    oddsum = reduce(sum, num[-1::-2])
    return (10 - ((evensum + oddsum * 3) % 10)) % 10


def check_server_port(address, port):
    TCP_IP = address or '127.0.0.1'
    TCP_PORT = port or 4242
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    try:
        s.connect((TCP_IP, TCP_PORT))
    except socket.error:
        available = False
    else:
        available = True
    finally:
        s.close()

    return available


def search_dicom_study(direction=None):
    if direction:
        research_obj = Issledovaniya.objects.filter(napravleniye__pk=direction).first()
        if not research_obj.research.podrazdeleniye or not research_obj.research.podrazdeleniye.can_has_pacs:
            return ''
        dicom_study = Issledovaniya.objects.values('study_instance_uid').filter(napravleniye=direction).first()
        if dicom_study and dicom_study['study_instance_uid']:
            return f'{DICOM_SERVER}/osimis-viewer/app/index.html?study={dicom_study["study_instance_uid"]}'
        else:
            if not check_server_port(DICOM_ADDRESS, DICOM_PORT):
                return ''
            try:
                str_dir = str(direction)
                ean13_dir = str(direction + 460000000000)
                check_sum = check_sum_ean13(ean13_dir)
                ean13_dir = f'{ean13_dir}{check_sum}'

                orthanc = Orthanc(DICOM_SERVER)
                for tag in DICOM_SEARCH_TAGS:
                    for dir in [ean13_dir, str_dir]:
                        query = {"Level": "Study", "Query": {"Modality": "*", "StudyDate": "*", tag: dir}}
                        dicom_study = orthanc.find(query)
                        if len(dicom_study) > 0:
                            Issledovaniya.objects.filter(napravleniye=direction).update(study_instance_uid=dicom_study[0])
                            return f'{DICOM_SERVER}/osimis-viewer/app/index.html?study={dicom_study[0]}'
            except Exception as e:
                print(e)
    return ''
