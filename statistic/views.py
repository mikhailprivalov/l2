from collections import defaultdict

import pytz
import simplejson as json
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone, dateformat
from django.views.decorators.csrf import csrf_exempt

import directory.models as directory
import slog.models as slog
from clients.models import CardBase
from directions.models import Napravleniya, TubesRegistration, IstochnikiFinansirovaniya, Result, RMISOrgs, ParaclinicResult
from directory.models import Researches
from laboratory import settings
from researches.models import Tubes
from statistics_tickets.models import StatisticsTicket
from users.models import DoctorProfile
from users.models import Podrazdeleniya
from copy import deepcopy

# from ratelimit.decorators import ratelimit
from utils.dates import try_parse_range
from laboratory import utils
from . import sql_func
from . import structure_sheet



@csrf_exempt
@login_required
def statistic_page(request):
    """ Страница статистики """
    labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации")  # Лаборатории
    tubes = directory.Tubes.objects.all()  # Пробирки
    podrs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT)  # Подлазделения
    getters_material = DoctorProfile.objects.filter(user__groups__name='Заборщик биоматериала').distinct()
    statistics_tickets_users = DoctorProfile.objects.filter(user__groups__name__in=['Оформление статталонов',
                                                                                    'Лечащий врач']).distinct()
    statistics_tickets_deps = Podrazdeleniya.objects.all().order_by('title')
    return render(request, 'statistic.html', {"labs": labs, "tubes": tubes, "podrs": podrs,
                                              "getters_material": json.dumps(
                                                  [{"pk": str(x.pk), "fio": str(x)} for x in getters_material]),
                                              "statistics_tickets_users": json.dumps(
                                                  [{"pk": -1, "fio": 'Пользователь не выбран'},
                                                   *[{"pk": str(x.pk), "fio": str(x)} for x in
                                                   statistics_tickets_users]]),
                                              "statistics_tickets_deps": json.dumps(
                                                  [{"pk": -1, "title": 'Подразделение не выбрано'},
                                                   *[{"pk": str(x.pk), "title": x.title} for x in
                                                    statistics_tickets_deps]])
                                              })


# @ratelimit(key=lambda g, r: r.user.username + "_stats_" + (r.POST.get("type", "") if r.method == "POST" else r.GET.get("type", "")), rate="20/m", block=True)
@csrf_exempt
@login_required
def statistic_xls(request):
    """ Генерация XLS """
    from directions.models import Issledovaniya
    import xlwt
    import openpyxl

    wb = xlwt.Workbook(encoding='utf-8')
    response = HttpResponse(content_type='application/ms-excel')

    request_data = request.POST if request.method == "POST" else request.GET
    pk = request_data.get("pk", "")
    tp = request_data.get("type", "")
    date_start_o = request_data.get("date-start", "")
    date_end_o = request_data.get("date-end", "")
    users_o = request_data.get("users", "[]")
    user_o = request_data.get("user")
    date_values_o = request_data.get("values", "{}")
    date_type = request_data.get("date_type", "d")
    depart_o = request_data.get("department")

    if date_start_o != "" and date_end_o != "":
        slog.Log(key=tp, type=100, body=json.dumps({"pk": pk, "date": {"start": date_start_o, "end": date_end_o}}),
                 user=request.user.doctorprofile).save()

    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")  # Словарь для транслитерации
    tr = {ord(a): ord(b) for a, b in zip(*symbols)}  # Перевод словаря для транслита

    borders = xlwt.Borders()
    borders.left = xlwt.Borders.THIN
    borders.right = xlwt.Borders.THIN
    borders.top = xlwt.Borders.THIN
    borders.bottom = xlwt.Borders.THIN

    # Отчет по динамике анализов
    if tp == "directions_list":
        from collections import OrderedDict
        pk = json.loads(pk)
        dn = Napravleniya.objects.filter(pk__in=pk)
        cards = {}

        napr_client = set()
        depart_napr = OrderedDict()
        depart_fraction = OrderedDict()
        one_param = "one_param"

        for d in dn:
            if d.department()==None or d.department().p_type != 2:
                continue
            c = d.client
            napr_client.add(c.pk)
            # Проверить, что все направления относятся к одной карте. И тип "Лаборатория"
            if len(napr_client) > 1:
                response['Content-Disposition'] = str.translate("attachment; filename=\"Назначения.xls\"", tr)
                ws = wb.add_sheet("Вакцинация")
                row_num = 0
                row = [
                    ("Пациент", 7000),
                    ("Карта", 6000),
                    ("Направление", 4000),
                    ("Дата", 4000),
                    ("Назначение", 7000),
                ]
                wb.save(response)
                return response
            # Распределить направления по подразделениям: "depart_napr"
            # {БИО:[напр1, напр2, напр3], КДЛ: [напр11, напр21, напр31], ИММ: [напр41, напр42, напр43]}

            tmp_num_dir = []
            department_title = d.department().id
            department_id = d.department().id

            if department_title in depart_napr.keys():
                tmp_num_dir = depart_napr.get(department_title)
                tmp_num_dir.append(d.pk)
                depart_napr[department_title] = tmp_num_dir
            else:
                tmp_num_dir.append(d.pk)
                depart_napr[department_title] = tmp_num_dir

            # По исследованиям строим структуру "depart_fraction":
            # Будущие заголовки в Excel. Те исследования у, к-рых по одной фракции в общий подсловарь,
            # у к-рых больше одного показателя (фракции) в самостоятельные подсловари. Выборка из справочника, НЕ из "Результатов"
            # пример стр-ра: {биохим: {услуги, имеющие по 1 фракции:[фр1-усл1, фр2-усл2, фр3-усл3],
            #                   усл1:[фр1, фр2, фр3],усл2:[фр1, фр2, фр3],
            #                   усл2:[фр1, фр2, фр3],усл2:[фр1, фр2, фр3]}
            # порядок фракций "По весу".

            one_param_temp = OrderedDict()

            for i in Issledovaniya.objects.filter(napravleniye=d):
                dict_research_fraction = OrderedDict()
                research_iss = i.research_id
                dict_research_fraction = ({p: str(t) + ',' + str(u) for p, t, u in
                                           directory.Fractions.objects.values_list('pk', 'title', 'units').filter(
                                               research=i.research).order_by("sort_weight")})

                if depart_fraction.get(department_id) != None:
                    if len(dict_research_fraction.keys()) == 1:
                        one_param_temp = depart_fraction[department_id][one_param]
                        one_param_temp.update(dict_research_fraction)
                        depart_fraction[department_id].update({one_param: one_param_temp})
                    else:
                        depart_fraction[department_id].update({research_iss: dict_research_fraction})
                else:
                    depart_fraction.update({department_id: {}})
                    if len(dict_research_fraction) == 1:
                        depart_fraction[department_id].update({one_param: dict_research_fraction})
                    else:
                        depart_fraction[department_id].update({research_iss: dict_research_fraction})
                        depart_fraction[department_id].update({one_param: {}})

    # Все возможные анализы в направлениях - стр-ра А
    # направления по лабораториям (тип лаборатории, [номера направлений])
        obj = []
        import datetime
        for type_lab, l_napr in depart_napr.items():
            a = ([[p, r, n, datetime.datetime.strftime(utils.localtime(t), "%d.%m.%y")] for p, r, n, t in
                  Issledovaniya.objects.values_list('pk', 'research_id', 'napravleniye_id', 'time_confirmation').filter(
                      napravleniye_id__in=l_napr)])
            obj.append(a)

        for i in obj:
            for j in i:
                result_k = ({fr_id: val for fr_id, val in
                             Result.objects.values_list('fraction', 'value').filter(issledovaniye_id=j[0])})
                j.append(result_k)

        finish_obj = []
        for i in obj:
            for j in i:
                j.pop(0)
                finish_obj.append(j)

        # Строим стр-ру {тип лаборатория: id-анализа:{(направление, дата):{id-фракции:результат,id-фракции:результат}}}
        finish_ord = OrderedDict()
        for t_lab, name_iss in depart_fraction.items():
            finish_ord[t_lab] = {}
            for iss_id, fract_dict in name_iss.items():
                if fract_dict:
                    frac = True
                else:
                    frac = False
                finish_ord[t_lab][iss_id] = {}
                opinion_dict = {('напр', 'дата',): fract_dict}
                val_dict = fract_dict.copy()
                finish_ord[t_lab][iss_id].update(opinion_dict)
                for k, v in fract_dict.items():
                    val_dict[k] = ''

                # Строим стр-ру {id-анализа:{(направление, дата,):{id-фракции:результат,id-фракции:результат}}}
                # one_param - это анализы у которых несколько параметров-фракции (ОАК, ОАМ)
                if (iss_id != 'one_param') or (iss_id != '') or (iss_id != None):
                    for d in finish_obj:
                        tmp_dict = {}
                        if iss_id == d[0]:
                            for i, j in d[3].items():
                                val_dict[i] = j
                            tmp_dict[(d[1], d[2],)] = deepcopy(val_dict)
                            finish_ord[t_lab][iss_id].update(tmp_dict)

                # Строим стр-ру {one_param:{(направление, дата,):{id-фракции:результат,id-фракции:результат}}}
                # one_param - это анализы у которых только один параметр-фракции (холестерин, глюкоза и др.)
                key_tuple = (0, 0,),
                if iss_id == 'one_param' and frac:
                    tmp_dict = {}
                    for d in finish_obj:
                        if key_tuple != (d[1], d[2],):
                            for k, v in fract_dict.items():
                                val_dict[k] = ''
                        for u, s in val_dict.items():
                            if d[3].get(u):
                                val_dict[u] = d[3].get(u)
                                tmp_dict[(d[1], d[2],)] = deepcopy(val_dict)
                                key_tuple = (d[1], d[2],)

                    finish_ord[t_lab][iss_id].update(tmp_dict)

        response['Content-Disposition'] = str.translate("attachment; filename=\"Назначения.xls\"", tr)
        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1
        font_style.borders = borders
        font_style_b = xlwt.XFStyle()
        font_style_b.alignment.wrap = 1
        font_style_b.font.bold = True
        font_style_b.borders = borders
        ws = wb.add_sheet("Динамика")
        row_num = 0

        for k, v in finish_ord.items():
            col_num = 0
            ws.write(row_num, 0, label=Podrazdeleniya.objects.values_list('title').get(pk=k))
            row_num += 1
            col_num = 0
            for name_iss, fr_id in v.items():
                if name_iss != 'one_param':
                    ws.write(row_num, 0, label=Researches.objects.values_list('title').get(pk=name_iss))
                else:
                    ws.write(row_num, 0, label=name_iss)
                row_num += 1
                a, b = '', ''
                for i, j in fr_id.items():
                    col_num = 0
                    a, b = i
                    ws.write(row_num, col_num, label=a)
                    col_num += 1
                    ws.write(row_num, col_num, label=b)
                    ss = ''
                    for g, h in j.items():
                        col_num += 1
                        ss = str(h)
                        ws.write(row_num, col_num, label=ss)
                    row_num += 1
                    col_num += 1
                row_num += 1
            row_num += 1

    # row = [
    #     ("Пациент", 7000),
    #     ("Карта", 6000),
    #     ("Направление", 4000),
    #     ("Дата", 4000),
    #     ("Назначение", 7000),
    # ]
    # for col_num in range(len(row)):
    #     ws.write(row_num, col_num, row[col_num][0], font_style_b)
    #     ws.col(col_num).width = row[col_num][1]
    # row_num += 1
    # for ck in cards.keys():
    #     c = cards[ck]
    #     started = False
    #     for dk in c["d"].keys():
    #         if not started:
    #             row = [
    #                 "{} {}".format(c["fio"], c["bd"]),
    #                 c["card"],
    #             ]
    #             started = True
    #         else:
    #             row = ["", ""]
    #         s2 = False
    #         for r in c["d"][dk]["r"]:
    #             if not s2:
    #                 s2 = True
    #                 row.append(str(dk))
    #                 row.append(c["d"][dk]["dn"])
    #             else:
    #                 row.append("")
    #                 row.append("")
    #                 row.append("")
    #                 row.append("")
    #             row.append(r["title"])
    #             for col_num in range(len(row)):
    #                 ws.write(row_num, col_num, row[col_num], font_style)
    #             row_num += 1
    #             row = []

    #
    # Вывести окончательную структуру в нужный формат: эксель (pdf, word, html, др.)
    #
    #
    #

    # if tp == "directions_list":
    #     pk = json.loads(pk)
    #
    #     dn = Napravleniya.objects.filter(pk__in=pk)
    #
    #     cards = {}
    #
    #     for d in dn:
    #         c = d.client
    #         if c.pk not in cards:
    #             cards[c.pk] = {
    #                 "card": c.number_with_type(),
    #                 "fio": c.individual.fio(),
    #                 "bd": c.individual.bd(),
    #                 "hn": d.history_num,
    #                 "d": {},
    #             }
    #         cards[c.pk]["d"][d.pk] = {
    #             "r": [],
    #             "dn": str(dateformat.format(d.data_sozdaniya.date(), settings.DATE_FORMAT)),
    #         }
    #         for i in Issledovaniya.objects.filter(napravleniye=d):
    #             cards[c.pk]["d"][d.pk]["r"].append({
    #                 "title": i.research.title,
    #             })
    #
    #     response['Content-Disposition'] = str.translate("attachment; filename=\"Назначения.xls\"", tr)
    #     font_style = xlwt.XFStyle()
    #     font_style.alignment.wrap = 1
    #     font_style.borders = borders
    #
    #     font_style_b = xlwt.XFStyle()
    #     font_style_b.alignment.wrap = 1
    #     font_style_b.font.bold = True
    #     font_style_b.borders = borders
    #
    #     ws = wb.add_sheet("Вакцинация")
    #     row_num = 0
    #     row = [
    #         ("Пациент", 7000),
    #         ("Карта", 6000),
    #         ("Направление", 4000),
    #         ("Дата", 4000),
    #         ("Назначение", 7000),
    #     ]
    #
    #     for col_num in range(len(row)):
    #         ws.write(row_num, col_num, row[col_num][0], font_style_b)
    #         ws.col(col_num).width = row[col_num][1]
    #     row_num += 1
    #
    #     for ck in cards.keys():
    #         c = cards[ck]
    #         started = False
    #         for dk in c["d"].keys():
    #             if not started:
    #                 row = [
    #                     "{} {}".format(c["fio"], c["bd"]),
    #                     c["card"],
    #                 ]
    #                 started = True
    #             else:
    #                 row = ["", ""]
    #
    #             s2 = False
    #
    #             for r in c["d"][dk]["r"]:
    #                 if not s2:
    #                     s2 = True
    #                     row.append(str(dk))
    #                     row.append(c["d"][dk]["dn"])
    #                 else:
    #                     row.append("")
    #                     row.append("")
    #                     row.append("")
    #                     row.append("")
    #                 row.append(r["title"])
    #
    #                 for col_num in range(len(row)):
    #                     ws.write(row_num, col_num, row[col_num], font_style)
    #                 row_num += 1
    #

    if tp == "statistics-visits":
        date_start, date_end = try_parse_range(date_start_o, date_end_o)
        t = request.GET.get("t", "sum")
        fio = request.user.doctorprofile.fio
        dep = request.user.doctorprofile.podrazdeleniye.get_title()
        dirs = Napravleniya.objects.filter(visit_date__range=(date_start, date_end,),
                                           visit_who_mark=request.user.doctorprofile).order_by("visit_date")

        if t == "sum":
            response['Content-Disposition'] = str.translate("attachment; filename=\"Суммарный отчёт по посещениям.xls\"",
                                                            tr)
            font_style = xlwt.XFStyle()
            font_style.alignment.wrap = 1
            font_style.borders = borders

            font_style_b = xlwt.XFStyle()
            font_style_b.alignment.wrap = 1
            font_style_b.font.bold = True
            font_style_b.borders = borders

            ws = wb.add_sheet("Посещения")
            row_num = 0
            row = [
                (fio, 7000),
                (dep, 7000),
                ("", 3000),
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num][0], font_style)
                ws.col(col_num).width = row[col_num][1]
            row_num += 1
            row = [
                date_start_o + " - " + date_end_o,
                "",
                "",
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
            row_num += 1
            row = [
                "",
                "",
                "",
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style if col_num > 0 else font_style_b)
            row_num += 1
            row = [
                "Услуга",
                "Источник финансирования",
                "Количество",
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style_b)
            row_num += 1
            iss = {}
            for d in dirs:
                for i in Issledovaniya.objects.filter(napravleniye=d).order_by("research__title").order_by(
                        "napravleniye__istochnik_f"):
                    rt = i.research.title
                    istf = i.napravleniye.istochnik_f.base.title + " - " + i.napravleniye.istochnik_f.title
                    if rt not in iss:
                        iss[rt] = {}

                    if istf not in iss[rt]:
                        iss[rt][istf] = 0

                    iss[rt][istf] += 1
            for k in iss:
                for istf in iss[k]:
                    row = [
                        k,
                        istf,
                        iss[k][istf],
                    ]
                    for col_num in range(len(row)):
                        ws.write(row_num, col_num, row[col_num], font_style)
                    row_num += 1
    elif tp == "vac":
        date_start, date_end = try_parse_range(date_start_o, date_end_o)
        response['Content-Disposition'] = str.translate("attachment; filename=\"Вакцинация.xls\"", tr)
        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1
        font_style.borders = borders

        font_style_b = xlwt.XFStyle()
        font_style_b.alignment.wrap = 1
        font_style_b.font.bold = True
        font_style_b.borders = borders

        ts = [
            "Название",
            "Доза",
            "Серия",
            "Срок годности",
            "Способ введения"
        ]

        ws = wb.add_sheet("Вакцинация")
        row_num = 0
        row = [
            ("Исполнитель", 6000),
            ("Подтверждено", 5000),
            ("RMIS UID", 5000),
            ("Вакцина", 5000),
            ("Код", 4000),
        ]

        for t in ts:
            row.append((t, 4000))
        row.append(("Этап", 2500))

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num][0], font_style_b)
            ws.col(col_num).width = row[col_num][1]
        row_num += 1

        for i in Issledovaniya.objects.filter(research__podrazdeleniye__vaccine=True, time_confirmation__range=(date_start, date_end,)).order_by("time_confirmation"):
            row = [
                i.doc_confirmation.get_fio(),
                i.time_confirmation.astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%d.%m.%Y %X"),
                i.napravleniye.client.individual.get_rmis_uid_fast(),
                i.research.title,
                i.research.code,
            ]
            v = {}
            for p in ParaclinicResult.objects.filter(issledovaniye=i):
                if p.field.title in ts:
                    v[p.field.title] = p.value
            for t in ts:
                row.append(v.get(t, ""))
            row.append("V")
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
            row_num += 1

    elif tp == "statistics-tickets-print":
        access_to_all = ('Просмотр статистики' in request.user.groups.values_list('name',
                                                                                  flat=True)) or request.user.is_superuser
        data_date = request_data.get("date_values")
        data_date = json.loads(data_date)
        import datetime
        from datetime import  timedelta
        import calendar
        if request_data.get("date_type") == 'd':
            d1 = datetime.datetime.strptime(data_date['date'], '%d.%m.%Y')
            d2 = datetime.datetime.strptime(data_date['date'], '%d.%m.%Y')
            month_obj = ''
        else:
            month_obj = int(data_date['month']) + 1
            _, num_days = calendar.monthrange(int(data_date['year']), month_obj)
            d1 = datetime.date(int(data_date['year']), month_obj, 1)
            d2 = datetime.date(int(data_date['year']),month_obj, num_days)

        type_fin = request_data.get("fin")
        users_o = json.loads(user_o)
        us_o = None
        if users_o != -1:
            us = int(users_o)
            us_o = [DoctorProfile.objects.get(pk=us)]
        elif depart_o != -1:
            depart = Podrazdeleniya.objects.get(pk=depart_o)
            us_o = DoctorProfile.objects.filter(podrazdeleniye=depart)

        wb = openpyxl.Workbook()
        wb.remove(wb.get_sheet_by_name('Sheet'))

        from openpyxl.styles import PatternFill, Border, Side, Alignment, Font, NamedStyle, Color, Fill, colors
        style_o = NamedStyle(name="style_o")
        style_o.font = Font(bold=True, size=11)
        wb.add_named_style(style_o)

        style_border = NamedStyle(name="style_border")
        bd = Side(style='thin', color="000000")
        style_border.border = Border(left=bd, top=bd, right=bd, bottom=bd)
        style_border.font = Font(bold=True, size=11)
        style_border.alignment = Alignment(wrap_text=True)
        wb.add_named_style(style_border)

        style_border1 = NamedStyle(name="style_border1")
        bd = Side(style='thin', color="000000")
        style_border1.border = Border(left=bd, top=bd, right=bd, bottom=bd)
        style_border1.font = Font(bold=False, size=11)
        style_border1.alignment = Alignment(wrap_text=True)
        wb.add_named_style(style_border1)

        my_fill = openpyxl.styles.fills.PatternFill(patternType='solid', start_color='a9d094',
                                                    end_color='a9d094')
        total_fill = openpyxl.styles.fills.PatternFill(patternType='solid', start_color='ffcc66',
                                                    end_color='ffcc66')

        pink_fill = openpyxl.styles.fills.PatternFill(patternType='solid', start_color='FCD5B4',
                                                    end_color='FCD5B4')

        def structure(ws1, i_obj, issl_obj, d1, d2, dict_job_l):
            """
            Назначить ширину колонок. Вход worksheet выход worksheen с размерами
            """
            from openpyxl.utils.cell import get_column_letter
            col = 1
            ws1.column_dimensions[get_column_letter(1)].width = 13
            ws1.column_dimensions[get_column_letter(col + 1)].width = 7
            ws1.column_dimensions[get_column_letter(col + 2)].width = 15
            ws1.column_dimensions[get_column_letter(col + 3)].width = 9
            ws1.column_dimensions[get_column_letter(col + 4)].width = 31
            ws1.column_dimensions[get_column_letter(col + 5)].width = 13
            ws1.column_dimensions[get_column_letter(col + 6)].width = 12
            ws1.column_dimensions[get_column_letter(col + 7)].width = 27
            ws1.column_dimensions[get_column_letter(col + 8)].width = 16
            ws1.column_dimensions[get_column_letter(col + 9)].width = 12
            ws1.column_dimensions[get_column_letter(col + 10)].width = 18
            ws1.column_dimensions[get_column_letter(col + 11)].width = 13
            ws1.column_dimensions[get_column_letter(col + 12)].width = 12
            ws1.column_dimensions[get_column_letter(col + 13)].width = 13
            ws1.column_dimensions[get_column_letter(col + 14)].width = 13
            ws1.column_dimensions[get_column_letter(col + 15)].width = 13
            ws1.column_dimensions[get_column_letter(col + 16)].width = 13
            ws1.column_dimensions[get_column_letter(col + 17)].width = 13
            ws1.column_dimensions[get_column_letter(col + 18)].width = 13
            ws1.column_dimensions[get_column_letter(col + 19)].width = 13
            ws1.column_dimensions[get_column_letter(col + 20)].width = 13
            ws1.column_dimensions[get_column_letter(col + 21)].width = 13

            # Закголовки столбцов
            ws1.cell(row=1, column=1).value = 'Сотрудник'
            ws1.cell(row=1, column=1).style = style_o
            ws1.cell(row=1, column=2).value = i_obj.fio
            ws1.cell(row=2, column=1).value = 'Должность'
            ws1.cell(row=2, column=1).style = style_o
            ws1.cell(row=2, column=2).value = i_obj.specialities.title if i_obj.specialities else ""
            ws1.cell(row=4, column=1).value = 'Период:'
            ws1.cell(row=4, column=1).style = style_o
            ws1.cell(row=5, column=1).value = d1
            ws1.cell(row=5, column=2).value = 'по'
            ws1.cell(row=5, column=3).value = d2
            ws1.cell(row=1, column=5).value = 'Код врача'
            ws1.cell(row=1, column=5).style = style_o
            ws1.cell(row=1, column=6).value = i_obj.personal_code
            ws1.cell(row=3, column=5).value = 'Источник'
            ws1.cell(row=3, column=5).style = style_o
            ws1.cell(row=3, column=6).value = 'ОМС'

            #Заголовки данных
            ws1.cell(row=7, column=1).value = 'Дата'
            ws1.cell(row=7, column=col + 1).value = 'Кол-во'
            ws1.cell(row=7, column=col+2).value = 'Услуга'
            ws1.cell(row=7, column=col+3).value = 'Соисполнитель'
            ws1.cell(row=7, column=col+4).value = 'ФИО пациента,\n№ направления'
            ws1.cell(row=7, column=col+5).value = 'Дата рождения'
            ws1.cell(row=7, column=col+6).value = '№ карты'
            ws1.cell(row=7, column=col+7).value = 'Данные полиса'
            ws1.cell(row=7, column=col+8).value = 'Код услуги'
            ws1.cell(row=7, column=col+9).value = 'Услуга \n (ует/мин)'
            ws1.cell(row=7, column=col+10).value = 'Время \n подтверждения'
            ws1.cell(row=7, column=col+12).value = 'Первичный прием'
            ws1.cell(row=7, column=col+11).value = 'Онкоподозрение'
            ws1.cell(row=7, column=col+13).value = 'Цель \n посещения\n(код)'
            ws1.cell(row=7, column=col+14).value = 'Диагноз \n МКБ'
            ws1.cell(row=7, column=col+15).value = 'Впервые'
            ws1.cell(row=7, column=col+16).value = 'Результат \n обращения \n(код)'
            ws1.cell(row=7, column=col+17).value = 'Исход(код)'
            ws1.cell(row=7, column=col+18).value = 'Стоимость'

            rows = ws1[f'A{7}:V{7}']
            for row in rows:
                for cell in row:
                    cell.style = style_border

            r = 7
            r1 = r + 1
            total_sum = []
            one_days = timedelta(1)
            current_date = ''
            for issled in issl_obj:
                current_date = issled[14]
                current_count = 1
                current_research = issled[1]
                current_coexec = ''
                f = issled[22] if issled[22] else ''
                n = issled[23] if issled[23] else ''
                p = issled[24] if issled[24] else ''
                current_napr = str(issled[7])
                current_patient_napr = f +' ' + n + ' ' + p + '\n' + current_napr
                current_born = utils.strdate(issled[25])
                current_card = issled[21]
                polis_n = issled[4] if issled[4] else ''
                polis_who = issled[5] if issled[5] else ''
                current_polis = polis_n +';\n' + polis_who
                current_code_reserch = issled[2]
                current_doc_conf = issled[8]
                current_def_uet = issled[9] if issled[9] else 0
                current_co_exec1 = issled[10]
                current_uet1 = issled[11] if issled[11] else 0
                current_co_exec2 = issled[12]
                current_uet2 = issled[13] if issled[13] else 0
                current_confirm = utils.strtime(issled[14])
                current_isfirst = issled[3]
                current_onko = issled[15]
                current_purpose = issled[16]
                current_diagnos = issled[17]
                current_firsttime = issled[6]
                current_result = issled[17]
                current_octome = issled[18]
                current_price = ''

                d_result = utils.strfdatetime(current_date, "%d.%m.%Y")
                if r != 7 and r != 8:
                    befor_date = ws1.cell(row=r, column=1).value
                    if d_result != befor_date and not (ws1.cell(row=r, column=1).value).istitle():
                        indirect_job = dict_job_l.get(befor_date)
                        if indirect_job:
                            for k_job,v_job in indirect_job.items():
                                r = r + 1
                                ws1.cell(row=r, column=1).value = befor_date
                                ws1.cell(row=r, column=col + 2).value = k_job
                                ws1.cell(row=r, column=col + 9).value = v_job
                                rows = ws1[f'A{r}:V{r}']
                                for row in rows:
                                    for cell in row:
                                        cell.fill = pink_fill
                        r = r + 1
                        ws1.cell(row=r, column=1).value = 'Итого за ' + (
                            utils.strfdatetime(current_date - one_days, "%d"))
                        ws1.cell(row=r, column=2).value = f'=SUM(B{r1}:B{r-1})'
                        ws1.cell(row=r, column=10).value = f'=SUM(J{r1}:J{r-1})'

                        total_sum.append(r)
                        ws1.row_dimensions.group(r1, r - 1, hidden=True)
                        rows = ws1[f'A{r}:V{r}']
                        for row in rows:
                            for cell in row:
                                cell.fill = my_fill
                        r1 = r + 1

                r = r + 1
                ws1.cell(row=r, column=1).value = d_result
                ws1.cell(row=r, column=col+1).value = 1
                ws1.cell(row=r, column=col+2).value = current_research
                sum_uet = 0
                co_exec = ''
                if (current_doc_conf == i_obj.pk) and (current_co_exec1 == i_obj.pk):
                    sum_uet = sum_uet + current_def_uet
                    co_exec = co_exec + 'ОСН'

                if (current_doc_conf == i_obj.pk) and (current_co_exec1 != i_obj.pk):
                    sum_uet = sum_uet + current_def_uet
                    co_exec = co_exec + 'ОСН'

                if (current_doc_conf != i_obj.pk) and (current_co_exec1 == i_obj.pk):
                    sum_uet = sum_uet + current_uet1
                    co_exec = co_exec + 'СО-1'

                if current_co_exec2 == i_obj.pk:
                    sum_uet = sum_uet + current_uet2
                    co_exec = co_exec + ', СО-2'
                ws1.cell(row=r, column=col+3).value = co_exec
                ws1.cell(row=r, column=col+4).value = current_patient_napr
                ws1.cell(row=r, column=col+5).value = current_born
                ws1.cell(row=r, column=col+6).value = current_card

                ws1.cell(row=r, column=col+7).value = current_polis
                ws1.cell(row=r, column=col+8).value = current_code_reserch
                ws1.cell(row=r, column=col+9).value = sum_uet
                ws1.cell(row=r, column=col+10).value = current_confirm

                ws1.cell(row=r, column=col+11).value = current_onko
                ws1.cell(row=r, column=col+12).value = current_isfirst
                ws1.cell(row=r, column=col+13).value = current_purpose
                ws1.cell(row=r, column=col+14).value = current_diagnos
                ws1.cell(row=r, column=col+15).value = current_firsttime
                ws1.cell(row=r, column=col+16).value = current_result
                ws1.cell(row=r, column=col+17).value = current_octome
                ws1.cell(row=r, column=col+18).value = ''

                rows = ws1[f'A{r}:V{r}']
                for row in rows:
                    for cell in row:
                        cell.style = style_border1

            r = r + 1
            ws1.cell(row=r, column=1).value = 'Итого за ' + (utils.strfdatetime(current_date, "%d"))
            ws1.cell(row=r, column=2).value = f'=SUM(B{r1}:B{r-1})'
            ws1.row_dimensions.group(r1, r-1, hidden=True)
            total_sum.append(r)
            rows = ws1[f'A{r}:V{r}']
            for row in rows:
                for cell in row:
                    cell.fill = my_fill

            t_s = '=SUM('
            for ts in total_sum:
                t_s = t_s + f'(B{ts})' + ','
            t_s = t_s + ')'
            r = r + 1
            ws1.cell(row=r, column=1).value = 'Итого Всего'
            ws1.cell(row=r, column=2).value = t_s
            rows = ws1[f'A{r}:V{r}']
            for row in rows:
                for cell in row:
                    cell.fill = total_fill

            return ws1

        start_date = datetime.datetime.combine(d1, datetime.time.min)
        end_date = datetime.datetime.combine(d2, datetime.time.max)
        #Проверить, что роль у объекта Врач-Лаборант, или Лаборант, или Врач параклиники, или Лечащий врач
        if us_o:
            for i in us_o:
                if i.is_member(["Лечащий врач", "Врач-лаборант", "Врач параклиники", "Лаборант", "Врач консультаций"]):
                    ws = wb.create_sheet(i.get_fio())
                    res_oq = sql_func.direct_job_sql(i.pk, start_date, end_date, type_fin)
                    res_job = sql_func.indirect_job_sql(i.pk, start_date, end_date)
                    dict_job = {}
                    for r_j in res_job:
                        key_type_job = r_j[1]
                        key_date = utils.strfdatetime(r_j[0], "%d.%m.%Y")
                        value_total = r_j[2]
                        temp_dict = dict_job.get(key_date,{})
                        temp_dict.update({key_type_job : value_total})
                        dict_job[key_date] = temp_dict

                    ws = structure(ws, i, res_oq, d1, d2, dict_job)

                    if month_obj:
                        date, res, title, title2 = None, None, None, None
                        # issledovaniye_id(0), research_id(1), date_confirm(2), doc_confirmation_id(3), def_uet(4),
                        # co_executor_id(5), co_executor_uet(6), co_executor2_id(7), co_executor2_uet(8), research_id(9),
                        # research_title(10), research - co_executor_2_title(11)
                        # строим стр-ру {дата:{наименование анализа:УЕТ за дату, СО2:УЕТ за дату}}
                        from _collections import OrderedDict
                        total_report_dict = OrderedDict()
                        r_sql = sql_func.total_report_sql(i.pk, start_date, end_date, type_fin)
                        titles_set = OrderedDict()
                        for n in r_sql:
                            titles_set[n[10]] = ''
                            titles_set[n[11]] = ''
                            temp_dict = {}
                            temp_uet, temp_uet2 = 0, 0
                            if (i.pk == n[3]):
                                temp_uet = n[4] if n[4] else 0
                            if (i.pk == n[5]) and (n[5] != n[3]):
                                temp_uet = n[6] if n[6] else 0
                            if i.pk == n[7]:
                                temp_uet2 = n[8] if n[8] else 0
                            #попытка получить значения за дату
                            if total_report_dict.get(n[2]):
                                temp_d = total_report_dict.get(n[2])
                                # попытка получить такие же анализы
                                current_uet = temp_d.get(n[10]) if temp_d.get(n[10]) else 0
                                current_uet2 = temp_d.get(n[11]) if temp_d.get(n[11]) else 0
                                current_uet = current_uet + temp_uet
                                current_uet2 = current_uet2 + temp_uet2
                                temp_dict = {n[10]:current_uet, n[11]:current_uet2}
                                total_report_dict[n[2]].update(temp_dict)
                            else:
                                total_report_dict[int(n[2])] = {n[10]:temp_uet, n[11]:temp_uet2}

                        titles_list = [tk for tk in titles_set.keys()]
                        ws = wb.create_sheet(i.get_fio() + 'Итог')
                        ws = structure_sheet.job_total_base(ws, month_obj)
                        ws, cell_research = structure_sheet.jot_total_titles(ws, titles_list)
                        ws = structure_sheet.job_total_data(ws, cell_research, total_report_dict)

        response['Content-Disposition'] = str.translate("attachment; filename=\"Статталоны.xlsx\"", tr)
        wb.save(response)
        return response

    elif tp == "statistics-research":
        response['Content-Disposition'] = str.translate("attachment; filename=\"Статталоны.xlsx\"", tr)
        pk = request_data.get("pk", "")
        pk = int(pk)
        date_start_o = request_data.get("date-start")
        date_start_o = json.loads(date_start_o)
        date_end_o = request_data.get("date-end")
        date_end_o = json.loads(date_end_o)

        from openpyxl.styles import Font, NamedStyle
        style_o = NamedStyle(name="style_o")
        style_o.font = Font(bold=True, size=11)
        wb = openpyxl.Workbook()
        wb.remove(wb.get_sheet_by_name('Sheet'))
        wb.add_named_style(style_o)
        ws = wb.create_sheet("Отчет")
        from openpyxl.utils.cell import get_column_letter
        col = 1
        ws.column_dimensions[get_column_letter(1)].width = 15
        ws.cell(row=1, column=1).value = 'Дата рождения'
        ws.cell(row=1, column=1).style = style_o
        ws.column_dimensions[get_column_letter(col + 1)].width = 8
        ws.cell(row=1, column=(col+1)).value = 'Возраст'
        ws.cell(row=1, column=(col+1)).style = style_o
        ws.column_dimensions[get_column_letter(col + 2)].width = 35
        ws.cell(row=1, column=(col + 2)).value = 'Физлицо'
        ws.cell(row=1, column=(col + 2)).style = style_o
        ws.column_dimensions[get_column_letter(col + 3)].width = 35
        ws.cell(row=1, column=(col + 3)).value = 'Исследование'
        ws.cell(row=1, column=(col + 3)).style = style_o
        ws.column_dimensions[get_column_letter(col + 4)].width = 35
        ws.cell(row=1, column=(col + 4)).value = 'Дата подтверждения'
        ws.cell(row=1, column=(col + 4)).style = style_o
        ws.column_dimensions[get_column_letter(col + 5)].width = 20
        ws.cell(row=1, column=(col + 5)).value = 'Карта'
        ws.cell(row=1, column=(col + 5)).style = style_o

        import datetime
        res_o = Researches.objects.get(pk=pk)
        d_s = datetime.datetime.strptime(date_start_o, '%d.%m.%Y')
        d_e = datetime.datetime.strptime(date_end_o, '%d.%m.%Y')
        list_o = Issledovaniya.objects.select_related('napravleniye__client').filter(time_confirmation__date__range=(d_s, d_e), research=res_o,
                napravleniye__isnull=False).order_by('time_confirmation')

        r = 1
        for i in list_o:
            r = r + 1
            patient_data = i.napravleniye.client.get_data_individual()
            date_o = utils.strfdatetime(i.time_confirmation, "%d.%m.%Y")
            ws.cell(row=r, column=1).value = patient_data['born']
            ws.cell(row=r, column=col + 1).value = patient_data['age']
            ws.cell(row=r, column=col + 2).value = patient_data['fio']
            ws.cell(row=r, column=col + 3).value = res_o.title
            ws.cell(row=r, column=col + 4).value = date_o
            ws.cell(row=r, column=col + 5).value = patient_data['card_num']

    elif tp == "journal-get-material":
        import datetime
        access_to_all = 'Просмотр статистики' in request.user.groups.values_list('name',
                                                                                 flat=True) or request.user.is_superuser
        users = [x for x in json.loads(users_o) if
                 (access_to_all or (x.isdigit() and int(x) == request.user.doctorprofile.pk)) and DoctorProfile.objects.filter(
                     pk=x).exists()]
        date_values = json.loads(date_values_o)
        monthes = {
            "0": "Январь",
            "1": "Февраль",
            "2": "Март",
            "3": "Апрель",
            "4": "Май",
            "5": "Июнь",
            "6": "Июль",
            "7": "Август",
            "8": "Сентябрь",
            "9": "Октябрь",
            "10": "Ноябрь",
            "11": "Декабрь",
        }
        date_values["month_title"] = monthes[date_values["month"]]
        response['Content-Disposition'] = str.translate("attachment; filename=\"Статистика_Забор_биоматериала.xls\"", tr)
        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1
        font_style.borders = borders

        font_style_b = xlwt.XFStyle()
        font_style_b.alignment.wrap = 1
        font_style_b.font.bold = True
        font_style_b.borders = borders

        for user_pk in users:
            user_row = DoctorProfile.objects.get(pk=user_pk)
            ws = wb.add_sheet("{} {}".format(user_row.get_fio(dots=False), user_pk))
            row_num = 0
            row = [
                ("Исполнитель: ", 4000),
                (user_row.fio, 7600)
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num][0], font_style)
                ws.col(col_num).width = row[col_num][1]

            row_num += 1
            row = [
                "Подразделение: ",
                user_row.podrazdeleniye.title
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)

            row_num += 1
            row = [
                "Дата: ",
                date_values["date"] if date_type == "d" else "{month_title} {year}".format(**date_values)
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
            daterow = row_num
            row_num += 3
            row = [
                ("№", 4000),
                ("ФИО", 7600),
                ("Возраст", 3000),
                ("Карта", 6000),
                ("Число направлений", 5000),
                ("Номера направлений", 6000),
                ("Наименования исследований", 20000),
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num][0], font_style_b)
                ws.col(col_num).width = row[col_num][1]

            row_num += 1

            if date_type == "d":
                day = date_values.get("date", "01.01.2015")
                day1 = datetime.date(int(day.split(".")[2]), int(day.split(".")[1]), int(day.split(".")[0]))
                day2 = day1 + datetime.timedelta(days=1)
            elif date_type == "m":
                month = int(date_values.get("month", "0")) + 1
                next_m = month + 1 if month < 12 else 1
                year = int(date_values.get("year", "2015"))
                next_y = year + 1 if next_m == 1 else year
                day1 = datetime.date(year, month, 1)
                day2 = datetime.date(next_y, next_m, 1)
            else:
                day1 = day2 = timezone.now()

            iss_list = Issledovaniya.objects.filter(tubes__doc_get=user_row, tubes__time_get__isnull=False,
                                                    tubes__time_get__range=(day1, day2)).order_by(
                "napravleniye__client__individual__patronymic",
                "napravleniye__client__individual__name",
                "napravleniye__client__individual__family").distinct()
            patients = {}
            for iss in iss_list:
                k = iss.napravleniye.client.individual_id
                if k not in patients:
                    client = iss.napravleniye.client.individual
                    patients[k] = {"fio": client.fio(short=True, dots=True),
                                   "age": client.age_s(direction=iss.napravleniye), "directions": [], "researches": [],
                                   "cards": []}
                if iss.napravleniye_id not in patients[k]["directions"]:
                    patients[k]["directions"].append(iss.napravleniye_id)
                kn = iss.napravleniye.client.number_with_type()
                if kn not in patients[k]["cards"]:
                    patients[k]["cards"].append(kn)
                patients[k]["researches"].append(iss.research.title)

            n = 0
            for p_pk in patients:
                n += 1
                row = [
                    str(n),
                    patients[p_pk]["fio"],
                    patients[p_pk]["age"],
                    ", ".join(patients[p_pk]["cards"]),
                    len(patients[p_pk]["directions"]),
                    ", ".join([str(x) for x in patients[p_pk]["directions"]]),
                    ", ".join(patients[p_pk]["researches"]),
                ]
                for col_num in range(len(row)):
                    ws.write(row_num, col_num, row[col_num], font_style)

                row_num += 1

            row = [
                "Число пациентов: ",
                str(len(patients))
            ]
            for col_num in range(len(row)):
                ws.write(daterow + 1, col_num, row[col_num], font_style)

    elif tp == "lab":
        lab = Podrazdeleniya.objects.get(pk=int(pk))
        response['Content-Disposition'] = str.translate(
            "attachment; filename=\"Статистика_Лаборатория_{}_{}-{}.xls\"".format(lab.title.replace(" ", "_"),
                                                                                date_start_o, date_end_o), tr)

        import directions.models as d
        from operator import itemgetter
        date_start, date_end = try_parse_range(date_start_o, date_end_o)

        for card_base in list(CardBase.objects.filter(hide=False)) + [None]:
            cb_title = "Все базы" if not card_base else card_base.short_title
            for finsource in list(IstochnikiFinansirovaniya.objects.filter(base=card_base)) + [False]:
                finsource_title = "Все источники"

                if isinstance(finsource, IstochnikiFinansirovaniya):
                    finsource_title = finsource.title

                ws = wb.add_sheet(cb_title + " " + finsource_title + " выполн.")

                font_style = xlwt.XFStyle()
                font_style.borders = borders
                row_num = 0
                row = [
                    "Период: ",
                    "{0} - {1}".format(date_start_o, date_end_o)
                ]

                for col_num in range(len(row)):
                    if col_num == 0:
                        ws.write(row_num, col_num, row[col_num], font_style)
                    else:
                        ws.write_merge(row_num, row_num, col_num, col_num + 2, row[col_num], style=font_style)

                row_num += 1

                font_style = xlwt.XFStyle()
                font_style.borders = borders

                row = [
                    (lab.title, 16000)
                ]

                for col_num in range(len(row)):
                    ws.write(row_num, col_num, row[col_num][0], font_style)
                    ws.col(col_num).width = row[col_num][1]
                    ws.write(row_num, col_num + 1, "", font_style)

                row_num = 2
                row = [
                    "Выполнено исследований",
                    cb_title + " " + finsource_title
                ]

                for col_num in range(len(row)):
                    if col_num == 0:
                        ws.write(row_num, col_num, row[col_num], font_style)
                    else:
                        ws.write_merge(row_num, row_num, col_num, col_num + 1, row[col_num], style=font_style)

                font_style = xlwt.XFStyle()
                font_style.alignment.wrap = 1
                font_style.borders = borders
                pki = int(pk)
                otds = {pki: defaultdict(lambda: 0)}
                otds_pat = {pki: defaultdict(lambda: 0)}

                ns = 0
                for obj in directory.Researches.objects.filter(podrazdeleniye__pk=lab.pk):
                    if finsource is not False:
                        iss_list = Issledovaniya.objects.filter(research__pk=obj.pk, time_confirmation__isnull=False,
                                                                time_confirmation__range=(date_start, date_end),
                                                                napravleniye__istochnik_f=finsource)
                    elif card_base:
                        iss_list = Issledovaniya.objects.filter(research__pk=obj.pk, time_confirmation__isnull=False,
                                                                time_confirmation__range=(date_start, date_end),
                                                                napravleniye__istochnik_f__base=card_base)
                    else:
                        iss_list = Issledovaniya.objects.filter(research__pk=obj.pk, time_confirmation__isnull=False,
                                                                time_confirmation__range=(date_start, date_end))

                    for researches in iss_list:
                        n = False
                        for x in d.Result.objects.filter(issledovaniye=researches):
                            x = x.value.lower().strip()
                            n = any([y in x for y in
                                     ["забор", "тест", "неправ", "ошибк", "ошибочный", "кров", "брак", "мало",
                                      "недостаточно", "реактив"]]) or x == "-"
                            if n:
                                break
                        if n:
                            continue
                        otd_pk = "external-" + str(
                            researches.napravleniye.imported_org_id) if not researches.napravleniye.doc else researches.napravleniye.doc.podrazdeleniye_id
                        if otd_pk not in otds:
                            otds[otd_pk] = defaultdict(lambda: 0)
                        otds[otd_pk][obj.pk] += 1
                        otds[pki][obj.pk] += 1
                        if any([x.get_is_norm() == "normal" for x in researches.result_set.all()]):
                            continue
                        if otd_pk not in otds_pat:
                            otds_pat[otd_pk] = defaultdict(lambda: 0)
                        otds_pat[otd_pk][obj.pk] += 1
                        otds_pat[pki][obj.pk] += 1

                style = xlwt.XFStyle()
                style.borders = borders
                font = xlwt.Font()
                font.bold = True
                style.font = font
                otd_local_keys = [x for x in otds.keys() if isinstance(x, int)]
                otd_external_keys = [int(x.replace("external-", "")) for x in otds.keys() if
                                     isinstance(x, str) and "external-" in x]
                for otdd in list(Podrazdeleniya.objects.filter(pk=pki)) + list(
                        Podrazdeleniya.objects.filter(pk__in=[x for x in otd_local_keys if x != pki])) + list(
                    RMISOrgs.objects.filter(pk__in=otd_external_keys)):
                    row_num += 2
                    row = [
                        otdd.title if otdd.pk != pki else "Сумма по всем отделениям",
                        "" if otdd.pk != pki else "Итого",
                    ]
                    for col_num in range(len(row)):
                        ws.write(row_num, col_num, row[col_num], style=style)
                    rows = []
                    ok = otds.get(otdd.pk, otds.get("external-{}".format(otdd.pk), {}))
                    for obj in directory.Researches.objects.filter(pk__in=[x for x in ok.keys()]):
                        row = [
                            obj.title,
                            ok[obj.pk],
                        ]
                        rows.append(row)
                        ns += 1
                    for row in sorted(rows, key=itemgetter(0)):
                        row_num += 1
                        for col_num in range(len(row)):
                            ws.write(row_num, col_num, row[col_num], font_style)

                ws_pat = wb.add_sheet(cb_title + " " + finsource_title + " паталог.")

                row_num = 0
                row = [
                    "Период: ",
                    "{0} - {1}".format(date_start_o, date_end_o)
                ]

                for col_num in range(len(row)):
                    if col_num == 0:
                        ws_pat.write(row_num, col_num, row[col_num], font_style)
                    else:
                        ws_pat.write_merge(row_num, row_num, col_num, col_num + 2, row[col_num], style=font_style)

                row_num = 1
                row = [
                    (lab.title, 16000),
                ]

                for col_num in range(len(row)):
                    ws_pat.write(row_num, col_num, row[col_num][0], font_style)
                    ws_pat.col(col_num).width = row[col_num][1]
                    ws_pat.write(row_num, col_num + 1, "", font_style)

                font_style = xlwt.XFStyle()
                font_style.borders = borders

                row_num = 2
                row = [
                    "Паталогии",
                    cb_title + " " + finsource_title
                ]

                for col_num in range(len(row)):
                    if col_num == 0:
                        ws_pat.write(row_num, col_num, row[col_num], font_style)
                    else:
                        ws_pat.write_merge(row_num, row_num, col_num, col_num + 1, row[col_num], style=font_style)

                otd_local_keys = [x for x in otds_pat.keys() if isinstance(x, int)]
                otd_external_keys = [int(x.replace("external-", "")) for x in otds_pat.keys() if
                                     isinstance(x, str) and "external-" in x]

                for otdd in list(Podrazdeleniya.objects.filter(pk=pki)) + list(
                        Podrazdeleniya.objects.filter(pk__in=[x for x in otd_local_keys if x != pki])) + list(
                    RMISOrgs.objects.filter(pk__in=otd_external_keys)):
                    row_num += 2
                    row = [
                        otdd.title,
                        "" if otdd.pk != pki else "Итого",
                    ]
                    for col_num in range(len(row)):
                        ws_pat.write(row_num, col_num, row[col_num], style=style)
                    rows = []
                    ok = otds_pat.get(otdd.pk, otds_pat.get("external-{}".format(otdd.pk), {}))
                    for obj in directory.Researches.objects.filter(pk__in=[x for x in otds_pat.get(otdd.pk, ok.keys())]):
                        row = [
                            obj.title,
                            ok[obj.pk],
                        ]
                        rows.append(row)
                    for row in sorted(rows, key=itemgetter(0)):
                        row_num += 1
                        for col_num in range(len(row)):
                            ws_pat.write(row_num, col_num, row[col_num], font_style)
                if ns == 0:
                    ws.sheet_visible = False
                    ws_pat.sheet_visible = False

    elif tp == "lab-staff":
        lab = Podrazdeleniya.objects.get(pk=int(pk))
        researches = list(
            directory.Researches.objects.filter(podrazdeleniye=lab, hide=False).order_by('title').order_by(
                "sort_weight").order_by("direction_id"))
        pods = list(Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT).order_by("title"))
        response['Content-Disposition'] = str.translate(
            "attachment; filename=\"Статистика_Исполнители_Лаборатория_{0}_{1}-{2}.xls\"".format(
                lab.title.replace(" ", "_"),
                date_start_o, date_end_o), tr)
        import datetime
        import directions.models as d
        from operator import itemgetter
        date_start, date_end = try_parse_range(date_start_o, date_end_o)
        iss = Issledovaniya.objects.filter(research__podrazdeleniye=lab, time_confirmation__isnull=False,
                                           time_confirmation__range=(date_start, date_end))

        font_style_wrap = xlwt.XFStyle()
        font_style_wrap.alignment.wrap = 1
        font_style_wrap.borders = borders
        font_style_vertical = xlwt.easyxf('align: rotation 90')
        font_style_vertical.borders = borders

        def val(v):
            return "" if v == 0 else v

        def nl(v):
            return v + ("" if len(v) > 19 else "\n")

        for executor in DoctorProfile.objects.filter(user__groups__name__in=("Врач-лаборант", "Лаборант"),
                                                     podrazdeleniye__p_type=Podrazdeleniya.LABORATORY).order_by(
            "fio").distinct():

            cnt_itogo = {}
            ws = wb.add_sheet(executor.get_fio(dots=False) + " " + str(executor.pk))

            row_num = 0
            row = [
                ("Исполнитель", 5500),
                ("Отделение", 5000)
            ]

            from django.utils.text import Truncator

            for research in researches:
                row.append((Truncator(research.title).chars(30), 1300,))

            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num][0], font_style_wrap if col_num < 2 else font_style_vertical)
                ws.col(col_num).width = row[col_num][1]

            row_num += 1
            itogo_row = [executor.get_fio(dots=True), nl("Итого")]
            empty_row = ["", ""]
            cnt_local_itogo = {}
            for pod in pods:
                row = [
                    executor.get_fio(dots=True),
                    nl(pod.title)
                ]
                cnt = {}
                for research in researches:
                    if research.title not in cnt.keys():
                        cnt[research.title] = 0
                    if research.title not in cnt_local_itogo.keys():
                        cnt_local_itogo[research.title] = 0
                    if research.title not in cnt_itogo.keys():
                        cnt_itogo[research.title] = 0

                    for i in iss.filter(doc_confirmation=executor, napravleniye__doc__podrazdeleniye=pod,
                                        research=research):
                        isadd = False
                        allempty = True
                        for r in Result.objects.filter(issledovaniye=i):
                            value = r.value.lower().strip()
                            if value != "":
                                allempty = False
                                n = any([y in value for y in
                                         ["забор", "тест", "неправ", "ошибк", "ошибочный", "кров", "брак", "мало",
                                          "недостаточно", "реактив"]])
                                if not n:
                                    isadd = True

                        if not isadd or allempty:
                            continue

                        cnt[research.title] += 1
                        cnt_itogo[research.title] += 1
                        cnt_local_itogo[research.title] += 1
                for research in researches:
                    row.append(val(cnt[research.title]))
                    # data["otds"][pod.title] += 1
                    # data["all"][pod.title] += 1
                    # cnt_all[pod.title] += 1
                for col_num in range(len(row)):
                    ws.write(row_num, col_num, row[col_num], font_style_wrap)
                row_num += 1

            for research in researches:
                itogo_row.append(val(cnt_local_itogo[research.title]))
                empty_row.append("")
            for col_num in range(len(itogo_row)):
                ws.write(row_num, col_num, itogo_row[col_num], font_style_wrap)
            row_num += 1
    elif tp == "otd":
        otd = Podrazdeleniya.objects.get(pk=int(pk))
        response['Content-Disposition'] = str.translate(
            "attachment; filename=\"Статистика_Отделение_{0}_{1}-{2}.xls\"".format(otd.title.replace(" ", "_"),
                                                                                 date_start_o, date_end_o), tr)

        ws = wb.add_sheet("Выписано направлений")

        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            "{0} - {1}".format(date_start_o, date_end_o)
        ]

        date_start_o, date_end_o = try_parse_range(date_start_o, date_end_o)

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1

        font_style = xlwt.XFStyle()

        row = [
            otd.title
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

        font_style = xlwt.XFStyle()

        row_num += 1
        row = [
            (u"Всего выписано", 6000),
            (str(Napravleniya.objects.filter(doc__podrazdeleniye=otd,
                                             data_sozdaniya__range=(date_start_o, date_end_o)).count()), 3000),
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num][0], font_style)
            ws.col(col_num).width = row[col_num][1]

        row_num += 1
        researches = Issledovaniya.objects.filter(napravleniye__doc__podrazdeleniye=otd,
                                                  napravleniye__data_sozdaniya__range=(date_start_o, date_end_o),
                                                  time_confirmation__isnull=False)
        naprs = len(set([v.napravleniye_id for v in researches]))
        row = [
            u"Завершенных",
            str(naprs)
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    elif tp == "list-users":
        response['Content-Disposition'] = str.translate("attachment; filename=\"Список_пользователей.xls\"", tr)
        ws = wb.add_sheet("Пользователи")
        row_num = 0
        font_style = xlwt.XFStyle()
        for p in Podrazdeleniya.objects.filter(hide=False).order_by("title"):
            has = False
            for u in DoctorProfile.objects.filter(podrazdeleniye=p).exclude(user__username="admin").order_by("fio"):
                has = True
                row = [
                    ("ID отделения %s" % p.pk, 9000),
                    (p.title, 9000),
                    ("ID пользователя %s" % u.pk, 9000),
                    (u.user.username, 5000),
                    (u.fio, 10000)
                ]
                for col_num in range(len(row)):
                    ws.write(row_num, col_num, row[col_num][0], font_style)
                    ws.col(col_num).width = row[col_num][1]
                row_num += 1
            if has:
                row_num += 1
    elif tp == "lab-receive":
        lab = Podrazdeleniya.objects.get(pk=int(pk))
        response['Content-Disposition'] = str.translate(
            "attachment; filename=\"Статистика_Принято_емкостей_{0}_{1}-{2}.xls\"".format(lab.title.replace(" ", "_"),
                                                                                        date_start_o, date_end_o), tr)

        import directions.models as d
        from operator import itemgetter
        date_start, date_end = try_parse_range(date_start_o, date_end_o)
        ws = wb.add_sheet(lab.title)

        font_style_wrap = xlwt.XFStyle()
        font_style_wrap.alignment.wrap = 1
        font_style_wrap.borders = borders
        font_style = xlwt.XFStyle()
        font_style.borders = borders

        row_num = 0
        row = [
            (lab.title + ", принято емкостей за {0}-{1}".format(date_start_o, date_end_o), 16000),
        ]

        replace = [{"from": "-", "to": " "}, {"from": ".", "to": " "}, {"from": " и ", "to": " "}]
        n = len(row) - 1
        pods = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.DEPARTMENT).order_by("title")
        for pod in pods:
            n += 1
            title = pod.title
            for rep in replace:
                title = title.replace(rep["from"], rep["to"])

            tmp = title.split()
            title = []
            nx = 0
            for x in tmp:
                x = x.strip()
                if len(x) == 0:
                    continue

                title.append(x if x.isupper() else x[0].upper() + ("" if nx > 0 else x[1:7]))
                nx += 1

            row.append(("".join(title), 3700,))
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num][0], font_style)
            ws.col(col_num).width = row[col_num][1]
        row_num += 1

        for tube in directory.Tubes.objects.filter(
                releationsft__fractions__research__podrazdeleniye=lab).distinct().order_by("title"):
            row = [
                tube.title
            ]
            for pod in pods:
                gets = d.TubesRegistration.objects.filter(issledovaniya__research__podrazdeleniye=lab,
                                                          type__tube=tube,
                                                          time_recive__range=(date_start, date_end),
                                                          doc_get__podrazdeleniye=pod).filter(
                    Q(notice="") |
                    Q(notice__isnull=True)).distinct()
                row.append("" if not gets.exists() else str(gets.count()))

            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
            row_num += 1

    elif tp == "all-labs":
        labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации")
        response['Content-Disposition'] = str.translate(
            "attachment; filename=\"Статистика_Все_Лаборатории_{0}-{1}.xls\"".format(date_start_o, date_end_o), tr)
        ws = wb.add_sheet("Выполненых анализов")

        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            "{0} - {1}".format(date_start_o, date_end_o)
        ]

        date_start_o, date_end_o = try_parse_range(date_start_o, date_end_o)

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = [
            (u"Лаборатория", 9000),
            (u"Выполнено анализов", 8000),
        ]

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num][0], font_style)
            ws.col(col_num).width = columns[col_num][1]

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1
        all = 0
        for lab in labs:
            row_num += 1
            c = Issledovaniya.objects.filter(research__podrazdeleniye=lab, time_confirmation__isnull=False,
                                             time_confirmation__range=(date_start_o, date_end_o)).count()
            row = [
                lab.title,
                c
            ]
            all += c
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1
        row = [
            "",
            "Всего: " + str(all),
        ]
        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 3
        font_style.alignment.horz = 3
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    elif tp == "tubes-using":
        response['Content-Disposition'] = str.translate(
            "attachment; filename=\"Статистика_Использование_Емкостей_{0}-{1}.xls\"".format(date_start_o, date_end_o), tr)

        per = "{0} - {1}".format(date_start_o, date_end_o)

        ws = wb.add_sheet("Общее использование емкостей")
        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            per
        ]

        date_start_o, date_end_o = try_parse_range(date_start_o, date_end_o)

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1

        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        columns = [
            (u"Тип емкости", 9000),
            (u"Материал взят в процедурном каб", 9000),
            (u"Принято лабораторией", 8000),
            (u"Не принято лабораторией", 8000),
            (u"Потеряны", 4000),
        ]

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num][0], font_style)
            ws.col(col_num).width = columns[col_num][1]

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1
        all_get = 0
        all_rec = 0
        all_nrec = 0
        all_lost = 0
        for tube in Tubes.objects.all():
            row_num += 1
            c_get = TubesRegistration.objects.filter(type__tube=tube, time_get__isnull=False,
                                                     time_get__range=(date_start_o, date_end_o)).count()
            c_rec = TubesRegistration.objects.filter(type__tube=tube, time_recive__isnull=False, notice="",
                                                     time_get__range=(date_start_o, date_end_o)).count()
            c_nrec = TubesRegistration.objects.filter(type__tube=tube, time_get__isnull=False,
                                                      time_get__range=(date_start_o, date_end_o)).exclude(
                notice="").count()
            str1 = ""
            str2 = ""
            if c_nrec > 0:
                str1 = str(c_nrec)
            if c_get - c_rec - all_nrec > 0:
                str2 = str(c_get - c_rec - all_nrec)
                all_lost += c_get - c_rec - all_nrec

            row = [
                tube.title,
                c_get,
                c_rec,
                str1,
                str2
            ]
            all_get += c_get
            all_rec += c_rec
            all_nrec += c_nrec
            for col_num in range(len(row)):
                font_style.alignment.wrap = 1
                font_style.alignment.horz = 1
                if col_num > 0:
                    font_style.alignment.wrap = 3
                    font_style.alignment.horz = 3
                ws.write(row_num, col_num, row[col_num], font_style)

        labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).exclude(title="Внешние организации")
        for lab in labs:
            ws = wb.add_sheet(lab.title)
            font_style = xlwt.XFStyle()
            row_num = 0
            row = [
                "За период: ",
                per
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
            row_num += 1

            font_style = xlwt.XFStyle()
            font_style.font.bold = True
            columns = [
                (u"Тип емкости", 9000),
                (u"Материал взят в процедурном каб", 9000),
                (u"Принято лабораторией", 8000),
                (u"Не принято лабораторией", 8000),
                (u"Потеряны", 4000),
            ]

            for col_num in range(len(columns)):
                ws.write(row_num, col_num, columns[col_num][0], font_style)
                ws.col(col_num).width = columns[col_num][1]

            font_style = xlwt.XFStyle()
            font_style.alignment.wrap = 1
            all_get = 0
            all_rec = 0
            all_nrec = 0
            all_lost = 0
            for tube in Tubes.objects.all():

                row_num += 1
                c_get = TubesRegistration.objects.filter(issledovaniya__research__podrazdeleniye=lab,
                                                         type__tube=tube, time_get__isnull=False,
                                                         time_get__range=(date_start_o, date_end_o)).count()
                c_rec = TubesRegistration.objects.filter(issledovaniya__research__podrazdeleniye=lab,
                                                         type__tube=tube, time_recive__isnull=False, notice="",
                                                         time_get__range=(date_start_o, date_end_o)).count()
                c_nrec = TubesRegistration.objects.filter(issledovaniya__research__podrazdeleniye=lab,
                                                          type__tube=tube, time_get__isnull=False,
                                                          time_get__range=(date_start_o, date_end_o)).exclude(
                    notice="").count()
                str1 = ""
                str2 = ""
                if c_nrec > 0:
                    str1 = str(c_nrec)
                if c_get - c_rec - all_nrec > 0:
                    str2 = str(c_get - c_rec - all_nrec)
                    all_lost += c_get - c_rec - all_nrec

                row = [
                    tube.title,
                    c_get,
                    c_rec,
                    str1,
                    str2
                ]
                all_get += c_get
                all_rec += c_rec
                all_nrec += c_nrec
                for col_num in range(len(row)):
                    font_style.alignment.wrap = 1
                    font_style.alignment.horz = 1
                    if col_num > 0:
                        font_style.alignment.wrap = 3
                        font_style.alignment.horz = 3
                    ws.write(row_num, col_num, row[col_num], font_style)

    elif tp == "uets":
        usrs = DoctorProfile.objects.filter(podrazdeleniye__p_type=Podrazdeleniya.LABORATORY).order_by(
            "podrazdeleniye__title")
        response['Content-Disposition'] = str.translate(
            "attachment; filename=\"Статистика_УЕТс_{0}-{1}.xls\"".format(date_start_o, date_end_o), tr)

        ws = wb.add_sheet("УЕТы")

        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            "{0} - {1}".format(date_start_o, date_end_o)
        ]

        date_start_o, date_end_o = try_parse_range(date_start_o, date_end_o)

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        row_num += 1
        row = [
            (u"Лаборатория", 8000),
            (u"ФИО", 8000),
            (u"УЕТы", 2500),
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num][0], font_style)
            ws.col(col_num).width = row[col_num][1]

        font_style = xlwt.XFStyle()
        for usr in usrs:
            researches_uets = {}
            researches = Issledovaniya.objects.filter(doc_save=usr, time_save__isnull=False,
                                                      time_save__range=(date_start_o, date_end_o))
            for issledovaniye in researches:
                if usr.labtype == 1:
                    uet_tmp = sum(
                        [v.uet_doc for v in directory.Fractions.objects.filter(research=issledovaniye.research)])
                else:
                    uet_tmp = sum(
                        [v.uet_lab for v in directory.Fractions.objects.filter(research=issledovaniye.research)])
                researches_uets[issledovaniye.pk] = {"uet": uet_tmp}
            researches = Issledovaniya.objects.filter(doc_confirmation=usr, time_confirmation__isnull=False,
                                                      time_confirmation__range=(date_start_o, date_end_o))
            for issledovaniye in researches:
                if usr.labtype == 1:
                    uet_tmp = sum(
                        [v.uet_doc for v in directory.Fractions.objects.filter(research=issledovaniye.research)])
                else:
                    uet_tmp = sum(
                        [v.uet_lab for v in directory.Fractions.objects.filter(research=issledovaniye.research)])
                researches_uets[issledovaniye.pk] = {"uet": uet_tmp}
            uets = sum([researches_uets[v]["uet"] for v in researches_uets.keys()])
            row_num += 1
            row = [
                usr.podrazdeleniye.title,
                usr.fio,
                uets,
            ]
            for col_num in range(len(row)):
                font_style.alignment.wrap = 1
                font_style.alignment.horz = 1
                if col_num > 2:
                    font_style.alignment.wrap = 3
                    font_style.alignment.horz = 3
                ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response
