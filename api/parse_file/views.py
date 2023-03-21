import tempfile

from django.http import HttpRequest, JsonResponse

from api.models import Application

from api.parse_file.pdf import extract_text_from_pdf
import simplejson as json

from api.views import endpoint
from openpyxl import load_workbook
from appconf.manager import SettingManager
from contracts.models import PriceCoast
from users.models import AssignmentResearches
from clients.models import Individual, HarmfulFactor, PatientHarmfullFactor, Card
from integration_framework.views import check_enp


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


def parse_factors_file(request):
    incorrect_employees = []
    company_inn = request.POST['companyInn']
    company_file = request.FILES['file']
    wb = load_workbook(filename=company_file)
    ws = wb.worksheets[0]
    employee_data = []
    for key, val in enumerate(ws.values):
        if key >= 3:
            if company_inn != f"{val[5]}":
                incorrect_employees.append({"fio": val[2], "reason": "ИНН организации не совпадает"})
            else:
                employee_data.append(
                    {
                        "snils": val[1].replace('-', '').replace(' ', ''),
                        "family": val[2].split(' ')[0],
                        "name": val[2].split(' ')[1],
                        "patronymic": val[2].split(' ')[2],
                        "gender": val[4][0],
                        "birthday": str(val[3]).split(' ')[0],
                        "position": val[6],
                        "harmful_factor": val[7].split(','),
                    }
                )
    return employee_data, incorrect_employees


def add_factors_to_employees(request):
    employee_data, incorrect_employees = parse_factors_file(request)
    harmful_factors_data = []
    for row in employee_data:
        params = {"enp": "", "snils": row["snils"], "check_mode": "l2-snils"}
        request_obj = HttpRequest()
        request_obj._body = params
        request_obj.user = request.user
        request_obj.method = 'POST'
        request_obj.META["HTTP_AUTHORIZATION"] = f'Bearer {Application.objects.first().key}'
        current_employee = check_enp(request_obj)
        if current_employee.data.get("message"):
            params = {"enp": "", "family": row["family"], "name": row["name"], "bd": row["birthday"].replace('-', ''), "check_mode": "l2-enp-full"}
            current_employee = check_enp(request_obj)
            if current_employee.data.get("message"):
                employee_indv = Individual(family=row["family"], name=row["name"], patronymic=row["patronymic"], birthday=row["birthday"], sex=row["gender"])
                employee_indv.save()
                employee_card = Card.add_l2_card(individual=employee_indv)
            elif len(current_employee.data) > 1:
                incorrect_employees.append({"fio": row["family"] + ' ' + row["name"] + ' ' + row["patronymic"], "reason": "Совпадение"})
                continue
            else:
                employee_card = Individual.import_from_tfoms(current_employee.data["list"], None, None, None, True)
        elif current_employee.data.get("patient_data") and type(current_employee.data.get("patient_data")) != list:
            employee_card = current_employee.data["patient_data"]["card"]
        else:
            employee_card = Individual.import_from_tfoms(current_employee.data["patient_data"], None, None, None, True)

        incorrect_factor = []
        for i in row["harmful_factor"]:
            harmful_factor = HarmfulFactor.objects.filter(title=i).first()
            if harmful_factor:
                harmful_factors_data.append({"factorId": harmful_factor.pk})
            else:
                incorrect_factor.append(f"{i}")
        if len(incorrect_factor) != 0:
            incorrect_employees.append({"fio": row["family"] + ' ' + row["name"] + ' ' + row["patronymic"], "reason": f"Не верные факторы: {incorrect_factor}"})
        PatientHarmfullFactor.save_card_harmful_factor(employee_card.pk, harmful_factors_data)

    return incorrect_employees


def load_file(request):
    link = ""
    if request.POST.get('isGenCommercialOffer') == "true":
        results = gen_commercial_offer(request)
        link = "commercial-offer"
    elif len(request.POST.get('companyInn')) != 0:
        results = add_factors_to_employees(request)
        return JsonResponse({"ok": True, "results": results, "company": True})
    else:
        results = dnk_covid(request)
    return JsonResponse({"ok": True, "results": results, "link": link})


def gen_commercial_offer(request):
    file_data = request.FILES['file']
    selected_price = request.POST.get('selectedPrice')

    wb = load_workbook(filename=file_data)
    ws = wb[wb.sheetnames[0]]
    starts = False
    counts_research = {}
    for row in ws.rows:
        cells = [str(x.value) for x in row]
        if not starts:
            if "код вредности" in cells:
                starts = True
                harmful_factor = cells.index("код вредности")
        else:
            harmful_factor_data = [i.replace(" ", "") for i in cells[harmful_factor].split(",")]
            templates_data = HarmfulFactor.objects.values_list("template_id", flat=True).filter(title__in=harmful_factor_data)
            researches_data = AssignmentResearches.objects.values_list('research_id', flat=True).filter(template_id__in=templates_data)
            researches_data = set(researches_data)
            for r in researches_data:
                if counts_research.get(r):
                    counts_research[r] += 1
                else:
                    counts_research[r] = 1
    price_data = PriceCoast.objects.filter(price_name__id=selected_price, research_id__in=list(counts_research.keys()))
    return [{'title': k.research.title, 'count': counts_research[k.research.pk], 'coast': k.coast} for k in price_data]
