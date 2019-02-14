import sys
from django.http import HttpResponse
from clients.models import Individual
from forms.models import FormsGroup, FormsList, FormsTemplate
from forms.forms_agreement import form_agree_hiv
from forms import forms_title_page
from forms.forms_title_page import form_health_passport
from forms.forms_route_sheet import form_route_sheet


def pdf(request):
    response = HttpResponse(content_type='application/pdf')
    t = request.GET.get("type")
    response['Content-Disposition'] = 'inline; filename="form-' + t + '.pdf"'
    i = Individual.objects.get(pk=request.GET.get('individual'))
    if t == '2':
        out_form = form_agree_hiv(i)
    elif t == '1':
        out_form = form_health_passport(i.fio(),i.bd())
    elif t == '3':
        out_form = form_route_sheet(t)

    pdf = out_form

    response.write(pdf)

#my testing get title_form by type
    form = "pers_data"
    thismodule = sys.modules[__name__]

    print(sys.modules[__name__])

    type_int = int(t)
    obj_form_title = FormsList.objects.filter(type_number=type_int)
    title_f = obj_form_title[0].title
    group_f = obj_form_title[0].form_group

    print(title_f)
    print(type(str_to_class(group_f.title)))

    print('forms_%s' % group_f)
    print(group_f.title)
    print('form_%s' % title_f)


    if hasattr(str_to_class(group_f.title), 'form_%s' % title_f):
        print("Yes it is")
    else:
        print("Bad, bad, bad")


    f = getattr(thismodule, 'form_%s' % obj_form_title[0].title)
    f(i.fio(),i.bd())


# end my test

    return response

def str_to_class(classname):
    return getattr(sys.modules[__name__], classname)

def form_personal_data():
    print("Это функция для печати Согласия о персональных данных")

 # thismodule = sys.modules[__name__]
 #    n = 0
 #    cntn = donepage.count()
 #    for d in donepage:
 #        n += 1
 #        iss = Issledovaniya.objects.filter(napravleniye=d)
 #        if not iss.exists():
 #            continue
 #        form = iss[0].research.direction_form
 #        if hasattr(thismodule, 'form%s' % form):
 #            f = getattr(thismodule, 'form%s' % form)
 #            f(c, d)