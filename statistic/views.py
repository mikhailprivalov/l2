from collections import defaultdict

import collections

from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import simplejson as json
import slog.models as slog
from clients.models import CardBase
from laboratory.decorators import group_required
from django.shortcuts import render
from users.models import Podrazdeleniya
from directions.models import Napravleniya, Issledovaniya, TubesRegistration, Tubes, IstochnikiFinansirovaniya, Result
import directory.models as directory
from django.http import HttpResponse
from users.models import DoctorProfile


@csrf_exempt
@login_required
def statistic_page(request):
    """ Страница статистики """
    labs = Podrazdeleniya.objects.filter(isLab=True)  # Лаборатории
    tubes = directory.Tubes.objects.all()  # Пробирки
    podrs = Podrazdeleniya.objects.filter(isLab=False, hide=False)  # Подлазделения
    getters_material = DoctorProfile.objects.filter(user__groups__name='Заборщик биоматериала').distinct()
    return render(request, 'statistic.html', {"labs": labs, "tubes": tubes, "podrs": podrs, "getters_material": json.dumps([{"pk": str(x.pk), "fio": str(x)} for x in getters_material])})


@csrf_exempt
@login_required
def statistic_xls(request):
    """ Генерация XLS """
    from directions.models import Issledovaniya
    import xlwt

    wb = xlwt.Workbook(encoding='utf-8')
    response = HttpResponse(content_type='application/ms-excel')
    if request.method == "POST":
        pk = request.POST.get("pk", "")  # Первичный ключ
        tp = request.POST.get("type", "")  # Тип статистики
        date_start_o = request.POST.get("date-start", "")  # Начало периода
        date_end_o = request.POST.get("date-end", "")  # Конец периода
        users_o = request.POST.get("users", "[]")
        date_values_o = request.POST.get("values", "{}")
        date_type = request.POST.get("date_type", "d")
    else:
        pk = request.GET.get("pk", "")
        tp = request.GET.get("type", "")  # Тип статистики
        date_start_o = request.GET.get("date-start", "")  # Начало периода
        date_end_o = request.GET.get("date-end", "")  # Конец периода
        users_o = request.GET.get("users", "[]")
        date_values_o = request.GET.get("values", "{}")
        date_type = request.GET.get("date_type", "d")

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

    if tp == "journal-get-material":
        import datetime
        access_to_all = 'Статистика' in request.user.groups.values_list('name', flat=True) or request.user.is_superuser
        users = [x for x in json.loads(users_o) if (access_to_all or int(x) == request.user.doctorprofile) and DoctorProfile.objects.filter(pk=x).exists()]
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
        response['Content-Disposition'] = str.translate("attachment; filename='Статистика_Забор_биоматериала.xls'", tr)
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
                (user_row.fio, 10000)
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

            row_num += 2
            row = [
                ("№", 4000),
                ("ФИО", 10000),
                ("Возраст", 3000),
                ("Число направлений", 5000),
                ("Наименования исследований", 20000),
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style_b)

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

            iss_list = Issledovaniya.objects.filter(tubes__doc_get=user_row, tubes__time_get__isnull=False, tubes__time_get__range=(day1, day2)).order_by("napravleniye__client__individual__patronymic",
                                                                                                                                                          "napravleniye__client__individual__name",
                                                                                                                                                          "napravleniye__client__individual__family").distinct()
            patients = {}
            for iss in iss_list:
                k = iss.napravleniye.client.individual.pk
                if k not in patients:
                    client = iss.napravleniye.client.individual
                    patients[k] = {"fio": client.fio(short=True, dots=True), "age": client.age_s(direction=iss.napravleniye), "directions": []}
                if iss.napravleniye.pk not in patients[k]["directions"]:
                    patients[k]["directions"].append(iss.napravleniye.pk)
            n = 0
            for p_pk in patients:
                n += 1

        ws = wb.add_sheet("Все выбранные пользователи")
    elif tp == "lab":
        lab = Podrazdeleniya.objects.get(pk=int(pk))
        response['Content-Disposition'] = str.translate("attachment; filename='Статистика_Лаборатория_{}_{}-{}.xls'".format(lab.title.replace(" ", "_"), date_start_o, date_end_o), tr)

        import datetime
        import directions.models as d
        from operator import itemgetter
        date_start = datetime.date(int(date_start_o.split(".")[2]), int(date_start_o.split(".")[1]),
                                   int(date_start_o.split(".")[0]))
        date_end = datetime.date(int(date_end_o.split(".")[2]), int(date_end_o.split(".")[1]),
                                 int(date_end_o.split(".")[0])) + datetime.timedelta(1)

        for card_base in CardBase.objects.filter(hide=False):
            for finsource in list(IstochnikiFinansirovaniya.objects.filter(base=card_base)) + [False]:
                finsource_title = "Все источники"

                if finsource is not False:
                    finsource_title = finsource.title

                ws = wb.add_sheet(card_base.short_title + " " + finsource_title + " выполн.")

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
                    card_base.title + " " + finsource_title
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

                def all(iterable):
                    for element in iterable:
                        if not element:
                            return False
                    return True

                ns = 0
                for obj in directory.Researches.objects.filter(podrazdeleniye__pk=lab.pk):
                    iss_list = []
                    if finsource is not False:
                        iss_list = Issledovaniya.objects.filter(research__pk=obj.pk, time_confirmation__isnull=False,
                                                                time_confirmation__range=(date_start, date_end),
                                                                napravleniye__istochnik_f=finsource)
                    else:
                        iss_list = Issledovaniya.objects.filter(research__pk=obj.pk, time_confirmation__isnull=False,
                                                                time_confirmation__range=(date_start, date_end),
                                                                napravleniye__istochnik_f__base=card_base)

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

                        if researches.napravleniye.doc.podrazdeleniye.pk not in otds:
                            otds[researches.napravleniye.doc.podrazdeleniye.pk] = defaultdict(lambda: 0)
                        otds[researches.napravleniye.doc.podrazdeleniye.pk][obj.pk] += 1
                        otds[pki][obj.pk] += 1
                        if any([x.get_is_norm() == "normal" for x in researches.result_set.all()]):
                            continue
                        if researches.napravleniye.doc.podrazdeleniye.pk not in otds_pat:
                            otds_pat[researches.napravleniye.doc.podrazdeleniye.pk] = defaultdict(lambda: 0)
                        otds_pat[researches.napravleniye.doc.podrazdeleniye.pk][obj.pk] += 1
                        otds_pat[pki][obj.pk] += 1

                style = xlwt.XFStyle()
                style.borders = borders
                font = xlwt.Font()
                font.bold = True
                style.font = font
                for otdd in list(Podrazdeleniya.objects.filter(pk=pki)) + list(
                        Podrazdeleniya.objects.filter(pk__in=[x for x in otds.keys() if x != pki])):
                    row_num += 2
                    row = [
                        otdd.title,
                        "" if otdd.pk != pki else "Итого",
                    ]
                    for col_num in range(len(row)):
                        ws.write(row_num, col_num, row[col_num], style=style)
                    rows = []
                    for obj in directory.Researches.objects.filter(pk__in=[x for x in otds[otdd.pk].keys()]):
                        row = [
                            obj.title,
                            otds[otdd.pk][obj.pk],
                        ]
                        rows.append(row)
                        ns += 1
                    for row in sorted(rows, key=itemgetter(0)):
                        row_num += 1
                        for col_num in range(len(row)):
                            ws.write(row_num, col_num, row[col_num], font_style)

                ws_pat = wb.add_sheet(card_base.short_title + " " + finsource_title + " паталог.")

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
                    card_base.title + " " + finsource_title
                ]

                for col_num in range(len(row)):
                    if col_num == 0:
                        ws_pat.write(row_num, col_num, row[col_num], font_style)
                    else:
                        ws_pat.write_merge(row_num, row_num, col_num, col_num + 1, row[col_num], style=font_style)

                for otdd in list(Podrazdeleniya.objects.filter(pk=pki)) + list(
                        Podrazdeleniya.objects.filter(pk__in=[x for x in otds_pat.keys() if x != pki])):
                    row_num += 2
                    row = [
                        otdd.title,
                        "" if otdd.pk != pki else "Итого",
                    ]
                    for col_num in range(len(row)):
                        ws_pat.write(row_num, col_num, row[col_num], style=style)
                    rows = []
                    for obj in directory.Researches.objects.filter(pk__in=[x for x in otds_pat[otdd.pk].keys()]):
                        row = [
                            obj.title,
                            otds_pat[otdd.pk][obj.pk],
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
            directory.Researches.objects.filter(podrazdeleniye=lab, hide=False).order_by('title').order_by("sort_weight").order_by("direction_id"))
        pods = list(Podrazdeleniya.objects.filter(hide=False, isLab=False).order_by("title"))
        response['Content-Disposition'] = str.translate(
            "attachment; filename='Статистика_Исполнители_Лаборатория_{0}_{1}-{2}.xls'".format(
                lab.title.replace(" ", "_"),
                date_start_o, date_end_o), tr)
        import datetime
        import directions.models as d
        from operator import itemgetter
        date_start = datetime.date(int(date_start_o.split(".")[2]), int(date_start_o.split(".")[1]),
                                   int(date_start_o.split(".")[0]))
        date_end = datetime.date(int(date_end_o.split(".")[2]), int(date_end_o.split(".")[1]),
                                 int(date_end_o.split(".")[0])) + datetime.timedelta(1)
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

        for executor in DoctorProfile.objects.filter(user__groups__name__in=("Врач-лаборант", "Лаборант"), podrazdeleniye__isLab=True).order_by("fio").distinct():

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
            data = {"otds": {}, "all": defaultdict(lambda: 0)}
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
            "attachment; filename='Статистика_Отделение_{0}_{1}-{2}.xls'".format(otd.title.replace(" ", "_"),
                                                                                 date_start_o, date_end_o), tr)

        ws = wb.add_sheet("Выписано направлений")
        row_num = 0

        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            "{0} - {1}".format(date_start_o, date_end_o)
        ]

        import datetime
        date_start_o = datetime.date(int(date_start_o.split(".")[2]), int(date_start_o.split(".")[1]),
                                     int(date_start_o.split(".")[0]))
        date_end_o = datetime.date(int(date_end_o.split(".")[2]), int(date_end_o.split(".")[1]),
                                   int(date_end_o.split(".")[0])) + datetime.timedelta(1)

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
        naprs = len(set([v.napravleniye.pk for v in researches]))
        row = [
            u"Завершенных",
            str(naprs)
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    elif tp == "list-users":
        response['Content-Disposition'] = str.translate("attachment; filename='Список_пользователей.xls'", tr)
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
            "attachment; filename='Статистика_Принято_емкостей_{0}_{1}-{2}.xls'".format(lab.title.replace(" ", "_"),
                                                                                        date_start_o, date_end_o), tr)

        import datetime
        import directions.models as d
        from operator import itemgetter
        date_start = datetime.date(int(date_start_o.split(".")[2]), int(date_start_o.split(".")[1]),
                                   int(date_start_o.split(".")[0]))
        date_end = datetime.date(int(date_end_o.split(".")[2]), int(date_end_o.split(".")[1]),
                                 int(date_end_o.split(".")[0])) + datetime.timedelta(1)
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
        otds = {}
        n = len(row) - 1
        pods = Podrazdeleniya.objects.filter(isLab=False, hide=False).order_by("title")
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
        labs = Podrazdeleniya.objects.filter(isLab=True)
        response['Content-Disposition'] = str.translate(
            "attachment; filename='Статистика_Все_Лаборатории_{0}-{1}.xls'".format(date_start_o, date_end_o), tr)
        ws = wb.add_sheet("Выполненых анализов")

        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            "{0} - {1}".format(date_start_o, date_end_o)
        ]

        import datetime
        date_start_o = datetime.date(int(date_start_o.split(".")[2]), int(date_start_o.split(".")[1]),
                                     int(date_start_o.split(".")[0]))
        date_end_o = datetime.date(int(date_end_o.split(".")[2]), int(date_end_o.split(".")[1]),
                                   int(date_end_o.split(".")[0])) + datetime.timedelta(1)

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
            "attachment; filename='Статистика_Использование_Емкостей_{0}-{1}.xls'".format(date_start_o, date_end_o), tr)

        per = "{0} - {1}".format(date_start_o, date_end_o)

        ws = wb.add_sheet("Общее использование емкостей")
        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            per
        ]

        import datetime
        date_start_o = datetime.date(int(date_start_o.split(".")[2]), int(date_start_o.split(".")[1]),
                                     int(date_start_o.split(".")[0]))
        date_end_o = datetime.date(int(date_end_o.split(".")[2]), int(date_end_o.split(".")[1]),
                                   int(date_end_o.split(".")[0])) + datetime.timedelta(1)

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

        labs = Podrazdeleniya.objects.filter(isLab=True)
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
        usrs = DoctorProfile.objects.filter(podrazdeleniye__isLab=True).order_by("podrazdeleniye__title")
        response['Content-Disposition'] = str.translate(
            "attachment; filename='Статистика_УЕТс_{0}-{1}.xls'".format(date_start_o, date_end_o), tr)

        ws = wb.add_sheet("УЕТы")
        row_num = 0

        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            "{0} - {1}".format(date_start_o, date_end_o)
        ]

        import datetime
        date_start_o = datetime.date(int(date_start_o.split(".")[2]), int(date_start_o.split(".")[1]),
                                     int(date_start_o.split(".")[0]))
        date_end_o = datetime.date(int(date_end_o.split(".")[2]), int(date_end_o.split(".")[1]),
                                   int(date_end_o.split(".")[0])) + datetime.timedelta(1)

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
                uet_tmp = 0
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
                uet_tmp = 0
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
