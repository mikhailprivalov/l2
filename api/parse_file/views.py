import json
import tempfile
from django.http import HttpRequest, JsonResponse

from api.models import Application
from api.parse_file.pdf import extract_text_from_pdf
import simplejson as json

from api.views import endpoint
from openpyxl import load_workbook
from appconf.manager import SettingManager
from clients.models import Individual, HarmfulFactor
from integration_framework.views import check_enp
from users.models import AssignmentResearches


def dnk_covid(request):
    prefixes = []
    key_dnk = SettingManager.get("dnk_kovid", default='false', default_type='s')
    to_return = None
    for x in "ABCDEF":
        prefixes.extend([f"{x}{i}" for i in range(1, 13)])
    file = request.FILES['file']
    if file.content_type == 'application/pdf' and file.size < 100000:
        with tempfile.TemporaryFile() as fp:
            fp.write(file.read())
            text = extract_text_from_pdf(fp)
        if text:
            text = text.replace("\n", "").split("Коронавирусы подобные SARS-CoVВККоронавирус SARS-CoV-2")
        to_return = []
        if text:
            for i in text:
                k = i.split("N")
                if len(k) > 1 and k[1].split(" ")[0].isdigit():
                    result = json.dumps({"pk": k[1].split(" ")[0], "result": [{"dnk_SARS": "Положительно" if "+" in i else "Отрицательно"}]})
                    to_return.append({"pk": k[1].split(" ")[0], "result": "Положительно" if "+" in i else "Отрицательно"})
                    http_func({"key": key_dnk, "result": result}, request.user)

    return to_return


def http_func(data, user):
    http_obj = HttpRequest()
    http_obj.POST.update(data)
    http_obj.user = user
    endpoint(http_obj)


def parse_medical_examination(request):
    result = []
    bed_employee = []
    company_inn = request.POST['companyInn']
    company_file = request.FILES['file']
    wb = load_workbook(filename=company_file)
    ws = wb.active
    counter_row = 0
    for row in ws.values:
        if counter_row >= 3:
            if company_inn != f'{row[5]}':
                bed_employee.append({"fio": row[2]})
            else:
                params = {"enp": "", "snils": row[1].replace('-', '').replace(' ', ''), "check_mode": "l2-snils"}
                request_obj = HttpRequest()
                request_obj._body = params
                request_obj.user = request.user
                request_obj.method = 'POST'
                request_obj.META["HTTP_AUTHORIZATION"] = f'Bearer {Application.objects.first().key}'
                employee = check_enp(request_obj)
                if employee.data.get("message"):
                    bed_employee.append({"fio": row[2]})
                elif employee.data.get("patient_data") and type(employee.data.get("patient_data")) != list:
                    employee_card = employee.data["patient_data"]["card"]
                else:
                    employee = employee.data
                    employee_card = Individual.import_from_tfoms(employee, None, None, None, True)
                harmful_factor_template = HarmfulFactor.objects.get(title=row[7]).template_id
                need_research = AssignmentResearches.objects.filter(pk=harmful_factor_template)
        counter_row += 1
    return result


def load_file(request):
    if request.POST['companyInn']:
        result = parse_medical_examination(request)
        return JsonResponse({"ok": True, "results": result})
    else:
        results = dnk_covid(request)
        return JsonResponse({"ok": True, "results": results})
