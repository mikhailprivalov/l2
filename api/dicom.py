from orthanc_rest_client import Orthanc
from directions.models import Issledovaniya
from laboratory.settings import DICOM_SEARCH_TAGS, DICOM_SERVER
from checkdigit import isbn


def search_dicom_study(direction=None):
    #на входе направление тип integer
    if direction:
        dicom_study = None
        dicom_study = Issledovaniya.objects.values('study_instance_uid').filter(napravleniye=direction).first()
        if dicom_study and dicom_study['study_instance_uid']:
            return f'{DICOM_SERVER}/osimis-viewer/app/index.html?study={dicom_study["study_instance_uid"]}'
        else:
            num_dir = str(direction + 460000000000)
            res = isbn.isbn13calculate(num_dir)
            ean13_dir = num_dir + res
            str_dir = str(direction)

            orthanc = Orthanc(DICOM_SERVER)
            for tag in DICOM_SEARCH_TAGS:
                for dir in [ean13_dir, str_dir]:
                    query = {"Level": "Study", "Query": {"Modality": "*", "StudyDate": "*", tag: dir}}
                    dicom_study = orthanc.find(query)
                    if len(dicom_study) > 0:
                        Issledovaniya.objects.filter(napravleniye=direction).update(study_instance_uid=dicom_study[0])
                        return f'{DICOM_SERVER}/osimis-viewer/app/index.html?study={dicom_study[0]}'

    return None
