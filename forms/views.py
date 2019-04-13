from django.http import HttpResponse
from django.utils.module_loading import import_string


def pdf(request):
    """
    Get form's number (decimal type: 101.15 - where "101" is form's group and "15"-number itsels).
    Can't use 1,2,3,4,5,6,7,8,9 for number itsels - which stands after the point.
    Bacause in database field store in decimal format xxx.yy - two number after dot, and active status.
    Must use: 01,02,03-09,10,11,12-19,20,21,22-29,30,31.....
    :param request:
    :return:
    """
    response = HttpResponse(content_type='application/pdf')
    t = request.GET.get("type")
    response['Content-Disposition'] = 'inline; filename="form-' + t + '.pdf"'

    f = import_string('forms.forms' + t[0:3] + '.form_' + t[4:6])
    response.write(f(request_data={**dict(request.GET.items()), "user": request.user}))
    return response
