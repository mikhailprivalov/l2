from rest_framework.response import Response
from rest_framework.decorators import api_view
from api.models import Application
from appconf.manager import SettingManager
from contracts.models import Company
from directions.models import Napravleniya
from hospitals.models import Hospitals
from integration_framework.admission_cert.sql_func import get_closed_case_by_company, directions_by_parent_cases_issledovaniye_only_research_id_final_report
from integration_framework.common_func import direction_pdf_result
from results.sql_func import get_expertis_results_by_issledovaniya
import simplejson as json
from slog.models import Log


@api_view(['GET'])
def get_med_protocols(request):
    token = request.META.get("HTTP_AUTHORIZATION")
    token = token.replace("Bearer ", "")
    if not token:
        return Response({"result": "error", "comment": "token is empty"})
    token_is_not_valid = False
    app = None
    try:
        app = Application.objects.filter(active=True, key=token).first()
        if not app:
            token_is_not_valid = True
    except:
        token_is_not_valid = True

    if token_is_not_valid:
        return Response({"result": "error", "comment": "token is not valid"})

    limit = int(request.GET.get("count", 500))

    companies_id = tuple([i.id for i in app.companies.all()])
    closed_case_need_send = get_closed_case_by_company(companies_id, limit)
    cases_iss = set([i.case_issledovaniye_id for i in closed_case_need_send])
    try:
        result_iss_id = directions_by_parent_cases_issledovaniye_only_research_id_final_report(tuple(cases_iss))
        if not result_iss_id:
            return Response({"result": "None", "comment": "No new results"})
    except:
        return Response({"result": "None", "comment": "No new results"})

    direction_iss = {
        i.iss_id: {
            "dir": i.napravleniye_id,
            "patient_family": i.patient_family,
            "patient_name": i.patient_name,
            "patient_patronymic": i.patient_patronymic,
            "sex": i.sex,
            "patient_birthday": i.patient_birthday,
            "work_place_db_id": i.work_place_db_id,
            "doctor": f"{i.doc_family} {i.doc_name} {i.doc_patronymic}",
            "date_confirm": i.date_confirm,
        }
        for i in result_iss_id
    }

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
    hospital = Hospitals.objects.filter(is_default=True).first()
    for k, v in final_value_result.items():
        vred = v["Вредный производственный фактор или вид работы"].split(";")
        vred = [i for i in vred]
        response_result.append(
            {
                "med_org": hospital.title,
                "family": direction_iss.get(k)["patient_family"],
                "name": direction_iss.get(k)["patient_name"],
                "name2": direction_iss.get(k)["patient_patronymic"],
                "bdate": direction_iss.get(k)["patient_birthday"],
                "snils": v.get("снилс", ""),
                "workplace": companies.get(direction_iss.get(k)["work_place_db_id"])["title"],
                "inn": companies.get(direction_iss.get(k)["work_place_db_id"])["inn"],
                "profid": direction_iss.get(k)["dir"],
                "proftype": v["Тип медосмотра"],
                "protocols": [
                    {
                        "protocol_date": direction_iss.get(k)["date_confirm"],
                        "protocolid": direction_iss.get(k)["dir"],
                        "treatcode": k,
                        "view": "Заключение",
                        "vred": vred,
                        "group": v["Диспансерная группа"],
                        "conclusion": f"Медицинские противопоказания по приказу 29н {(v['Медицинские противопоказания к работе']).lower()}",
                        "contraindication": False if (v["Медицинские противопоказания к работе"]).lower() == "не выявлено" else True,
                        "doctor": direction_iss.get(k)["doctor"],
                        "reinspection": "",
                    }
                ],
            }
        )

    return Response(response_result)


@api_view(['GET'])
def get_result_protocol(request):
    token = request.META.get("HTTP_AUTHORIZATION")
    token = token.replace("Bearer ", "")
    if not token:
        return Response({"result": "error", "comment": "token is empty"})
    token_is_not_valid = False
    app = None
    try:
        app = Application.objects.filter(active=True, key=token).first()
        if not app:
            token_is_not_valid = True
    except:
        token_is_not_valid = True

    if token_is_not_valid:
        return Response({"result": "error", "comment": "token is not valid"})
    companies_id = [i.pk for i in app.companies.all()]
    direction_id = request.GET.get("protocolid")

    direction = Napravleniya.objects.filter(pk=direction_id).first()
    if direction.parent_case:
        if direction.parent_case.napravleniye.work_place_db_id:
            if direction.parent_case.napravleniye.work_place_db_id not in companies_id:
                return Response({"result": "error", "comment": "Acces denied"})
        else:
            return Response({"result": "error", "comment": "No work_place in case protocolId"})
    else:
        return Response({"result": "error", "comment": "No case for protocolId"})
    img_stamp = True
    pdf_content = direction_pdf_result(direction_id, img_stamp)
    return Response({"pdf_base64": pdf_content})


@api_view(['POST'])
def result_accept_protocol(request):
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
    companies_id = [i.pk for i in app.companies.all()]
    data = json.loads(request.body)
    direction_id = data.get("protocolid")
    status = data.get("status")
    error = data.get("error")

    direction = Napravleniya.objects.filter(pk=direction_id).first()
    if direction.parent_case:
        if direction.parent_case.napravleniye.work_place_db_id:
            if direction.parent_case.napravleniye.work_place_db_id not in companies_id:
                return Response({"result": "error", "comment": "Acces denied"})
        else:
            return Response({"result": "error", "comment": "No work_place in case protocolId"})
    else:
        return Response({"result": "error", "comment": "No case for protocolId"})

    Log.log(key=direction_id, type=140002, body={direction.pk: {"status": status, "error": error, "protocolid": direction_id}})
    if status == "ok":
        direction.is_sent_to_work_place = True
        direction.save()
        direction.parent_case.napravleniye.is_sent_to_work_place = True
        direction.parent_case.napravleniye.save()
        return Response({"result": "ok", "comment": "Сообщение принято успешно"})

    return Response({"result": "error", "comment": f"Ошибка сохранения статуса - {direction_id}"})
