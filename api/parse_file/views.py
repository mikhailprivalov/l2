import csv
import io
import re
import tempfile

from django.http import HttpRequest, JsonResponse

from api.models import Application

from api.parse_file.pdf import extract_text_from_pdf
import simplejson as json

from api.patients.views import patients_search_card
from api.views import endpoint
from openpyxl import load_workbook
from appconf.manager import SettingManager
from contracts.models import PriceCoast, Company, MedicalExamination
from ecp_integration.integration import fill_slot_from_xlsx
from laboratory.settings import CONTROL_AGE_MEDEXAM
from statistic.views import commercial_offer_xls_save_file, data_xls_save_file
from users.models import AssignmentResearches
from clients.models import Individual, HarmfulFactor, PatientHarmfullFactor, Card, CardBase
from integration_framework.views import check_enp
from utils.dates import age_for_year, normalize_dots_date


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
    return endpoint(http_obj)


def add_factors_from_file(request):
    incorrect_patients = []
    company_inn = request.POST["companyInn"]
    company_file = request.FILES["file"]
    wb = load_workbook(filename=company_file)
    ws = wb.worksheets[0]
    starts = False
    snils, fio, birthday, gender, inn_company, code_harmful = (
        "",
        "",
        "",
        "",
        "",
        "",
    )
    bearer_token = None
    application = Application.objects.filter(active=True, is_background_worker=True).first()
    if application:
        bearer_token = f"Bearer {application.key}"
    else:
        new_application = Application(name="background_worker", is_background_worker=True)
        new_application.save()
        bearer_token = f"Bearer {new_application.key}"
    for row in ws.rows:
        cells = [str(x.value) for x in row]
        if not starts:
            if "код вредности" in cells:
                snils = cells.index("снилс")
                fio = cells.index("фио")
                birthday = cells.index("дата рождения")
                gender = cells.index("пол")
                inn_company = cells.index("инн организации")
                code_harmful = cells.index("код вредности")
                position = cells.index("должность")
                examination_date = cells.index("дата мед. осмотра")
                starts = True
        else:
            if company_inn != cells[inn_company].strip():
                incorrect_patients.append({"fio": cells[fio], "reason": "ИНН организации не совпадает"})
                continue
            snils_data = cells[snils].replace("-", "").replace(" ", "")
            fio_data = cells[fio].split(' ')
            family_data = fio_data[0]
            name_data = fio_data[1]
            patronymic_data = None
            if len(fio_data) > 2:
                patronymic_data = fio_data[2]
            birthday_data = cells[birthday].split(' ')[0]
            code_harmful_data = cells[code_harmful].split(',')
            exam_data = cells[examination_date].split(' ')[0]
            gender_data = cells[gender][0]
            params = {"enp": "", "snils": snils_data, "check_mode": "l2-snils"}
            request_obj = HttpRequest()
            request_obj._body = params
            request_obj.user = request.user
            request_obj.method = "POST"
            request_obj.META["HTTP_AUTHORIZATION"] = bearer_token
            current_patient = check_enp(request_obj)
            if current_patient.data.get("message"):
                patient_card = search_by_fio(request_obj, family_data, name_data, patronymic_data, birthday_data)
                if patient_card is None:
                    possible_family = find_and_replace(family_data, "е", "ё")
                    patient_card = search_by_possible_fio(request_obj, family_data, name_data, patronymic_data, birthday_data, possible_family)
                    if patient_card is None:
                        patient_indv = Individual(
                            family=family_data,
                            name=name_data,
                            patronymic=patronymic_data,
                            birthday=birthday_data,
                            sex=gender_data,
                        )
                        patient_indv.save()
                        patient_card = Card.add_l2_card(individual=patient_indv)
            elif current_patient.data.get("patient_data") and type(current_patient.data.get("patient_data")) != list:
                patient_card_pk = current_patient.data["patient_data"]["card"]
                patient_card = Card.objects.filter(pk=patient_card_pk).first()
            else:
                patient_card = Individual.import_from_tfoms(current_patient.data["patient_data"], None, None, None, True)
            incorrect_factor = []
            harmful_factors_data = []
            for i in code_harmful_data:
                current_code = i.replace(" ", "")
                harmful_factor = HarmfulFactor.objects.filter(title=current_code).first()
                if harmful_factor:
                    harmful_factors_data.append({"factorId": harmful_factor.pk})
                else:
                    incorrect_factor.append(f"{current_code}")
            if len(incorrect_factor) != 0:
                incorrect_patients.append({"fio": cells[fio], "reason": f"Неверные факторы: {incorrect_factor}"})
            PatientHarmfullFactor.save_card_harmful_factor(patient_card.pk, harmful_factors_data)
            company_obj = Company.objects.filter(inn=company_inn).first()
            patient_card.work_position = cells[position].strip()
            patient_card.work_place_db = company_obj
            patient_card.save()
            MedicalExamination.save_examination(patient_card, company_obj, exam_data)

    return incorrect_patients


def load_file(request):
    link = ""
    if request.POST.get('isGenCommercialOffer') == "true":
        results = gen_commercial_offer(request)
        link = "open-xls"
    elif request.POST.get('isWritePatientEcp') == "true":
        results = write_patient_ecp(request)
        link = "open-xls"
    elif len(request.POST.get('companyInn')) != 0:
        results = add_factors_from_file(request)
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
    patients = []

    for row in ws.rows:
        cells = [str(x.value) for x in row]
        if not starts:
            if "код вредности" in cells:
                starts = True
                harmful_factor = cells.index("код вредности")
                fio = cells.index("фио")
                born = cells.index("дата рождения")
                position = cells.index("должность")
                sex = cells.index("пол")
        else:
            harmful_factor_data = [i.replace(" ", "") for i in cells[harmful_factor].split(",")]
            born_data = cells[born].split(" ")[0]
            age = -1
            if born_data != "None":
                age = age_for_year(born_data)
                if "м" in cells[sex]:
                    adds_harmfull = CONTROL_AGE_MEDEXAM.get("м")
                else:
                    adds_harmfull = CONTROL_AGE_MEDEXAM.get("ж")
                if adds_harmfull:
                    for i in sorted(adds_harmfull.keys()):
                        if age < i:
                            harmful_factor_data.append(adds_harmfull[i])
                            break
            templates_data = HarmfulFactor.objects.values_list("template_id", flat=True).filter(title__in=harmful_factor_data)
            researches_data = AssignmentResearches.objects.values_list('research_id', flat=True).filter(template_id__in=templates_data)
            researches_data = set(researches_data)
            for r in researches_data:
                if counts_research.get(r):
                    counts_research[r] += 1
                else:
                    counts_research[r] = 1
            patients.append({"fio": cells[fio], "born": born_data, "harmful_factor": cells[harmful_factor], "position": cells[position], "researches": researches_data, "age": age})

    price_data = PriceCoast.objects.filter(price_name__id=selected_price, research_id__in=list(counts_research.keys()))
    data_price = [{'title': k.research.title, 'count': counts_research[k.research.pk], 'coast': k.coast} for k in price_data]
    research_price = {d.research.pk: f"{d.research.title}@{d.coast}" for d in price_data}
    file_name = commercial_offer_xls_save_file(data_price, patients, research_price)
    return file_name


def search_by_fio(request_obj: HttpRequest, family: str, name: str, patronymic: str | None, birthday: str) -> Card | None:
    patient_card = None
    params_tfoms = {
        "enp": "",
        "family": family,
        "name": name,
        "bd": birthday,
        "check_mode": "l2-enp-full",
    }
    params_internal = {
        "type": CardBase.objects.get(internal_type=True).pk,
        "extendedSearch": True,
        "form": {
            "family": family,
            "name": name,
            "patronymic": patronymic,
            "birthday": birthday,
            "archive": False,
        },
        "limit": 1,
    }
    request_obj._body = params_tfoms
    current_patient = check_enp(request_obj)
    if current_patient.data.get("message"):
        request_obj._body = json.dumps(params_internal)
        data = patients_search_card(request_obj)
        results_json = json.loads(data.content.decode('utf-8'))
        if len(results_json["results"]) > 0:
            patient_card_pk = results_json["results"][0]["pk"]
            patient_card = Card.objects.filter(pk=patient_card_pk).first()
    elif len(current_patient.data["list"]) > 1:
        return patient_card
    else:
        patient_card = Individual.import_from_tfoms(current_patient.data["list"], None, None, None, True)
    return patient_card


def find_and_replace(text: str, symbol1: str, symbol2: str) -> list:
    result = []
    for i in range(len(text)):
        if text[i] == symbol1:
            current_text = text[0:i] + symbol2 + text[i + 1 :]
            result.append(current_text)
        elif text[i] == symbol2:
            current_text = text[0:i] + symbol1 + text[i + 1 :]
            result.append(current_text)
    return result


def search_by_possible_fio(request_obj: HttpRequest, family: str, name: str, patronymic: str | None, birthday: str, possible_family: list) -> Card | None:
    if not possible_family:
        return None
    patient_card = None
    for i in possible_family:
        current_family = i
        patient_card = search_by_fio(request_obj, current_family, name, patronymic, birthday)
        if patient_card is not None:
            break
    return patient_card


def load_csv(request):
    file_data = request.FILES['file']
    file_data = file_data.read().decode('utf-8')
    io_string = io.StringIO(file_data)

    data = csv.reader(io_string, delimiter='\t')
    header = next(data)

    application = None

    for app in Application.objects.filter(csv_header__isnull=False).exclude(csv_header__exact=""):
        if app.csv_header in header:
            application = app
            break

    if application is None or application.csv_header not in header:
        return JsonResponse({"ok": False, "message": "Файл не соответствует ни одному приложению"})

    app_key = application.key.hex

    method = re.search(r'^(.+)\s\d+\s.*$', header[1]).group(1)
    results = []
    pattern = re.compile(r'^\d+$')

    for row in data:
        if len(row) > 5 and pattern.match(row[2]):
            r = {
                "pk": row[2],
                "result": row[5],
            }

            result = json.dumps({"pk": r["pk"], "result": {method: r["result"]}})

            resp = http_func({"key": app_key, "result": result, "message_type": "R"}, request.user)

            resp = json.loads(resp.content)

            results.append(
                {
                    "pk": row[2],
                    "result": row[5],
                    "comment": "успешно" if resp["ok"] else "не удалось сохранить результат",
                }
            )

    return JsonResponse({"ok": True, "results": results, "method": method})


def write_patient_ecp(request):
    file_data = request.FILES['file']
    wb = load_workbook(filename=file_data)
    ws = wb[wb.sheetnames[0]]
    starts = False
    patients = []
    for row in ws.rows:
        cells = [str(x.value) for x in row]
        if not starts:
            if "врач" in cells:
                starts = True
                family = cells.index("фaмилия")
                name = cells.index("имя")
                patronymic = cells.index("отчество")
                born = cells.index("дата рождения")
                doctor = cells.index("врач")
        else:
            born_data = cells[born].split(" ")[0]
            if "." in born_data:
                born_data = normalize_dots_date(born_data)
            patient = {"family": cells[family], "name": cells[name], "patronymic": cells[patronymic], "birthday": born_data, "snils": ""}
            result = fill_slot_from_xlsx(cells[doctor], patient)
            is_write = "Ошибка"
            if result and result.get('register'):
                is_write = "записан"
            patients.append({**patient, "is_write": is_write, "doctor": cells[doctor]})
    file_name = data_xls_save_file(patients, "Запись")
    return file_name
