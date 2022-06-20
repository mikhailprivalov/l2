import json
from django.http import HttpResponse
import openpyxl

from api.reports import structure_sheet
from api.reports import sql_func
from api.reports import handle_func

from laboratory.settings import SEARCH_PAGE_STATISTIC_PARAMS


def statistic_params_search(request):
    if request.method == "POST":
        data = json.loads(request.body)

        groups_user = [str(x) for x in request.user.groups.all()]
        response = HttpResponse("неверные параметры")

        param = data.get("param") or None
        research_id = data.get("researchId") or None
        if research_id:
            research_id = int(research_id)
        directions = data.get("directions") or None
        if not (param and research_id and directions):
            return response
        some_report = []
        for k, v in SEARCH_PAGE_STATISTIC_PARAMS.items():
            if k in groups_user:
                some_report.extend(v)
        if len(some_report) == 0:
            return response

        correct_group_param = False
        correct_group_research_id = False
        for v in some_report:
            correct_group_param = False
            correct_group_research_id = False
            for key, val in v.items():
                if key == "id" and val == param:
                    correct_group_param = True
                if key == "reserches_pk" and (research_id in val or val == "*"):
                    correct_group_research_id = True
                if correct_group_research_id and correct_group_param:
                    break
            if correct_group_research_id and correct_group_param:
                break

        if not (correct_group_param and correct_group_research_id):
            return response

        symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ", u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")  # Словарь для транслитерации
        tr = {ord(a): ord(b) for a, b in zip(*symbols)}  # Перевод словаря для транслита

        response = HttpResponse(content_type='application/ms-excel')
        wb = openpyxl.Workbook()
        wb.remove(wb.get_sheet_by_name('Sheet'))
        ws = wb.create_sheet('лист1')

        directions_data = tuple(list(set(directions)))
        if param == '1':
            result = sql_func.report_buh_gistology(directions_data)
            final_structure = handle_func.patologistology_buh(result)
            ws = structure_sheet.patologistology_buh_base(ws)
            ws = structure_sheet.patologistology_buh_data(ws, final_structure)

        title = "отчет"
        response['Content-Disposition'] = str.translate(f"attachment; filename=\"{title}.xlsx\"", tr)
        wb.save(response)
        return response
