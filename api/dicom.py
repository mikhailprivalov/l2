import logging
import socket
from functools import reduce
from directions.models import Issledovaniya, Napravleniya
from laboratory.settings import DICOM_SEARCH_TAGS, DICOM_SERVER, DICOM_SERVERS, DICOM_PORT, DICOM_ADDRESS, DICOM_SERVER_DELETE, ACSN_MODE, REMOTE_DICOM_SERVER, REMOTE_DICOM_PEER
import requests
import simplejson as json


logger = logging.getLogger(__name__)


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
            if len(DICOM_SERVERS) > 1:
                return check_dicom_study_instance_uid(DICOM_SERVERS, dicom_study['study_instance_uid'])
            else:
                return f"{DICOM_SERVER}/osimis-viewer/app/index.html?study={dicom_study['study_instance_uid']}"
        else:
            if not check_server_port(DICOM_ADDRESS, DICOM_PORT):
                return ''
            try:
                str_dir = str(direction)
                ean13_dir = str(direction + 460000000000)
                check_sum = check_sum_ean13(ean13_dir)
                ean13_dir = f'{ean13_dir}{check_sum}'

                dicom_study_link = find_image_firstly([ean13_dir, str_dir])
                if ACSN_MODE:
                    acsn = Issledovaniya.objects.values('acsn_id').filter(napravleniye_id=direction).first()
                    dicom_study_link = change_acsn(dicom_study_link, acsn['acsn_id'])

                if dicom_study_link:
                    Issledovaniya.objects.filter(napravleniye_id=direction).update(study_instance_uid=dicom_study_link[0], study_instance_uid_tag=dicom_study_link[1])
                    try:
                        d: Napravleniya = Napravleniya.objects.filter(pk=direction).first()

                        if d:
                            d.send_task_result()
                    except Exception as e:
                        print('FAIL send_task_result')  # noqa: T001
                        print(e)  # noqa: T001

                    return f'{DICOM_SERVER}/osimis-viewer/app/index.html?study={dicom_study_link[0]}'

            except Exception as e:
                print(e)  # noqa: T001
    return ''


def find_image_firstly(data_direction):
    for tag in DICOM_SEARCH_TAGS:
        for dir in data_direction:
            data = {'Level': 'Study', 'Query': {tag: dir}, "Expand": True}
            if len(DICOM_SERVERS) > 1:
                is_dicom_study = check_dicom_study(DICOM_SERVERS, data)
                if is_dicom_study.get("dicom"):
                    return is_dicom_study.get("dicom")
            else:
                is_dicom_study = check_dicom_study([DICOM_SERVER], data)
                if is_dicom_study.get("dicom"):
                    return is_dicom_study.get("dicom")
    return None


def change_acsn(link_study, accession_number):
    data_replace = {"Replace": {"AccessionNumber": accession_number}}
    dicom_study = requests.post(f'{DICOM_SERVER}/studies/{link_study}/modify', data=json.dumps(data_replace))
    if dicom_study and dicom_study.json()['ID']:
        requests.delete(f'{DICOM_SERVER_DELETE}/studies/{link_study}')
        link_study = dicom_study.json()['ID']
    if REMOTE_DICOM_SERVER:
        requests.post(f'{REMOTE_DICOM_SERVER}/peers/{REMOTE_DICOM_PEER}/store', data=link_study)

    return link_study


def check_dicom_study(servers_addr, data):
    for server_addr in servers_addr:
        try:
            dicom_study = requests.post(f'{server_addr}/tools/find', data=json.dumps(data))
            result = dicom_study.json()
            if len(result) > 0:
                return {"dicom": (result[0]["ID"], result[0]["MainDicomTags"]["StudyInstanceUID"]), "server": server_addr}
        except Exception as e:
            logger.error(e)
    return {}


def check_dicom_study_instance_uid(servers_addr, data):
    for server_addr in servers_addr:
        try:
            dicom_study = requests.get(f'{server_addr}/studies/{data}')
            if dicom_study and len(dicom_study.json()) > 0:
                return f'{server_addr}/osimis-viewer/app/index.html?study={data}'
        except Exception as e:
            logger.error(e)
    return ''
