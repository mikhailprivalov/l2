from rest_framework.response import Response
from rest_framework.decorators import api_view

from api.models import Application

from integration_framework.admission_cert.sql_func import get_closed_case_by_company
from statistic.forms.forms100_sql_func import directions_by_parent_cases_issledovaniye


@api_view(['GET'])
def get_med_protocols(request):
    token = request.META.get("HTTP_AUTHORIZATION")
    token = token.replace("Bearer ", "")
    if not token:
        return Response({"message": "token is empty"})
    token_is_not_valid = False
    app = None
    try:
        app = Application.objects.filter(active=True, key=token).first()
        print(app)
        if not app:
            token_is_not_valid = True
    except:
        token_is_not_valid = True

    if token_is_not_valid:
        return Response({"message": "token is not valid"})

    companies_id = tuple([i.id for i in app.companies.all()])
    closed_case_need_send = get_closed_case_by_company(companies_id)
    cases_iss = set([i.case_issledovaniye_id for i in closed_case_need_send])
    result_iss_id = directions_by_parent_cases_issledovaniye(tuple(cases_iss))
    count = request.GET.get("count")
    view = request.GET.get("view")

    return Response({"result": {"count": count}, "view": view})
