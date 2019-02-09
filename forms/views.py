from django.http import HttpResponse
from clients.models import Individual

from forms.forms_agreement import form_agree_hiv
from forms.forms_title_page import form_health_passport


def pdf(request):
    response = HttpResponse(content_type='application/pdf')
    t = request.GET.get("type")
    response['Content-Disposition'] = 'inline; filename="form-' + t + '.pdf"'
    i = Individual.objects.get(pk=request.GET.get('individual'))
    if t == '2':
        out_form = form_agree_hiv(i)
    elif t == '1':
        out_form = form_health_passport(i.fio(),i.bd())

    pdf = out_form

    response.write(pdf)

    return response
