from collections import defaultdict

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required
from django.shortcuts import render
from users.models import Podrazdeleniya
from directions.models import Napravleniya, Issledovaniya, TubesRegistration, Tubes
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
    return render(request, 'statistic.html', {"labs": labs, "tubes": tubes, "podrs": podrs})


@csrf_exempt
@login_required
def statistic_xls(request):
    """ Генерация XLS """
    from directions.models import Issledovaniya
    import xlwt

    wb = xlwt.Workbook(encoding='utf-8')
    response = HttpResponse(content_type='application/ms-excel')
    if request.method == "POST":
        pk = request.POST["pk"]  # Первичный ключ
        tp = request.POST["type"]  # Тип статистики
        date_start_o = request.POST["date-start"]  # Начало периода
        date_end_o = request.POST["date-end"]  # Конец периода
    else:
        pk = request.GET["pk"]  # Первичный ключ
        tp = request.GET["type"]  # Тип статистики
        date_start_o = request.GET["date-start"]  # Начало периода
        date_end_o = request.GET["date-end"]  # Конец периода

    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")  # Словарь для транслитерации
    tr = {ord(a): ord(b) for a, b in zip(*symbols)}  # Перевод словаря для транслита

    borders = xlwt.Borders()
    borders.left = xlwt.Borders.THIN
    borders.right = xlwt.Borders.THIN
    borders.top = xlwt.Borders.THIN
    borders.bottom = xlwt.Borders.THIN

    if tp == "lab":
        lab = Podrazdeleniya.objects.get(pk=int(pk))
        response['Content-Disposition'] = str.translate(
            "attachment; filename='Статистика_Лаборатория_{0}_{1}-{2}.xls'".format(lab.title.replace(" ", "_"),
                                                                                   date_start_o, date_end_o), tr)

        ws = wb.add_sheet("Выполненых анализов")

        font_style = xlwt.XFStyle()
        font_style.borders = borders
        row_num = 0
        row = [
            "Период: ",
            "{0} - {1}".format(date_start_o, date_end_o)
        ]

        import datetime
        date_start = datetime.date(int(date_start_o.split(".")[2]), int(date_start_o.split(".")[1]),
                                   int(date_start_o.split(".")[0]))
        date_end = datetime.date(int(date_end_o.split(".")[2]), int(date_end_o.split(".")[1]),
                                 int(date_end_o.split(".")[0])) + datetime.timedelta(1)

        for col_num in range(len(row)):
            if col_num == 0:
                ws.write(row_num, col_num, row[col_num], font_style)
            else:
                ws.write_merge(row_num, row_num, col_num, col_num+2, row[col_num], style=font_style)

        row_num += 1

        font_style = xlwt.XFStyle()
        font_style.borders = borders

        row = [
            (lab.title, 16000)
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num][0], font_style)
            ws.col(col_num).width = row[col_num][1]
            ws.write(row_num, col_num+1, "", font_style)

        row_num = 2
        row = [
            "Выполнено исследований",
            ""
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1
        font_style.borders = borders

        otds = {}
        otds_pat = {}
        import directions.models as d
        def all(iterable):
            for element in iterable:
                if not element:
                    return False
            return True

        for obj in directory.Researches.objects.filter(subgroup__podrazdeleniye__pk=lab.pk, direction_id__isnull=False):
            for iss in Issledovaniya.objects.filter(research__pk=obj.pk, time_confirmation__isnull=False,
                                                    time_confirmation__range=(date_start, date_end)):
                if all(["гемолиз" in y.value.lower() for y in d.Result.objects.filter(issledovaniye=iss)]) or all(
                        ["забор" in y.value.lower() for y in d.Result.objects.filter(issledovaniye=iss)]) or all(
                        ["тест" in y.value.lower() for y in d.Result.objects.filter(issledovaniye=iss)]) or all(
                        ["неправ" in y.value.lower() for y in d.Result.objects.filter(issledovaniye=iss)]) or all(
                        ["-" in y.value for y in d.Result.objects.filter(issledovaniye=iss)]):
                    continue
                if iss.napravleniye.doc.podrazileniye.pk not in otds:
                    otds[iss.napravleniye.doc.podrazileniye.pk] = defaultdict(lambda: 0)
                otds[iss.napravleniye.doc.podrazileniye.pk][obj.pk] += 1
                if any([y.get_is_norm() in ["maybe", "not_normal"] for y in
                        d.Result.objects.filter(issledovaniye=iss)]):
                    if iss.napravleniye.doc.podrazileniye.pk not in otds_pat:
                        otds_pat[iss.napravleniye.doc.podrazileniye.pk] = defaultdict(lambda: 0)
                    otds_pat[iss.napravleniye.doc.podrazileniye.pk][obj.pk] += 1

        style = xlwt.XFStyle()
        style.borders = borders
        font = xlwt.Font()
        font.bold = True
        style.font = font
        from operator import itemgetter
        for otdd in Podrazdeleniya.objects.filter(pk__in=[x for x in otds.keys()]):
            row_num += 2
            row = [
                otdd.title,
                ""
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
            for row in reversed(sorted(rows, key=itemgetter(1))):
                row_num += 1
                for col_num in range(len(row)):
                    ws.write(row_num, col_num, row[col_num], font_style)

        ws = wb.add_sheet("Паталогии")
        row_num = 0
        row = [
            "Период: ",
            "{0} - {1}".format(date_start_o, date_end_o)
        ]

        for col_num in range(len(row)):
            if col_num == 0:
                ws.write(row_num, col_num, row[col_num], font_style)
            else:
                ws.write_merge(row_num, row_num, col_num, col_num+2, row[col_num], style=font_style)

        row_num = 1
        row = [
            (lab.title, 16000),
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num][0], font_style)
            ws.col(col_num).width = row[col_num][1]
            ws.write(row_num, col_num+1, "", font_style)

        font_style = xlwt.XFStyle()
        font_style.borders = borders

        row_num = 2
        row = [
            "Паталогии",
            ""
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

        for otdd in Podrazdeleniya.objects.filter(pk__in=[x for x in otds_pat.keys()]):
            row_num += 2
            row = [
                otdd.title,
                ""
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], style=style)
            rows = []
            for obj in directory.Researches.objects.filter(pk__in=[x for x in otds_pat[otdd.pk].keys()]):
                row = [
                    obj.title,
                    otds_pat[otdd.pk][obj.pk],
                ]
                rows.append(row)
            for row in reversed(sorted(rows, key=itemgetter(1))):
                row_num += 1
                for col_num in range(len(row)):
                    ws.write(row_num, col_num, row[col_num], font_style)

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
            (str(Napravleniya.objects.filter(doc__podrazileniye=otd,
                                             data_sozdaniya__range=(date_start_o, date_end_o)).count()), 3000),
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num][0], font_style)
            ws.col(col_num).width = row[col_num][1]

        row_num += 1
        iss = Issledovaniya.objects.filter(napravleniye__doc__podrazileniye=otd,
                                           napravleniye__data_sozdaniya__range=(date_start_o, date_end_o),
                                           time_confirmation__isnull=False)
        naprs = len(set([v.napravleniye.pk for v in iss]))
        row = [
            u"Завершенных",
            str(naprs)
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    elif tp == "tube":
        pass
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
            c = Issledovaniya.objects.filter(research__subgroup__podrazdeleniye=lab, time_confirmation__isnull=False,
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
                c_get = TubesRegistration.objects.filter(issledovaniya__research__subgroup__podrazdeleniye=lab,
                                                         type__tube=tube, time_get__isnull=False,
                                                         time_get__range=(date_start_o, date_end_o)).count()
                c_rec = TubesRegistration.objects.filter(issledovaniya__research__subgroup__podrazdeleniye=lab,
                                                         type__tube=tube, time_recive__isnull=False, notice="",
                                                         time_get__range=(date_start_o, date_end_o)).count()
                c_nrec = TubesRegistration.objects.filter(issledovaniya__research__subgroup__podrazdeleniye=lab,
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
        usrs = DoctorProfile.objects.filter(podrazileniye__isLab=True).order_by("podrazileniye__title")
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
            if usr.labtype == 0: continue
            researches_uets = {}
            iss = Issledovaniya.objects.filter(doc_save=usr, time_save__isnull=False,
                                               time_save__range=(date_start_o, date_end_o))
            for issledovaniye in iss:
                uet_tmp = 0
                if usr.labtype == 1:
                    uet_tmp = sum(
                        [v.uet_doc for v in directory.Fractions.objects.filter(research=issledovaniye.research)])
                else:
                    uet_tmp = sum(
                        [v.uet_lab for v in directory.Fractions.objects.filter(research=issledovaniye.research)])
                researches_uets[issledovaniye.pk] = {"uet": uet_tmp}
            iss = Issledovaniya.objects.filter(doc_confirmation=usr, time_confirmation__isnull=False,
                                               time_confirmation__range=(date_start_o, date_end_o))
            for issledovaniye in iss:
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
                usr.podrazileniye.title,
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
