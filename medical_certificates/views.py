from django.http import HttpResponse
from django.utils.module_loading import import_string

from hospitals.models import Hospitals


def pdf(request):
    """
    :param request:
    :return:
    """
    response = HttpResponse(content_type='application/pdf')
    t = request.GET.get("type")
    response['Content-Disposition'] = 'inline; filename="form-' + t + '.pdf"'
    f = import_string('medical_certificates.forms.forms' + t[0:3] + '.form_' + t[3:5])
    response.write(
        f(
            request_data={
                **dict(request.GET.items()),
                "user": request.user,
                "hospital": request.user.doctorprofile.get_hospital() if hasattr(request.user, "doctorprofile") else Hospitals.get_default_hospital(),
            }
        )
    )
    return response
