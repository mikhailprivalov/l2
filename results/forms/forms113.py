from directions.models import Issledovaniya, Napravleniya
from django.utils.module_loading import import_string


def form_01(direction: Napravleniya, iss: Issledovaniya, fwb, doc, leftnone, user=None, has_any_signature=None, request=None):
    """
    112.01 - Заключение из MedicalCertificate
    """
    form_result = import_string('medical_certificates.forms.forms380' + '.form_11')
    params = {"dir": direction.pk, "hospital": request.user.doctorprofile.hospital, "from_result_protocol": True}

    return form_result(params)
