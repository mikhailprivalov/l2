from rest_framework.response import Response
from rest_framework.decorators import api_view

from api.models import Application
from contracts.models import Company

from integration_framework.admission_cert.sql_func import get_closed_case_by_company, directions_by_parent_cases_issledovaniye_only_research_id_final_report
from results.sql_func import get_expertis_results_by_issledovaniya


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
        if not app:
            token_is_not_valid = True
    except:
        token_is_not_valid = True

    if token_is_not_valid:
        return Response({"message": "token is not valid"})

    companies_id = tuple([i.id for i in app.companies.all()])
    closed_case_need_send = get_closed_case_by_company(companies_id)
    cases_iss = set([i.case_issledovaniye_id for i in closed_case_need_send])
    result_iss_id = directions_by_parent_cases_issledovaniye_only_research_id_final_report(tuple(cases_iss))
    direction_iss = {i.iss_id: {
        "dir": i.napravleniye_id,
        "patient_family":i.patient_family,
        "patient_name":i.patient_name,
        "patient_patronymic":i.patient_patronymic,
        "sex": i.sex,
        "patient_birthday": i.patient_birthday,
        "work_place_db_id": i.work_place_db_id
    } for i in result_iss_id}

    paraclinic_result = get_expertis_results_by_issledovaniya(tuple(direction_iss.keys()))
    final_value_result = {}
    for i in paraclinic_result:
        if not final_value_result.get(i.issledovaniye_id):
            final_value_result[i.issledovaniye_id] = {i.title: i.value}
        else:
            final_value_result[i.issledovaniye_id][i.title] = i.value
    response_result = []
    companies_obj = Company.objects.all()
    companies = {i.pk: {"title": i.title, "inn": i.inn} for i in companies_obj}
    for k, v in final_value_result.items():
        response_result.append(
            {
                "med_org": "ИГКБ №9",
                "family": direction_iss.get(k)["patient_family"],
                "name": direction_iss.get(k)["patient_name"],
                "name2": direction_iss.get(k)["patient_patronymic"],
                "bdate": direction_iss.get(k)["patient_birthday"],
                "snils": v.get("снилс"),
                "workplace": companies.get(direction_iss.get(k)["work_place_db_id"])["title"],
                "inn": companies.get(direction_iss.get(k)["work_place_db_id"])["inn"],
                "profid": direction_iss.get(k)["dir"],
                "proftype": v["Тип медосмотра"],
                "protocols": [
                    {
                        "protocol_date": "2025-03-14",
                        "protocolid": direction_iss.get(k)["dir"],
                        "treatcode": k,
                        "view": "Заключение",
                        "vred": v["Вредный производственный фактор или вид работы"].split(";"),
                        "group": v["Диспансерная группа"],
                        "conclusion": f"Медицинские противопоказания по приказу 29н {(v['Медицинские противопоказания к работе']).lower()}",
                        "contraindication": False if (v["Медицинские противопоказания к работе"]).lower() == "не выявлено" else True,
                        "doctor": "Проверочный Врач",
                        "reinspection": ""
                    }
                ]
            }
        )

    count = request.GET.get("count")
    view = request.GET.get("view")

    return Response({"result": {"count": count}, "view": view})
