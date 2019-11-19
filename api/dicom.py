from orthanc_rest_client import Orthanc
from directions.models import Issledovaniya
from laboratory.settings import DICOM_SEARCH_TAGS, DICOM_SERVER
from functools import reduce
import urllib3.request as u


def sum(x, y):
    return int(x) + int(y)

def check_sum_ean13(num):
    evensum = reduce(sum, num[-2::-2])
    oddsum = reduce(sum, num[-1::-2])
    return (10 - ((evensum + oddsum * 3) % 10)) % 10

def search_dicom_study(direction=None):
    #на входе направление тип integer
    if direction:
        dicom_study = None
        dicom_study = Issledovaniya.objects.values('study_instance_uid').filter(napravleniye=direction).first()
        if dicom_study and dicom_study['study_instance_uid']:
            return f'{DICOM_SERVER}/osimis-viewer/app/index.html?study={dicom_study["study_instance_uid"]}'
        else:
            try:
                u.urlopen(DICOM_SERVER)
            except:
                return ''

            str_dir = str(direction)
            ean13_dir = str(direction + 460000000000)
            check_sum = check_sum_ean13(ean13_dir)
            ean13_dir = f'{ean13_dir}{check_sum}'

            orthanc = Orthanc(DICOM_SERVER)
            for tag in DICOM_SEARCH_TAGS:
                for dir in [ean13_dir, str_dir]:
                    query = {"Level": "Study", "Query": {"Modality": "*", "StudyDate": "*", tag: dir}}
                    dicom_study = orthanc.find(query)
                    print(dicom_study)
                    if len(dicom_study) > 0:
                        Issledovaniya.objects.filter(napravleniye=direction).update(study_instance_uid=dicom_study[0])
                        return f'{DICOM_SERVER}/osimis-viewer/app/index.html?study={dicom_study[0]}'

    return ''
