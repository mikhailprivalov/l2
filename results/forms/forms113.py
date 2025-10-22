from directions.models import Issledovaniya, Napravleniya
from django.utils.module_loading import import_string

from hospitals.models import Hospitals


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, has_any_signature=None, request=None):
    """
    112.01 - Заключение из MedicalCertificate
    """
    form_result = import_string('medical_certificates.forms.forms380' + '.form_11')
    try:
        hospital = request.user.doctorprofile.hospital
    except:
        hospital = Hospitals.objects.filter(is_default=True).first()
    params = {"dir": direction.pk, "hospital": hospital, "from_result_protocol": True}

    return form_result(params)
